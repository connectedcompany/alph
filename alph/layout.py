import networkx as nx
import numpy as np
import pandas as pd

BARNES_HUT_ON_THRESHOLD = 500


def force_atlas_sknet(G, n_components=2, init_seed=None, **fa2_args):
    """
    Wrapper for sckikit-network's implementation of Force Atlas 2, to accept nx Graphs and return a `pos`-like structure.

    Parameters
    ----------
    G : nx.Graph
        Graph to display
    n_components : int = 2
        Dimension of the graph layout.
    n_iter : int = 50
        Number of iterations to update positions.
        If ``None``, use the value of self.n_iter.
    approx_radius : float = -1
        If a positive value is provided, only the nodes within this distance a given node are used to compute
        the repulsive force.
    lin_log : bool = False
        If ``True``, use lin-log mode.
    gravity_factor : float = 0.01
        Gravity force scaling constant.
    repulsive_factor : float = 0.1
        Repulsive force scaling constant.
    tolerance : float = 0.1
        Tolerance defined in the swinging constant.
    speed : float = 0.1
        Speed constant.
    speed_max : float = 10
        Constant used to impose constrain on speed.
    init_seed : int = None
        Set initial positions repeatably - or randomly if no seed given

    For full up-to-date parameterisation,
    see https://github.com/sknetwork-team/scikit-network/blob/master/sknetwork/embedding/force_atlas.py
    """

    from scipy.sparse import csr_matrix
    from sknetwork.embedding.force_atlas import ForceAtlas

    # randomise initial positions
    pos_init = None
    if init_seed is not None:
        num_nodes = len(G.nodes)
        pos_init_rng = np.random.default_rng(init_seed)
        pos_init = pos_init_rng.standard_normal(
            (num_nodes, n_components)
        )  # standard_normal used w/ default_rng instead of randn

    csr_graph = csr_matrix(
        nx.to_scipy_sparse_array(G)
    )  # to_scipy_sparse_matrix generates a pre-nx3.0 warning
    fa = ForceAtlas(n_components=n_components, **fa2_args)
    embedding = fa.fit_transform(csr_graph, pos_init=pos_init)

    # normalise
    embedding = embedding / np.max(np.abs(embedding))

    return dict(zip(G.nodes(), embedding))


def default_force_atlas_nan_coord_bug_alt_layout(G, weight_attr):
    return nx.spring_layout(G, weight=weight_attr)


def force_atlas(
    G,
    pos=None,
    weight_attr=None,
    iterations=5000,
    nan_coord_bug_alt_layout=default_force_atlas_nan_coord_bug_alt_layout,
    **kwargs
):
    """
    See https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0098679 for detail on params
    """

    # fa2 is optional
    from fa2 import ForceAtlas2

    fa2_kwargs = {
        **dict(
            # Behavior alternatives
            # ForceAtlas2 has a “Dissuade Hubs” mode that, once activated, affects the shape
            # of the graph by dividing the attraction force of each node by its degree plus 1
            # for nodes it points to. When active, it is meant to grant authorities (nodes
            # with a high indegree) a more central position than hubs (nodes with a high
            # outdegree). This is useful for social networks and web networks, where authorities
            # are sometimes considered more important than hubs. “Dissuade Hubs” tends to push
            # hubs to the periphery while keeping authorities in the center.
            outboundAttractionDistribution=True,  # Dissuade hubs
            linLogMode=False,  # NOT IMPLEMENTED
            adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
            # If the edges are weighted, this weight will be taken into consideration in the
            # computation of the attraction force. This can have a dramatic impact on the result.
            # If set to 0, the weights are ignored. If it is set to 1, then the attraction is
            # proportional to the weight. Values above 1 emphasize the weight effects.
            edgeWeightInfluence=1.0,  # default: 1.0 - can help control effect of lone outlier edges
            # Performance
            jitterTolerance=1.0,  # Tolerance
            # BarnesHut improves spatialization performances on big graphs Relying on an
            # approximate computation of repulsion forces, such optimization generates
            # approximation and may be counter-productive on small networks
            barnesHutOptimize=G.number_of_nodes() > BARNES_HUT_ON_THRESHOLD,
            barnesHutTheta=1.2,  # default: 1.2 "This is useful for large graph but harmful to small ones."
            multiThreaded=False,  # NOT IMPLEMENTED
            # Tuning
            scalingRatio=2.0,  # default: 2.0 - how much repulsion you want. More makes a more sparse graph.
            # The “Strong gravity” option sets a force that attracts the nodes that are distant
            # from the center more (d(n) is this distance). This force has the drawback of being
            # so strong that it is sometimes stronger than the other forces. It may result in a
            # biased placement of the nodes. However, its advantage is to force a very compact
            # layout, which may be useful for certain purposes.
            strongGravityMode=False,  # default: False
            gravity=1.0,  # default: 1.0 - attracts nodes to the center. Prevents islands from drifting away
            # Log
            verbose=False,
        ),
        **kwargs,
    }

    fa2 = ForceAtlas2(**fa2_kwargs)

    res = fa2.forceatlas2_networkx_layout(
        G, pos=pos, weight_attr=weight_attr, iterations=iterations
    )

    if any([pd.isna(xy[0]) or pd.isna(xy[1]) for xy in res.values()]):
        if nan_coord_bug_alt_layout:
            res = nan_coord_bug_alt_layout(G, weight_attr)
        else:
            print(
                "Hit fa2 bug - one or more nodes had a np.nan co-ordinate. "
                "Pass alternate layout to work arouund."
            )

    return res


def default_inter_combo_layout(G, weight_attr=None, **kwargs):
    return nx.fruchterman_reingold_layout(G, weight=weight_attr, **kwargs)


def default_intra_combo_layout(G, weight_attr=None, strongGravityMode=True, **kwargs):
    return force_atlas(
        G, weight_attr=weight_attr, strongGravityMode=strongGravityMode, **kwargs
    )


def default_network_layout(G, weight_attr=None, strongGravityMode=True, **kwargs):
    return force_atlas(
        G, weight_attr=weight_attr, strongGravityMode=strongGravityMode, **kwargs
    )
