# **gr**alt

A network visualisation library using [Altair](https://altair-viz.github.io/) for declarative, data driven renderering.

## Features

- plot any NetworkX Graph
- support for any Python layout function returning a NetworkX `pos`
  structure
- Altair-style data driven node and edge decoration - size,
  color, stroke, opacity, scales, conditions and more
- convenience args for node labels, halos
- 1-level combo node support

## How it works

1. Generate a nx Graph
2. Pick a layout
3. Define node and edge appearance attributes
4. Plots layered nodes + edges

## Usage

Simply call the `g_viz` function with desired options.

Minimally, given a weighted network G:

```
from cocolib.viz.charts.network import g_viz

G = ...
g_viz(G, weight_attr="weight")
```

## Examples

See [`examples.ipynb`](./examples.ipynb).

## API

### Supported layout functions

- [NetworkX layouts](https://networkx.org/documentation/stable/reference/drawing.html#module-networkx.drawing.layout): Spring, Fruchterman-Reingold, etc
- NetworkX-wrapped [graphviz layouts](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_agraph.graphviz_layout.html):
  dot, neato etc
- Gephi ForceAtlas2 based on the
  [forceatlas2 Python implementation](https://github.com/bhargavchippada/forceatlas2) -
  see [layout.py](./layout.py) for configuration options, and
  [this paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0098679)
  for more detail
- Any other that returns a NetworkX-style node positions dictionary

### Supported arguments

| arg                              | type(s)                | default              | description                                                                        |
| -------------------------------- | ---------------------- | -------------------- | ---------------------------------------------------------------------------------- |
| G                                | Networkx Graph         |                      | graph to visualise                                                                 |
| weight_attr                      | str                    |                      | edge weight attribute, for weighted graphs                                         |
| layout_fn                        | function               | ForceAtlas2          | Function that, given a graph, returns a layout                                     |
| node args                        | dict                   |                      | See below                                                                          |
| edge args                        | dict                   |                      | See below                                                                          |
| combo_group_by                   | str or list            |                      | Attribute to use to create grouped combo nodes                                     |
| combo_node_additional_attrs      | dict                   |                      | Attributes to add to combo node edges                                              |
| combo_layout_fn                  | function               | Fruchterman-Reingold | Layout function for combo nodes                                                    |
| combo_node_args                  | dict                   |                      | See below                                                                          |
| combo_edge_args                  | dict                   |                      | See below                                                                          |
| combo_empty_attr_action          | drop, group or promote | `drop`               | What to do with nodes that have an empty value for the combo_group_by attribute    |
| combo_size_scale_domain          | 2-item list or tuple   | `[0, 25]`            | Lower/upper bound of num nodes to apply to combo node size range                   |
| combo_size_scale_range           | 2-item list or tuple   | `[6^2, 180^2]`       | Combo node size range                                                              |
| combo_inner_graph_scale_factor   | float                  | `0.6`                | Scale down inner graph to fit inside combo nodes by this factor - normally <1      |
| non_serializable_datetime_format | str                    | `%d %b %Y`           | Format string for non-serialisable date / time types that otherwise break Altair   |
| width                            | int                    | `800`                | Figure width (px)                                                                  |
| height                           | int                    | `600`                | Figure height (px)                                                                 |
| padding                          | int                    |                      | Padding inside figure edges. No node centres will be placed outside this boundary. |

### Node args

| arg              | type(s)       | default   |
| ---------------- | ------------- | --------- |
| size             | int, alt.\*   | `400`     |
| tooltip_attrs    | list          |           |
| fill             | str, alt.\*   | `#000`    |
| opacity          | float, alt.\* | `1`       |
| stroke           | str, alt.\*   | `#565656` |
| strokeWidth      | int, alt.\*   | `0`       |
| halo_offset      | int           |           |
| halo_opacity     | float, alt.\* | `1`       |
| halo_stroke      | str, alt.\*   | `#343434` |
| halo_strokeWidth | int, alt.\*   | `2`       |
| label_attr       | str           |           |
| label_offset     | int           | `6`       |
| label_size       | int           | `10`      |
| label_color      | str           | `black`   |

### Edge args

| arg         | type(s)        | default                                                                            |
| ----------- | -------------- | ---------------------------------------------------------------------------------- |
| weight_attr | str            | `weight`                                                                           |
| color       | str, alt.\*    | `#606060`                                                                          |
| opacity     | float , alt.\* | `alt.Size(weight_attr, scale=alt.Scale(range=[0.3, 1])` if weighted, `1` otherwise |
| strokeWidth | int, alt.\*    | `alt.Size(weight_attr, scale=alt.Scale(range=[0.1, 5])` if weighted, `2` otherwise |

---

## Tips

- Get to know your layout algos - especially the 2-3 most used ones. They can have a dramatic
  effect on the results. A combination of FA2, Spring and Fruchterman is extremely versatile
  if set up right.
- Pass `seed` to layout functions where possible, for repeatable layouts
- Set padding to ensure node elements stay within figure boundaries

## Known limitations

- One combo level currently supported
- Node `size` attribute does not support all Altair options - currently only
  `alt.value` and `alt.Size` with linear `domain` and `range` scales. More will be
  supported as needed.

  The reason for this is the desire to not burden the user with
  having to calculate label and halo positions when node sizes vary.

  Will review this tradeoff based on in-use experience.

## See also

- [nx-altair](https://github.com/Zsailer/nx_altair) is a nice project that takes a slightly
  different approach to combining NetworkX and Altair for network viz.
