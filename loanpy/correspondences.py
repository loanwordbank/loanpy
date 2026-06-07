"""Sound correspondences from aligned cognate tables."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence


def _is_alternating_language_sequence(
    table: Sequence[Mapping[str, str]],
    descendant_language_ids: set[str],
    ancestor_language_ids: set[str],
) -> bool:
    """Return True if rows strictly alternate descendant / ancestor languages."""
    if len(table) % 2:
        logging.info("Odd number of rows.")
        return False
    for index, row in enumerate(table):
        allowed = (
            descendant_language_ids if index % 2 == 0 else ancestor_language_ids
        )
        if row["Language_ID"] not in allowed:
            logging.info("Problem in row %s: %s not in %s", index, row, allowed)
            return False
    return True


def add_separator(
    correspondences: dict[str, dict],
    sep: str = " < ",
) -> dict[str, dict]:
    """Return a copy of *correspondences* with tuple pair keys as ``\"a < b\"`` strings.

    Use when writing TOML (string keys only). In-memory scorers from
    :func:`get_sound_correspondences` use ``(descendant, ancestor)`` tuple keys.
    """
    out = dict(correspondences)

    def _stringify(key: tuple[str, str] | str) -> str:
        if isinstance(key, tuple) and len(key) == 2:
            return f"{key[0]}{sep}{key[1]}"
        return key

    for section in ("AbsoluteFrequency", "Cognateset_IDs", "Examples"):
        if section in out:
            out[section] = {_stringify(k): v for k, v in out[section].items()}
    return out


def load_scorer(
    data: Mapping[str, object],
    *,
    sep: str = " < ",
    missing: int | float = -1000,
    imputed: int | float = 1,
) -> defaultdict[tuple[str, str], int | float]:
    """Load a segment-pair scorer from a TOML scorer dict.

    Uses ``AbsoluteFrequency`` when present (as written by :func:`add_separator`).
    Otherwise, when *imputed* is given, builds flat scores from
    ``SoundCorrespondences`` (presence-only scorers such as hand-edited tables).
    Unlisted pairs map to *missing*.
    """
    pairs: dict[tuple[str, str], int | float] = {}
    if freq := data.get("AbsoluteFrequency", {}):
        for pair_key, count in freq.items():
            source, target = pair_key.split(sep, 1)
            pairs[(source, target)] = count
    else:
        for source, targets in data.get("SoundCorrespondences", {}).items():
            for target in targets:
                pairs[(source, target)] = imputed
    return defaultdict(lambda: missing, pairs)


def get_sound_correspondences(
    table: Sequence[Mapping[str, str]],
    aligned_col: str,
    prefix_descendant: str = "",
    prefix_ancestor: str = "",
) -> dict[str, dict]:
    """Extract segment correspondences from paired cognate alignment rows.

    Expects ``table`` to list cognate rows in **descendant, ancestor, descendant,
    ancestor, …** order (same convention as many CLDF ``cognates.csv`` exports).
    Each consecutive pair of rows is zipped segment-wise along ``aligned_col``.

    Parameters
    ----------
    table:
        Sequence of row dicts (e.g. from ``csv.DictReader``).
    aligned_col:
        Column with space-separated aligned segments (e.g. ``"Uralign"``).
    prefix_descendant, prefix_ancestor:
        Optional prefixes prepended to segment tokens in pair keys and examples.

    Returns
    -------
    dict
        Keys:

        * ``SoundCorrespondences`` — descendant segment → ranked ancestor segments
        * ``AbsoluteFrequency`` — ``(desc, anc)`` → count
        * ``Cognateset_IDs`` — ``(desc, anc)`` → cognate set ids
        * ``Examples`` — ``(desc, anc)`` → example alignment strings

    Examples
    --------
    Build a frequency table for alignment scoring::

        rows = list(csv.DictReader(open("cognates.csv", encoding="utf-8")))
        stats = get_sound_correspondences(rows, "Uralign")
        scorer = stats["AbsoluteFrequency"]

    Reload the same weights from a TOML scorer file::

        import tomllib
        from loanpy.correspondences import add_separator, load_scorer

        with open("globalign.toml", "rb") as f:
            data = tomllib.load(f)
        scorer = load_scorer(data, missing=-1000, imputed=12)

    Notes
    -----
    * **Quantitative analysis** — ``make_results.py`` in the Indo-Iranian–Hungarian
      study calls this on CLDF cognate tables to build TOML scorers and in-memory
      weights for :class:`~loanpy.align.Uralign` and :class:`~loanpy.align.Altign`.
    * **CLDF workflows** — training data from any wordlist with alternating
      descendant/ancestor rows and an alignment column can be passed in; no
      hard-coded language names are required.
    """
    correspondences: dict[str, dict] = {
        key: defaultdict(list)
        for key in (
            "SoundCorrespondences",
            "AbsoluteFrequency",
            "Cognateset_IDs",
            "Examples",
        )
    }

    for index in range(0, len(table) - 1, 2):
        descendant_row, ancestor_row = table[index], table[index + 1]
        for descendant_seg, ancestor_seg in zip(
            descendant_row[aligned_col].split(),
            ancestor_row[aligned_col].split(),
        ):
            correspondences["SoundCorrespondences"][descendant_seg].append(
                ancestor_seg
            )
            pair_key = (
                f"{prefix_descendant}{descendant_seg}",
                f"{prefix_ancestor}{ancestor_seg}",
            )
            correspondences["AbsoluteFrequency"][pair_key].append(1)
            correspondences["Cognateset_IDs"][pair_key].append(
                ancestor_row["Cognateset_ID"]
            )
            example = (
                f"{prefix_descendant}{descendant_row[aligned_col]}"
                f" < {prefix_ancestor}{ancestor_row[aligned_col]}"
            )
            correspondences["Examples"][pair_key].append(example)

    correspondences["SoundCorrespondences"] = {
        descendant: [
            ancestor for ancestor, _ in Counter(ancestors).most_common()
        ]
        for descendant, ancestors in correspondences["SoundCorrespondences"].items()
    }
    correspondences["AbsoluteFrequency"] = {
        pair: sum(counts)
        for pair, counts in correspondences["AbsoluteFrequency"].items()
    }
    correspondences["AbsoluteFrequency"] = dict(
        sorted(correspondences["AbsoluteFrequency"].items(), key=lambda item: item[1])
    )
    correspondences["Cognateset_IDs"] = {
        pair: list(dict.fromkeys(ids))
        for pair, ids in correspondences["Cognateset_IDs"].items()
    }

    return correspondences
