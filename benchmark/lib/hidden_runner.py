"""Run one hidden test module inside a workspace and print JSON counts.

Copied into the workspace next to the hidden tests and run as a subprocess, so the
code under test never runs inside the benchmark's own process.
"""

import json
import os
import sys
import unittest


def main(module):
    suite = unittest.defaultTestLoader.loadTestsFromName(module)
    result = unittest.TestResult()
    suite.run(result)
    failed = [str(t) for t, _ in result.failures + result.errors]
    print(json.dumps({"module": module, "run": result.testsRun, "failed": failed}))


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    main(sys.argv[1])
