import unittest

from scripts.claude_review import diff_stats, heuristic_review, pr_diff_url


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+API_TOKEN = "example"
+def export_data():
+    return "ok"
diff --git a/tests/test_app.py b/tests/test_app.py
index 3333333..4444444 100644
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -1,2 +1,3 @@
+def test_export_data():
+    assert True
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_pr_diff_url(self):
        self.assertEqual(
            pr_diff_url("https://github.com/owner/repo/pull/123"),
            "https://github.com/owner/repo/pull/123.diff",
        )

    def test_diff_stats(self):
        stats = diff_stats(SAMPLE_DIFF)
        self.assertEqual(stats.files, ["app.py", "tests/test_app.py"])
        self.assertEqual(stats.additions, 5)
        self.assertEqual(stats.deletions, 0)
        self.assertEqual(stats.hunks, 2)

    def test_structured_review_contains_required_sections(self):
        review = heuristic_review("https://github.com/owner/repo/pull/123", SAMPLE_DIFF)
        self.assertIn("## Summary", review)
        self.assertIn("## Identified Risks", review)
        self.assertIn("## Improvement Suggestions", review)
        self.assertIn("## Confidence", review)
        self.assertIn("Potential secret", review)


if __name__ == "__main__":
    unittest.main()
