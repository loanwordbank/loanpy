"""Loanpy — linguistic toolkit for loanword detection and sound change.

Version 4 provides segmentation clustering, alignment scoring, sound-correspondence
mining, edit-distance utilities, and adaptation (substitution plus phonotactic repair).
"""

from loanpy.adapt import Adapt
from loanpy.cluster import Cluster
from loanpy.correspondences import (
    CorrespondenceLookup,
    add_separator,
    get_sound_correspondences,
    load_cognate_table,
    load_scorer,
)
from loanpy.edit import (
    apply_edit,
    edit_distance_matrix,
    edit_distance_with2ops,
    path_to_edit_operations,
    shortest_edit_path,
    substitute_operations,
)
from loanpy.phonotactics import expand_phonotactics, get_closest_phonotactics
from loanpy.align import Altign, Uralign

__version__ = "4.0.0"

__all__ = [
    "Adapt",
    "Altign",
    "Cluster",
    "CorrespondenceLookup",
    "Uralign",
    "__version__",
    "apply_edit",
    "edit_distance_matrix",
    "edit_distance_with2ops",
    "expand_phonotactics",
    "get_closest_phonotactics",
    "add_separator",
    "get_sound_correspondences",
    "load_cognate_table",
    "load_scorer",
    "path_to_edit_operations",
    "shortest_edit_path",
    "substitute_operations",
]
