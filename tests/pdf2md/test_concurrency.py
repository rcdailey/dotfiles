from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "home" / "dot_local" / "bin" / "executable_pdf2md"


class ConcurrentCacheTest(unittest.TestCase):
    def test_parallel_invocations_convert_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = root / "modules"
            (modules / "markitdown").mkdir(parents=True)
            (modules / "pdfminer").mkdir()
            (modules / "markitdown" / "__init__.py").write_text(
                "import os\n"
                "import time\n"
                "from types import SimpleNamespace\n"
                "class MarkItDown:\n"
                "    def convert(self, path):\n"
                "        with open(os.environ['CONVERSION_LOG'], 'a') as log:\n"
                "            log.write('convert\\n')\n"
                "        time.sleep(1)\n"
                "        return SimpleNamespace(text_content='converted')\n",
                encoding="utf-8",
            )
            (modules / "pdfminer" / "__init__.py").write_text("", encoding="utf-8")
            (modules / "pdfminer" / "high_level.py").write_text(
                "def extract_text(path):\n    return 'x' * 100\n",
                encoding="utf-8",
            )
            (modules / "pdfminer" / "pdfpage.py").write_text(
                "class PDFPage:\n"
                "    @staticmethod\n"
                "    def get_pages(file):\n"
                "        return [object()]\n",
                encoding="utf-8",
            )

            source = root / "document.pdf"
            source.write_bytes(b"pdf")
            conversion_log = root / "conversions.log"
            env = os.environ | {
                "CONVERSION_LOG": str(conversion_log),
                "PYTHONPATH": str(modules),
                "XDG_CACHE_HOME": str(root / "cache"),
            }

            processes = [
                subprocess.Popen(
                    [sys.executable, str(SCRIPT), str(source)],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for _ in range(4)
            ]
            results = [process.communicate(timeout=10) for process in processes]

            for process, (stdout, stderr) in zip(processes, results, strict=True):
                self.assertEqual(process.returncode, 0, stderr)
                self.assertIn("converted", stdout)
            self.assertEqual(conversion_log.read_text(encoding="utf-8"), "convert\n")


if __name__ == "__main__":
    unittest.main()
