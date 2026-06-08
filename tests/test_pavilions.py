"""Unit tests for pavilion walk-sheet location resolution (src/pavilions.py).

Run: python -m unittest discover -s tests
"""

import os
import unittest
from unittest import mock

from src import pavilions


class _Dog:
    def __init__(self, id, name, outcome_date=None):
        self.id = id
        self.name = name
        self.outcome_date = outcome_date


# A4 has an accent; A1/A3 share a name; A5 ("Bell") is a fuzzy decoy for "Bella".
ROSTER = [
    _Dog("A1", "Bella"),
    _Dog("A2", "Max"),
    _Dog("A3", "Bella"),
    _Dog("A4", "Señorita"),
    _Dog("A5", "Bell"),
]


class ResolveNameTests(unittest.TestCase):
    def setUp(self):
        self.index = pavilions._build_name_index(ROSTER)
        self.names = list(self.index.keys())

    def test_exact_unique(self):
        self.assertEqual(
            pavilions._resolve_name("Max", self.index, self.names, {}), "A2"
        )

    def test_normalization_is_case_and_space_insensitive(self):
        self.assertEqual(
            pavilions._resolve_name("  mAx  ", self.index, self.names, {}), "A2"
        )

    def test_duplicate_name_dropped(self):
        self.assertIsNone(pavilions._resolve_name("bella", self.index, self.names, {}))

    def test_fuzzy_match_above_cutoff(self):
        self.assertEqual(
            pavilions._resolve_name("Maxx", self.index, self.names, {}), "A2"
        )

    def test_fuzzy_below_cutoff_dropped(self):
        self.assertIsNone(pavilions._resolve_name("Zeus", self.index, self.names, {}))

    def test_fuzzy_tie_is_dropped(self):
        # Two active names both clear the cutoff -> ambiguous, must drop.
        dogs = [_Dog("C1", "Charlie"), _Dog("C2", "Charlene")]
        idx = pavilions._build_name_index(dogs)
        self.assertIsNone(pavilions._resolve_name("Charle", idx, list(idx.keys()), {}))

    def test_empty_name_dropped(self):
        self.assertIsNone(pavilions._resolve_name("", self.index, self.names, {}))

    def test_alias_resolves_hard_misread(self):
        self.assertEqual(
            pavilions._resolve_name("sra", self.index, self.names, {"sra": "Señorita"}),
            "A4",
        )

    def test_alias_to_duplicate_is_dropped(self):
        self.assertIsNone(
            pavilions._resolve_name("bela", self.index, self.names, {"bela": "Bella"})
        )

    def test_alias_does_not_fall_through_to_fuzzy(self):
        # Alias target ("Bella") is no longer in the roster; "Bell" is active and
        # similar — but an alias must never fuzzy-match to a different dog.
        roster = [d for d in ROSTER if d.name != "Bella"]
        idx = pavilions._build_name_index(roster)
        self.assertIsNone(
            pavilions._resolve_name("blla", idx, list(idx.keys()), {"blla": "Bella"})
        )


class ResolveLocationsTests(unittest.TestCase):
    def _run(self, state, aliases=None):
        with (
            mock.patch.object(pavilions, "_fetch_state", return_value=state),
            mock.patch.object(pavilions, "_load_aliases", return_value=aliases or {}),
            mock.patch.dict(os.environ, {"PAVILION_API_BASE": "https://x.test"}),
        ):
            return pavilions.resolve_locations(ROSTER)

    def test_no_endpoint_is_noop(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PAVILION_API_BASE", None)
            self.assertEqual(pavilions.resolve_locations(ROSTER), {})

    def test_basic_match(self):
        self.assertEqual(
            self._run({"pavilions": {"C": {"kennels": {"70": "Max"}}}}),
            {"A2": "C-70"},
        )

    def test_same_dog_two_kennels_is_dropped(self):
        # One dog resolved to two distinct kennels is ambiguous -> no badge.
        loc = self._run({"pavilions": {"C": {"kennels": {"70": "Max", "71": "Max"}}}})
        self.assertEqual(loc, {})

    def test_invalid_pavilion_and_kennel_skipped(self):
        loc = self._run(
            {
                "pavilions": {
                    "X": {"kennels": {"70": "Max"}},  # bad pavilion
                    "C": {"kennels": {"abc": "Max"}},  # bad kennel
                }
            }
        )
        self.assertEqual(loc, {})

    def test_alias_used_end_to_end(self):
        loc = self._run(
            {"pavilions": {"D": {"kennels": {"5": "sra"}}}},
            aliases={"sra": "Señorita"},
        )
        self.assertEqual(loc, {"A4": "D-5"})

    def test_flag_suppresses_badge(self):
        loc = self._run(
            {
                "pavilions": {"C": {"kennels": {"70": "Max"}}},
                "flags": ["C-70"],
            }
        )
        self.assertEqual(loc, {})

    def test_override_sets_location(self):
        loc = self._run({"overrides": {"A1": "B-3"}})
        self.assertEqual(loc, {"A1": "B-3"})

    def test_override_beats_flag_and_ocr(self):
        loc = self._run(
            {
                "pavilions": {"C": {"kennels": {"70": "Max"}}},  # A2 -> C-70
                "flags": ["C-70"],  # would clear A2
                "overrides": {"A2": "C-70"},  # override wins
            }
        )
        self.assertEqual(loc, {"A2": "C-70"})

    def test_override_clear_removes_badge(self):
        loc = self._run(
            {
                "pavilions": {"C": {"kennels": {"70": "Max"}}},
                "overrides": {"A2": None},
            }
        )
        self.assertEqual(loc, {})

    def test_override_for_unknown_dog_ignored(self):
        self.assertEqual(self._run({"overrides": {"ZZZ": "C-1"}}), {})

    def test_override_with_bad_pk_ignored(self):
        self.assertEqual(self._run({"overrides": {"A1": "not-a-pk"}}), {})


if __name__ == "__main__":
    unittest.main()
