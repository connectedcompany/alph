import networkx as nx
import numpy as np
import pandas as pd

from .util import nx_graph_from_edges

EMPTY_COMBO_VALUE_PLACEHOLDER = "__combo_empty"
COMBO_PROMOTED_NODE_ATTR = "__combo_promoted"
COMBO_GROUP_VALUE_ATTR = "__combo_group_value"
NEW_COMBO_EDGE_WEIGHT_AGG_ATTR_NAME = "weight"


def combo_graph_mapper(
    G,
    combo_group_by,
    weight_attr=None,
    combo_edge_weight_agg_attr=None,
    combo_edge_weight_threshold=None,
    combo_node_additional_attrs: dict = None,
    combo_edge_agg_attrs: dict = None,
    empty_combo_attr_action="drop",
    empty_combo_attr_fill_source="",  #  None is problematic as key, for display etc
    include_edgeless_combo_nodes=True,
):
    """
    :param combo_group_by:              Attribute to group nodes by when forming combo nodes
    :param weight_attr:                 Edge weight attr, if one exists, and combo_edge_weight_agg_attr not specificed,
                                        will be used for aggregation; otherwise
    :param combo_edge_weight_agg_attr:  How to aggregate node edges that span combo groups; overrides weight_attr, can use values
                                        given via combo_edge_agg_attrs. If not set and weight_attr not given, falls back to simple edge count.
    :param combo_edge_agg_attrs:        Pandas groupby-style dict, describing how to aggregate edge attributes that span nodes -
                                        for example {"combo_edge_attr_name": ("edge_attr_name", "sum")}
    :param empty_combo_attr_action:     What to do for nodes without combo attr:
                                        - "drop" drops them
                                        - "group" treats empty combo attr as own category
                                        - "promote" creates a combo category for each item
    """

    assert (
        isinstance(combo_group_by, str) or len(combo_group_by) == 1
    ), "for now, just one layer"
    assert empty_combo_attr_action in ["drop", "group", "promote"]

    combo_edge_weight_agg_attr = (
        combo_edge_weight_agg_attr or weight_attr or NEW_COMBO_EDGE_WEIGHT_AGG_ATTR_NAME
    )
    combo_edge_agg_attrs = combo_edge_agg_attrs or {}
    if combo_edge_weight_agg_attr not in combo_edge_agg_attrs:
        combo_edge_agg_attrs.update(
            {
                combo_edge_weight_agg_attr: (weight_attr, "sum")
                if weight_attr
                else ("target", "count")
            }
        )

    combo_group_by = (
        combo_group_by if isinstance(combo_group_by, str) else combo_group_by[0]
    )

    combo_node_additional_attrs = combo_node_additional_attrs or {}

    G = G.copy()

    # drop mode means we ditch noddes without combo attr
    if empty_combo_attr_action == "drop":
        G.remove_nodes_from(
            [n for n, val in G.nodes(data=combo_group_by) if pd.isnull(val)]
        )

    # whereas promote means we need a mapping
    promoted_nodes = {}
    if empty_combo_attr_action == "promote":
        for n, val in G.nodes(data=combo_group_by):
            if pd.isnull(val):
                placeholder_id = f"{EMPTY_COMBO_VALUE_PLACEHOLDER}_{n}"
                G.nodes[n][COMBO_GROUP_VALUE_ATTR] = placeholder_id
                G.nodes[n][COMBO_PROMOTED_NODE_ATTR] = True
                promoted_nodes[placeholder_id] = n
            else:
                G.nodes[n][COMBO_GROUP_VALUE_ATTR] = val

    else:
        for n, val in G.nodes(data=combo_group_by):
            G.nodes[n][COMBO_GROUP_VALUE_ATTR] = (
                val if pd.notnull(val) else EMPTY_COMBO_VALUE_PLACEHOLDER
            )

    # store all unique combo values for convenience
    combo_values_by_node = {n: val for n, val in G.nodes(data=COMBO_GROUP_VALUE_ATTR)}
    combo_values_set = set(combo_values_by_node.values())

    #  create a df of edges from original graph, to be aggregated to combo edges
    df = nx.to_pandas_edgelist(G)
    df["source"] = df["source"].map(combo_values_by_node)
    df["target"] = df["target"].map(combo_values_by_node)

    #  ensure we don't double count edges
    df["source"], df["target"] = np.where(
        df["source"] <= df["target"],
        (df["source"], df["target"]),
        (df["target"], df["source"]),
    )

    # aggreagate combo edges
    combo_edge_selector = df["source"] != df["target"]
    combo_edges = (
        df[combo_edge_selector]
        .groupby(["source", "target"], dropna=False)
        .agg(**combo_edge_agg_attrs)
        .reset_index()
    )

    # create inter-combo graph
    inter_combo_G_nodes = (
        combo_values_set
        if include_edgeless_combo_nodes
        else set(combo_edges["source"].tolist() + combo_edges["target"].tolist())
    )

    inter_combo_G = nx_graph_from_edges(
        combo_edges,
        node_attrs={
            id: {
                **combo_node_additional_attrs.get(id, {}),
                **({COMBO_PROMOTED_NODE_ATTR: True} if id in promoted_nodes else {}),
            }
            for id in inter_combo_G_nodes
        },
        weight_attr=combo_edge_weight_agg_attr,
        weight_threshold=combo_edge_weight_threshold,
        add_missing_node_attr_nodes=True,  # want combo nodes even if they don't have any edges
    )

    # create intra-combo graphs
    intra_combo_Gs = {}
    for val in combo_values_set:
        G_val = G.copy()
        G_val.remove_nodes_from(
            [n for n, v in combo_values_by_node.items() if v != val]
        )
        G_val.remove_edges_from(
            [
                (s, t)
                for s, t in G_val.edges()
                if combo_values_by_node.get(s) != val
                or combo_values_by_node.get(t) != val
            ]
        )

        intra_combo_Gs[val] = G_val

    return inter_combo_G, intra_combo_Gs
