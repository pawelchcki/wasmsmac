"""Explicit outer execution of one prepared Sea browser command (Linux/POSIX).

This process can witness Popen/wait, not its own caller's tool session/chunk.
No automatic retry, complete-browser credit or fabricated historical schema.
"""
if not __debug__:
    raise RuntimeError('Sea outer runner refuses optimized Python: assertion checking is required')

import argparse
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import terraform_sea_height_prepare as preparation


def members(group):
    result = []
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal(): continue
        try:
            text = (path / 'stat').read_text(); fields = text[text.rfind(')') + 2:].split()
            # Descendants can change process group while still belonging to
            # our new session. The session, not just its first group, is owned.
            if int(fields[3]) == group:
                result.append({'pid': int(path.name), 'start_ticks': int(fields[19])})
        except (FileNotFoundError, ProcessLookupError, PermissionError): pass
    return result


def reap(group):
    # Only observed session identities are considered. Never wait for an
    # unrelated child merely because this process temporarily is a subreaper.
    for row in members(group):
        try:
            os.waitpid(row['pid'], os.WNOHANG)
        except ChildProcessError: pass


def signal_members(session, kill_signal):
    for row in members(session):
        # Revalidate start identity and session immediately before signalling;
        # a numeric PID disappearing or being reused supplies no authority.
        if row not in members(session): continue
        try: os.kill(row['pid'], kill_signal)
        except ProcessLookupError: pass


def run_owned(argv, cwd, env, output, timeout, cleanup_seconds=5):
    """Only this freshly created session is signalled/reaped; no shell/pattern kill."""
    assert sys.platform.startswith('linux') and Path('/proc/self/stat').exists(), 'Unsupported process ownership platform'
    assert type(argv) is list and argv and all(type(value) is str for value in argv)
    assert timeout > 0 and cleanup_seconds > 0
    output = Path(output)
    # The standalone outer process adopts orphaned descendants so a killed
    # Node/browser tree can be reaped. Restore the caller's previous flag.
    libc = ctypes.CDLL(None, use_errno=True); previous = ctypes.c_int()
    assert libc.prctl(37, ctypes.byref(previous), 0, 0, 0) == 0
    assert libc.prctl(36, 1, 0, 0, 0) == 0
    start, wall = time.monotonic(), time.time()
    record = {'kind': 'terraform-sea-owned-process-completion.v1', 'command_argv': argv,
              'cwd': str(cwd), 'started_wall_time': wall, 'timeout_seconds': timeout,
              'actual_os_process_exit_code': None, 'actual_wait_returned': False, 'spawn_error': None,
              'outer_timed_out': False, 'forced_cleanup': False, 'owned_group_absent': None,
              'external_tool_receipt': {'supported': False, 'reason': 'The outer process cannot attest its caller tool session/chunk'},
              'complete_browser_cases': 0}
    process = None
    try:
        with (output / 'driver.log').open('xb') as log:
            try:
                process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            except OSError as error:
                record['spawn_error'] = str(error)
                return record
            record.update(pid=process.pid, process_group=process.pid, session_id=os.getsid(process.pid),
                          initial_owned_identities=members(process.pid))
            preparation.write_new(output / 'external-start.json', preparation.encoded(record))
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['outer_timed_out'] = True; record['forced_cleanup'] = True
                signal_members(process.pid, signal.SIGTERM)
                try: code = process.wait(timeout=cleanup_seconds)
                except subprocess.TimeoutExpired:
                    signal_members(process.pid, signal.SIGKILL)
                    code = process.wait(timeout=cleanup_seconds)
            record.update(actual_os_process_exit_code=code, actual_wait_returned=True)
        return record
    except BaseException as error:
        record['lifecycle_error'] = type(error).__name__ + ': ' + str(error)
        return record
    finally:
        if process is not None:
            if process.poll() is None:
                record['forced_cleanup'] = True
                try: signal_members(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: process.wait(timeout=cleanup_seconds)
                except subprocess.TimeoutExpired:
                    try: signal_members(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                    try: process.wait(timeout=cleanup_seconds)
                    except subprocess.TimeoutExpired: record['lifecycle_error'] = 'Owned leader did not reap within bounded SIGKILL wait'
            # Popen.wait/poll genuinely reaped the leader, including error paths.
            record.update(actual_os_process_exit_code=process.returncode, actual_wait_returned=process.returncode is not None)
            reap(process.pid)
            alive = members(process.pid)
            for kill_signal in (signal.SIGTERM, signal.SIGKILL):
                if not alive: break
                record['forced_cleanup'] = True
                try: signal_members(process.pid, kill_signal)
                except ProcessLookupError: pass
                deadline = time.monotonic() + cleanup_seconds
                while time.monotonic() < deadline:
                    reap(process.pid); alive = members(process.pid)
                    if not alive: break
                    time.sleep(.01)
            record['remaining_owned_identities'] = alive
            record['owned_group_absent'] = not alive
        record['elapsed_seconds'] = time.monotonic() - start
        # No collection of unrelated child PIDs or borrowed process groups.
        record['subreaper_restored'] = libc.prctl(36, previous.value, 0, 0, 0) == 0


def load_preflight(path, expected_digest):
    path = Path(path).resolve(strict=True)
    assert preparation.sha(path) == expected_digest, 'Different prepared metadata'
    record = json.loads(path.read_bytes()); preparation.validate_record(record)
    assert path.parent == Path(record['config']['output'])
    assert preparation.pins(record['config']) == record['pins'], 'Inputs changed after prepare'
    for name, digest in record['prepared_files'].items():
        assert name in ('declared-map.MP', 'executed-rules.txt', 'fixture-main.gls.js', 'fixture-world.gls.js')
        assert preparation.sha(path.parent / name) == digest
    assert set(record['prepared_files']) == {'declared-map.MP', 'executed-rules.txt', 'fixture-main.gls.js', 'fixture-world.gls.js'}
    for name, digest in record['tool_sources'].items(): assert preparation.sha(name) == digest
    assert record['tool_sources'][str(Path(__file__).resolve())] == preparation.sha(__file__)
    return record


def native_report_exit(report):
    native = report.get('native_exit')
    if type(native) is dict and type(native.get('raw_code')) is int and native.get('body_state') == 'exited' and native.get('status_text') == f"GLSMAC exited ({native['raw_code']}).":
        return native['raw_code']
    return None


def report_bindings(report, preflight):
    source, inputs = preflight['pins']['source'], preflight['inputs']
    expected = {'host_head': source['head'], 'native_source_tree': source['native_tree'], 'default_tree': source['default_tree'],
                'runtime_js_sha256': preflight['pins']['runtime']['GLSMAC.js'], 'runtime_wasm_sha256': preflight['pins']['runtime']['GLSMAC.wasm'],
                'seed_requested': preflight['seed_requested'], 'map_sha256': inputs['map_sha256'],
                'driver_sha256': source['files'][preparation.DRIVER],
                'sea_input_sha256': source['files']['tools/wasm-tests/terraform-sea-height-inputs.mjs'],
                'observer_sha256': preflight['prepared_files']['fixture-main.gls.js'],
                'world_input_sha256': preflight['prepared_files']['fixture-world.gls.js']}
    bad = [key for key, value in expected.items() if report.get(key) != value]
    override = report.get('source_override', {})
    if override.get('original_sha256') != preflight['expected']['rules']: bad.append('original_rules')
    if override.get('rate_one_sha256') != inputs['executed_rules_sha256']: bad.append('executed_rules')
    if json.dumps(override.get('rows'), sort_keys=True) != json.dumps(inputs['override_table'], sort_keys=True): bad.append('override_table')
    return {'match': not bad, 'mismatched_fields': bad}


def execute(path, expected_digest):
    record = load_preflight(path, expected_digest); config = record['config']; out = Path(config['output'])
    # An atomic one-use claim makes even a failed launch a consumed attempt.
    preparation.write_new(out / 'execution-claim.json', preparation.encoded({'preflight_sha256': expected_digest, 'argv': record['argv'], 'candidate_execution_requested': True}))
    env = preparation.clean_environment()
    env['PATH'] = str(Path(config['server_python']).parent) + os.pathsep + env.get('PATH', '')
    env.update(record['environment'])
    completion = run_owned(record['argv'], config['source_root'], env, out, record['outer_timeout_seconds'])
    completion.update(kind='terraform-sea-portable-external-completion.v1',
                      actual_os_node_exit_code=completion['actual_os_process_exit_code'],
                      preflight_sha256=expected_digest, runner_sha256=preparation.sha(__file__),
                      source_head=record['pins']['source']['head'], native_app_exit=None, reported_native_exit=None,
                      postpins_match=False, postpins_error=None, report_input_bindings={'match': False, 'reason': 'No actual report supplied'},
                      reported_status=None, status='failed-or-unsupported')
    try: completion['postpins_match'] = preparation.pins(config) == record['pins']
    except Exception as error: completion['postpins_error'] = str(error)
    report = out / 'report.json'
    if report.exists():
        completion['report_sha256'] = preparation.sha(report)
        try:
            reported = json.loads(report.read_bytes())
            completion['report_input_bindings'] = report_bindings(reported, record)
            completion['reported_status'] = reported.get('status')
            completion['reported_native_exit'] = reported.get('native_exit')
            completion['native_app_exit'] = native_report_exit(reported)
        except (ValueError, TypeError, KeyError) as error: completion['report_read_error'] = str(error)
    for name in ('application.log', 'application-log-chunks.jsonl'):
        if (out / name).exists(): completion[name + '_sha256'] = preparation.sha(out / name)
    okay = (completion['actual_wait_returned'] and completion['actual_os_node_exit_code'] == 0 and
            completion['owned_group_absent'] is True and not completion['forced_cleanup'] and
            not completion['outer_timed_out'] and completion['postpins_match'] and completion['native_app_exit'] == 0 and completion['reported_status'] == 'passed' and
            not completion.get('lifecycle_error') and completion['subreaper_restored'] and completion['report_input_bindings']['match'])
    if okay: completion['status'] = 'process-and-reported-native-exit-zero-not-complete-browser-credit'
    preparation.write_new(out / 'portable-external-completion.json', preparation.encoded(completion))
    return completion, 0 if okay else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', required=True, type=Path)
    parser.add_argument('--expected-preflight-sha256', required=True)
    parser.add_argument('--execute', action='store_true', help='Actually launch the pinned Node browser command ONCE; omitted means inspect only')
    args = parser.parse_args()
    if not args.execute:
        record = load_preflight(args.preflight, args.expected_preflight_sha256)
        print(json.dumps({'candidate_executed': False, 'argv': record['argv'], 'environment': record['environment'],
                          'phase': 'inspect-only-no-child-launch'}, indent=2)); return
    completion, code = execute(args.preflight, args.expected_preflight_sha256)
    print(json.dumps(completion, indent=2)); raise SystemExit(code)


if __name__ == '__main__': main()
