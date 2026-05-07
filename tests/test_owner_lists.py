import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bot.handlers_owner import _chunk_message_lines


class OwnerListChunkingTestCase(unittest.TestCase):
    def test_chunking_splits_long_booking_lists(self):
        lines = ["<b>Barcha buyurtmalar</b>"] + [f"Line {idx} {'x' * 120}" for idx in range(80)]

        chunks = _chunk_message_lines(lines, max_len=500)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 500 for chunk in chunks))
        self.assertIn("Line 0", chunks[0])
        self.assertIn("Line 79", chunks[-1])


if __name__ == "__main__":
    unittest.main()
