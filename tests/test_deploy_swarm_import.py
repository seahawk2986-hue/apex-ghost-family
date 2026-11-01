"""Importing Scripts/DeploySwarm.py must not deploy shards or write manifests."""
import importlib.util
import os
import sys
import unittest
from unittest import mock

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Scripts")


class DeploySwarmImportTest(unittest.TestCase):
    def test_import_spawns_no_children_or_mutates_search_path(self):
        before = sys.path.copy()
        module_path = os.path.join(SCRIPTS, "DeploySwarm.py")
        spec = importlib.util.spec_from_file_location("DeploySwarm", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        with mock.patch("subprocess.Popen") as popen:
            spec.loader.exec_module(module)
        self.assertEqual(popen.call_count, 0,
                         f"import spawned {popen.call_count} child process(es)")
        self.assertEqual(sys.path, before,
                         "import changed the process-wide module search path")


if __name__ == "__main__":
    unittest.main()
