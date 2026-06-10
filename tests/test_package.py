"""Tests for package metadata and public API."""

import importlib

import loanpy
from loanpy import (
    Adapt,
    Cluster,
    CorrespondenceLookup,
    Uralign,
    add_separator,
    apply_edit,
    edit_distance_matrix,
    edit_distance_with2ops,
    expand_phonotactics,
    get_closest_phonotactics,
    get_sound_correspondences,
    load_scorer,
    path_to_edit_operations,
    shortest_edit_path,
    substitute_operations,
)


def test_version():
    assert loanpy.__version__ == "4.0.0"


def test_public_exports():
    expected = {
        "Adapt",
        "Cluster",
        "CorrespondenceLookup",
        "Uralign",
        "add_separator",
        "apply_edit",
        "edit_distance_matrix",
        "edit_distance_with2ops",
        "expand_phonotactics",
        "get_closest_phonotactics",
        "get_sound_correspondences",
        "load_scorer",
        "path_to_edit_operations",
        "shortest_edit_path",
        "substitute_operations",
    }
    assert expected <= set(loanpy.__all__)


def test_top_level_imports_match_submodules():
    assert Adapt.__name__ == "Adapt"
    assert get_sound_correspondences.__module__ == "loanpy.correspondences"
    assert load_scorer.__module__ == "loanpy.correspondences"


def test_reload_preserves_version():
    importlib.reload(loanpy)
    assert loanpy.__version__ == "4.0.0"
