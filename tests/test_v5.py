import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import server

class BasicTests(unittest.TestCase):
    def test_grouping(self):
        result = core.group_nas_files([{'path':'video/wan2.2/f.safetensors','size':10,'format':'SAFETENSORS'}])
        self.assertEqual(result[0]['bytes'],10)
        self.assertEqual(result[0]['files'],1)
    def test_memory_human(self):
        self.assertEqual(core.human(2*1024**3),'2.0 GiB')
    def test_local_token_entropy(self):
        self.assertGreaterEqual(len(server.TOKEN),32)
    def test_run_job_rejects_unregistered(self):
        with patch.object(core,'snapshot',return_value=([],0,0,'',[],None,None)),patch.object(core,'log_event'):
            with server.LOCK:
                server.STATE.update(busy=True,job='test',error=None)
            server.run_job('load','not-a-model',[])
            self.assertFalse(server.STATE['busy'])
            self.assertIn('no longer registered',server.STATE['error'])
    def test_classification(self):
        self.assertEqual(core.classify_nas_file('voice/qwen3-tts/model.safetensors')[0],'Speech / audio')
    def test_no_runtime_config_writes(self):
        src=(Path(__file__).resolve().parents[1]/'server.py').read_text()
        self.assertNotIn('systemctl enable',src)
        self.assertNotIn('docker run',src)

if __name__=='__main__': unittest.main()
