import os
import sys
import json
import yaml
import unittest
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from task1 import (
    load_documents,
    zero_shot_prompt,
    few_shot_prompt,
    chain_of_thought_prompt,
    extract_kdes,
    collect_llm_output,
)


def _write_dummy_pdf(path, text="3.2.1 Ensure anonymous-auth is disabled"):
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, txt=text)
        pdf.output(path)
    except ImportError:
        content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
        body = (
            "%PDF-1.4\n"
            "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            f"4 0 obj\n<< /Length {len(content)} >>\nstream\n{content}\nendstream\nendobj\n"
            "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        )
        xref_offset = len(body)
        xref = (
            "xref\n0 6\n"
            "0000000000 65535 f \n"
            f"{body.index('1 0 obj'):010d} 00000 n \n"
            f"{body.index('2 0 obj'):010d} 00000 n \n"
            f"{body.index('3 0 obj'):010d} 00000 n \n"
            f"{body.index('4 0 obj'):010d} 00000 n \n"
            f"{body.index('5 0 obj'):010d} 00000 n \n"
        )
        trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
        with open(path, "w") as f:
            f.write(body + xref + trailer)


MOCK_LLM_RESPONSE = json.dumps([
    {"name": "anonymous-auth", "requirements": ["3.2.1 Ensure anonymous-auth is disabled"]}
])


class TestTask1(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_load_documents(self):
        p1 = os.path.join(self.tmpdir, "cis-r1.pdf")
        p2 = os.path.join(self.tmpdir, "cis-r2.pdf")
        _write_dummy_pdf(p1)
        _write_dummy_pdf(p2)
        doc1, doc2 = load_documents(p1, p2)
        self.assertIn("filename", doc1)
        self.assertIn("chunks", doc2)

    def test_zero_shot_prompt(self):
        result = zero_shot_prompt("3.2.1 Ensure anonymous-auth is disabled")
        self.assertIsInstance(result, str)
        self.assertIn("3.2.1 Ensure anonymous-auth is disabled", result)

    def test_few_shot_prompt(self):
        result = few_shot_prompt("3.1.1 Ensure file permissions are set")
        self.assertIsInstance(result, str)
        self.assertIn("3.1.1 Ensure file permissions are set", result)

    def test_chain_of_thought_prompt(self):
        result = chain_of_thought_prompt("2.1.1 Enable audit Logs")
        self.assertIsInstance(result, str)
        self.assertIn("2.1.1 Enable audit Logs", result)

    @patch("task1.run_gemma", return_value=MOCK_LLM_RESPONSE)
    @patch("task1.collect_llm_output")
    def test_extract_kdes(self, mock_collect, mock_gemma):
        doc = {
            "filename": "cis-r1.pdf",
            "filepath": os.path.join(self.tmpdir, "cis-r1.pdf"),
            "num_pages": 1,
            "num_chunks": 1,
            "pages": {},
            "chunks": ["3.2.1 Ensure anonymous-auth is disabled"],
            "full_text": "3.2.1 Ensure anonymous-auth is disabled",
        }
        output_txt = os.path.join(self.tmpdir, "output.txt")
        f1, f2 = extract_kdes(None, doc, doc, output_txt)
        self.assertTrue(os.path.exists(f1))
        with open(f1) as fh:
            data = yaml.safe_load(fh)
        self.assertIsInstance(data, dict)

    def test_collect_llm_output(self):
        output_file = os.path.join(self.tmpdir, "llm_output.txt")
        collect_llm_output(output_file, "my prompt", "Zero Shot", "llm result")
        with open(output_file, "r") as f:
            content = f.read()
        self.assertIn("*LLM Name*", content)
        self.assertIn("*Prompt Used*", content)
        self.assertIn("*Prompt Type*", content)
        self.assertIn("*LLM Output*", content)


if __name__ == "__main__":
    unittest.main()