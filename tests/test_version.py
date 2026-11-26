import os, re, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import asynchttp


class Version(unittest.TestCase):
    def test_package_and_pyproject_match(self):
        v = re.search(r'^version = "([^"]+)"', open(os.path.join(ROOT, "pyproject.toml")).read(), re.M).group(1)
        self.assertEqual(v, asynchttp.__version__)
        self.assertIn(f"## {v}", open(os.path.join(ROOT, "CHANGELOG.md")).read())


if __name__ == "__main__":
    unittest.main()
