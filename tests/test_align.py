"""Tests for loanpy.align."""

from collections import defaultdict

from loanpy import Altign


class TestAltignGaps:
    def test_collapses_consecutive_gaps_on_b(self):
        seq_a = ["x", "y", "z"]
        seq_b = ["a", "-", "-"]
        a2, b2 = Altign.gaps(seq_a, seq_b)
        assert a2 == ["x", "+", "y.z"]
        assert b2 == ["a"]

    def test_trailing_gap_inserts_plus_marker(self):
        seq_a = ["a", "b", "c"]
        seq_b = ["x", "y", "-"]
        a2, b2 = Altign.gaps(seq_a, seq_b)
        assert "+" in a2
        assert b2[-1] != "-"

    def test_no_trailing_gap_no_plus_marker(self):
        seq_a = ["a", "b"]
        seq_b = ["x", "y"]
        a2, b2 = Altign.gaps(seq_a, seq_b)
        assert a2 == ["a", "b"]
        assert b2 == ["x", "y"]
        assert "+" not in a2

    def test_trailing_single_gap_adds_plus(self):
        seq_a = ["a", "b"]
        seq_b = ["x", "-"]
        a2, b2 = Altign.gaps(seq_a, seq_b)
        assert a2 == ["a", "+", "b"]
        assert b2 == ["x"]


class TestAltignGetScore:
    def test_direct_correspondence(self):
        scorer = defaultdict(lambda: -1000, {("a", "a"): 5})
        assert Altign.get_score(["a"], ["a"], scorer, freq_filter=2) == 5

    def test_partial_donor_cluster_match(self):
        scorer = defaultdict(lambda: -1000, {("a", "x.y"): 4})
        assert Altign.get_score(["a"], ["x.y.z"], scorer, freq_filter=2) == 4

    def test_vowel_length_fallback(self):
        scorer = defaultdict(lambda: -1000)
        assert Altign.get_score(["aː"], ["a"], scorer, freq_filter=2) == 2

    def test_penalty_when_no_match(self):
        scorer = defaultdict(lambda: -1000)
        assert Altign.get_score(["a"], ["b"], scorer, freq_filter=2) == -1000
