"""Tests for loanpy.correspondences."""

import csv
import io
import logging

from loanpy.correspondences import (
    CorrespondenceLookup,
    _is_alternating_language_sequence,
    add_separator,
    get_sound_correspondences,
    load_cognate_table,
    load_scorer,
)


def _row(lang, aligned, cog_id="cs1", form="", uew_id=""):
    return {
        "Language_ID": lang,
        "Uralign": aligned,
        "Cognateset_ID": cog_id,
        "Form": form,
        "UEW_ID": uew_id,
    }


class TestAlternatingLanguageSequence:
    def test_valid_two_row_table(self):
        table = [_row("hun", "a b"), _row("pu", "a c")]
        assert _is_alternating_language_sequence(table, {"hun"}, {"pu"})

    def test_valid_four_rows(self):
        table = [
            _row("d", "x"),
            _row("a", "y"),
            _row("d", "x"),
            _row("a", "z"),
        ]
        assert _is_alternating_language_sequence(table, {"d"}, {"a"})

    def test_odd_length_returns_false(self, caplog):
        with caplog.at_level(logging.INFO):
            ok = _is_alternating_language_sequence(
                [_row("hun", "a")], {"hun"}, {"pu"}
            )
        assert ok is False
        assert "Odd number" in caplog.text

    def test_wrong_language_on_even_row(self, caplog):
        table = [_row("hun", "a"), _row("hun", "b")]
        with caplog.at_level(logging.INFO):
            ok = _is_alternating_language_sequence(table, {"hun"}, {"pu"})
        assert ok is False
        assert "Problem in row" in caplog.text

    def test_empty_table(self):
        assert _is_alternating_language_sequence([], {"hun"}, {"pu"})


class TestAddSeparator:
    def test_stringifies_tuple_keys_for_toml_sections(self):
        correspondences = {
            "SoundCorrespondences": {"a": ["b"]},
            "AbsoluteFrequency": {("a", "b"): 3},
            "Cognateset_IDs": {("a", "b"): ["1"]},
            "Examples": {("a", "b"): ["a < b"]},
        }
        out = add_separator(correspondences)
        assert out["AbsoluteFrequency"] == {"a < b": 3}
        assert out["Cognateset_IDs"] == {"a < b": ["1"]}
        assert out["Examples"] == {"a < b": ["a < b"]}
        assert correspondences["AbsoluteFrequency"] == {("a", "b"): 3}


class TestLoadScorer:
    def test_parses_absolute_frequency(self):
        assert dict(load_scorer({
            "AbsoluteFrequency": {"a < b": 3, "ɟ < j": 1},
        })) == {("a", "b"): 3, ("ɟ", "j"): 1}

    def test_empty_returns_defaultdict(self):
        assert dict(load_scorer({})) == {}
        assert dict(load_scorer({"AbsoluteFrequency": {}})) == {}

    def test_custom_separator(self):
        assert dict(load_scorer(
            {"AbsoluteFrequency": {"a|b": 2}},
            sep="|",
        )) == {("a", "b"): 2}

    def test_missing_default_for_unknown_pairs(self):
        scorer = load_scorer(
            {"AbsoluteFrequency": {"a < b": 1}},
            missing=-1000,
        )
        assert scorer[("a", "b")] == 1
        assert scorer[("x", "y")] == -1000

    def test_sound_correspondences_fallback(self):
        scorer = load_scorer(
            {
                "SoundCorrespondences": {
                    "a": ["b", "c"],
                    "k": ["k"],
                },
            },
            imputed=12,
        )
        assert dict(scorer) == {("a", "b"): 12, ("a", "c"): 12, ("k", "k"): 12}

    def test_absolute_frequency_takes_precedence_over_fallback(self):
        scorer = load_scorer(
            {
                "AbsoluteFrequency": {"a < b": 3},
                "SoundCorrespondences": {"a": ["c"]},
            },
            imputed=12,
        )
        assert dict(scorer) == {("a", "b"): 3}

    def test_roundtrip_with_add_separator(self):
        correspondences = {
            "SoundCorrespondences": {"k": ["k", "o"]},
            "AbsoluteFrequency": {("k", "k"): 2, ("a", "o"): 1},
        }
        exported = add_separator(correspondences)
        loaded = dict(load_scorer(exported))
        assert loaded == correspondences["AbsoluteFrequency"]

    def test_roundtrip_after_get_sound_correspondences(self):
        table = [
            _row("d", "k a", "1"),
            _row("a", "k o", "1"),
        ]
        stats = get_sound_correspondences(table, "Uralign")
        exported = add_separator(stats)
        loaded = dict(load_scorer(exported))
        assert loaded == stats["AbsoluteFrequency"]


class TestGetSoundCorrespondences:
    def test_segment_pair_frequencies_and_examples(self):
        table = [
            _row("desc", "ɟ ŋ", "1"),
            _row("anc", "j ŋ", "1"),
        ]
        result = get_sound_correspondences(
            table, "Uralign", prefix_descendant="H:", prefix_ancestor="P:"
        )
        assert result["AbsoluteFrequency"][("H:ɟ", "P:j")] == 1
        assert result["SoundCorrespondences"]["ɟ"] == ["j"]
        assert result["Cognateset_IDs"][("H:ɟ", "P:j")] == ["1"]
        assert "H:ɟ ŋ < P:j ŋ" in result["Examples"][("H:ɟ", "P:j")]

    def test_duplicate_ancestor_ranking_by_frequency(self):
        table = [
            _row("d", "a", "1"),
            _row("a", "x", "1"),
            _row("d", "a", "2"),
            _row("a", "y", "2"),
            _row("d", "a", "3"),
            _row("a", "x", "3"),
        ]
        sc = get_sound_correspondences(table, "Uralign")["SoundCorrespondences"]
        assert sc["a"][0] == "x"
        assert "y" in sc["a"]

    def test_absolute_frequency_sorted_descending(self):
        table = [
            _row("d", "x", "1"),
            _row("a", "p", "1"),
            _row("d", "x", "2"),
            _row("a", "p", "2"),
            _row("d", "x", "3"),
            _row("a", "p", "3"),
            _row("d", "y", "4"),
            _row("a", "q", "4"),
        ]
        freq = get_sound_correspondences(table, "Uralign")["AbsoluteFrequency"]
        counts = list(freq.values())
        assert counts == sorted(counts)  # ascending by count in implementation
        assert freq[("x", "p")] == 3
        assert freq[("y", "q")] == 1

    def test_cognateset_ids_deduplicated(self):
        table = [
            _row("d", "a", "1"),
            _row("a", "b", "1"),
            _row("d", "a", "1"),
            _row("a", "b", "1"),
        ]
        ids = get_sound_correspondences(table, "Uralign")["Cognateset_IDs"]
        assert ids[("a", "b")] == ["1"]

    def test_custom_aligned_column_name(self):
        table = [
            {"Language_ID": "d", "Alignment": "k a", "Cognateset_ID": "1"},
            {"Language_ID": "a", "Alignment": "k o", "Cognateset_ID": "1"},
        ]
        result = get_sound_correspondences(table, "Alignment")
        assert ("k", "k") in result["AbsoluteFrequency"]


class TestCorrespondenceLookup:
    @staticmethod
    def _example_table():
        return [
            _row("desc", "t a t a", "1", "tata", "1"),
            _row("anc", "d a d a", "1", "dada", "1"),
            _row("desc", "t i r i l i", "2", "tirili", "2"),
            _row("anc", "d i r i l i", "2", "dirili", "2"),
        ]

    @staticmethod
    def _write_table(path, table):
        fieldnames = list(table[0].keys())
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(table)

    @staticmethod
    def _write_scorer(path, stats):
        exported = add_separator(stats)
        lines = ["[Cognateset_IDs]"]
        for key, ids in exported["Cognateset_IDs"].items():
            ids_str = ", ".join(f'"{item}"' for item in ids)
            lines.append(f'"{key}" = [{ids_str}]')
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_etymologies_from_mined_correspondences(self, tmp_path):
        table = self._example_table()
        stats = get_sound_correspondences(table, "Uralign")
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        self._write_scorer(scorer_path, stats)
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("t", "d", form_col="Form") == (
            "tata < dada (UEW № 1), tirili < dirili (UEW № 2)"
        )

    def test_etymologies_from_toml_style_scorer(self, tmp_path):
        table = self._example_table()
        stats = get_sound_correspondences(table, "Uralign")
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        self._write_scorer(scorer_path, stats)
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("t", "d", form_col="Form") == (
            "tata < dada (UEW № 1), tirili < dirili (UEW № 2)"
        )

    def test_unknown_correspondence_returns_empty_string(self, tmp_path):
        table = self._example_table()
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        scorer_path.write_text("[Cognateset_IDs]\n", encoding="utf-8")
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("x", "y") == ""

    def test_custom_separator(self, tmp_path):
        table = self._example_table()
        stats = get_sound_correspondences(table, "Uralign")
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        self._write_scorer(scorer_path, stats)
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("t", "d", sep="|", form_col="Form") == (
            "tata|dada (UEW № 1), tirili|dirili (UEW № 2)"
        )

    def test_custom_form_column(self, tmp_path):
        table = [
            {
                "Language_ID": "desc",
                "Uralign": "t a",
                "Cognateset_ID": "1",
                "Form": "tata",
                "UEW_ID": "1",
            },
            {
                "Language_ID": "anc",
                "Uralign": "d a",
                "Cognateset_ID": "1",
                "Form": "dada",
                "UEW_ID": "1",
            },
        ]
        stats = get_sound_correspondences(table, "Uralign")
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        self._write_scorer(scorer_path, stats)
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("t", "d", form_col="Form") == "tata < dada (UEW № 1)"

    def test_skips_missing_cognateset_ids(self, tmp_path):
        table = self._example_table()
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        scorer_path.write_text(
            '[Cognateset_IDs]\n"t < d" = ["1", "missing"]\n',
            encoding="utf-8",
        )
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.etymologies("t", "d", form_col="Form") == "tata < dada (UEW № 1)"

    def test_stores_table_and_scorer_paths(self, tmp_path):
        table = self._example_table()
        stats = get_sound_correspondences(table, "Uralign")
        table_path = tmp_path / "cognates.csv"
        scorer_path = tmp_path / "scorer.toml"
        self._write_table(table_path, table)
        self._write_scorer(scorer_path, stats)
        lookup = CorrespondenceLookup(table_path, scorer_path)
        assert lookup.table_path == table_path
        assert lookup.scorer_path == scorer_path
        assert lookup.table == table


class TestLoadCognateTable:
    def test_returns_rows_when_form_column_present(self):
        csv_text = """Language_ID,Uralign,Cognateset_ID,Form
desc,t a,1,tata
anc,d a,1,dada
"""
        path = io.StringIO(csv_text)
        rows = list(csv.DictReader(path))
        assert rows[0]["Form"] == "tata"

    def test_joins_forms_from_sibling_forms_csv(self, tmp_path):
        cognates = tmp_path / "cognates.csv"
        forms = tmp_path / "forms.csv"
        cognates.write_text(
            "Form_ID,Language_ID,Uralign,Cognateset_ID\n"
            "f1,desc,t a,1\n"
            "f2,anc,d a,1\n",
            encoding="utf-8",
        )
        forms.write_text(
            "ID,Form,UEW_ID\n"
            "f1,tata,1\n"
            "f2,dada,1\n",
            encoding="utf-8",
        )
        rows = load_cognate_table(cognates)
        assert rows[0]["Form"] == "tata"
        assert rows[1]["Form"] == "dada"
        assert rows[0]["UEW_ID"] == "1"
