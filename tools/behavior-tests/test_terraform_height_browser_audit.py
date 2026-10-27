"""Protocol regressions; optional retained browser artifacts are read-only.

TERRAFORM_HEIGHT_CAPTURE=/path/to/accepted/artifacts runs the same mutations
against all six actual retained packets, in addition to asset-free protocol data.
Neither test family executes a game or establishes new native/browser coverage.
"""
import copy
import importlib.util
import json
import os
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
    trace = {'ui': {}, 'tiles': tiles, 'unit_details': {u['id']: {'moved_this_turn': False, 'quotes': {'E': {'allowed_now': True, 'reason': None}}} for u in units},
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
    inputs = {'actor': 8, 'can_terraform': True, 'raise_rule': {'turns': 1}}
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


if __name__ == '__main__':
    unittest.main()
