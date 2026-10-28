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

    def helper(self,code):
        root=Path(__file__).resolve().parents[2]
        uri=(root/'tools/wasm-tests/unit-body-movement-browser-fixture.mjs').as_uri()
        script="import{movementChild}from"+json.dumps(uri)+";"+code
        env=dict(os.environ);env.pop('SMAC_ASSETS_DIR',None)
        completed=subprocess.run(['node','--input-type=module','-e',script],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=5,text=True)
        self.assertEqual(completed.returncode,0,completed.stdout)
        line=next(line for line in completed.stdout.splitlines() if line.startswith('RESULT|'))
        return json.loads(line.removeprefix('RESULT|'))

    def test_async_real_readonly_git_preserves_source_tree_and_waits(self):
        result=self.helper("const r=await movementChild('git',['rev-parse','HEAD:src'],{cwd:process.cwd()});console.log('RESULT|'+JSON.stringify(r));")
        self.assertEqual(result['stdout'].strip(),subprocess.check_output(['git','rev-parse','HEAD:src'],cwd=Path(__file__).resolve().parents[2],text=True).strip());self.assertEqual(result['status'],0)
        self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertIsNone(result['error'])
        self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])

    def test_async_git_in_actual_default_node_worker_has_persisted_body_receipt(self):
        root=Path(__file__).resolve().parents[2];uri=(root/'tools/wasm-tests/unit-body-movement-browser-fixture.mjs').as_uri()
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);receipt=folder/'actual-body.json';source=folder/'metadata-only.test.mjs'
            source.write_text("import{test}from'node:test';import assert from'node:assert/strict';import{writeFileSync}from'node:fs';import{movementChild}from"+json.dumps(uri)+";test('read-only metadata only',async()=>{const r=await movementChild('git',['rev-parse','HEAD:src'],{cwd:"+json.dumps(str(root))+"});writeFileSync("+json.dumps(str(receipt))+",JSON.stringify(r));assert.equal(r.error,null);assert.equal(r.status,0);assert.equal(r.wait_completed,true);});")
            env=dict(os.environ);env.pop('SMAC_ASSETS_DIR',None)
            limits=dict(runner.BUDGETS,outer_seconds=3,term_seconds=.2,kill_wait_seconds=.5,cleanup_seconds=.2,postkill_seconds=.2)
            outcome,raw=runner.capture_child(['node','--test','--test-concurrency=1',str(source)],cwd=root,env=env,out=folder,limits=limits)
            self.assertEqual(outcome['raw_node_exit'],0,raw.decode(errors='replace'));self.assertTrue(outcome['os_wait_completed'])
            self.assertEqual(outcome['owned_group_after_cleanup'],'absent');self.assertEqual(outcome['tracked_descendants_after_cleanup'],[])
            self.assertTrue(receipt.exists(),'No actual inner body receipt; file PASS alone is insufficient')
            result=json.loads(receipt.read_text());self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertEqual(result['status'],0)
            self.assertEqual(result['stdout'].strip(),subprocess.check_output(['git','rev-parse','HEAD:src'],cwd=Path(__file__).resolve().parents[2],text=True).strip())
            self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])

    def test_async_actual_nonzero_is_not_promoted_by_fake_pass_output(self):
        result=self.helper("const r=await movementChild('python3',['-c',\"print('All tests passed.');raise SystemExit(7)\"],{cwd:process.cwd()});console.log('RESULT|'+JSON.stringify(r));")
        self.assertEqual(result['status'],7);self.assertTrue(result['wait_completed']);self.assertIn('All tests passed.',result['stdout'])
        self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])

    def test_async_spawn_error_status_zero_counterexample_never_reports_exit_zero(self):
        result=self.helper("import cp from 'node:child_process';import{syncBuiltinESMExports}from'node:module';import{EventEmitter}from'node:events';import{PassThrough}from'node:stream';cp.spawn=()=>{const p=new EventEmitter();p.stdout=new PassThrough();p.stderr=new PassThrough();process.nextTick(()=>{const e=Object.assign(Error('spawn git EPERM'),{code:'EPERM',status:0});p.emit('error',e);});return p;};syncBuiltinESMExports();const r=await movementChild('git',['rev-parse','HEAD:src'],{cwd:process.cwd()});console.log('RESULT|'+JSON.stringify(r));")
        self.assertIsNone(result['status']);self.assertFalse(result['spawned']);self.assertFalse(result['wait_completed'])
        self.assertEqual(result['spawn_error_code'],'EPERM');self.assertIn('EPERM',result['error'])

    def test_async_timeout_kills_and_waits_owned_child(self):
        result=self.helper("const r=await movementChild('python3',['-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print(123,flush=True);time.sleep(10)'],{cwd:process.cwd(),timeout_ms:400,term_ms:50,kill_wait_ms:500});console.log('RESULT|'+JSON.stringify(r));")
        self.assertTrue(result['timed_out']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])
        self.assertNotEqual(result['status'],0);self.assertLess(result['elapsed_ms'],2000)
        self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])

    def test_async_cancellation_reaps_instead_of_leaving_owned_child(self):
        result=self.helper("const c=new AbortController();const p=movementChild('python3',['-c','import time;time.sleep(10)'],{cwd:process.cwd(),signal:c.signal,timeout_ms:1000,term_ms:50,kill_wait_ms:500});setTimeout(()=>c.abort(),200);const r=await p;console.log('RESULT|'+JSON.stringify(r));")
        self.assertTrue(result['cancelled']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])
        self.assertTrue(result['spawned']);self.assertTrue(result['wait_completed']);self.assertFalse(result['unknown_wait'])

    def test_async_signal_in_normal_after_hook_remains_usable(self):
        result=self.helper("import{test}from'node:test';test('cheap helper lifecycle only',async t=>{t.after(async()=>{const r=await movementChild('python3',['-c','print(1)'],{cwd:process.cwd(),signal:t.signal});console.log('RESULT|'+JSON.stringify(r));});});")
        self.assertFalse(result['cancelled']);self.assertEqual(result['status'],0);self.assertTrue(result['wait_completed'])

    def test_child_audit_rejects_error_status_zero_missing_wait_or_cancel(self):
        value=dict(command='git',args=['rev-parse','HEAD:src'],cwd='/tmp',pid=123,spawned=True,wait_completed=True,status=0,signal=None,error=None,spawn_error_code=None,timed_out=False,cancelled=False,output_limit=False,unknown_wait=False,timeout_ms=10000,term_ms=1000,kill_wait_ms=1000)
        runner.audited_child(value,'git',value['args'],'/tmp')
        for key,replacement in [('error','spawnSync git EPERM'),('spawned',False),('wait_completed',False),('cancelled',True),('timed_out',True),('pid',None),('status',True)]:
            with self.subTest(key=key),self.assertRaises(AssertionError):runner.audited_child(dict(value,**{key:replacement}),'git',value['args'],'/tmp')


    def test_reused_child_under_owned_parent_is_never_readopted(self):
        tracked={10:2,11:3}
        table={10:dict(pid=10,start_ticks=2,ppid=1),
               11:dict(pid=11,start_ticks=99,ppid=10),
               12:dict(pid=12,start_ticks=100,ppid=11)}
        with patch.object(runner,'process_table',return_value=(table,0)):
            sample=runner.own_sample(10,tracked)
        self.assertEqual([r['pid'] for r in sample['observed_owned']],[10])
        self.assertEqual(tracked,{10:2,11:3})

    def test_waited_pid_reused_by_foreign_group_is_never_signalled(self):
        def row(pid,start,ppid):return dict(pid=pid,start_ticks=start,ppid=ppid,pgid=100,session=100,state='S')
        original={100:row(100,1,1),101:row(101,2,100)}
        foreign={100:row(100,90,1),101:row(101,91,100)}
        class Waited:
            pid=100;returncode=0
            def communicate(self,timeout):return b'owned-wait-complete',b''
        with tempfile.TemporaryDirectory() as directory,patch.object(runner.subprocess,'Popen',return_value=Waited()),patch.object(runner,'process_table',side_effect=[(original,0),(foreign,0),(foreign,0)]),patch.object(runner,'group_probe',return_value='present'),patch.object(runner.os,'killpg') as group_signal,patch.object(runner.os,'kill') as pid_signal:
            result,raw=runner.capture_child(['dummy'],cwd=Path(directory),env={},out=Path(directory))
        self.assertTrue(result['os_wait_completed']);self.assertEqual(result['raw_node_exit'],0)
        self.assertTrue(result['group_ownership_unknown']);self.assertEqual(result['tracked_descendants_after_cleanup'],[])
        group_signal.assert_not_called();pid_signal.assert_not_called()

    def test_package_code_changes_reject_with_unchanged_manifests(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('playwright','playwright-core'):
                (root/name/'lib').mkdir(parents=True)
                (root/name/'package.json').write_text('{"version":"test"}')
                (root/name/'lib/driver.js').write_text('original executable bytes')
            pre=dict(dependency_symlink=str(root),dependency_contents_sha256=runner.dependency_contents(root))
            runner.unchanged_dependencies(pre)
            for name in ('playwright','playwright-core'):
                path=root/name/'lib/driver.js';original=path.read_text();path.write_text('modified executable bytes')
                with self.assertRaises(AssertionError):runner.unchanged_dependencies(pre)
                path.write_text(original)
            extra=root/'playwright/lib/added.js';extra.write_text('new executable bytes')
            with self.assertRaises(AssertionError):runner.unchanged_dependencies(pre)
            extra.unlink();(root/'playwright/lib/driver.js').unlink()
            with self.assertRaises(AssertionError):runner.unchanged_dependencies(pre)

    def test_unreadable_nested_package_directory_cannot_create_or_match_a_partial_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('playwright','playwright-core'):
                (root/name/'lib').mkdir(parents=True)
                (root/name/'package.json').write_text('{}')
                (root/name/'lib/driver.js').write_text('readable by a known executable path')
            baseline=runner.dependency_contents(root)
            actual_scandir=os.scandir
            for name in ('playwright','playwright-core'):
                for error in (PermissionError,OSError):
                    with self.subTest(package=name,error=error.__name__):
                        denied=root/name/'lib'
                        def denied_nested_listing(path):
                            if Path(path)==denied:raise error('deterministic inaccessible package directory')
                            return actual_scandir(path)
                        self.assertTrue((denied/'driver.js').read_bytes())
                        with patch.object(os,'scandir',side_effect=denied_nested_listing):
                            with self.assertRaises(error):runner.dependency_contents(root)
                            # Old rglob could prepare this partial map, then
                            # accept matching omissions during every post-scan.
                            partial=copy.deepcopy(baseline);partial[name].pop('lib/driver.js')
                            pre=dict(dependency_symlink=str(root),dependency_contents_sha256=partial)
                            with self.assertRaises(error):runner.unchanged_dependencies(pre)
            self.assertEqual(runner.dependency_contents(root),baseline)

    def test_package_symlink_cannot_escape_content_pin(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('playwright','playwright-core'):
                (root/name).mkdir();(root/name/'package.json').write_text('{}')
            (root/'outside.js').write_text('outside declared package')
            (root/'playwright/escape.js').symlink_to(root/'outside.js')
            with self.assertRaises(AssertionError):runner.dependency_contents(root)

    def test_python_optimization_rejected_before_import_cli_or_case_credit(self):
        root=Path(__file__).resolve().parents[2];script=root/'tools/behavior-tests/state_trace/unit_body_movement_runner.py'
        base=dict(os.environ);base.pop('PYTHONOPTIMIZE',None);base['PYTHONPATH']=str(root/'tools/behavior-tests')
        variants=[(['-O'],None),(['-OO'],None),([], '1'),([], '0')]
        entries=[['-c',"import state_trace.unit_body_movement_runner;print('UNSAFE_CASE_CREDIT')"],['-m','state_trace.unit_body_movement_runner','--help'],[str(script),'--help']]
        for flags,optimize in variants:
            for entry in entries:
                env=dict(base)
                if optimize is not None:env['PYTHONOPTIMIZE']=optimize
                with self.subTest(flags=flags,env=optimize,entry=entry):
                    child=subprocess.run([sys.executable,*flags,*entry],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
                    self.assertNotEqual(child.returncode,0);self.assertIn('requires unoptimized Python',child.stderr);self.assertNotIn('UNSAFE_CASE_CREDIT',child.stdout)
        for entry in entries:
            child=subprocess.run([sys.executable,*entry],cwd=root,env=base,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=5)
            self.assertEqual(child.returncode,0,child.stderr)


    def test_historical_freeze_is_retained_without_substituting_execution_identity(self):
        import hashlib
        ui=Path(__file__).resolve().parents[2]/'tools/behavior-tests/ui'
        original=(ui/'unit-body-movement-source-freeze-v2.json').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),'41fd6d3bbf06a19144efec9176c3559ba0d655894fea2cb34a7d7a8de2b807bf')
        freeze=json.loads(original);mapping=json.loads((ui/'unit-body-movement-source-equivalence-v2.json').read_text())
        self.assertEqual(mapping['actual_executed_commit'],freeze['head'])
        self.assertNotEqual(mapping['actual_executed_commit'],mapping['public_equivalent_commit'])
        self.assertFalse(mapping['public_commit_was_game_executed'])
        self.assertEqual(len(mapping['source_files_sha256']),41)
        for path,digest in freeze['changed_files_sha256'].items():self.assertEqual(mapping['source_files_sha256'][path],digest)
        self.assertEqual(mapping['native_tree'],runner.SOURCE);self.assertEqual(mapping['default_tree'],runner.DEFAULT)

    def test_proposed_profile_matches_fixed_executable_boundaries(self):
        self.assertEqual(runner.BUDGETS,dict(node_ms=180000,observation_ms=120000,outer_seconds=190,term_seconds=3,kill_wait_seconds=5,cleanup_seconds=8,postkill_seconds=2,census_calls=32,sample_delay_ms=10))
        self.assertEqual(runner.SOURCE,'23e54d08b7dbb00f6b42d325c180a8c868b30ee2')
        self.assertEqual(runner.DEFAULT,'a69dd4e0a9620f90bd12c8eb8636ca22e24ed47c')

if __name__=='__main__':unittest.main()
