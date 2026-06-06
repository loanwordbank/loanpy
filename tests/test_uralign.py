"""Tests for loanpy.align.Uralign."""

from loanpy import Uralign


class TestUralignHu:
    def test_initial_vowel_both_descendant_and_ancestor(self):
        hu = ["a", "l", "m"]
        pu = ["a", "l"]
        out_h, out_p = Uralign.hu(hu.copy(), pu.copy(), "V", "V")
        assert out_h[0] == "#-"
        assert out_p[0] == "-"

    def test_initial_vowel_descendant_only(self):
        hu = ["a", "l"]
        pu = ["k", "a"]
        out_h, out_p = Uralign.hu(hu.copy(), pu.copy(), "V", "C")
        assert out_h[0] == "#-"
        assert out_p[0] != "-"

    def test_no_initial_gap_when_disabled(self):
        hu = ["a", "b"]
        pu = ["c", "d"]
        out_h, out_p = Uralign.hu(
            hu.copy(), pu.copy(), "V", "V", initial_gap=False
        )
        assert out_h[0] != "#-"

    def test_final_gap_shorter_descendant(self):
        hu = ["k", "a"]
        pu = ["k", "a", "t", "a"]
        out_h, out_p = Uralign.hu(hu.copy(), pu.copy(), "C", "C")
        assert out_h[-1] == "-#"
        assert out_p[-1] == "t.a"

    def test_final_gap_longer_descendant_clusters_tail(self):
        hu = ["k", "a", "t", "a", "n"]
        pu = ["k", "a"]
        out_h, out_p = Uralign.hu(hu.copy(), pu.copy(), "C", "C")
        assert "+" in out_h
        assert "t.a.n" in ".".join(out_h) or out_h[-1] == "t.a.n"

    def test_final_gap_equal_length_no_padding(self):
        hu = ["k", "a"]
        pu = ["p", "u"]
        out_h, out_p = Uralign.hu(hu.copy(), pu.copy(), "C", "C")
        assert "-#" not in out_h[-1]
        assert len(out_h) == len(out_p) == 2

    def test_no_final_gap_truncates_to_shorter(self):
        hu = ["a", "b", "c"]
        pu = ["x", "y"]
        out_h, out_p = Uralign.hu(
            hu.copy(), pu.copy(), "V", "C", initial_gap=False, final_gap=False
        )
        assert out_h == ["a", "b"]
        assert out_p == ["x", "y"]


class TestUralignGetScore:
    def test_sums_scores_above_threshold(self):
        scorer = {("a", "x"): 5, ("b", "y"): 3}
        assert Uralign.get_score(["a", "b"], ["x", "y"], scorer, freq_filter=2) == 8

    def test_penalizes_unknown_pairs(self):
        assert Uralign.get_score(["a"], ["z"], {}, freq_filter=2) == -1000

    def test_penalizes_pairs_below_threshold(self):
        scorer = {("a", "x"): 1}
        assert Uralign.get_score(["a"], ["x"], scorer, freq_filter=2) == -1000

    def test_exact_threshold_counts_positive(self):
        scorer = {("a", "x"): 2}
        assert Uralign.get_score(["a"], ["x"], scorer, freq_filter=2) == 2

    def test_empty_alignment_zero(self):
        assert Uralign.get_score([], [], {}, freq_filter=2) == 0
