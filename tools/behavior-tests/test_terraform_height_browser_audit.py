"""Protocol regressions; optional retained browser artifacts are read-only.

TERRAFORM_HEIGHT_CAPTURE=/path/to/accepted/artifacts runs the same mutations
against all six actual retained packets, in addition to asset-free protocol data.
Neither test family executes a game or establishes new native/browser coverage.
"""
import copy
import importlib.util
import json
import os
import hashlib
import tempfile
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).parent / 'state_trace/terraform_height_browser_audit.py'
spec = importlib.util.spec_from_file_location('height_audit', MODULE_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def protocol_fixture():
    """Synthetic schema inputs only, never an original/candidate observation."""
    players = [{'id': f'p{i}', 'raw_id': i, 'faction': 'GAIANS' if i == 0 else f'other{i}'} for i in range(7)]
    units = [{'id': f'u{i}', 'raw_id': i, 'owner': f'p{(i - 1) % 7}', 'movement': 1.0, 'health': 1.0, 'order': 'NO_ORDERS'} for i in range(1, 9)]
    units[-1]['owner'] = 'p0'
    bases = [{'id': f'b{i}', 'raw_id': i, 'owner': f'p{i - 1}'} for i in range(1, 8)]
    tiles = {}
    for y in range(16):
        for x in range(y % 2, 16, 2):
            tiles[f'{x},{y}'] = {'x': x, 'y': y, 'elevation': {'center': 240, **{name: 240 for name in audit.CORNERS}},
                'neighbors': {}, 'terrain_epoch': 0, 'canonical': {'active': False, 'elevation': None, 'is_water': None},
                'imported': {'active': True, 'source_elevation': 240, 'source_water': False, 'source_corners': [240] * 4},
                'is_land': True, 'is_water': False, 'native_type': {'domain': 'land'},
                'native_height_band': {name: False for name in audit.BANDS}, 'unknown_native': {'value': -0.0}}
    tiles['8,8']['neighbors']['E'] = {'x': 10, 'y': 8}
    trace = {'policy': {'version': 1, 'ignore_technologies': True}, 'ui': {}, 'tiles': tiles, 'unit_details': {u['id']: {'moved_this_turn': False, 'quotes': {'E': {'allowed_now': True, 'reason': None}}} for u in units},
             'player_details': {p['id']: {'energy': {'credits': 10}, 'energy_revision': 1} for p in players},
             'base_details': {b['id']: {'unknown': 'unchanged'} for b in bases}}
    world = {'width': 16, 'height': 16, 'turn': 1, 'players': players, 'units': units, 'bases': bases, 'terrain_trace': trace}
    quote = {'version': 1, 'supported': True, 'action': 'raise', 'resuming': False, 'paid_fee': 0, 'base_fee': 4, 'fee': 4, 'credits': 10,
             'mode': 'functional_approximation', 'policy': 'application.band-slope-height.v1', 'fee_policy': 'application.band-fee.v1',
             'unit_id': 8, 'owner': 0, 'turn': 1, 'x': 8, 'y': 8, 'source_elevation': 240, 'source_water': False,
             'destination_elevation': 1500, 'destination_water': False, 'plan': [{'x': 8, 'y': 8, 'canonical': {'elevation': 1500, 'is_water': False}}]}
    packets = []
    for i in range(6):
        ui = {'actor': 8, 'owner': 0, 'turn': 1, 'session': 0 if i == 0 else 1, 'dialog_generation': (0, 1, 2, 3, 3, 4)[i],
              'height_stage': audit.STAGES[i], 'modal': audit.SCOPES[i] == 'height', 'popup_id': 'terraforming_height' if audit.SCOPES[i] == 'height' else None,
              'sliding': False, 'hiding': False, 'native_pending': False, 'tile_locked': False, 'pending': None, 'choice': 1 if i >= 4 else 0,
              'height_presentation': None if i == 0 else {'stage': audit.STAGES[i], 'quote': copy.deepcopy(quote)},
              'movement': 1.0, 'movement_bits': 1065353216, 'dialog': {'fee': 4, 'reserves': 10} if audit.SCOPES[i] == 'height' else None}
        request = {key: ui[key] for key in ('actor', 'owner', 'turn', 'session', 'dialog_generation')}
        request.update(query=i + 1, scope=audit.SCOPES[i])
        packets.append({'query': i + 1, 'query_owner': request, 'ui': ui, 'world': copy.deepcopy(world)})
    final = packets[-1]
    final['ui'].update(movement=0.0, movement_bits=0)
    after = final['world']
    after['units'][-1]['movement'] = 0.0
    after['terrain_trace']['unit_details']['u8'].update(moved_this_turn=True)
    after['terrain_trace']['unit_details']['u8']['quotes']['E'].update(allowed_now=False, reason='Unit is out of moves')
    after['terrain_trace']['player_details']['p0']['energy']['credits'] = 6
    after['terrain_trace']['player_details']['p0']['energy_revision'] = 2
    for key in ('8,8', '10,8'):
        tile = after['terrain_trace']['tiles'][key]
        tile['terrain_epoch'] = 1
        tile['canonical'].update(active=True, elevation=1500 if key == '8,8' else 240, is_water=False)
    target = after['terrain_trace']['tiles']['8,8']
    target['elevation']['center'] = 1500
    target['imported'].update(active=False, source_corners=None, source_elevation=None, source_water=None)
    after['terrain_trace']['tiles']['10,8']['elevation']['left'] = 241
    receipt = {'name': 'unit_terraform', 'event_id': '0_68', 'caller': 0, 'success': True, 'data': {'unit_id': 8, 'action': 'raise', 'confirmed_height': True}}
    inputs = {'policy': {'version': 1, 'ignore_technologies': True}, 'actor': 8, 'can_terraform': True, 'raise_rule': {'turns': 1}}
    events = []
    for i in range(6):
        fence = (i + 1) * 3
        events.extend([{'seq': fence - 2, 'kind': 'input.ingress', 'data': {'ingress': i, 'type': 'keydown'}},
                       {'seq': fence - 1, 'kind': 'input.dispatch', 'data': {'ingress': i, 'phase': 'begin', 'type': 'keydown', 'code': 'P', 'modifiers': 6}},
                       {'seq': fence, 'kind': 'input.dispatch', 'data': {'ingress': i, 'phase': 'end', 'handled': True}}])
    records = [('TH_INPUTS', inputs, 0), ('TH_TRACE', {'events': events}, 1)]
    records.extend(('TH_NATIVE', row, (i + 1) * 10) for i, row in enumerate(packets))
    records.append(('TH_RECEIPT', receipt, 55))
    report = {'native_input': copy.deepcopy(inputs), 'height_receipt': copy.deepcopy(receipt),
              'native_snapshots': [{'checkpoint': name, 'query_after_native_key': (i + 1) * 3,
                                    'observation': audit.node_projection(row)} for i, (name, row) in enumerate(zip(audit.CHECKPOINTS, packets))]}
    return records, report


class AuditMutations:
    def setUp(self):
        self.records, self.report = copy.deepcopy(self.original)

    def packets(self):
        return [value for kind, value, _ in self.records if kind == 'TH_NATIVE']

    def sync_report(self):
        for item, row in zip(self.report['native_snapshots'], self.packets()):
            item['observation'] = audit.node_projection(row)
        receipt = next((value for kind, value, _ in self.records if kind == 'TH_RECEIPT'), None)
        if receipt is not None:
            self.report['height_receipt'] = copy.deepcopy(receipt)

    def reject(self):
        # Update the reported copy as well: semantic checks must reject facts,
        # not merely a stale hash or a report/raw mismatch.
        self.sync_report()
        with self.assertRaises((AssertionError, KeyError, TypeError)):
            audit.audit_records(self.records, self.report)

    def test_valid_capture_and_readonly_inputs(self):
        before = copy.deepcopy((self.records, self.report))
        result = audit.audit_records(self.records, self.report)
        self.assertEqual(result['per_world'], {'players': 7, 'units': 8, 'bases': 7, 'tiles': 128})
        self.assertEqual(result['native_float_unit_fields_checked'], 96)
        self.assertTrue(audit.equal(before, (self.records, self.report)))

    def test_reject_swapped_checkpoints(self):
        indexes = [i for i, row in enumerate(self.records) if row[0] == 'TH_NATIVE']
        left, right = indexes[1:3]
        self.records[left], self.records[right] = self.records[right], self.records[left]
        self.reject()

    def test_reject_duplicate_query(self):
        self.packets()[2]['query'] = 2
        self.reject()

    def test_reject_wrong_scope(self):
        self.packets()[1]['query_owner']['scope'] = 'root'
        self.reject()

    def test_reject_wrong_stage(self):
        self.packets()[2]['ui']['height_stage'] = 'submitted'
        self.reject()

    def test_reject_stale_owner(self):
        self.packets()[3]['query_owner']['owner'] = 1
        self.reject()

    def test_reject_missing_or_wrong_native_key(self):
        for kind, value, _ in self.records:
            if kind == 'TH_TRACE':
                begins = [e for e in value['events'] if e['kind'] == 'input.dispatch' and e['data'].get('phase') == 'begin' and e['data'].get('code') == 'P']
                if begins:
                    begins[0]['data']['code'] = 'Q'
                    break
        self.reject()

    def test_reject_missing_world_policy(self):
        self.packets()[1]['world']['terrain_trace'].pop('policy')
        self.reject()

    def test_reject_changed_world_policy(self):
        for policy in ({'version': 1, 'ignore_technologies': False}, {'version': 2, 'ignore_technologies': True}, {'version': True, 'ignore_technologies': True}, {'version': 1, 'ignore_technologies': 1}):
            with self.subTest(policy=policy):
                self.setUp()
                for row in self.packets(): row['world']['terrain_trace']['policy'] = policy.copy()
                self.reject()

    def test_reject_different_actual_input_policy(self):
        for kind, value, _ in self.records:
            if kind == 'TH_INPUTS': value['policy']['ignore_technologies'] = False
        self.report['native_input']['policy']['ignore_technologies'] = False
        self.reject()

    def test_reject_missing_actual_coverage(self):
        for field in ('players', 'units', 'bases', 'tiles'):
            with self.subTest(field=field):
                self.setUp()
                for row in self.packets():
                    if field == 'tiles': row['world']['terrain_trace']['tiles'].pop('0,0')
                    else: row['world'][field].pop()
                self.reject()

    def test_reject_duplicate_identity(self):
        for row in self.packets(): row['world']['units'][0]['raw_id'] = row['world']['units'][1]['raw_id']
        self.reject()

    def test_reject_unknown_band_field_change(self):
        for row in self.packets(): row['world']['terrain_trace']['tiles']['8,8']['native_height_band']['future_field'] = False
        self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']['native_height_band']['future_field'] = True
        self.reject()

    def test_reject_wrong_known_band(self):
        self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']['native_height_band']['below_ocean'] = True
        self.reject()

    def test_reject_arbitrary_epoch(self):
        self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']['terrain_epoch'] += 3
        self.reject()

    def test_reject_wrong_canonical_target(self):
        self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']['canonical']['elevation'] += 1
        self.reject()

    def test_reject_wrong_canonical_pin(self):
        base, final = self.packets()[0], self.packets()[-1]
        patches = {f"{p['x']},{p['y']}" for p in self.packets()[1]['ui']['height_presentation']['quote']['plan']}
        key = next(key for key, tile in final['world']['terrain_trace']['tiles'].items()
                   if key not in patches and tile['canonical']['active'] and not base['world']['terrain_trace']['tiles'][key]['canonical']['active'])
        final['world']['terrain_trace']['tiles'][key]['canonical']['is_water'] = True
        self.reject()

    def test_reject_wrong_energy_revision(self):
        payer = next(p['id'] for p in self.packets()[0]['world']['players'] if p['raw_id'] == 0)
        self.packets()[-1]['world']['terrain_trace']['player_details'][payer]['energy_revision'] += 3
        self.reject()

    def test_reject_wrong_policy_quote_fee(self):
        for row in self.packets()[1:]: row['ui']['height_presentation']['quote']['base_fee'] += 1
        self.reject()

    def test_reject_wrong_raw_receipt_identity(self):
        for field, value in [('name', 'move_unit'), ('caller', 1), ('event_id', ''), ('success', False)]:
            with self.subTest(field=field):
                self.setUp()
                receipt = next(value for kind, value, _ in self.records if kind == 'TH_RECEIPT' and value['name'] == 'unit_terraform')
                receipt[field] = value
                # Actual logs contain other receipts: sync only the payment report.
                self.report['height_receipt'] = copy.deepcopy(receipt)
                for item, row in zip(self.report['native_snapshots'], self.packets()): item['observation'] = audit.node_projection(row)
                with self.assertRaises((AssertionError, KeyError, TypeError)): audit.audit_records(self.records, self.report)

    def test_reject_wrong_raw_receipt_payload(self):
        for field, value in [('unit_id', 9), ('action', 'lower'), ('confirmed_height', False)]:
            with self.subTest(field=field):
                self.setUp()
                receipt = next(value for kind, value, _ in self.records if kind == 'TH_RECEIPT' and value['name'] == 'unit_terraform')
                receipt['data'][field] = value
                self.report['height_receipt'] = copy.deepcopy(receipt)
                with self.assertRaises((AssertionError, KeyError, TypeError)): audit.audit_records(self.records, self.report)

    def test_reject_report_only_receipt(self):
        self.report['height_receipt']['event_id'] = 'invented'
        with self.assertRaises(AssertionError): audit.audit_records(self.records, self.report)

    def test_reject_ack_outside_draft_completion(self):
        index = next(i for i, (kind, value, _) in enumerate(self.records) if kind == 'TH_RECEIPT' and value['name'] == 'unit_terraform')
        kind, value, _ = self.records[index]
        self.records[index] = (kind, value, -1)
        self.report['height_receipt'] = copy.deepcopy(value)
        with self.assertRaises(AssertionError): audit.audit_records(self.records, self.report)

    def test_reject_integral_float_coercion(self):
        self.packets()[-1]['world']['units'][0]['health'] = 1
        self.reject()

    def test_reject_signed_zero_loss(self):
        final = self.packets()[-1]
        actor = next(row for row in final['world']['units'] if row['raw_id'] == 8)
        actor['movement'] = -0.0
        final['ui'].update(movement=-0.0, movement_bits=2147483648)
        self.reject()


class ProtocolAuditTests(AuditMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = protocol_fixture()


@unittest.skipUnless(os.environ.get('TERRAFORM_HEIGHT_CAPTURE'), 'Set TERRAFORM_HEIGHT_CAPTURE for retained actual six-packet mutation replay')
class ActualCaptureAuditTests(AuditMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = Path(os.environ['TERRAFORM_HEIGHT_CAPTURE'])
        cls.original = (audit.parse_records((cls.directory / 'application.log').read_bytes()), json.loads((cls.directory / 'report.json').read_bytes()))

    def sync_report(self):
        super().sync_report()
        self.report['height_receipt'] = copy.deepcopy(next(value for kind, value, _ in self.records if kind == 'TH_RECEIPT' and value['name'] == 'unit_terraform'))

    def test_exact_retained_artifact_audit(self):
        result = audit.audit_artifacts(self.directory)
        self.assertEqual(result['parsed_native_world_changed_fields'], 229)
        self.assertEqual(result['raw_bytes'], 14465994)
        self.assertEqual(result['raw_sha256'], '7877baed15b88c2700f3042fe5c31f64c6ee66517dcef04541c1ced832bad473')


def finalization_fixture():
    """Synthetic metadata envelope; never claimed to be a real engine run."""
    records, report = protocol_fixture()
    events = next(value['events'] for kind, value, _ in records if kind == 'TH_TRACE')
    events.extend([{'seq': 19, 'kind': 'input.ingress', 'data': {'ingress': 7, 'type': 'keydown'}},
                   {'seq': 20, 'kind': 'input.dispatch', 'data': {'ingress': 7, 'phase': 'begin', 'type': 'keydown', 'code': 'Q', 'modifiers': 6}},
                   {'seq': 21, 'kind': 'input.dispatch', 'data': {'ingress': 7, 'phase': 'end', 'handled': True}}])
    lines = []
    for kind, value, _ in sorted(records, key=lambda row: row[2]):
        encoded = json.dumps(json.dumps(value)) if kind == 'TH_TRACE' else json.dumps(value)
        lines.append(kind + '|' + encoded)
    text = chr(10).join(lines) + chr(10) + 'TH_EXIT_REQUEST' + chr(10)
    raw = text.encode()
    records = audit.parse_records(raw)
    length = audit.utf16_length(text)
    call = {'sequence': 1, 'channel': 'stdout', 'before_utf16': 0, 'after_utf16': length,
            'message_utf16': length - 1, 'observed_ms': 1.0, 'runtime_out_bound': True,
            'runtime_err_bound': True, 'runtime_callMain_present': True}
    callback = {'installed_before_runtime_capture': True, 'initial_text': '', 'initial_utf16': 0,
                'calls': [call], 'first_callback': {**call, 'message': text[:-1]},
                'original_source': 'protocol log function', 'stdout_source': 'protocol stdout', 'stderr_source': 'protocol stderr'}
    barrier = {'kind': 'main', 'fetch_id': 'main-fetch', 'network_id': 'main-network', 'frame_id': 'frame',
               'continued': True, 'before_unmodified_runtime_response': True, 'continuation_acknowledged_node_ms': 2.0,
               'ack': {'installed_before_runtime_capture': True, 'original_source': callback['original_source'],
                       'stdout_source': callback['stdout_source'], 'stderr_source': callback['stderr_source']}}
    workers = [{'kind': 'worker', 'fetch_id': f'fetch{i}', 'network_id': f'target{i}', 'target_id': f'target{i}',
                'frame_id': 'frame', 'continued': True, 'continued_without_frame_lookup': True,
                'continuation_acknowledged_node_ms': 3.0} for i in range(8)]
    config = {'installations': 1, 'barrier': barrier, 'callbacks': callback, 'worker_requests': workers,
              'original_log_source_sha256': hashlib.sha256(callback['original_source'].encode()).hexdigest(),
              'protocol_events': [{'kind': 'continue-acknowledged', 'role': {key: row[key] for key in ('kind', 'fetch_id', 'network_id', 'frame_id')}} for row in [barrier] + workers]}
    digest = hashlib.sha256(raw).hexdigest()
    chunks = [{'start_utf16': 0, 'end_utf16': length, 'text': text}]
    report.update(status='passed', native_raw_exit_code=0, native_exit={'body_state': 'exited', 'status_text': 'GLSMAC exited (0).', 'raw_code': 0},
                  browser_errors=[], errors=[], native_log_configuration=config,
                  log_transport={'sealed': True, 'partial': False, 'settled_failure': None, 'unread_tail': False,
                                 'raw_sha256': digest, 'joined_chunk_sha256': digest, 'retained_utf8': len(raw), 'retained_utf16': length,
                                 'reads': [{'start_utf16': 0, 'end_utf16': length, 'transferred_utf16': length, 'transferred_utf8': len(raw)}]})
    return report, raw, chunks, records


class FinalizationMutations:
    def setUp(self):
        self.report, self.raw, self.chunks, self.records = copy.deepcopy(self.original_final)

    def reject(self):
        with self.assertRaises((AssertionError, KeyError, TypeError)):
            audit.validate_finalization(self.report, self.raw, self.chunks, self.records)

    def test_finalization_valid_and_native_fields_alone_never_claim_full_browser(self):
        result = audit.validate_finalization(self.report, self.raw, self.chunks, self.records)
        self.assertTrue(result['native_exit_verified'])
        self.assertEqual(audit.audit_records(self.records, self.report)['browser_cases_audited'], 0)

    def test_reject_missing_or_false_seal(self):
        self.report['log_transport'].pop('sealed')
        self.reject()
        self.setUp(); self.report['log_transport']['sealed'] = False; self.reject()

    def test_reject_unknown_tail_and_settled_error(self):
        for field, value in [('unread_tail', 'unknown'), ('settled_failure', 'late read failure'), ('partial', True)]:
            with self.subTest(field=field):
                self.setUp(); self.report['log_transport'][field] = value; self.reject()

    def test_reject_native_exit_only_report_or_nonzero_status(self):
        self.report.pop('native_exit'); self.reject()
        self.setUp(); self.report['native_exit']['status_text'] = 'GLSMAC exited (1).'; self.reject()
        self.setUp(); self.report['native_raw_exit_code'] = 1; self.reject()

    def test_reject_late_fatal_raw_suffix_even_with_rebound_hash(self):
        self.raw += b'TH_ERROR|late native failure\n'
        self.report['log_transport']['raw_sha256'] = hashlib.sha256(self.raw).hexdigest()
        self.report['log_transport']['joined_chunk_sha256'] = hashlib.sha256(self.raw).hexdigest()
        self.reject()

    def test_reject_browser_or_barrier_error(self):
        self.report['browser_errors'].append('late browser error'); self.reject()
        self.setUp(); self.report['native_log_configuration']['protocol_events'].append({'kind': 'rejected', 'error': 'late barrier failure'}); self.reject()

    def test_reject_missing_main_ack(self):
        self.report['native_log_configuration']['barrier'].pop('continued'); self.reject()

    def test_reject_missing_worker_or_failed_worker_ack(self):
        self.report['native_log_configuration']['worker_requests'].pop(); self.reject()
        self.setUp(); self.report['native_log_configuration']['worker_requests'][0]['continued'] = False; self.reject()

    def test_reject_unlinked_cdp_ack(self):
        config = self.report['native_log_configuration']
        event = next(row for row in config['protocol_events'] if row['kind'] == 'continue-acknowledged' and row['role']['kind'] == 'worker')
        event['role']['network_id'] = 'wrong-network'
        self.reject()

    def test_reject_first_capture_binding_mismatch(self):
        for field in ('runtime_out_bound', 'runtime_err_bound', 'runtime_callMain_present'):
            with self.subTest(field=field):
                self.setUp(); self.report['native_log_configuration']['callbacks']['first_callback'][field] = False; self.reject()

    def test_reject_chunk_offset_or_length_mismatch(self):
        self.chunks[-1]['end_utf16'] += 1; self.reject()
        self.setUp(); self.report['log_transport']['retained_utf8'] += 1; self.reject()

    def test_reject_missing_actual_q_dispatch(self):
        for kind, value, _ in self.records:
            if kind == 'TH_TRACE':
                for event in value['events']:
                    if event['kind'] == 'input.dispatch' and event['data'].get('code') == 'Q': event['data']['code'] = 'X'
        self.reject()


class ProtocolFinalizationTests(FinalizationMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_final = finalization_fixture()


@unittest.skipUnless(os.environ.get('TERRAFORM_HEIGHT_CAPTURE'), 'Set capture for actual envelope mutation replay')
class ActualFinalizationTests(FinalizationMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = Path(os.environ['TERRAFORM_HEIGHT_CAPTURE'])
        raw = (directory / 'application.log').read_bytes()
        cls.original_final = (json.loads((directory / 'report.json').read_bytes()), raw,
            [json.loads(line) for line in (directory / 'application-log-chunks.jsonl').read_text().splitlines() if line], audit.parse_records(raw))

    def test_legacy_preflight_rejects_unknown_or_missing_renamed_kind(self):
        directory = Path(os.environ['TERRAFORM_HEIGHT_CAPTURE'])
        encoded = (directory / 'preflight.json').read_bytes(); preflight = json.loads(encoded)
        native_input = next(value for kind, value, _ in self.records if kind == 'TH_INPUTS')
        self.assertTrue(audit.validate_preflight(directory, preflight, encoded, self.report, native_input).startswith('historical-'))
        for value in (None, 'unknown.v99'):
            changed = copy.deepcopy(preflight); changed['kind'] = value; changed_bytes = json.dumps(changed).encode()
            with self.assertRaises((AssertionError, KeyError)): audit.validate_preflight(directory, changed, changed_bytes, self.report, native_input)

    def test_legacy_preflight_binds_available_report_source_seed_and_live_rule(self):
        directory = Path(os.environ['TERRAFORM_HEIGHT_CAPTURE'])
        encoded = (directory / 'preflight.json').read_bytes(); preflight = json.loads(encoded)
        for field in ('seed_requested', 'driver_sha256', 'observer_sha256', 'world_input_sha256', 'height_observation_sha256'):
            with self.subTest(field=field):
                report = copy.deepcopy(self.report); report[field] = 'wrong source'
                native_input = next(value for kind, value, _ in self.records if kind == 'TH_INPUTS')
                with self.assertRaises((AssertionError, KeyError)): audit.validate_preflight(directory, preflight, encoded, report, native_input)
        native_input = copy.deepcopy(next(value for kind, value, _ in self.records if kind == 'TH_INPUTS'))
        native_input['raise_rule']['sea']['name'] = 'invented name'
        with self.assertRaises(AssertionError): audit.validate_preflight(directory, preflight, encoded, self.report, native_input)

    def test_legacy_outer_completion_cannot_be_reused_for_other_capture(self):
        directory = Path(os.environ['TERRAFORM_HEIGHT_CAPTURE']); bindings = copy.deepcopy(audit.LEGACY_CAPTURE_BINDINGS)
        self.assertTrue(audit.validate_external_exit(directory / 'raw-outcome.json', self.report['native_exit'], bindings)['supported'])
        bindings['report_sha256'] = '0' * 64
        with self.assertRaises(AssertionError): audit.validate_external_exit(directory / 'raw-outcome.json', self.report['native_exit'], bindings)


class ExternalOutcomeTests(unittest.TestCase):
    def test_missing_unknown_wrongrun_nonzero_and_unreaped_external_result(self):
        native = {'body_state': 'exited', 'status_text': 'GLSMAC exited (0).', 'raw_code': 0}
        bindings = {key: 'a' * 64 for key in ('raw_sha256', 'report_sha256', 'preflight_sha256')}; bindings['host_head'] = 'b' * 40
        data = {'kind': 'terraform-height-external-process-outcome.v1', 'version': 1, 'capture_bindings': bindings,
                'status': 'exited', 'raw_process_exit': 0, 'tool_session_id': 123, 'tool_completion_chunk_id': 'actual-chunk',
                'tool_completion_result': {'chunk_id': 'actual-chunk', 'exit_code': 0}, 'source': 'protocol-only external-launcher metadata',
                'command': 'node --test tools/wasm-tests/terraform-height-browser.test.mjs', 'native_exit': native, 'browser_server_driver_reaped': True}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'outcome.json'
            self.assertFalse(audit.validate_external_exit(path, native, bindings)['supported'])
            path.write_text(json.dumps(data)); self.assertTrue(audit.validate_external_exit(path, native, bindings)['supported'])
            for change in (lambda d: d.update(kind='unknown'), lambda d: d['capture_bindings'].update(raw_sha256='wrong'),
                           lambda d: d.update(raw_process_exit=1), lambda d: d['tool_completion_result'].update(exit_code=1),
                           lambda d: d.pop('tool_completion_result'), lambda d: d.update(browser_server_driver_reaped=False)):
                mutated = copy.deepcopy(data); change(mutated); path.write_text(json.dumps(mutated))
                with self.assertRaises((AssertionError, KeyError, TypeError)): audit.validate_external_exit(path, native, bindings)

class PreflightSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        sha = lambda value: hashlib.sha256(value).hexdigest()
        main, world = b'protocol main input', b'protocol world input'
        self.map = bytearray(8379); self.map[:11] = b'TERRANMAP\0\x1a'
        for offset, value in [(15, 16), (19, 16), (35, 128)]: self.map[offset:offset + 4] = value.to_bytes(4, 'little')
        for name, data in [('fixture-main.gls.js', main), ('fixture-world.gls.js', world), ('fixture-map.MP', self.map)]: (self.directory / name).write_bytes(data)
        shared = {name: sha(name.encode()) for name in ('browser-log-cursor.mjs', 'browser-native-log-hook.mjs', 'runtime-fetch-barrier.mjs', 'terraform-browser-geometry.mjs', 'terraform-browser-pointer.mjs')}
        files = {'tools/wasm-tests/' + name: value for name, value in shared.items()}
        files.update({'tools/wasm-tests/terraform-height-observation.mjs': 'a' * 64, 'tools/wasm-tests/fixtures/terraform-height-main.gls.js': sha(main),
                      'tools/wasm-tests/terraform-browser-inputs.mjs': 'b' * 64, 'executed_node_driver': 'c' * 64, 'preflight_producer': 'd' * 64,
                      'tools/wasm-tests/fixtures/terraform-controls-world.gls.js': 'e' * 64,
                      'GLSMAC_data/tests/_state_trace_observer.gls.js': 'f' * 64, 'GLSMAC_data/tests/_terrain_trace_observer.gls.js': '1' * 64,
                      'GLSMAC_data/tests/_terraform_cooperation_observer.gls.js': '2' * 64})
        self.pref = {'version': 1, 'kind': 'terraform-height-producer-preflight.v1', 'candidate_executed': False, 'phase': 'before-native-launch',
                     'head': 'a' * 40, 'native_tree': 'b' * 40, 'default_tree': 'c' * 40, 'runtime': {'js': 'd' * 64, 'wasm': 'e' * 64},
                     'original_rules_sha256': 'f' * 64, 'executed_rules_sha256': '1' * 64, 'source_sha256': files,
                     'input_sha256': {'main': sha(main), 'world': sha(world), 'map': sha(self.map), 'helpers': '2' * 64},
                     'production_default_sha256': '3' * 64, 'declared_map': {'width': 16, 'height': 16, 'tiles': 128, 'bytes': 8379},
                     'seed_requested': '1651011033:1377505029:3019448108:3247278135', 'browser_budget_ms': 180000,
                     'native_policy_observation': 'not available before launch; require actual TH_INPUTS and every retained native world in the auditor',
                     'override_table': [{'row': i, 'field': 'shared_turns', 'field_index': 4, 'old': 12, 'new': 1, 'applies_to': ['land', 'sea'], 'land_name': f'Land {i}', 'sea_name': f'Sea {i}', 'land_prerequisite': 'None', 'sea_prerequisite': 'None'} for i in range(20)]}
        self.report = {'host_head': self.pref['head'], 'native_source_tree': self.pref['native_tree'], 'default_tree': self.pref['default_tree'],
                       'runtime_js_sha256': self.pref['runtime']['js'], 'runtime_wasm_sha256': self.pref['runtime']['wasm'],
                       'source_override': {'original_sha256': self.pref['original_rules_sha256'], 'rate_one_sha256': self.pref['executed_rules_sha256']},
                       'seed_requested': self.pref['seed_requested'], 'production_default_sha256': self.pref['production_default_sha256'],
                       'observer_sha256': sha(main), 'world_input_sha256': sha(world), 'observer_helpers_sha256': '2' * 64,
                       'driver_sha256': files['executed_node_driver'], 'height_observation_sha256': files['tools/wasm-tests/terraform-height-observation.mjs'],
                       'shared_helpers_sha256': shared}
        self.native = {'raise_rule': {'source_row': 16, 'id': 'raise', 'name': 'Land 16', 'prerequisite': 'None', 'turns': 1, 'sea': {'name': 'Sea 16', 'prerequisite': 'None', 'turns': 1}}}

    def validate(self):
        encoded = json.dumps(self.pref).encode()
        self.report['preflight_sha256'] = hashlib.sha256(encoded).hexdigest()
        return audit.validate_preflight(self.directory, self.pref, encoded, self.report, self.native)

    def test_explicit_v1_complete_binding(self):
        self.assertEqual(self.validate(), 'terraform-height-producer-preflight.v1')

    def test_unknown_null_or_missing_kind_never_falls_back(self):
        for kind in ('unknown.v9', None, 'missing'):
            with self.subTest(kind=kind):
                self.setUp()
                if kind == 'missing': self.pref.pop('kind')
                else: self.pref['kind'] = kind
                with self.assertRaises((AssertionError, KeyError)): self.validate()

    def test_v1_binds_digest_seed_files_and_mandatory_sources(self):
        for mutate in (lambda x: x.report.update(seed_requested='wrong'), lambda x: x.pref['source_sha256'].pop('preflight_producer'),
                       lambda x: x.report.update(shared_helpers_sha256={}), lambda x: (x.directory / 'fixture-world.gls.js').write_bytes(b'wrong input')):
            with self.subTest(mutate=mutate):
                self.setUp(); mutate(self)
                with self.assertRaises((AssertionError, KeyError)): self.validate()
        self.setUp(); encoded = json.dumps(self.pref).encode(); self.report['preflight_sha256'] = '0' * 64
        with self.assertRaises(AssertionError): audit.validate_preflight(self.directory, self.pref, encoded, self.report, self.native)


if __name__ == '__main__':
    unittest.main()
