import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import generate_profile_cards as cards


class ProfileCardsTests(unittest.TestCase):
    def test_recent_repositories_filter_and_sort(self):
        def repo(name, **extra):
            return dict(name=name, fork=False, archived=False, size=1,
                        pushed_at="2026-01-01T00:00:00Z", **extra)
        older = repo("older")
        newer = repo("newer")
        newer["pushed_at"] = "2026-02-01T00:00:00Z"
        fork = repo("fork")
        fork["fork"] = True
        archived = repo("archived")
        archived["archived"] = True
        empty = repo("empty")
        empty["size"] = 0
        self.assertEqual(cards.recent_repositories([older, fork, archived, empty, repo(cards.USER), newer]), [newer, older])

    def test_readme_refresh_preserves_manual_content_and_versions_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            readme = root / "README.md"
            readme.write_text('Intro\n<!-- RECENT-REPOS:START -->old<!-- RECENT-REPOS:END -->\nFooter\n'
                              + '\n'.join(f'<img src="./profile/{name}.svg"/>' for name in ("banner", "stats", "top-langs", "streak")))
            for name in ("banner", "stats", "top-langs", "streak"):
                (root / f"{name}.svg").write_text("<svg/>")
            cards.update_recent_repositories(readme, [])
            cards.update_image_urls(readme, root)
            first = readme.read_text()
            self.assertTrue(first.startswith("Intro\n"))
            self.assertIn("Footer", first)
            self.assertNotIn("-->old<!--", first)
            self.assertEqual(first.count("?v="), 4)
            cards.update_image_urls(readme, root)
            self.assertEqual(first, readme.read_text())
            (root / "stats.svg").write_text("<svg>changed</svg>")
            cards.update_image_urls(readme, root)
            self.assertNotEqual(first, readme.read_text())

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
