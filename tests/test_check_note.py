import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_note.py"


class CheckNoteTests(unittest.TestCase):
    def run_check(self, note_text, files=()):
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary)
            note = vault / "course" / "lesson.md"
            note.parent.mkdir()
            note.write_text(note_text, encoding="utf-8")
            for name in files:
                path = vault / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(note), "--vault", str(vault)],
                capture_output=True,
                text=True,
            )

    def test_resolves_existing_wikilinks_and_relative_images(self):
        result = self.run_check(
            "[[05.pdf]]\n[[Lecture 04|上一讲]]\n![图](assets/fig-05.png)\n",
            ["course/05.pdf", "other/Lecture 04.md", "course/assets/fig-05.png"],
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reports_missing_note_and_image_with_line_numbers(self):
        result = self.run_check("[[Missing]]\n![图](assets/missing.png)\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("1: unresolved wiki link: Missing", result.stdout)
        self.assertIn("2: missing local file: assets/missing.png", result.stdout)

    def test_ignores_links_in_fenced_code_and_external_urls(self):
        result = self.run_check(
            "```markdown\n[[Example]]\n![x](missing.png)\n```\n"
            "[Docs](https://example.com)\n[[#本节]]\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_does_not_resolve_image_link_as_markdown_note(self):
        result = self.run_check("![[assets/diagram.png]]\n", ["course/assets/diagram.md"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved wiki link: assets/diagram.png", result.stdout)


if __name__ == "__main__":
    unittest.main()
