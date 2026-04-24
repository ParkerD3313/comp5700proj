import os
import sys
import json
import unittest
import tempfile
import zipfile
import pandas as pd
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task3 import (
    load_task2_files,
    map_differences_to_controls,
    run_kubescape,
    export_kubescape_csv,
)


def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _make_kubescape_json(tmpdir):
    data = {
        "summaryDetails": {
            "controls": {
                "C-0262": {
                    "name": "Anonymous access enabled",
                    "severity": "High",
                    "status": "failed",
                    "ResourceCounters": {
                        "passedResources": 0,
                        "failedResources": 3,
                        "skippedResources": 0,
                        "excludedResources": 0,
                    },
                    "complianceScore": 0.0,
                    "score": 0.0,
                }
            }
        }
    }
    path = os.path.join(tmpdir, "ks_output.json")
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def _make_sample_df():
    return pd.DataFrame([{
        "control_id": "C-0262",
        "control_name": "Anonymous access enabled",
        "severity": "High",
        "status": "failed",
        "passed_resources": 0,
        "failed_resources": 3,
        "skipped_resources": 0,
        "excluded_resources": 0,
        "compliance_score": 0.0,
        "score": 0.0,
    }])


class TestTask3(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_load_task2_files(self):
        p1 = os.path.join(self.tmpdir, "name.txt")
        p2 = os.path.join(self.tmpdir, "full.txt")
        _write(p1, "kde-a\nkde-b\n")
        _write(p2, "kde-a,ABSENT-IN-f2,PRESENT-IN-f1,NA\n")
        l1, l2 = load_task2_files(p1, p2)
        self.assertEqual(l1, ["kde-a", "kde-b"])
        self.assertIn("kde-a,ABSENT-IN-f2,PRESENT-IN-f1,NA", l2)

    def test_map_differences_to_controls(self):
        lines1 = ["anonymous-auth"]
        lines2 = ["anonymous-auth,ABSENT-IN-f2,PRESENT-IN-f1,NA"]
        out = os.path.join(self.tmpdir, "controls.txt")
        map_differences_to_controls(lines1, lines2, out)
        with open(out) as f:
            content = f.read()
        self.assertIn("C-0262", content)

    @patch("task3.subprocess.run")
    def test_run_kubescape(self, mock_run):
        ks_json = _make_kubescape_json(self.tmpdir)
        scan_dir = os.path.join(self.tmpdir, "project-yamls")
        os.makedirs(scan_dir)
        controls_file = os.path.join(self.tmpdir, "controls.txt")
        _write(controls_file, "C-0262\n")

        def fake_run(cmd, **kwargs):
            import shutil
            out_path = cmd[cmd.index("-o") + 1]
            shutil.copy(ks_json, out_path)

        mock_run.side_effect = fake_run
        df = run_kubescape(controls_file, scan_dir)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertIn("control_name", df.columns)

    def test_export_kubescape_csv(self):
        df = _make_sample_df()
        csv_path = os.path.join(self.tmpdir, "results.csv")
        export_kubescape_csv(df, csv_path, "project-yamls")
        loaded = pd.read_csv(csv_path)
        for col in ("FilePath", "Severity", "Control name", "Failed resources", "All Resources", "Compliance score"):
            self.assertIn(col, loaded.columns)


if __name__ == "__main__":
    unittest.main()