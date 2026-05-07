import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import bot


class RuntimeConfigTestCase(unittest.TestCase):
    def test_production_requires_redis_storage(self):
        env = {key: value for key, value in os.environ.items() if key != "REDIS_URL"}
        env["APP_ENV"] = "production"

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ValueError):
                bot.build_storage()


if __name__ == "__main__":
    unittest.main()
