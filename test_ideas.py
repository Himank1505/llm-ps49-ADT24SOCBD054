"""Tests that run without an API key: a fake LLM function replaces the Gemini call."""
import json
import unittest

import ideas

GOOD = [{"title": f"Idea {i}", "description": "Does X. Helps Y.", "tools": ["Python", "Streamlit", "SQLite"],
         "modules": ["Setup", "Core logic", "UI"], "difficulty": d, "estimated_time": "10 days", "outcome": "Live demo"}
        for i, d in enumerate(["Easy", "Medium", "Hard", "easy", "MEDIUM"], 1)]


class TestIdeas(unittest.TestCase):
    def test_prompt_contains_inputs(self):
        p = ideas.build_prompt("Cybersecurity", "Beginner", 3)
        for text in ("Cybersecurity", "Beginner", "3 week(s)", "exactly 5"):
            self.assertIn(text, p)

    def test_parse_plain_json(self):
        out = ideas.parse_ideas(json.dumps(GOOD))
        self.assertEqual(len(out), 5)
        self.assertEqual([i["difficulty"] for i in out], ["Easy", "Medium", "Hard", "Easy", "Medium"])

    def test_parse_fenced_and_chatty_reply(self):
        reply = "Sure! Here you go:\n```json\n" + json.dumps(GOOD) + "\n```\nHope this helps."
        self.assertEqual(len(ideas.parse_ideas(reply)), 5)

    def test_parse_wrapped_object_and_string_lists(self):
        item = dict(GOOD[0], tools="Python, Flask, SQLite", modules="Setup; Core; UI")
        out = ideas.parse_ideas(json.dumps({"ideas": [item]}))
        self.assertEqual(out[0]["tools"], ["Python", "Flask", "SQLite"])
        self.assertEqual(out[0]["modules"], ["Setup", "Core", "UI"])

    def test_unknown_difficulty_defaults_to_medium(self):
        out = ideas.parse_ideas(json.dumps([dict(GOOD[0], difficulty="Insane")]))
        self.assertEqual(out[0]["difficulty"], "Medium")

    def test_items_missing_fields_are_skipped(self):
        out = ideas.parse_ideas(json.dumps([GOOD[0], {"title": "No other fields"}]))
        self.assertEqual(len(out), 1)

    def test_garbage_raises(self):
        with self.assertRaises(Exception):
            ideas.parse_ideas("I cannot help with that.")

    def test_retry_once_then_success(self):
        replies = iter(["not json at all", json.dumps(GOOD)])
        out = ideas.generate_ideas("AI", "Beginner", 2, "key", llm=lambda p, k: next(replies))
        self.assertEqual(len(out), 5)

    def test_gives_up_after_two_bad_replies(self):
        with self.assertRaises(ValueError):
            ideas.generate_ideas("AI", "Beginner", 2, "key", llm=lambda p, k: "nope")

    def test_markdown_export(self):
        md = ideas.ideas_to_markdown(ideas.parse_ideas(json.dumps(GOOD)), "AI", "Beginner", 2)
        self.assertIn("## 1. Idea 1", md)


if __name__ == "__main__":
    unittest.main()
