"""Public preparation and real cheap-child lifecycle checks; no game/browser."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'state_trace'))
import terraform_sea_height_prepare as prep
import terraform_sea_height_run as runner


def public_source(folder):
    """A real temporary Git source/module contract, never candidate observations."""
    root = Path(folder) / 'source-é'; root.mkdir()
    for name in prep.FILES:
        path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('// public input\n')
    (root / 'src').mkdir(); (root / 'src/native.cpp').write_text('// declared native input\n')
    (root / 'GLSMAC_data/default').mkdir(); (root / 'GLSMAC_data/default/main.gls.js').write_text('// declared script\n')
    (root / prep.DRIVER).write_text("const seed='" + prep.SEED + "';\nconst test={timeout:180000};\nthrow Error('must never execute this test');\n")
    (root / 'tools/wasm-tests/terraform-sea-height-inputs.mjs').write_text("""
export const seaHeightInput={version:2,players:7,production_stock:'actual choice.cost + 3'};
export function seaHeightTerrain(){return Buffer.from('TERRANMAP\\0\\x1a'+'public-map');}
export function seaHeightOverrideManifest(original,executed){
 if(original.toString()!=='turns8'||executed.toString()!=='turns1')throw Error('unexpected actual bytes');
 return Array.from({length:20},(_,row)=>({row,field_index:4,old:8,new:1,applies_to:['land','sea']}));
}
""")
    (root / 'tools/wasm-tests/terraform-browser-inputs.mjs').write_text("export const rateOneSource=original=>Buffer.from(original.toString().replace('8','1'));\n")
    (root / '.gitignore').write_text('tools/wasm-tests/node_modules/\n')
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=Public fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'public inputs'], cwd=root, check=True)
    modules = root / 'tools/wasm-tests/node_modules'
    for name in ('playwright', 'playwright-core', 'pngjs'):
        (modules / name).mkdir(parents=True)
        (modules / name / 'package.json').write_text(json.dumps({'name': name, 'version': 'public-model'}))
    runtime, web, assets, browsers = [Path(folder) / name for name in ('runtime', 'web', 'assets', 'browsers')]
    for path in (runtime, web, assets, browsers): path.mkdir()
    (browsers / 'resources.pak').write_bytes(b'public-browser-resource-not-executed')
    (browsers / 'libvk_swiftshader.so').write_bytes(b'public-library-not-loaded')
    for path in (runtime, web):
        (path / 'GLSMAC.js').write_bytes(b'public-js-not-executable')
        (path / 'GLSMAC.wasm').write_bytes(b'public-wasm-not-executable')
    (web / 'bootstrap.js').write_text('throw Error("never launched");')
    (assets / 'alphax.txt').write_bytes(b'turns8')
    font = Path(folder) / 'font.conf'; font.write_text('<fontconfig/>')
    expected = {name: prep.git(root, 'rev-parse', ref) for name, ref in [('head', 'HEAD'), ('native_tree', 'HEAD:src'), ('default_tree', 'HEAD:GLSMAC_data/default')]}
    expected.update(js=prep.sha(runtime / 'GLSMAC.js'), wasm=prep.sha(runtime / 'GLSMAC.wasm'), rules=prep.sha(assets / 'alphax.txt'), executed_rules=hashlib.sha256(b'turns1').hexdigest())
    (runtime / 'provenance.json').write_text(json.dumps({'src_tree': expected['native_tree'], 'runtime': {name: prep.sha(runtime / name) for name in ('GLSMAC.js', 'GLSMAC.wasm')}}))
    config = {'source_root': str(root), 'runtime': str(runtime), 'web': str(web), 'assets': str(assets),
              'browsers': str(browsers), 'node_modules': str(modules), 'node': str(Path(shutil.which('node')).resolve()),
              'server_python': str(Path(shutil.which('python3')).resolve()), 'browser_executable': str(Path(sys.executable).resolve()),
              'font_config': str(font), 'output': str(Path(folder) / 'output-é')}
    return config, expected


class SeaPreparationTests(unittest.TestCase):
    def test_browser_payload_changes_reject_before_execution_claim(self):
        for variant in ('resource', 'library', 'added', 'removed'):
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as folder:
                config, expected = public_source(folder); record = prep.prepare(config, expected)
                root = Path(config['browsers']); path = Path(config['output']) / 'preflight.json'
                if variant == 'resource': (root / 'resources.pak').write_bytes(b'changed resource')
                if variant == 'library': (root / 'libvk_swiftshader.so').write_bytes(b'changed library')
                if variant == 'added': (root / 'new-resource').write_bytes(b'new input')
                if variant == 'removed': (root / 'resources.pak').unlink()
                with self.assertRaisesRegex(AssertionError, 'Inputs changed after prepare'):
                    runner.load_preflight(path, prep.sha(path))
                self.assertFalse((path.parent / 'execution-claim.json').exists())

    def test_native_and_language_loader_variables_are_removed_and_policy_is_bound(self):
        blocked = ['LD_PRELOAD', 'LD_LIBRARY_PATH', 'LD_AUDIT', 'LD_DEBUG',
                   'DYLD_INSERT_LIBRARIES', 'GLIBC_TUNABLES', 'NODE_OPTIONS', 'PYTHONPATH']
        with patch.dict(os.environ, {**{name: 'untracked-loader-value' for name in blocked}, 'LANG': 'C'}):
            clean = prep.clean_environment()
        self.assertTrue(all(name not in clean for name in blocked))
        self.assertEqual(clean['LANG'], 'C')
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder); record = prep.prepare(config, expected)
            self.assertEqual(record['loader_environment_policy'], prep.LOADER_POLICY)
            del record['loader_environment_policy']
            with self.assertRaises(KeyError): prep.validate_record(record)

    def test_real_prepare_derives_inputs_without_launch_and_is_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder)
            record = prep.prepare(config, expected); out = Path(config['output'])
            self.assertFalse(record['candidate_executed'])
            self.assertEqual(record['inputs']['declared']['production_stock'], 'actual choice.cost + 3')
            self.assertEqual((out / 'declared-map.MP').read_bytes(), b'TERRANMAP\0\x1apublic-map')
            self.assertEqual((out / 'executed-rules.txt').read_bytes(), b'turns1')
            self.assertFalse((out / 'driver.log').exists()); self.assertFalse((out / 'report.json').exists())
            path = out / 'preflight.json'; original = path.read_bytes()
            runner.load_preflight(path, prep.sha(path))
            with self.assertRaises(AssertionError): prep.prepare(config, expected)
            self.assertEqual(path.read_bytes(), original)
            # Inspect is an actual CLI boundary and cannot execute the driver.
            result = subprocess.run([sys.executable, str(Path(runner.__file__)), '--preflight', str(path), '--expected-preflight-sha256', prep.sha(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['phase'], 'inspect-only-no-child-launch')
            self.assertFalse((out / 'driver.log').exists())

    def test_preparation_cannot_inherit_an_unpinned_node_loader(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder)
            with patch.dict(os.environ, {'NODE_OPTIONS': '--require /nonexistent-unpinned-loader'}):
                record = prep.prepare(config, expected)
            self.assertFalse(record['candidate_executed'])
            self.assertFalse((Path(config['output']) / 'driver.log').exists())

    def test_existing_execution_claim_cannot_launch_again(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder); prep.prepare(config, expected)
            out = Path(config['output']); path = out / 'preflight.json'
            (out / 'execution-claim.json').write_text('prior attempt remains immutable')
            with self.assertRaises(FileExistsError): runner.execute(path, prep.sha(path))
            self.assertFalse((out / 'driver.log').exists())

    def test_future_report_must_bind_the_actual_prepared_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder); record = prep.prepare(config, expected)
            source = record['pins']['source']; files = source['files']
            report = {'host_head': source['head'], 'native_source_tree': source['native_tree'], 'default_tree': source['default_tree'],
                'runtime_js_sha256': record['pins']['runtime']['GLSMAC.js'], 'runtime_wasm_sha256': record['pins']['runtime']['GLSMAC.wasm'],
                'seed_requested': record['seed_requested'], 'map_sha256': record['inputs']['map_sha256'],
                'driver_sha256': files[prep.DRIVER], 'sea_input_sha256': files['tools/wasm-tests/terraform-sea-height-inputs.mjs'],
                'observer_sha256': record['prepared_files']['fixture-main.gls.js'], 'world_input_sha256': record['prepared_files']['fixture-world.gls.js'],
                'source_override': {'original_sha256': expected['rules'], 'rate_one_sha256': record['inputs']['executed_rules_sha256'], 'rows': record['inputs']['override_table']}}
            self.assertTrue(runner.report_bindings(report, record)['match'])
            for field in ('map_sha256', 'seed_requested', 'driver_sha256', 'host_head'):
                changed = copy.deepcopy(report); changed[field] = 'wrong'
                self.assertFalse(runner.report_bindings(changed, record)['match'])
            changed = copy.deepcopy(report); changed['source_override']['rows'][0]['new'] = True
            self.assertFalse(runner.report_bindings(changed, record)['match'])

    def test_wrong_head_runtime_profile_and_dirty_source_reject_before_output(self):
        for change in ('head', 'runtime', 'rules', 'dirty', 'untracked'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                config, expected = public_source(folder)
                if change == 'head': expected['head'] = '0' * 40
                if change == 'runtime': (Path(config['web']) / 'GLSMAC.wasm').write_bytes(b'other')
                if change == 'rules': (Path(config['assets']) / 'alphax.txt').write_bytes(b'other')
                if change == 'dirty': (Path(config['source_root']) / prep.DRIVER).write_text('other')
                if change == 'untracked': (Path(config['source_root']) / 'src/added.cpp').write_text('untracked')
                with self.assertRaises(AssertionError): prep.prepare(config, expected)
                self.assertFalse(Path(config['output']).exists())

    def test_prepared_unknown_schema_command_and_source_mutation_reject(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder); record = prep.prepare(config, expected)
            path = Path(config['output']) / 'preflight.json'
            for field, value in [('kind', 'unknown'), ('version', True), ('argv', ['echo', 'node --test']), ('candidate_executed', True)]:
                changed = copy.deepcopy(record); changed[field] = value
                path.write_bytes(prep.encoded(changed))
                with self.assertRaises(AssertionError): runner.load_preflight(path, prep.sha(path))
            path.write_bytes(prep.encoded(record))
            (Path(config['node_modules']) / 'pngjs/package.json').write_text('mutated dependency')
            with self.assertRaises(AssertionError): runner.load_preflight(path, prep.sha(path))
            self.assertFalse((path.parent / 'execution-claim.json').exists())

    def test_prepared_bytes_and_tool_sources_cannot_change_silently(self):
        with tempfile.TemporaryDirectory() as folder:
            config, expected = public_source(folder); record = prep.prepare(config, expected)
            path = Path(config['output']) / 'preflight.json'
            (path.parent / 'declared-map.MP').write_bytes(b'changed')
            with self.assertRaises(AssertionError): runner.load_preflight(path, prep.sha(path))
            self.assertFalse((path.parent / 'execution-claim.json').exists())


class SeaOwnedChildTests(unittest.TestCase):
    def escape_code(self, parent_delay=0):
        return """import os,time
r,w=os.pipe();child=os.fork()
if child==0:
 os.close(r);os.setsid();os.write(w,b'x');os.close(w);time.sleep(10)
else:
 os.close(w);os.read(r,1);os.close(r);print('ESCAPED|'+str(child),flush=True);time.sleep(""" + str(parent_delay) + ")\n"

    def assert_escape_waited(self, result, raw):
        child = int(raw.decode().strip().split('|')[1])
        self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['forced_cleanup'])
        self.assertTrue(result['owned_group_absent']); self.assertTrue(result['observed_owned_session_absent'])
        self.assertTrue(result['known_owned_identities_absent']); self.assertTrue(result['ownership_supported'])
        self.assertEqual(result['remaining_owned_identities'], []); self.assertEqual(result['unresolved_adopted_children'], [])
        actual = next(row for row in result['adopted_children_actual_waits'] if row['pid'] == child)
        self.assertIsInstance(actual['start_ticks'], int); self.assertTrue(os.WIFSIGNALED(actual['wait_status']))
        observed = next(row for row in result['owned_identity_provenance'] if row['pid'] == child)
        self.assertIn(child, observed['observed_sessions']); self.assertNotEqual(child, result['session_id'])
        self.assertTrue(result['subreaper_restored'])

    def test_setsid_orphan_after_closed_root_is_adopted_and_actually_waited(self):
        result, raw = self.run_child(self.escape_code())
        self.assertEqual(result['actual_os_process_exit_code'], 0)
        self.assert_escape_waited(result, raw)

    def test_timeout_setsid_tree_keeps_true_leader_wait_separate_from_native(self):
        result, raw = self.run_child(self.escape_code(10), timeout=1)
        self.assertTrue(result['outer_timed_out']); self.assertLess(result['actual_os_process_exit_code'], 0)
        self.assert_escape_waited(result, raw)
        self.assertNotIn('native_app_exit', result)

    def test_observed_escape_with_unrelated_baseline_preserves_that_child(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(10)'])
        try:
            result, raw = self.run_child(self.escape_code(.2))
            self.assert_escape_waited(result, raw)
            self.assertIsNone(unrelated.poll())
            self.assertNotIn(unrelated.pid, [row['pid'] for row in result['adopted_children_actual_waits']])
        finally:
            unrelated.terminate(); unrelated.wait(timeout=2)

    def test_unproven_unreadable_and_reused_adoptees_never_authorize_signal_or_wait(self):
        def row(pid,start,parent,session): return dict(pid=pid,start_ticks=start,parent=parent,session=session,group=session)
        for mode in ('ambiguous', 'unreadable', 'reused'):
            scope=dict(owner=999,known={100:1},foreign={200:2},provenance={100:'actual-Popen-leader'},sessions={},adoption_allowed=False,unsupported=set(),unresolved=[],waited_adopted=[],root_start=1)
            table={100:row(100,1,999,100),200:row(200,2,999,999)}
            if mode!='unreadable': table[300]=row(300,3,999,300)
            if mode=='reused': scope['known'][300]=4
            with self.subTest(mode=mode),patch.object(runner,'process_table',return_value=table),patch.object(runner,'direct_children',return_value={100,200,300}),patch.object(runner.os,'kill') as kill,patch.object(runner.os,'waitpid',return_value=(0,0)) as wait:
                self.assertEqual(runner.members(100,scope),[{'pid':100,'start_ticks':1}])
                runner.signal_members(100,15,scope);runner.reap(100,scope)
                self.assertTrue(scope['unsupported'])
                self.assertTrue(all(call.args[0]==100 for call in kill.call_args_list))
                self.assertTrue(all(call.args[0]==100 for call in wait.call_args_list))
                if mode=='reused': self.assertEqual(scope['known'][300],4)
                else: self.assertEqual(scope['unresolved'][0]['pid'],300)

    def test_missing_child_observation_is_unsupported_not_an_empty_owned_tree(self):
        scope=dict(owner=999,known={100:1},foreign={},provenance={100:'actual-Popen-leader'},sessions={},adoption_allowed=True,unsupported=set(),unresolved=[],waited_adopted=[],root_start=1)
        table={100:dict(pid=100,start_ticks=1,parent=999,session=100,group=100)}
        with patch.object(runner,'process_table',return_value=table),patch.object(runner,'direct_children',return_value=None),patch.object(runner.os,'kill') as kill:
            self.assertEqual(runner.members(100,scope),[{'pid':100,'start_ticks':1}])
            self.assertIn('direct-child-observation-unavailable',scope['unsupported'])
            self.assertEqual(scope['unresolved'],[{'pid':None,'start_ticks':None}])
            runner.signal_members(100,15,scope)
            self.assertTrue(all(call.args[0]==100 for call in kill.call_args_list))
        with patch.object(runner,'direct_children',return_value=None),self.assertRaisesRegex(RuntimeError,'before launch'):
            runner.new_ownership()

    def test_unreadable_leader_still_reaps_actual_Popen_without_clean_certificate(self):
        actual = runner.process_table
        def hidden_new_child(): return {pid:row for pid,row in actual().items() if row['parent']!=os.getpid()}
        with patch.object(runner,'process_table',side_effect=hidden_new_child):
            result, _ = self.run_child('import time;time.sleep(10)')
        self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['owned_group_absent'])
        self.assertIsInstance(result['pid'],int)
        self.assertFalse(result['ownership_supported']); self.assertFalse(result['known_owned_identities_absent'])
        self.assertIn('unreadable-owned-leader',result['ownership_unsupported_reasons'])
        self.assertTrue(result['subreaper_restored'])

    def test_preexisting_unrelated_zombie_is_not_reaped_by_outer_runner(self):
        unrelated = subprocess.Popen([sys.executable,'-c',"import sys;print('ready',flush=True);sys.exit(7)"],stdout=subprocess.PIPE)
        try:
            self.assertEqual(unrelated.stdout.readline(),b'ready\n')
            result, _ = self.run_child("print('owned only')")
            self.assertTrue(result['known_owned_identities_absent'])
            self.assertNotIn(unrelated.pid,[row['pid'] for row in result['adopted_children_actual_waits']])
            self.assertEqual(unrelated.wait(timeout=2),7)
        finally:
            if unrelated.poll() is None: unrelated.kill();unrelated.wait(timeout=2)
            unrelated.stdout.close()

    def test_same_session_descendant_with_new_group_is_terminated_and_reaped(self):
        code = """import os,time
r,w=os.pipe();child=os.fork()
if child==0:
 os.close(r);os.setpgrp();os.write(w,b'x');os.close(w);time.sleep(10)
else:
 os.close(w);os.read(r,1);os.close(r);print('CHILD_GROUP|'+str(child),flush=True)
"""
        result, raw = self.run_child(code)
        child = int(raw.decode().strip().split('|')[1])
        self.assertNotEqual(child, result['pid'])
        self.assertEqual(result['actual_os_process_exit_code'], 0)
        self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['forced_cleanup'])
        self.assertTrue(result['owned_group_absent']); self.assertEqual(result['remaining_owned_identities'], [])
        self.assertTrue(result['subreaper_restored'])

    def test_reused_start_identity_is_not_signalled(self):
        with patch.object(runner, 'members', side_effect=[[{'pid': 101, 'start_ticks': 1}],
                                                         [{'pid': 101, 'start_ticks': 2}]]), patch.object(runner.os, 'kill') as kill:
            runner.signal_members(100, 15, {})
        kill.assert_not_called()

    def run_child(self, code, timeout=2):
        with tempfile.TemporaryDirectory() as folder:
            result = runner.run_owned([sys.executable, '-c', code], folder, os.environ.copy(), folder, timeout, cleanup_seconds=.5)
            return result, (Path(folder) / 'driver.log').read_bytes()

    def test_real_os_zero_nonzero_and_unicode_are_not_native_exit(self):
        for code in (0, 7):
            result, output = self.run_child("import sys;print('réel 🌊',flush=True);sys.exit(" + str(code) + ")")
            self.assertEqual(result['actual_os_process_exit_code'], code)
            self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['owned_group_absent'])
            self.assertFalse(result['forced_cleanup']); self.assertFalse(result['external_tool_receipt']['supported'])
            self.assertEqual(result['complete_browser_cases'], 0)
            self.assertIn('réel 🌊'.encode(), output)
            self.assertNotIn('native_app_exit', result)
            self.assertNotIn('actual_os_node_exit_code', result)
            self.assertTrue(result['subreaper_restored'])

    def test_native_report_missing_nonzero_or_boolean_is_not_node_zero(self):
        self.assertIsNone(runner.native_report_exit({}))
        for code in (0, 1):
            self.assertEqual(runner.native_report_exit({'native_exit': {'body_state':'exited','status_text':f'GLSMAC exited ({code}).','raw_code':code}}), code)
        self.assertIsNone(runner.native_report_exit({'native_exit': {'body_state':'exited','status_text':'GLSMAC exited (0).','raw_code':False}}))

    def test_record_write_failure_still_waits_and_reaps_actual_child(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'external-start.json').write_text('preserve this existing file')
            result = runner.run_owned([sys.executable, '-c', 'import time;time.sleep(10)'], folder, os.environ.copy(), folder, 1, .5)
            self.assertTrue(result['lifecycle_error'].startswith('FileExistsError'))
            self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['owned_group_absent'])
            self.assertTrue(result['forced_cleanup'])
            self.assertEqual((Path(folder) / 'external-start.json').read_text(), 'preserve this existing file')

    def test_spawn_failure_is_unknown_exit_not_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            result = runner.run_owned(['/nonexistent-public-node'], folder, os.environ.copy(), folder, 1, .5)
            self.assertIsNone(result['actual_os_process_exit_code'])
            self.assertFalse(result['actual_wait_returned']); self.assertTrue(result['spawn_error'])

    def test_timeout_reaps_owned_group_and_leaves_unrelated_child_alone(self):
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(10)'], start_new_session=True)
        try:
            result, _ = self.run_child('import time;time.sleep(10)', timeout=.1)
            self.assertTrue(result['outer_timed_out']); self.assertTrue(result['forced_cleanup'])
            self.assertTrue(result['actual_wait_returned']); self.assertTrue(result['owned_group_absent'])
            self.assertLess(result['actual_os_process_exit_code'], 0)
            self.assertIsNone(unrelated.poll())
        finally:
            unrelated.terminate(); unrelated.wait(timeout=2)

    def test_orphaned_owned_descendant_is_adopted_and_reaped(self):
        result, _ = self.run_child("import os,time;child=os.fork();time.sleep(10) if child==0 else None")
        self.assertEqual(result['actual_os_process_exit_code'], 0)
        self.assertTrue(result['forced_cleanup']); self.assertTrue(result['owned_group_absent'])
        self.assertEqual(result['remaining_owned_identities'], [])


if __name__ == '__main__': unittest.main()
