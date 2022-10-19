import networkx as nx
import pandas as pd
import pytest
from alph import combo


def sorted_edges(G, data):
    """
    Helper to deal with undirected nx graphs messing about with vertex order
    in edges (u,v) -> (v,u)...
    """
    return sorted(
        [(*sorted((u, v)), d) for u, v, d in G.edges(data=data)],
        key=lambda x: (x[0], x[1]),
    )


def empty_cat(val=None):
    """Helper for prefixed combo category values to make tests more readable"""

    return (
        combo.EMPTY_COMBO_VALUE_PLACEHOLDER
        if pd.isnull(val)
        else f"{combo.EMPTY_COMBO_VALUE_PLACEHOLDER}_{val}"
    )


@pytest.fixture
def G_with_empties():
    G = nx.Graph()
    G.add_nodes_from(
        [
            ("a", {"team": "uno"}),
            ("b", {"team": None}),
            ("c", {"team": "uno"}),
            ("d", {"something": "else"}),
        ]
    )
    G.add_edges_from(
        [
            ("a", "b", {"weight": 0.1}),
            ("a", "c", {"weight": 0.2}),
            ("b", "c", {"weight": 0.3}),
            ("b", "d", {"weight": 0.5}),
        ]
    )
    return G


class Test_combo_graphs:
    def test_simple_unweighted(self):
        G = nx.Graph()
        G.add_nodes_from(
            [
                ("a", {"team": "uno"}),
                ("b", {"team": "uno"}),
                ("c", {"team": "dos"}),
            ]
        )
        G.add_edges_from(
            [
                ("a", "b"),
                ("a", "c"),
                ("b", "c"),
            ]
        )

        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G,
            combo_group_by="team",
        )

        assert set([n for n in inter_combo_G.nodes()]) == set(["dos", "uno"])
        assert [e for e in inter_combo_G.edges(data="weight")] == [("dos", "uno", 2)]

        assert set(intra_combo_Gs.keys()) == set(["uno", "dos"])

        assert [n for n in intra_combo_Gs["uno"].nodes()] == ["a", "b"]
        assert [e for e in intra_combo_Gs["uno"].edges(data=True)] == [("a", "b", {})]

        assert [n for n in intra_combo_Gs["dos"].nodes()] == ["c"]
        assert intra_combo_Gs["dos"].number_of_edges() == 0

    def test_simple_weighted(self):
        G = nx.Graph()
        G.add_nodes_from(
            [
                ("a", {"team": "uno"}),
                ("b", {"team": "uno"}),
                ("c", {"team": "dos"}),
            ]
        )
        G.add_edges_from(
            [
                ("a", "b", {"weight": 0.1}),
                ("a", "c", {"weight": 0.3}),
                ("b", "c", {"weight": 0.2}),
            ]
        )

        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G,
            combo_group_by="team",
            weight_attr="weight",
        )

        assert set([n for n in inter_combo_G.nodes()]) == set(["uno", "dos"])
        assert [e for e in inter_combo_G.edges(data="weight")] == [("dos", "uno", 0.5)]

        assert set(intra_combo_Gs.keys()) == set(["uno", "dos"])

        assert [n for n in intra_combo_Gs["uno"].nodes()] == ["a", "b"]
        assert [e for e in intra_combo_Gs["uno"].edges(data="weight")] == [
            ("a", "b", 0.1)
        ]

        assert [n for n in intra_combo_Gs["dos"].nodes()] == ["c"]
        assert intra_combo_Gs["dos"].number_of_edges() == 0

    def test_missing_combo_attr_drop(self, G_with_empties):
        # **drop** empty combo attr nodes
        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G_with_empties,
            combo_group_by="team",
            weight_attr="weight",
            empty_combo_attr_action="drop",
        )
        assert [n for n in inter_combo_G.nodes()] == ["uno"]
        assert list(intra_combo_Gs.keys()) == ["uno"]
        assert [n for n in intra_combo_Gs["uno"].nodes()] == ["a", "c"]
        assert [e for e in intra_combo_Gs["uno"].edges(data="weight")] == [
            ("a", "c", 0.2)
        ]

    def test_missing_combo_attr_group(self, G_with_empties):
        # **gruop together** empty combo attr nodes
        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G_with_empties,
            combo_group_by="team",
            weight_attr="weight",
            empty_combo_attr_action="group",
        )
        assert set([n for n in inter_combo_G.nodes()]) == set(["uno", empty_cat()])
        assert [e for e in inter_combo_G.edges(data="weight")] == [
            (empty_cat(), "uno", 0.4)
        ]

        assert set(intra_combo_Gs.keys()) == {"uno", empty_cat()}
        assert [n for n in intra_combo_Gs["uno"].nodes()] == ["a", "c"]
        assert [e for e in intra_combo_Gs["uno"].edges(data="weight")] == [
            ("a", "c", 0.2)
        ]
        assert [n for n in intra_combo_Gs[empty_cat()].nodes()] == ["b", "d"]
        assert [e for e in intra_combo_Gs[empty_cat()].edges(data="weight")] == [
            ("b", "d", 0.5)
        ]

    def test_missing_combo_attr_promote(self, G_with_empties):
        # **gruop together** empty combo attr nodes
        inter_combo_G, intra_combo_Gs = combo.combo_graph_mapper(
            G_with_empties,
            combo_group_by="team",
            weight_attr="weight",
            empty_combo_attr_action="promote",
            combo_node_additional_attrs={"something": "different"},
        )

        # inter-combo assertions
        assert set([n for n in inter_combo_G.nodes()]) == set(
            ["uno", empty_cat("b"), empty_cat("d")]
        )

        assert sorted_edges(inter_combo_G, data="weight") == [
            (empty_cat("b"), empty_cat("d"), 0.5),
            (empty_cat("b"), "uno", 0.4),
        ]
        assert inter_combo_G.nodes[empty_cat("b")][combo.COMBO_PROMOTED_NODE_ATTR]
        assert not inter_combo_G.nodes["uno"].get(combo.COMBO_PROMOTED_NODE_ATTR)

        # intra-combo assertions
        assert set(intra_combo_Gs.keys()) == {"uno", empty_cat("b"), empty_cat("d")}
        assert [n for n in intra_combo_Gs["uno"].nodes()] == ["a", "c"]
        assert [e for e in intra_combo_Gs["uno"].edges(data="weight")] == [
            ("a", "c", 0.2)
        ]
        assert [n for n in intra_combo_Gs[empty_cat("b")].nodes()] == ["b"]
        assert [n for n in intra_combo_Gs[empty_cat("d")].nodes()] == ["d"]

    def test_add_node_attrs(self, G_with_empties):
        # **drop** empty combo attr nodes
        inter_combo_G, _ = combo.combo_graph_mapper(
            G_with_empties,
            combo_group_by="team",
            weight_attr="weight",
            empty_combo_attr_action="drop",
            combo_node_additional_attrs={"uno": {"attr1": 1, "attr2": 2}},
        )
        assert [n for n in inter_combo_G.nodes()] == ["uno"]
        assert inter_combo_G.nodes["uno"] == {"attr1": 1, "attr2": 2}

    # TODO:
    # - test use of name field as group label
    # - return non-combo'd nodes if they don't hae a combo category
    # - check uniqueness of node ids across all combo levels
    # - error checks for params etc.
