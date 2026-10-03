import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from examples import EXAMPLES
from notes_engine import (
    NotesError,
    count_words,
    export_notes,
    generate_notes,
    reduction_percentage,
    request_ai,
    validate_ai_output,
    validate_input,
)

SOURCE = " ".join(["word"] * 100)

MOCK_OUTPUT = {
    "summary": "Plants use sunlight to produce food and release oxygen.",
    "key_points": [
        "Plants produce food.",
        "Oxygen is released.",
    ],
}

class StudyNotesTests(unittest.TestCase):
    def test_word_count(self):
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("Hello,\nworld!"), 2)
        self.assertEqual(
            count_words("Don't split well-known words; café is fine."),
            7,
        )

def test_reduction(self):
        self.assertEqual(reduction_percentage(100, 40), 60.0)
        self.assertEqual(reduction_percentage(3, 1), 66.67)
        self.assertEqual(reduction_percentage(10, 12), -20.0)

with self.assertRaises(ValueError):
            reduction_percentage(0, 0)

def test_invalid_input(self):
        for text in (
            None,
            "",
            "Too short.",
            "word " * 3001,
            "a" * 30001,
        ):
            with self.subTest(text_type=type(text).__name__):
                with self.assertRaises(NotesError):
                    validate_input(text)

def test_input_boundaries(self):
        for size in (30, 3000):
            self.assertEqual(
                count_words(validate_input("word " * size)),
                size,
            )

def test_three_examples_are_valid(self):
        self.assertEqual(len(EXAMPLES), 3)

for example in EXAMPLES:
            self.assertEqual(
                validate_input(example["text"]),
                example["text"],
            )

def test_missing_key(self):
        with self.assertRaises(NotesError):
            generate_notes(SOURCE, "")

def test_invalid_settings(self):
        with self.assertRaises(NotesError):
            generate_notes(SOURCE, "test-placeholder", ratio=0.9)

with self.assertRaises(NotesError):
            generate_notes(SOURCE, "invalid\nkey")

def test_success_and_export(self):
        result = generate_notes(
            SOURCE,
            "test-placeholder",
            requester=lambda *args, **kwargs: MOCK_OUTPUT,
        )

self.assertEqual(result["original_words"], 100)
        self.assertEqual(result["summary_words"], 9)
        self.assertEqual(result["reduction_percent"], 91.0)
        self.assertEqual(result["api_requests"], 1)
        self.assertIn("Text reduction: 91.00%", export_notes(result))
        self.assertNotIn("test-placeholder", json.dumps(result))

def test_retries_long_summary_once(self):
        attempts = []

def fake_request(*args, **kwargs):
            attempts.append(kwargs["retry"])

if kwargs["retry"]:
                return MOCK_OUTPUT

return {
                **MOCK_OUTPUT,
                "summary": "long " * 60,
            }

result = generate_notes(
            SOURCE,
            "test-placeholder",
            requester=fake_request,
        )

self.assertEqual(attempts, [False, True])
        self.assertEqual(result["api_requests"], 2)

def test_does_not_silently_truncate(self):
        with self.assertRaises(NotesError):
            generate_notes(
                SOURCE,
                "test-placeholder",
                requester=lambda *args, **kwargs: {
                    **MOCK_OUTPUT,
                    "summary": "long " * 60,
                },
            )

def test_invalid_model_output(self):
        invalid_outputs = [
            None,
            {},
            {**MOCK_OUTPUT, "summary": ""},
            {**MOCK_OUTPUT, "key_points": []},
            {**MOCK_OUTPUT, "key_points": ["Same", "same"]},
            {**MOCK_OUTPUT, "key_points": ["Valid", 42]},
        ]

for output in invalid_outputs:
            with self.subTest(output=output):
                with self.assertRaises(NotesError):
                    validate_ai_output(output)

def test_api_request_and_response(self):
        response = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": json.dumps(MOCK_OUTPUT),
                    },
                }
            ]
        }

with patch(
            "notes_engine.urlopen",
            return_value=io.BytesIO(json.dumps(response).encode()),
        ) as mocked:
            output = request_ai(SOURCE, "test-placeholder", 40)

self.assertEqual(output, MOCK_OUTPUT)

request = mocked.call_args.args[0]
        payload = json.loads(request.data)

self.assertEqual(
            payload["response_format"]["type"],
            "json_schema",
        )
        self.assertFalse(payload["store"])

def test_network_error(self):
        with patch(
            "notes_engine.urlopen",
            side_effect=URLError("Connection failed"),
        ):
            with self.assertRaises(NotesError):
                request_ai(SOURCE, "test-placeholder", 40)

def test_api_errors(self):
        for status in (400, 401, 403, 404, 429, 500):
            error = HTTPError(
                "https://example.invalid",
                status,
                "Private error details",
                {},
                None,
            )

with patch("notes_engine.urlopen", side_effect=error):
                with self.assertRaises(NotesError) as caught:
                    request_ai(SOURCE, "test-placeholder", 40)

self.assertNotIn(
                    "Private error details",
                    str(caught.exception),
                )

if __name__ == "__main__":
    unittest.main()
