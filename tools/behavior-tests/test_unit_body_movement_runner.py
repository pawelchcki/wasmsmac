"""No game/server/browser. Unicode, scoped identity and cheap real OS wait proofs."""
from pathlib import Path
import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from state_trace import unit_body_movement_runner as runner


def packet(start,text):return dict(start_utf16=start,end_utf16=start+len(text.encode('utf-16-le',errors='surrogatepass'))//2,text=text)

class MovementRunnerTests(unittest.TestCase):
    def test_valid_utf16_surrogate_split_joins_actual_utf8(self):
        rows=[packet(0,'a\ud83d'),packet(2,'\ude80z')]
        self.assertEqual(runner.audit_chunks('a🚀z',[json.dumps(p) for p in rows]),2)

    def test_missing_reordered_or_unequal_chunks_reject(self):
        rows=[packet(0,'a'),packet(1,'b')]
        for values in (rows[:1],rows[::-1],[dict(rows[0],end_utf16=2),rows[1]],rows+[packet(2,'x')]):
            with self.subTest(values=values),self.assertRaises(AssertionError):runner.audit_chunks('ab',[json.dumps(p) for p in values])

    def test_unpaired_surrogate_tail_remains_unsupported(self):
        with self.assertRaises(UnicodeError):runner.audit_chunks('a',[json.dumps(packet(0,'a\ud83d'))])

    def test_pid_reuse_does_not_claim_foreign_children(self):
        current={10:dict(pid=10,start_ticks=99,ppid=1),11:dict(pid=11,start_ticks=3,ppid=10)}
        with patch.object(runner,'process_table',return_value=(current,0)):
            result=runner.own_sample(10,{10:2})
        self.assertEqual(result['observed_owned'],[]);self.assertFalse(result['exhaustive_host_inventory'])

    def test_reparented_same_identity_is_retained_and_foreign_sibling_omitted(self):
        current={11:dict(pid=11,start_ticks=3,ppid=1),12:dict(pid=12,start_ticks=4,ppid=999)}
        with patch.object(runner,'process_table',return_value=(current,0)):
            result=runner.own_sample(10,{10:2,11:3})
        self.assertEqual([r['pid'] for r in result['observed_owned']],[11])

    def child(self,code,**changes):
        limits=dict(runner.BUDGETS);limits.update(outer_seconds=2,term_seconds=.2,kill_wait_seconds=1,cleanup_seconds=.1,postkill_seconds=.1);limits.update(changes)
        with tempfile.TemporaryDirectory() as directory:
            result,raw=runner.capture_child([sys.executable,'-c',code],cwd=Path(directory),env=dict(os.environ),out=Path(directory),limits=limits)
            self.assertTrue((Path(directory)/'owned-process.json').exists())
        self.assertFalse(result['exhaustive_host_descendants_supported'])
        self.assertEqual(result['owned_group_after_cleanup'],'absent');self.assertEqual(result['tracked_descendants_after_cleanup'],[])
        return result,raw

    def test_real_owned_zero_child_is_os_waited(self):
        result,raw=self.child("print('owned-child-only',flush=True)")
        self.assertEqual(result['raw_node_exit'],0);self.assertTrue(result['os_wait_completed'])
        self.assertIn(b'owned-child-only',raw);self.assertFalse(result['forced_cleanup']);self.assertFalse(result['outer_timeout'])

    def test_real_nonzero_cannot_be_promoted_by_printed_pass(self):
        result,raw=self.child("print('GLSMAC exited (0)\\nAll tests passed.',flush=True);raise SystemExit(7)")
        self.assertEqual(result['raw_node_exit'],7);self.assertTrue(result['os_wait_completed'])
        self.assertIn(b'All tests passed.',raw)
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(AssertionError):runner.audit({},result,Path(directory))

    def test_real_deadline_term_and_kill_oswait_are_bounded(self):
        result,raw=self.child("import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('ready-only',flush=True);time.sleep(10)",outer_seconds=.2)
        self.assertTrue(result['outer_timeout']);self.assertTrue(result['forced_cleanup']);self.assertTrue(result['os_wait_completed'])
        self.assertEqual(result['raw_node_exit'],-signal.SIGKILL);self.assertLess(result['elapsed_seconds'],3)
        self.assertIn(b'ready-only',raw)

    def test_unknown_kill_wait_is_not_inferred_zero_and_no_unbounded_communicate(self):
        class Unknown:
            pid=7654321;returncode=None
            def __init__(self):self.timeouts=[]
            def communicate(self,timeout):
                self.timeouts.append(timeout);raise subprocess.TimeoutExpired(['fake'],timeout,output=b'partial')
        process=Unknown()
        sample=dict(observed_owned=[],node_visible=False,exhaustive_host_inventory=False)
        limits=dict(runner.BUDGETS,outer_seconds=.001,term_seconds=.001,kill_wait_seconds=.001,cleanup_seconds=.001,postkill_seconds=.001)
        with tempfile.TemporaryDirectory() as directory,patch.object(runner.subprocess,'Popen',return_value=process),patch.object(runner,'own_sample',return_value=sample),patch.object(runner,'group_probe',return_value='absent'),patch.object(runner.os,'killpg'):
            result,raw=runner.capture_child(['fake'],cwd=Path(directory),env={},out=Path(directory),limits=limits)
        self.assertIsNone(result['raw_node_exit']);self.assertFalse(result['os_wait_completed']);self.assertTrue(result['kill_wait_incomplete'])
        self.assertEqual(raw,b'partial');self.assertTrue(all(t is not None and t>0 for t in process.timeouts))

    def test_browser_fixture_source_has_no_backend_mutable_read_in_sampler(self):
        root=Path(__file__).resolve().parents[2]
        fixture=(root/'tools/wasm-tests/unit-body-movement-browser-fixture.mjs').read_text()
        sample=fixture.split("if (phase == 'sampling') {",1)[1].split("if (phase == 'pending')",1)[0]
        for forbidden in ('get_unit(', 'get_tile(', 'has_pending_actions(', 'observer.read(', 'is_locked(', 'movement', 'project('):
            self.assertNotIn(forbidden,sample)
        self.assertIn("if (sampled < 29)",sample);self.assertIn('receipt_seq != null',sample)
        self.assertIn("timer(10,",fixture);self.assertNotIn('timer(0,',fixture)

    def test_proposed_profile_matches_fixed_executable_boundaries(self):
        self.assertEqual(runner.BUDGETS,dict(node_ms=180000,observation_ms=120000,outer_seconds=190,term_seconds=3,kill_wait_seconds=5,cleanup_seconds=8,postkill_seconds=2,census_calls=32,sample_delay_ms=10))
        self.assertEqual(runner.SOURCE,'23e54d08b7dbb00f6b42d325c180a8c868b30ee2')
        self.assertEqual(runner.DEFAULT,'a69dd4e0a9620f90bd12c8eb8636ca22e24ed47c')

if __name__=='__main__':unittest.main()
