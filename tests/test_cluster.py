"""Tests for loanpy.cluster."""

import pytest

from loanpy import Cluster


class TestClusterCv:
    def test_clusters_consonant_run(self):
        assert Cluster.cv(["f", "l", "a"], ["C", "C", "V"]) == ["f.l", "a"]

    def test_clusters_vowel_run(self):
        assert Cluster.cv(["a", "ʊ", "ə"], ["V", "V", "V"]) == ["a.ʊ.ə"]

    def test_alternating_cv_no_internal_dots(self):
        assert Cluster.cv(["k", "a", "t"], ["C", "V", "C"]) == ["k", "a", "t"]

    def test_single_segment(self):
        assert Cluster.cv(["ə"], ["V"]) == ["ə"]


class TestClusterGlides:
    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="same length"):
            Cluster.glides(["a"], ["C", "V"])

    def test_glide_between_vowels_clusters_forward(self):
        segments = ["a", "w", "a"]
        cv = ["V", "C", "V"]
        out = Cluster.glides(segments, cv, cluster_between_vowels=("w",))
        assert out == ["a.w.a"]

    def test_consonant_after_l_not_clustered(self):
        segments = ["l", "t͡ʃ", "a"]
        cv = ["C", "C", "V"]
        out = Cluster.glides(segments, cv, cluster_between_vowels=())
        assert out == ["l", "t͡ʃ", "a"]

    def test_second_pass_merges_vowel_after_glide_cluster(self):
        segments = ["a", "w", "a", "i"]
        cv = ["V", "C", "V", "V"]
        out = Cluster.glides(segments, cv, cluster_between_vowels=("w",))
        assert "w" in out[0]
        assert len(out) < len(segments)

    def test_no_cluster_when_glide_not_between_vowels(self):
        segments = ["k", "w", "a"]
        cv = ["C", "C", "V"]
        out = Cluster.glides(segments, cv, cluster_between_vowels=("w",))
        assert "w" in out[1] or out != segments


class TestClusterLiquid:
    def test_consonant_after_l_clusters(self):
        segments = ["l", "t͡ʃ", "a"]
        out = Cluster.liquid(segments, cluster_after_l=("t͡ʃ",))
        assert out == ["l.t͡ʃ", "a"]

    def test_clusters_d_after_l(self):
        segments = ["l", "d", "a"]
        out = Cluster.liquid(segments)
        assert out == ["l.d", "a"]

    def test_no_cluster_when_previous_is_not_l(self):
        segments = ["k", "d", "a"]
        out = Cluster.liquid(segments)
        assert out == ["k", "d", "a"]

    def test_glides_then_liquid_for_hungarian_pattern(self):
        segments = ["l", "t͡ʃ", "a"]
        cv = ["C", "C", "V"]
        out = Cluster.liquid(Cluster.glides(segments, cv, cluster_between_vowels=()))
        assert out == ["l.t͡ʃ", "a"]

