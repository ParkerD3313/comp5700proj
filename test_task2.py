import os
import sys
import yaml
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task2 import (
    load_yamls,
    compare_kde_names,
    compare_kde_and_requirements,
)


def _write_yaml(path, data: dict):
    nested = {}
    for i, (name, reqs) in enumerate(data.items(), start=1):
        nested[f"element{i}"] = {"name": name, "requirements": reqs}
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(nested, f, allow_unicode=True)


class TestTask2(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_load_yamls(self):
        p1 = os.path.join(self.tmpdir, "a.yaml")
        p2 = os.path.join(self.tmpdir, "b.yaml")
        _write_yaml(p1, {"anonymous-auth": ["3.2.1 Ensure anon auth disabled"]})
        _write_yaml(p2, {"audit logging": ["2.1.1 Enable audit logs"]})
        d1, d2 = load_yamls(p1, p2)
        self.assertIn("anonymous-auth", d1)
        self.assertIn("audit logging", d2)

    def test_compare_kde_names(self):
        d1 = {"kde-only-in-1": ["r1"], "common": ["r2"]}
        d2 = {"common": ["r2"]}
        out = os.path.join(self.tmpdir, "name_diff.txt")
        compare_kde_names(d1, d2, "f1.yaml", "f2.yaml", out)
        with open(out) as f:
            content = f.read()
        self.assertIn("kde-only-in-1", content)

    def test_compare_kde_and_requirements(self):
        d1 = {"shared-kde": ["req-only-in-1", "common-req"]}
        d2 = {"shared-kde": ["common-req"]}
        out = os.path.join(self.tmpdir, "full_diff.txt")
        compare_kde_and_requirements(d1, d2, "f1", "f2", out)
        with open(out) as f:
            content = f.read()
        self.assertIn("req-only-in-1", content)
        self.assertIn("ABSENT-IN", content)
        self.assertIn("PRESENT-IN", content)


if __name__ == "__main__":
    unittest.main()