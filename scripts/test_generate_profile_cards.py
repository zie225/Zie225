import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import generate_profile_cards as cards


class ProfileCardsTests(unittest.TestCase):
    def test_streak_today_and_yesterday(self):
        start = date(2026, 1, 1)
        def days(counts):
            return [(start + timedelta(days=i), n) for i, n in enumerate(counts)]
        self.assertEqual(cards.streaks(days([1, 1, 0, 1, 1, 1])), (3, 3))
        self.assertEqual(cards.streaks(days([1, 1, 0])), (2, 2))
        self.assertEqual(cards.streaks(days([1, 0, 0])), (0, 1))
        self.assertEqual(cards.streaks(days([0, 0])), (0, 0))

    def test_calendar_requires_complete_counts(self):
        parser = cards.CalendarParser()
        parser.feed('<td id="day" data-date="2026-01-01"></td>')
        with self.assertRaises(ValueError):
            parser.days()

    def test_calendar_reads_real_tooltip_format(self):
        parser = cards.CalendarParser()
        start = date(2025, 1, 1)
        for i in range(365):
            label = "1,234 contributions" if i == 364 else "No contributions"
            parser.feed(f'<td id="d{i}" data-date="{start + timedelta(days=i)}"></td>'
                        f'<tool-tip for="d{i}">{label} on January 1st.</tool-tip>')
        days = parser.days()
        self.assertEqual(len(days), 365)
        self.assertEqual(sum(n for _, n in days), 1234)

    def test_api_failure_keeps_existing_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in ("stats", "top-langs", "streak"):
                (output / f"{name}.svg").write_text("last good card")
            with patch.object(cards, "PROFILE_DIR", output), patch.object(cards, "api", side_effect=RuntimeError("API rate limit")):
                with self.assertRaises(RuntimeError):
                    cards.generate()
            self.assertTrue(all(p.read_text() == "last good card" for p in output.iterdir()))


if __name__ == "__main__":
    unittest.main()
