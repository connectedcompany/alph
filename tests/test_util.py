import numpy as np
import pandas as pd
import pytest
from alph.util import generate_interaction_graph, normalise_pos, nx_graph_from_edges


class Test_nx_graph_from_edges:
    def test_empty(self):
        with pytest.raises(ValueError, match=r"(?i)missing"):
            res = nx_graph_from_edges(pd.DataFrame(), node_attrs={})

        res = nx_graph_from_edges(
            pd.DataFrame(columns=["a", "b"]), source="a", target="b", node_attrs={}
        )
        assert len(res) == 0

    def test_unweighted(self):
        edges = [("a", "b"), ("b", "c")]
        df = pd.DataFrame(edges, columns=["source", "target"])

        res = nx_graph_from_edges(df, node_attrs={})

        assert len(res) == 3
        assert res.has_edge("b", "c")

    def test_node_attr(self):
        edges = [("a", "b")]
        df = pd.DataFrame(edges, columns=["source", "target"])

        res = nx_graph_from_edges(df, node_attrs={"a": {"greeting": "hello"}})

        assert res.nodes["a"]["greeting"] == "hello"
        assert "greeting" not in res.nodes["b"]

    def test_add_missing_nodes(self):
        edges = [("a", "b")]
        df = pd.DataFrame(edges, columns=["source", "target"])

        res = nx_graph_from_edges(
            df,
            node_attrs={"c": {"greeting": "hello"}},
            add_missing_node_attr_nodes=True,
        )

        assert len(res) == 3
        assert "greeting" in res.nodes["c"]

    def test_add_missing_nodes_to_empty(self):
        edges = []
        df = pd.DataFrame(edges, columns=["source", "target"])

        res = nx_graph_from_edges(
            df,
            node_attrs={"c": {"attr": "val"}},
            add_missing_node_attr_nodes=True,
        )

        assert len(res) == 1
        assert "c" in res.nodes()
        assert res.nodes["c"] == {"attr": "val"}

    def test_unweighted(self):
        edges = [("a", "b", 0.1), ("b", "c", 0.2)]
        df = pd.DataFrame(edges, columns=["source", "target", "wt"])

        res = nx_graph_from_edges(df, node_attrs={}, edge_attr=["wt"])

        assert len(res) == 3
        assert res.get_edge_data("a", "b", "wt")["wt"] == 0.1

    def test_weighted(self):
        edges = [("a", "b", 0.1), ("b", "c", 0.2)]
        df = pd.DataFrame(edges, columns=["source", "target", "wt"])

        res = nx_graph_from_edges(df, node_attrs={}, edge_attr=["wt"])

        assert len(res) == 3
        assert res.get_edge_data("a", "b", "wt")["wt"] == 0.1

    def test_threshold(self):
        edges = [("a", "b", 0.1), ("b", "c", 0.2)]
        df = pd.DataFrame(edges, columns=["source", "target", "weight"])

        res = nx_graph_from_edges(
            df,
            node_attrs={},
            edge_attr="weight",
            weight_attr="weight",
            weight_threshold=0.2,
        )

        assert len(res) == 3
        assert not res.has_edge("a", "b")
        assert res.has_edge("b", "c")

    def test_drop_isolated(self):
        edges = [("a", "b", 0.1), ("b", "c", 0.2)]
        df = pd.DataFrame(edges, columns=["source", "target", "weight"])

        res = nx_graph_from_edges(
            df,
            node_attrs={"d": {"additiona": True}},
            add_missing_node_attr_nodes=True,
            edge_attr="weight",
            weight_attr="weight",
            drop_isolated_nodes=True,
        )

        assert len(res) == 3
        assert "d" not in res.nodes()


@pytest.mark.parametrize(
    "pos, range, aspect_ratio, padding,expected",
    [
        # empties
        ({}, *(3 * [None]), {}),
        #  within existing range
        (
            {"a": [0.5, -0.5], "b": [1, -1]},
            *([None] * 3),
            {"a": [0.5, -0.5], "b": [1, -1]},
        ),
        # scale down, scale according to longest side
        (
            {"a": [0.5, -0.5], "b": [10, -1]},
            *([None] * 3),
            {"a": [0.05, -0.05], "b": [1, -0.1]},
        ),
        # all positives, with explicit aspect ratio of 1 (no effect)
        (
            {"a": [0, 0.1], "b": [0.2, 0.5]},
            *([None] * 3),
            {"a": [-1, -0.6], "b": [-0.2, 1]},
        ),
        # aspect ratio
        (
            {"a": [0, 0.1], "b": [0.2, 0.5]},
            None,
            2,
            None,
            {"a": [-2, -0.6], "b": [-0.4, 1]},
        ),
        # custom range
        (
            {"a": [0, -0.1], "b": [0.2, 1.0]},
            [-1, 3],
            None,
            None,
            {"a": [1, 0.8], "b": [1.4, 3]},
        ),
        # numpy input
        (
            {"a": np.array([0.5, -0.5]), "b": np.array([1, -1])},
            *([None] * 3),
            {"a": [0.5, -0.5], "b": [1, -1]},
        ),
        # padding
        (
            {"a": [0, -0.9], "b": [0.2, 1.0]},
            [0, 10],
            None,
            1,
            {"a": [5, 1.4], "b": [5.8, 9]},
        ),
    ],
)
def test_normalise_pos(pos, range, aspect_ratio, padding, expected):
    res = normalise_pos(pos, range=range, aspect_ratio=aspect_ratio, padding=padding)

    # need extra treatment for floats
    assert list(res.keys()) == list(expected.keys())
    for k, xy in res.items():
        assert xy == pytest.approx(expected[k])


class Test_generate_interaction_graph:
    def test_empty(_):
        G = generate_interaction_graph([], 1)
        assert len(G.nodes) == 0

    def test_one_node(_):
        G = generate_interaction_graph(1, 1)
        assert len(G.nodes) == 1

    def test_two_named_nodes(_):
        G = generate_interaction_graph(["x", "y"], 10)
        assert len(G.nodes) == 2
        assert set(G.nodes) == {"x", "y"}
        # TODO: fix flakiness so we can uncomment
        # assert G.get_edge_data("x", "y")["weight"] > 1

        G = generate_interaction_graph(
            ["x", "y"], 10, edge_weights="prob_interaction_per_unit_time"
        )
        # TODO: fix flakiness so we can uncomment
        # assert G.get_edge_data("x", "y")["weight"] < 1

    def test_nodes_only(_):
        G = generate_interaction_graph(1000, 2)
        mean_weight = np.mean([w for _, _, w in G.edges(data="weight")])
        assert len(G.nodes) == 1000
        assert pytest.approx(2, 0.1) == mean_weight

    def test_edge_weights_as_time_to_next_interaction(_):
        G = generate_interaction_graph(["a", "b", "c"], 10)
        assert len(G.nodes) == 3
        assert set(G.nodes) == {"a", "b", "c"}

    def test_edge_weights_as_interaction_per_unit_time_probs(_):
        G = generate_interaction_graph(
            1000, 4, edge_weights="prob_interaction_per_unit_time"
        )
        mean_inv_weight = 1 / np.mean([1 / w for _, _, w in G.edges(data="weight")])
        assert len(G.nodes) == 1000
        assert pytest.approx(1 - np.exp(-1 / 4 * 1), 0.2) == mean_inv_weight
