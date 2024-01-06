# **alph** - <b>al</b>tair for your gra<b>ph</b>

A Python library using [Altair](https://altair-viz.github.io/) for declarative, data-driven network visualisation.

<p align="center"><img alt="Alph graph" src="https://github.com/connectedcompany/alph/raw/main/examples/images/small_graph.png" width=60%/></p>

## Why

Tidy, legible graph visualisations can be elusive. Alph helps by bringing together effective styling, layout and pruning options from across the Python ecosystem.

## How it works

1. Get your data into a NetworkX Graph
2. Pick a network layout function, or bring your own node coordinates
3. Define node and edge style attributes
4. Plot using a simple function call

Best bet is probably to dive straight into the [examples](./examples/), and come back to the API documentation below as needed.

## Features

- plot any NetworkX Graph
- support for any layout expressed as a NetworkX `pos` structure (a dict like `{node_id: (x,y), ...}`)
- several readily accessible and tuneable layout functions (see [example](examples/3_layouts_gallery.ipynb))
- Altair-style data driven node and edge styling - size, colour, stroke, opacity, scales, conditionals and more
- convenience args for node labels, halos
- experimental 1-level "combo" node support

## Installation

### Minimal

```
pip install alph
```

### Recommended

1. for graphviz layout support, install graphviz on your platform - e.g. `brew install graphviz` on Mac,
   `sudo apt install libgraphviz-dev graphviz` on Colab, Debian, Ubuntu etc - or [download the installer](https://graphviz.org/download/)

2. Install alph with graphviz support:
   ```
   pip install "alph[graphviz]"
   ```
3. Install the ForceAtlas2 layout library from our fork, along with cython for speedup
   ```
   pip install cython "git+https://github.com/connectedcompany/forceatlas2.git"
   ```

> #### Why is the ForceAtlas2 install separate?
>
> [ForceAtlas2](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0098679) is a classic,
> user feedback led layout algorithm from the [Gephi](https://gephi.org/) team, and the [ForceAtlas2 library](https://github.com/bhargavchippada/forceatlas2)
> implementation is an excellent, performant Python port. There are two things to be aware of:
>
> 1. **GPL licence** - the ForceAtlas2 library, and some of the works it is derived from, are GPL licensed -
>    hence care is needed when distributing and linking to it. We thus intend to keep its install optional
>    long term. Since alph uses a plugin design for layout providers, this is straightforward for us to
>    accommodate, and maintain explicit separation for use cases where GPL is an issue.
>
> 2. **Our fork** - recently, releases of the library have been sporadic - though there is stated intent for
>    regular maintenance to resume. In the meantime, we've created a temporary fork to be able to roll in
>    changes. Currently, our fork incorporates a simple change that enables deterministic layouts.

## Usage

Simply call the `alph` function with desired options.

Minimally, given a weighted network G:

```
from alph import alph

G = ...
alph(G, weight_attr="weight")
```

## Examples

See [`examples`](./examples). Here's an overview:

- Some of the supported layouts (from the [layouts gallery example](examples/3_layouts_gallery.ipynb)):
  ![Layouts gallery](https://github.com/connectedcompany/alph/raw/main/examples/images/layouts.png)

- Use of geolocation coordinates for graph layout, (from the [flight routes example](examples/5_flight_routes.ipynb)):
  ![Geo-location based layout](https://github.com/connectedcompany/alph/raw/main/examples/images/flight_routes.png)

- Basic styling (from the [styling example](examples/2_styling.ipynb)):
  ![Styling](https://github.com/uros-r/alph/blob/colab-friendly-examples/examples/images/styling.png?raw=true)
- A styled interaction network (from the [dolphins example](examples/4_dolphins.ipynb)):
  ![Dolphins](https://github.com/connectedcompany/alph/raw/main/examples/images/dolphins.png)

- "Combo"-style layout (experimental) - category-driven node grouping with edge weight aggregation, from the [Les Mis example](examples/6_les_mis_experimental_combo.ipynb):
  ![Combo layout](https://github.com/connectedcompany/alph/raw/main/examples/images/combo.png)

---

# API

### Supported layout functions

- [NetworkX layouts](https://networkx.org/documentation/stable/reference/drawing.html#module-networkx.drawing.layout): Spring, Fruchterman-Reingold, etc
- NetworkX-wrapped [graphviz layouts](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.nx_agraph.graphviz_layout.html):
  dot, neato etc. You can use `args` for specific layouts - for example, for neato: `args="-Goverlap=scale -Gstart=123"`
- Gephi ForceAtlas2 based on the
  [forceatlas2 Python implementation](https://github.com/bhargavchippada/forceatlas2) -
  see [layout.py](./alph/layout.py) for configuration options, and
  [this paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0098679)
  for more detail
- ForceAtlas implementation within [scikit-network](https://github.com/sknetwork-team/scikit-network)
- Any other that returns a NetworkX-style node positions dictionary

### Supported arguments

| arg                              | type(s)                | default              | description                                                                                                                                                                                 |
| -------------------------------- | ---------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G                                | Networkx Graph         |                      | graph to visualise                                                                                                                                                                          |
| weight_attr                      | str                    |                      | edge weight attribute, for weighted graphs                                                                                                                                                  |
| layout_fn                        | function               | ForceAtlas2          | Function that, given a graph, returns a layout                                                                                                                                              |
| node args                        | dict                   |                      | See below                                                                                                                                                                                   |
| edge args                        | dict                   |                      | See below                                                                                                                                                                                   |
| combo_group_by                   | str or list            |                      | Attribute to use to create grouped combo nodes                                                                                                                                              |
| combo_layout_fn                  | function               | Fruchterman-Reingold | Layout function for combo nodes                                                                                                                                                             |
| combo_node_args                  | dict                   |                      | See below                                                                                                                                                                                   |
| combo_edge_args                  | dict                   |                      | See below                                                                                                                                                                                   |
| combo_edge_weight_agg_attr       | dict                   |                      | Attribute to use to weigh combo edges; if set, overrides weight_attr. Can use values given via combo_edge_agg_attrs. If not set and weight_attr not given, falls back to simple edge count. |
| combo_edge_agg_attrs             | dict                   |                      | Pandas groupby-style dict, describing how to aggregate edge attributes that span nodes - for example `{"combo_edge_attr_name": ("edge_attr_name", "sum")}`                                  |
| combo_edge_weight_threshold      | dict                   |                      | Drop edges below this weight                                                                                                                                                                |
| include_edgeless_combo_nodes     | dict                   |                      | Whether or not to incorporate disconnected combo nodes                                                                                                                                      |
| combo_node_additional_attrs      | dict                   |                      | Attributes to add to combo nodes                                                                                                                                                            |
| edge_node_additional_attrs       | dict                   |                      | Attributes to add to combo node edges, like `{"edge_attr_name": agg_fn}`; agg fn is applied across all attr values for edges that link grouped nodes                                        |
| combo_empty_attr_action          | drop, group or promote | `drop`               | What to do with nodes that have an empty value for the combo_group_by attribute                                                                                                             |
| combo_size_scale_domain          | 2-item list or tuple   | `[0, 25]`            | Lower/upper bound of num nodes to apply to combo node size range                                                                                                                            |
| combo_size_scale_range           | 2-item list or tuple   | `[6**2, 180**2]`     | Combo node size range                                                                                                                                                                       |
| combo_inner_graph_scale_factor   | float                  | `0.6`                | Scale down inner graph to fit inside combo nodes by this factor - normally <1                                                                                                               |
| non_serializable_datetime_format | str                    | `%d %b %Y`           | Format string for non-serialisable date / time types that otherwise break Altair                                                                                                            |
| width                            | int                    | `800`                | Figure width (px)                                                                                                                                                                           |
| height                           | int                    | `600`                | Figure height (px)                                                                                                                                                                          |
| prop_kwargs                      | dict                   |                      | Optional properties such as title                                                                                                                                                           |
| padding                          | int                    |                      | Padding inside figure edges. No node centres will be placed outside this boundary.                                                                                                          |
| nodes_layer_params               | selection or other     |                      | Altair params to be added to the nodes layer via `.add_params()` - typically a selection                                                                                                    |

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

- Node `size` attribute does not support all Altair options - currently only
  `alt.value` and `alt.Size` with linear `domain` and `range` scales. More can be
  added as needed.

  This is a design choice, made to not burden the user with calculating things like
  label and halo positions when node sizes vary. Will review this tradeoff based
  on in-use experience.

- One combo level currently supported

## See also

- [nx-altair](https://github.com/Zsailer/nx_altair) is a nice project that takes a slightly
  different approach to combining NetworkX and Altair for network viz.
