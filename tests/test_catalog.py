import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_catalog", ROOT / "scripts/build_catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTests(unittest.TestCase):
    def test_committed_data_matches_only_the_authored_sources(self):
        data = catalog.compile_catalog()
        self.assertEqual(data, json.loads((ROOT / "web/dist/catalog.json").read_text()))
        self.assertEqual(len(data["entries"]), 700)
        self.assertEqual(len(data["categories"]), 28)
        self.assertEqual(data["entries"][-1]["id"], "RW-0700")
        self.assertTrue(all(e["origin"] == "synthetic_catalog" for e in data["entries"]))

    def test_duplicate_and_missing_source_entries_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog").mkdir()
            for name in catalog.SOURCES:
                (root / "catalog" / name).write_bytes((ROOT / "catalog" / name).read_bytes())
            path = root / "catalog" / catalog.SOURCES[0]
            original = path.read_text()
            rows = original.splitlines()
            rows[2] = rows[1]
            path.write_text("\n".join(rows))
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                catalog.compile_catalog(root)
            path.write_text("\n".join(original.splitlines()[0:1] + original.splitlines()[2:]))
            with self.assertRaisesRegex(ValueError, "Expected"):
                catalog.compile_catalog(root)


if __name__ == "__main__":
    unittest.main()
