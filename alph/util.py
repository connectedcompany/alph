from functools import partial

import networkx as nx
import numpy as np
import pandas as pd

DEFAULT_POS_RANGE = (-1, 1)


################
# Network creation and manipulation
################


def nx_graph_from_edges(
    df: pd.DataFrame,
    source="source",
    target="target",
    node_attrs: dict = None,
    edge_attr="all",
    weight_attr=None,
    weight_threshold=None,
    add_missing_node_attr_nodes: bool = False,
    drop_isolated_nodes=False,
):
    """
    Given a dataframe, generate a networkx graph
    :param edge_attr:                       edge attributes to include - or 'all'
    :param add_missing_node_attr_nodes:     whether to add any attrs in node_attrs that are not in edges
    """
    if source not in df.columns or target not in df.columns:
        raise ValueError(f"Missing source and / or target columns {source} / {target}")
    node_attrs = node_attrs or {}

    if weight_threshold and not weight_attr:
        raise ValueError("Need a weight attribute for weight threshold")
    if edge_attr == "all":
        edge_attr = [
            c for c in df.columns if c not in [source, target]
        ] or None  #  nx doesn't like []

    G = nx.from_pandas_edgelist(df, source=source, target=target, edge_attr=edge_attr)
    if add_missing_node_attr_nodes:
        G.add_nodes_from([(k, v) for k, v in node_attrs.items()])
    else:
        nx.set_node_attributes(G, node_attrs)

    if weight_threshold:
        G.remove_edges_from(
            [(s, t) for s, t, w in G.edges(data=weight_attr) if w < weight_threshold]
        )

    if drop_isolated_nodes:
        G.remove_nodes_from(list(nx.isolates(G)))

    return G


def normalise_pos(pos, range=None, aspect_ratio=None, padding=None):
    """
    Given a networkx-style pos structure - a dict like
    {node_id: (x,y)} - return normalised x, y coord values
    according to given range

    :param range:        range for x and y coords
    :param aspect_ratio: usual width / height ratio - default 1
    :param padding       how much space to leave around the edges
                         in range coords
    """

    range = range or DEFAULT_POS_RANGE
    assert (len(range) == 2) and (range[0] <= range[1])
    if not pos:
        return {}
    if not isinstance(pos, dict):
        raise ValueError(f"Only nx pos-like dict structures supported")

    if padding:
        range = (range[0] + padding, range[1] - padding)

    xy_vals = [v for xy in pos.values() for v in xy]

    upper_bound = max(map(abs, xy_vals))
    lower_bound = -upper_bound if any([n < 0 for n in xy_vals]) else 0

    # interpoloate between bounds
    mapper = partial(np.interp, xp=[lower_bound, upper_bound], fp=range)

    res = {k: tuple(map(mapper, xy)) for k, xy in pos.items()}
    if aspect_ratio is not None:
        res = {k: (xy[0] * aspect_ratio, xy[1]) for k, xy in res.items()}

    return res


def generate_interaction_graph(
    nodes,
    mean_time_between_interactions,
    edge_weight_attr="weight",
    edge_weights="expected_time_to_interaction",
    how="scale_free",
    cast_to=nx.Graph,
    seed=None,
):
    """
    :param nodes: number of nodes, or node names
    :param mean_time_between_interactions: time units between interactions
    :param cast_to: we get a MultiDiGraph if we don't cast
    """
    assert how == "scale_free"
    assert edge_weights in [
        "expected_time_to_interaction",
        "prob_interaction_per_unit_time",
    ]
    if not nodes:
        return nx.Graph()
    np_random = np.random if seed is None else np.random.default_rng(seed)

    n_nodes = nodes if isinstance(nodes, int) else len(nodes)

    # directed scale free graph returns at least 3 nodes
    if n_nodes == 1:
        G = nx.Graph()
        G.add_node(0 if isinstance(nodes, int) else nodes[0])
    elif n_nodes == 2:
        G = nx.Graph([(0, 1)])
    else:
        G = nx.directed.scale_free_graph(n=n_nodes, seed=seed)

    if cast_to:
        G = cast_to(G)

    # assumptions in our model:
    # - interaction probabilites independent of node degree
    # - interactions are poisson distributed; hence time between poisson events is exponential
    # we optionally convert expected time to interaction for each pair of nodes (i.e. edge)
    # to probabilities, by looking up the value of the CDF (1 - exp(-lambda * x)) - this is
    # by analogy with failure analysis; the failure (or interaction) rate isn't a probability,
    # as can be > 1 (e.g. time to failure = 0.5, rate = 1/0.5=2).
    # See e.g. http://nomtbf.com/2016/06/measures-failure-rate-probability-failure-different/
    edge_weights_dict = {}
    for edge in G.edges:
        time_between_interations = np_random.exponential(mean_time_between_interactions)
        if edge_weights == "prob_interaction_per_unit_time":
            rate = 1 / time_between_interations
            prob_per_unit_time = 1 - np.exp(-rate * 1)
            edge_weights_dict[edge] = prob_per_unit_time
        else:
            edge_weights_dict[edge] = time_between_interations

    nx.set_edge_attributes(G, edge_weights_dict, edge_weight_attr)

    if isinstance(nodes, int):
        return G

    # name the nodes
    node_mapping = dict(zip(range(n_nodes), nodes))
    return nx.relabel_nodes(G, node_mapping)


def is_lab_notebook():
    import re

    import psutil

    return any(re.search("jupyter-lab", x) for x in psutil.Process().parent().cmdline())


def set_altair_renderer():
    """
    To facilitate generating GitHub-friendly previews, sense whether we're in a
    jupyterlab environment and if so set mimetype renderer. This is a bit hacky,
    but only needs to work for the maintairer for now, and not get in the way for others.
    """

    if is_lab_notebook():
        import altair as alt

        alt.renderers.enable("mimetype")  # or jupyterlab - should be synonymous
