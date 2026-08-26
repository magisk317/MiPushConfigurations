#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

from build_index import load_json


class StrictJsonLoadingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "config.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_accepts_valid_utf8_json(self) -> None:
        self.path.write_text('{"配置": {"enabled": true}}', encoding="utf-8")

        self.assertEqual({"配置": {"enabled": True}}, load_json(self.path))

    def test_rejects_duplicate_keys_in_nested_objects(self) -> None:
        self.path.write_text(
            '{"config": {"enabled": true, "enabled": false}}',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "duplicate object key: enabled"):
            load_json(self.path)

    def test_rejects_utf8_bom(self) -> None:
        self.path.write_bytes(b"\xef\xbb\xbf{}")

        with self.assertRaisesRegex(ValueError, "UTF-8 BOM is not allowed"):
            load_json(self.path)

    def test_rejects_invalid_utf8(self) -> None:
        self.path.write_bytes(b'{"value":"\xff"}')

        with self.assertRaisesRegex(ValueError, "invalid UTF-8"):
            load_json(self.path)


if __name__ == "__main__":
    unittest.main()
