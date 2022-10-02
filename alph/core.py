from functools import partial
from typing import Callable, Union

import altair as alt
import pandas as pd

from . import combo
from . import layers as ll
from . import layout
from .preproc import (
    PANDAS_DT_TYPES,
    PYTHON_DT_TYPES,
    get_non_serializable_datetime_type_columns,
)
from .util import normalise_pos

DEFAULT_COMBO_SIZE_SCALE_DOMAIN = (0, 25)
DEFAULT_COMBO_SIZE_SCALE_RANGE = ((2 * 3) ** 2, (2 * 90) ** 2)
DEFAULT_COMBO_INNER_GRAPH_SCALE_FACTOR = 0.6
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600


def alph(
    G,
    weight_attr=None,
    layout_fn: Union[Callable, None] = None,
    node_args=None,
    edge_args=None,
    #  combo
    combo_group_by: Union[str, list, tuple] = None,
    combo_node_additional_attrs: Union[dict, None] = None,
    combo_layout_fn: Union[dict, Callable] = None,
    combo_node_args=None,
    combo_edge_args=None,
    combo_empty_attr_action="drop",
    combo_size_scale_domain=DEFAULT_COMBO_SIZE_SCALE_DOMAIN,
    combo_size_scale_range=DEFAULT_COMBO_SIZE_SCALE_RANGE,
    combo_inner_graph_scale_factor=DEFAULT_COMBO_INNER_GRAPH_SCALE_FACTOR,
    # data args
    non_serializable_datetime_format="%d %b %Y",
    # main viz args
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
    prop_kwargs=None,
    padding=None,
):
    """Plot NetworkX Graph with altair

    :param G:                               Graph to visualise
    :param weight_attr:                     Name of the weight attribute on graph edges, if weighted
    :param layout_fn:                       Optional node position function, taking a graph as input, and returning
                                            a networkx "pos"-style structure, structured as
                                            {"a_node_id": array([x,y]), ...} - where -1 <= x|y <= 1
                                            attribute for a weighted network
    :param node_args:                       Args to pass to node layer
    :param edge_args:                       Args to pass to edge layer
    :param combo_group_by:                  Name of node attribute to use for combo grouping
    :param combo_empty_attr_action:         What to do with nodes that have an empty value for the combo_group_by
                                            attribute:
                                            - 'drop' drops them
                                            - 'group' groups them into a shared 'empty category' combo
                                            - 'promote' turns each node into a combo network node
    :param combo_size_scale_domain:         Lower/upper bound of num nodes to apply to combo node size range
    :param combo_size_scale_range:          Combo node size range
    :param combo_inner_graph_scale_factor   Scale down inner graph to fit inside combo nodes by this
                                            factor - normally < 1
    :param non_serializable_datetime_format: Format string for datetime and other temporal types that may
                                            appear in the dataset and trip up Altair
    :param width:                           Figure width (px)
    :param height:                          Figure height (px)
    :param prop_kwargs:                     Additional figure layer properties, for example title
    :param padding:                         Padding inside figure edges. No node centres will be placed outside
                                            this boundary. As well as aesthetically, this is useful for ensuring
                                            nodes / captions stay inside the figure frame.
    """

    G = G.copy()
    is_combo = bool(combo_group_by)
    # pos_args = pos_args or {}
    # combo_pos_args = combo_pos_args or {}
    assert (layout_fn is None) or callable(layout_fn)
    assert (combo_layout_fn is None) or callable(combo_layout_fn)

    node_args, edge_args = node_args or {}, edge_args or {}
    combo_node_args, combo_edge_args = (
        combo_node_args or {},
        combo_edge_args or {},
    )

    # Helper to bring pos co-ordinates to width / height canvas. altair can
    # do this for us anyway, however doing it ourselves, explicitly, means we don't
    # get repeatedly caught up in pos to altair mapping wrangles. Furthermore, exact
    # dimensions of pos aren't deterministic as some / many sims aren't deterministic
    # - e.g. annealing, force / energy functions with randomness etc.
    pos_to_altair_coords = partial(
        normalise_pos,
        range=[0, min(width, height)],
        aspect_ratio=width / height,
        padding=padding,
    )

    #  nx_altair is less tolerant of pandas date types than altair, and needs some help
    # TODO: do this without converting to dataframe
    #  TODO: tidy up nesting levels, generalise....
    node_attrs_df = pd.DataFrame([node[1] for node in G.nodes(data=True)])
    non_serializable_attrs = get_non_serializable_datetime_type_columns(
        node_attrs_df,
        types=PYTHON_DT_TYPES + PANDAS_DT_TYPES,
        ignore_pandas_dt_cols=False,
        ignore_na=False,
    )
    if non_serializable_attrs:
        if non_serializable_datetime_format:
            for _, d in G.nodes(data=True):
                for attr in non_serializable_attrs:
                    if pd.isnull(d.get(attr)):
                        d[attr] = None  # NaT is still a dt type
                    elif hasattr(d[attr], "strftime"):
                        d[attr] = d[attr].strftime(non_serializable_datetime_format)
                    else:
                        # timedelta and pd.Timedelta don't have strftime
                        d[attr] = str(d[attr])

        else:
            raise ValueError(
                f"The following col(s) had non-serializable datetime types: {non_serializable_attrs}"
            )

    if is_combo:
        layout_fn = layout_fn or partial(
            layout.default_intra_combo_layout, weight_attr=weight_attr
        )

        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G,
            combo_group_by=combo_group_by,
            combo_node_additional_attrs=combo_node_additional_attrs,
            weight_attr=weight_attr,
            empty_combo_attr_action=combo_empty_attr_action,
            # empty_combo_attr_fill_source=combo_empty_attr_fill_source,
            # weight_threshold=None,
            # include_edgeless_combo_nodes=True,
        )

        combo_pos = (
            combo_layout_fn(inter_combo_G)
            if combo_layout_fn
            else layout.default_inter_combo_layout(
                inter_combo_G, weight_attr=weight_attr
            )
        )
        combo_pos = pos_to_altair_coords(combo_pos)

        final_layers = ll.generate_combo_layers(
            inter_combo_G,
            intra_combo_Gs,
            intra_combo_layout_fn=layout_fn,
            nodes_layer=ll.nodes_layer(
                **{
                    **dict(size=50, fill=alt.value("black")),
                    **node_args,
                }
            ),
            edges_layer=ll.default_intra_combo_edges_layer(
                weight_attr=weight_attr, **edge_args
            ),
            combo_pos=combo_pos,
            combo_nodes_layer=ll.default_combo_nodes_layer(**combo_node_args),
            combo_edges_layer=ll.default_combo_edges_layer(
                weight_attr=weight_attr, **combo_edge_args
            ),
            size_scale_domain=combo_size_scale_domain,
            size_scale_range=combo_size_scale_range,
            inner_graph_scale_factor=combo_inner_graph_scale_factor,
        )

    else:
        if layout_fn:
            pos = layout_fn(G)
        else:
            pos = layout.default_network_layout(G, weight_attr=weight_attr)

        pos = pos_to_altair_coords(pos)

        final_layers = ll.apply_layers(
            [
                ll.edges_layer(weight_attr=weight_attr, **edge_args),
                ll.default_nodes_layer(**node_args),
            ],
            G,
            pos,
        )

    return (
        alt.layer(*final_layers).properties(
            width=width,
            height=height,
            **(prop_kwargs or {}),
        )
        # see https://altair-viz.github.io/user_guide/scale_resolve.html
        .resolve_scale(
            color="independent",
            size="independent",
            opacity="independent",
            strokeWidth="independent",
            fill="independent",
        )
        # configure_* statements break ability to layer charts
        # configure_axis not needed as we set this for every axis
        #   .configure_axis(grid=True, title=None, ticks=False, domain=False, labels=False)
        #   .configure_view(strokeWidth=0)  #  remove border
    )
