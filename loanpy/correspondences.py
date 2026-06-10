"""Sound correspondences from aligned cognate tables."""

from __future__ import annotations

import csv
import logging
import tomllib
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path


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


def load_cognate_table(
    table_path: str | Path,
    *,
    forms_path: str | Path | None = None,
    form_col: str = "Form",
    form_id_col: str = "Form_ID",
    id_col: str = "UEW_ID",
) -> list[dict[str, str]]:
    """Load cognate rows from a CLDF-style CSV, joining surface forms if needed.

    When ``form_col`` or ``id_col`` is absent from the table, looks up each row's
    ``form_id_col`` in ``forms_path`` (default: ``forms.csv`` beside the table)
    and copies the missing columns onto the row in place.

    Parameters
    ----------
    table_path:
        Path to the cognate table (e.g. ``cognates.csv``).
    forms_path:
        Path to ``forms.csv``. Defaults to ``table_path``'s parent directory.
    form_col:
        Column holding orthographic forms. Default ``"Form"``.
    form_id_col:
        Foreign-key column referencing ``forms.csv::ID``. Default ``"Form_ID"``.
    id_col:
        Column holding the Uralonet entry id. Default ``"UEW_ID"``.
    """
    table_path = Path(table_path)
    rows = list(csv.DictReader(table_path.open(encoding="utf-8")))
    if not rows:
        return rows

    needs_form = form_col not in rows[0]
    needs_id = bool(id_col) and id_col not in rows[0]
    if not needs_form and not needs_id:
        return rows
    if form_id_col not in rows[0]:
        return rows

    if forms_path is None:
        forms_path = table_path.parent / "forms.csv"
    forms_path = Path(forms_path)
    forms = {
        row["ID"]: row
        for row in csv.DictReader(forms_path.open(encoding="utf-8"))
    }
    for row in rows:
        form_row = forms[row[form_id_col]]
        if needs_form:
            row[form_col] = form_row[form_col]
        if needs_id and id_col in form_row:
            row[id_col] = form_row[id_col]
    return rows


def _lookup_cognateset_ids(
    cognateset_ids: Mapping[object, object],
    tok_a: str,
    tok_b: str,
    sep: str,
) -> list[str]:
    """Return cognate-set ids for a segment pair from a TOML or in-memory mapping."""
    string_key = f"{tok_a}{sep}{tok_b}"
    if string_key in cognateset_ids:
        value = cognateset_ids[string_key]
    elif (tok_a, tok_b) in cognateset_ids:
        value = cognateset_ids[(tok_a, tok_b)]
    else:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _index_cognateset_forms(
    table: Sequence[Mapping[str, str]],
    form_col: str,
    id_col: str = "UEW_ID",
) -> dict[str, tuple[str, str, str]]:
    """Map cognate-set ids to descendant form, ancestor form, and entry id."""
    forms: dict[str, tuple[str, str, str]] = {}
    for index in range(0, len(table) - 1, 2):
        descendant_row, ancestor_row = table[index], table[index + 1]
        cognateset_id = descendant_row["Cognateset_ID"]
        entry_id = descendant_row.get(id_col, "") if id_col else ""
        forms[cognateset_id] = (
            descendant_row[form_col],
            ancestor_row[form_col],
            entry_id,
        )
    return forms


class CorrespondenceLookup:
    """Sound-correspondence statistics tied to the cognate table they were mined from.

    Parameters
    ----------
    table_path:
        Path to the cognate CSV (e.g. CLDF ``cognates.csv``). Rows must follow
        **descendant, ancestor, descendant, ancestor, …** order.
    scorer_path:
        Path to a TOML scorer written with :func:`add_separator`. Must include
        a ``Cognateset_IDs`` section for :meth:`etymologies`.
    forms_path:
        Optional path to ``forms.csv`` when orthographic forms are not already
        present in the cognate table. Defaults to ``forms.csv`` beside
        ``table_path``.

    Examples
    --------
    List attested etymology pairs for a segment correspondence::

        from loanpy import CorrespondenceLookup

        lookup = CorrespondenceLookup(
            "data/UEW-hu/cldf/cognates.csv",
            "scorers/Uralign-UEW.toml",
        )
        print(lookup.etymologies("ɡː", "ŋ.k", form_col="Form"))

    Notes
    -----
    Used after mining correspondences from CLDF cognate tables: the TOML scorer
    records which cognate sets exemplify each segment pair, and this class joins
    those ids back to orthographic forms in the source table.
    """

    def __init__(
        self,
        table_path: str | Path,
        scorer_path: str | Path,
        *,
        forms_path: str | Path | None = None,
    ) -> None:
        self.table_path = Path(table_path)
        self.scorer_path = Path(scorer_path)
        self.table = load_cognate_table(
            self.table_path,
            forms_path=forms_path,
        )
        with self.scorer_path.open("rb") as f:
            self.scorer = tomllib.load(f)
        self._forms_cache: dict[str, dict[str, tuple[str, str, str]]] = {}

    def _forms_by_cognateset(
        self,
        form_col: str,
        id_col: str = "UEW_ID",
    ) -> dict[str, tuple[str, str, str]]:
        cache_key = f"{form_col}\0{id_col}"
        if cache_key not in self._forms_cache:
            self._forms_cache[cache_key] = _index_cognateset_forms(
                self.table,
                form_col,
                id_col,
            )
        return self._forms_cache[cache_key]

    def etymologies(
        self,
        tok_a: str,
        tok_b: str,
        *,
        sep: str = " < ",
        form_col: str = "form",
        id_col: str = "UEW_ID",
    ) -> str:
        """Return comma-separated etymology pairs for a sound correspondence.

        Looks up ``tok_a`` and ``tok_b`` in the scorer's ``Cognateset_IDs``
        mapping, then resolves each id to descendant and ancestor surface forms
        from :attr:`table`.

        Parameters
        ----------
        tok_a:
            Descendant-language segment (left-hand side of the correspondence).
        tok_b:
            Ancestor-language segment (right-hand side).
        sep:
            Separator between the two forms in each pair. Default ``" < "``.
        form_col:
            Column name holding orthographic forms in :attr:`table`.
            Default ``"form"``.
        id_col:
            Column name holding the entry id shown in parentheses after each
            form. Default ``"UEW_ID"``. Pass ``""`` to omit ids.

        Returns
        -------
        str
            Comma-separated ``desc (UEW № id){sep}anc (id)`` pairs. Only the
            first parenthesis in the output includes the ``UEW №`` prefix;
            later ones contain the id alone.

        Examples
        --------
        >>> lookup = CorrespondenceLookup(table_path, scorer_path)
        >>> lookup.etymologies("t", "d", form_col="Form")
        'tata (UEW № 1) < dada (1), tirili (2) < dirili (2)'
        """
        cognateset_ids = _lookup_cognateset_ids(
            self.scorer.get("Cognateset_IDs", {}),
            tok_a,
            tok_b,
            " < ",
        )
        if not cognateset_ids:
            return ""

        forms_by_id = self._forms_by_cognateset(form_col, id_col)
        pairs: list[str] = []
        first_id = True
        for cognateset_id in cognateset_ids:
            entry = forms_by_id.get(cognateset_id)
            if entry is None:
                continue
            desc_form, anc_form, entry_id = entry
            if id_col and entry_id:
                if first_id:
                    desc_part = f"{desc_form} (UEW № {entry_id})"
                    first_id = False
                else:
                    desc_part = f"{desc_form} ({entry_id})"
                pair = f"{desc_part}{sep}{anc_form} ({entry_id})"
            else:
                pair = f"{desc_form}{sep}{anc_form}"
            pairs.append(pair)
        return ", ".join(pairs)
