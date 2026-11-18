import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('release_check', ROOT / 'scripts/check_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class HistoryReleaseTests(unittest.TestCase):
    def test_missing_sibling_or_implicit_recording_blocks_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('paranoid', 'paranoid-gain', 'paranoid-record'):
                shutil.copytree(ROOT / 'skills' / name, root / 'skills' / name,
                                ignore=shutil.ignore_patterns('__pycache__'))
            self.assertEqual(release.check_history_package(root), [])
            agent = root / 'skills/paranoid-record/agents/openai.yaml'
            agent.write_text(agent.read_text().replace('allow_implicit_invocation: false', 'allow_implicit_invocation: true'))
            self.assertTrue(release.check_history_package(root))
            (root / 'skills/paranoid/scripts/control_history.py').unlink()
            self.assertTrue(any('control_history.py' in error for error in release.check_history_package(root)))
