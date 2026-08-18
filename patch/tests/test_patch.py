#!/usr/bin/python3
"""Minimal tests for patch_windows_connectivity_dll.

Run with:  python3 -m unittest discover patch/tests
       or:  python3 patch/tests/test_patch.py

The fixtures are the real WindowsConnectivity.dll shipped with two different
MyWhoosh releases (5.7.2 and 5.8.2), which use *different* method-body offsets.
That is exactly what the by-name lookup is meant to survive, so we assert the
patch lands on the right method in both.
"""

import glob
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # patch/ - the module under test

from patch_windows_connectivity_dll import (  # noqa: E402
    Assembly,
    MetadataError,
    PATCHED,
    TARGET_METHOD,
    TARGET_TYPE,
    patch_windows_connectivity_dll,
)

FIXTURES = sorted(glob.glob(os.path.join(HERE, "fixtures", "*.dll")))


class TestFindAndPatch(unittest.TestCase):
    def test_fixtures_present(self):
        self.assertTrue(FIXTURES, "no *.dll fixtures found")

    def test_find_method(self):
        for dll in FIXTURES:
            with self.subTest(dll=os.path.basename(dll)):
                with open(dll, "rb") as f:
                    asm = Assembly(f.read())
                found = asm.find_method(TARGET_TYPE, TARGET_METHOD)
                self.assertIsNotNone(found, "target method not located")
                rva, sig = found
                self.assertNotEqual(rva, 0, "method has no body")
                self.assertTrue(asm.returns_bool(sig), "return type not bool")

    def test_patch_then_idempotent(self):
        for dll in FIXTURES:
            with self.subTest(dll=os.path.basename(dll)):
                with tempfile.NamedTemporaryFile(suffix=".dll", delete=False) as tmp:
                    with open(dll, "rb") as src:
                        tmp.write(src.read())
                    path = tmp.name
                try:
                    # First patch succeeds and writes ldc.i4.1; ret at the body.
                    self.assertEqual(patch_windows_connectivity_dll(path), 0)
                    with open(path, "rb") as f:
                        data = f.read()
                    asm = Assembly(data)
                    rva, _ = asm.find_method(TARGET_TYPE, TARGET_METHOD)
                    off = asm.body_offset(rva)
                    self.assertEqual(data[off:off + len(PATCHED)], PATCHED)

                    # Re-running is a no-op and still succeeds.
                    self.assertEqual(patch_windows_connectivity_dll(path), 0)
                    with open(path, "rb") as f:
                        self.assertEqual(f.read(), data, "second patch changed bytes")
                finally:
                    os.unlink(path)

    def test_garbage_is_rejected(self):
        # A non-managed / corrupt file must skip gracefully (return 1), not crash.
        with tempfile.NamedTemporaryFile(suffix=".dll", delete=False) as tmp:
            tmp.write(b"MZ" + b"\x00" * 4096)  # looks like DOS, no valid PE
            path = tmp.name
        try:
            self.assertEqual(patch_windows_connectivity_dll(path), 1)
        finally:
            os.unlink(path)

    def test_not_a_pe(self):
        with self.assertRaises(MetadataError):
            Assembly(b"not a pe at all")


if __name__ == "__main__":
    unittest.main()
