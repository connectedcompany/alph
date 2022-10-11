import altair as alt
import networkx as nx
import numpy as np
import pandas as pd

from . import combo
from .util import normalise_pos

DEFAULT_NODE_SIZE = (2 * 10) ** 2
COMBO_SIZE_ATTR_NAME = "__combo_size"


def _interpolate_node_size_from_num_nodes(G, num_nodes_range, size_range):
    assert len(num_nodes_range) == len(size_range) == 2
    return np.interp(G.number_of_nodes(), num_nodes_range, size_range)


def _invisible_axis():
    return alt.Axis(
        title="",
        grid=False,
        labels=False,
        ticks=False,
        domain=False,
    )


def _size_to_r(size):
    return (size**0.5) / 2


def _optional_str_or_seq_arg(val):
    return [val] if isinstance(val, str) else (val or [])


def _wrap_altair_numeric_value(val):
    if isinstance(val, (int, float)):
        return alt.value(val)
    return val


def _wrap_altair_str_value(val):
    if isinstance(val, str):
        return alt.value(val)
    return val


def _nx_nodes_to_pandas(G, pos):
    attributes = set(["x", "y"] + [k for n in G.nodes() for k in G.nodes[n].keys()])

    df = pd.DataFrame(index=G.nodes(), columns=attributes)

    for n in G.nodes:
        data = dict(x=pos[n][0], y=pos[n][1], **G.nodes[n])
        df.loc[n] = data

    return df


def _nx_edges_to_pandas(G, pos, **kwargs):
    attributes = set(
        ["source", "target", "x", "y", "edge", "pair"]
        + [k for e in G.edges() for k in G.edges[e].keys()]
    )
    attributes = list(set(attributes))

    df = pd.DataFrame(index=range(G.size() * 2), columns=attributes)

    for i, e in enumerate(G.edges):
        idx = i * 2

        d1 = dict(
            edge=i,
            source=e[0],
            target=e[1],
            pair=e,
            x=pos[e[0]][0],
            y=pos[e[0]][1],
            **G.edges[e],
        )

        d2 = dict(
            edge=i,
            source=e[0],
            target=e[1],
            pair=e,
            x=pos[e[1]][0],
            y=pos[e[1]][1],
            **G.edges[e],
        )

        df.loc[idx] = d1
        df.loc[idx + 1] = d2

    return df


def nodes_layer(
    size=DEFAULT_NODE_SIZE,
    tooltip_attrs=None,
    fill="#000",
    opacity=1,
    stroke="#565656",
    strokeWidth=0,
    halo_offset=None,
    halo_opacity=1,
    halo_stroke="#343434",
    halo_strokeWidth=2,
    label_attr=None,
    label_offset=6,
    label_size=10,
    label_color="black",
    label_text_align="center",
):
    """Note the use of r rather than size - more in comment below"""
    size = _wrap_altair_numeric_value(size)
    fill = _wrap_altair_str_value(fill)
    opacity = _wrap_altair_numeric_value(opacity)
    stroke = _wrap_altair_str_value(stroke)
    strokeWidth = _wrap_altair_numeric_value(strokeWidth)
    halo_opacity = _wrap_altair_numeric_value(halo_opacity)
    halo_stroke = _wrap_altair_str_value(halo_stroke)
    halo_strokeWidth = _wrap_altair_numeric_value(halo_strokeWidth)

    tooltip_attrs = _optional_str_or_seq_arg(tooltip_attrs)

    def inner(G, pos):
        data = _nx_nodes_to_pandas(G, pos)

        if isinstance(size, dict):  #  alt.value
            data["__node_size"] = size["value"]
        elif isinstance(size, str):
            data["__node_size"] = data[size]
        elif isinstance(size, alt.Size):
            # assert size[]
            # assert isinstance(size["shorthand"], str)
            if size["shorthand"] != alt.Undefined:
                if isinstance(size["scale"], alt.Scale):
                    assert size["scale"]["type"] in [
                        alt.Undefined,
                        "linear",
                    ], "Only linear supported ATM"
                    assert isinstance(size["scale"]["domain"], (list, tuple, np.array))
                    assert isinstance(size["scale"]["range"], (list, tuple, np.array))
                    domain, range = size["scale"]["domain"], size["scale"]["range"]
                    data["__node_size"] = data[size["shorthand"]].apply(
                        lambda x: np.interp(x, domain, range)
                    )
                else:
                    data["__node_size"] = data[size["shorthand"]]
            elif size["field"] != alt.Undefined:
                data["__node_size"] = data[size["field"]]
            else:
                raise ValueError(f"Unsupported size structure: {size}")

        data["__node_r"] = data["__node_size"].apply(_size_to_r)

        if halo_offset is not None:
            assert isinstance(halo_offset, (int, float))
            data["__node_halo_size"] = (
                # TODO: halo offset and stoke width to data
                2
                * (data["__node_r"] + halo_offset + halo_strokeWidth["value"] // 2)
            ) ** 2

        if label_attr is not None:
            assert isinstance(label_offset, (int, float))
            # TODO: label offset to data
            data["__y_label"] = (
                data["y"]
                - data["__node_r"]
                - label_offset
                - (0 if halo_offset is None else halo_offset)
            )

        chart = alt.Chart(data)
        res = None

        if halo_offset is not None:
            border = chart.mark_circle().encode(
                x=alt.X("x", axis=_invisible_axis()),
                y=alt.Y("y", axis=_invisible_axis()),
                size=alt.Size("__node_halo_size", scale=None, legend=None),
                fill=alt.value("rgba(0,0,0,0"),
                opacity=halo_opacity,
                strokeWidth=halo_strokeWidth,
                stroke=halo_stroke,
            )
            res = border

        nodes = chart.mark_circle().encode(
            x=alt.X("x", axis=_invisible_axis()),
            y=alt.Y("y", axis=_invisible_axis()),
            size=size,
            fill=fill,
            opacity=opacity,
            tooltip=tooltip_attrs,
            strokeWidth=strokeWidth,
            stroke=stroke,
        )
        res = res + nodes if res else nodes

        if label_attr:
            labels = chart.mark_text(
                baseline="middle",
                size=label_size,
                color=label_color,
                align=label_text_align,
            ).encode(
                x=alt.X("x", axis=_invisible_axis()),
                y=alt.Y("__y_label:Q", axis=_invisible_axis()),
                text=label_attr,
            )
            res += labels

        return res

    return inner


def edges_layer(
    weight_attr="weight",
    color="#606060",
    opacity=None,
    strokeWidth=None,
):
    color = _wrap_altair_str_value(color)
    strokeWidth = _wrap_altair_numeric_value(strokeWidth)
    opacity = _wrap_altair_numeric_value(opacity)

    def inner(G, pos):
        nonlocal opacity, strokeWidth

        if G.number_of_edges() == 0:
            return None

        if opacity is None:
            opacity = (
                alt.Size(weight_attr, scale=alt.Scale(range=[0.3, 1]), legend=None)
                if weight_attr
                else alt.value(1.0)
            )
        if strokeWidth is None:
            strokeWidth = (
                alt.Size(weight_attr, scale=alt.Scale(range=[0.1, 5]), legend=None)
                if weight_attr
                else alt.value(2.0)
            )

        data = _nx_edges_to_pandas(G, pos)
        return (
            alt.Chart(data)
            .mark_line()
            .encode(
                **dict(
                    x=alt.X("x", axis=_invisible_axis()),
                    y=alt.Y("y", axis=_invisible_axis()),
                    detail="edge",
                    opacity=opacity,
                    strokeWidth=strokeWidth,
                    color=color,
                )
            )
        )

    return inner


########
# helpers
########


def apply_layers(layers, G, pos):
    res = []
    layers = [layers] if callable(layers) else layers

    for layer in filter(None, layers):
        if callable(layer):
            layer = layer(G, pos)
        elif not isinstance(layer, alt.Chart):
            raise ValueError(f"Layer must be a function or a Chart - was {type(layer)}")

        if layer is not None:
            res.append(layer)

    return res


########
# combo
########


def generate_combo_layers(
    inter_combo_G,
    intra_combo_Gs_by_cat,
    combo_pos,
    combo_nodes_layer,
    combo_edges_layer,
    intra_combo_layout_fn,
    nodes_layer,
    edges_layer,
    size_scale_domain,
    size_scale_range,
    inner_graph_scale_factor,
):
    res = []

    # add combo edges layer
    res.extend(apply_layers(combo_edges_layer, G=inter_combo_G, pos=combo_pos))

    # for each combo caegory
    # - render combo node
    # - render intra-combo graph

    for combo_val, G_intra_combo in intra_combo_Gs_by_cat.items():
        if G_intra_combo.number_of_nodes() == 0:
            print(f"Skipping nodeless graph for combo category {combo_val}")
            continue

        assert (
            combo_val in combo_pos
        ), f"Expected combo cat {combo_val} to be in combo pos {combo_pos}"

        x_combo, y_combo = tuple(combo_pos[combo_val])

        if G_intra_combo.number_of_nodes() == 1 and (
            not combo_val or combo_val.startswith(combo.EMPTY_COMBO_VALUE_PLACEHOLDER)
        ):
            res.extend(
                apply_layers(
                    [edges_layer, nodes_layer],
                    G=G_intra_combo,
                    pos={[n for n in G_intra_combo.nodes()][0]: (x_combo, y_combo)},
                )
            )

        else:
            G_combo = nx.Graph()
            G_combo.add_node(combo_val, **inter_combo_G.nodes[combo_val])
            combo_size = _interpolate_node_size_from_num_nodes(
                G_intra_combo,
                num_nodes_range=size_scale_domain,
                size_range=size_scale_range,
            )
            nx.set_node_attributes(G_combo, combo_size, COMBO_SIZE_ATTR_NAME)

            res.extend(
                apply_layers(
                    combo_nodes_layer, G=G_combo, pos={combo_val: (x_combo, y_combo)}
                )
            )

            # We now need to lay out the intra-combo graph, and fit it inside the combo;
            #  to do this, we need to
            # - figure out the combo size, and hence radius
            #  - invoke the intra-combo graph layout function to get the pos
            # - normalise the pos to -1, 1
            # - scale pos by a fraction of the combo radius, to fit inside the combo node
            combo_r = _size_to_r(combo_size)

            pos = intra_combo_layout_fn(G_intra_combo)
            pos = normalise_pos(pos, range=[-1, 1])
            pos = {
                id: (
                    x_combo + xy[0] * combo_r * inner_graph_scale_factor,
                    y_combo + xy[1] * combo_r * inner_graph_scale_factor,
                )
                for id, xy in pos.items()
            }

            res.extend(apply_layers([edges_layer, nodes_layer], G_intra_combo, pos))

    return res


########
## skins
########


def default_nodes_layer(**kwargs):
    return nodes_layer(
        **{
            **dict(
                size=10**2,
                halo_offset=None,
                label_offset=12,
            ),
            **kwargs,
        }
    )


def default_intra_combo_edges_layer(weight_attr, **kwargs):
    return edges_layer(
        **{
            **dict(
                weight_attr=weight_attr,
                color="black",
                strokeWidth=alt.Size(
                    weight_attr,
                    scale=alt.Scale(range=[0.3, 1]),
                    legend=None,
                ),
                opacity=alt.Size(
                    weight_attr,
                    scale=alt.Scale(range=[0.5, 1]),
                    legend=None,
                ),
            ),
            **kwargs,
        }
    )


def default_combo_edges_layer(weight_attr, **kwargs):
    return edges_layer(
        **{
            **dict(
                weight_attr=weight_attr,
                color="#606060",
                opacity=alt.Size(
                    weight_attr, scale=alt.Scale(range=[0.3, 1]), legend=None
                ),
                strokeWidth=alt.Size(
                    weight_attr, scale=alt.Scale(range=[0.1, 10]), legend=None
                ),
            ),
            **kwargs,
        }
    )


def default_combo_nodes_layer(**kwargs):
    return nodes_layer(
        **{
            **dict(
                size=alt.Size(
                    COMBO_SIZE_ATTR_NAME,
                    scale=None,
                    legend=None,
                ),
                fill=alt.value("#d9d9d9"),
                stroke=alt.value("#565656"),
                strokeWidth=alt.value(3),
                label_offset=12,
            ),
            **kwargs,
        }
    )
