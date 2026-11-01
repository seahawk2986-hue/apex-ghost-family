"""Importing Scripts/DeploySwarm.py must not deploy shards or write manifests."""
import importlib
import os
import sys
import unittest
from unittest import mock

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Scripts")


class DeploySwarmImportTest(unittest.TestCase):
    def test_import_spawns_no_children(self):
        sys.path.insert(0, SCRIPTS)
        try:
            sys.modules.pop("DeploySwarm", None)
            with mock.patch("subprocess.Popen") as popen:
                importlib.import_module("DeploySwarm")
            self.assertEqual(popen.call_count, 0,
                             f"import spawned {popen.call_count} child process(es)")
        finally:
            sys.modules.pop("DeploySwarm", None)
            sys.path.remove(SCRIPTS)


if __name__ == "__main__":
    unittest.main()
