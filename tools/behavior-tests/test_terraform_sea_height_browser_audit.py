"""Public protocol models and separately optional retained Sea mutations.

These tests never run a game. Public model counts are not private capture or
original-game evidence. Set TERRAFORM_SEA_HEIGHT_CAPTURE for retained mutations.
"""
import copy
import importlib.util
import json
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value

sea = load('sea_audit', ROOT / 'state_trace/terraform_sea_height_browser_audit.py')
land_models = load('land_protocol_models', ROOT / 'test_terraform_height_browser_audit.py')


def model():
    """Uniform240 land around one authored deep tile: corner means55 after.

    AFTER values are independent literals. The real capture has varied centers;
    its expected means are independently computed from its own BEFORE values.
    """
    records, report = land_models.protocol_fixture()
    before = copy.deepcopy(next(v for k, v, _ in records if k == 'TH_NATIVE')['world'])
    tiles = before['terrain_trace']['tiles']; points = set(tiles)
    offsets = dict(zip(sea.DIRECTIONS, [(-2, 0), (-1, -1), (0, -2), (1, -1), (2, 0), (1, 1), (0, 2), (-1, 1)]))
    touched_vertices = {(7, 8), (8, 7), (9, 8), (8, 9)}
    for tile in tiles.values():
        x, y = tile['x'], tile['y']
        tile['neighbors'] = {name: {'x': (x + dx) % 16, 'y': y + dy} if f'{(x + dx) % 16},{y + dy}' in points else None for name, (dx, dy) in offsets.items()}
        tile['elevation']['center'] = -1460 if (x, y) == (8, 8) else 240
        for corner in sea.height.CORNERS:
            tile['elevation'][corner] = -185 if sea.vertex(x, y, corner, 16) in touched_vertices else 240
        water = (x, y) == (8, 8)
        tile.update(is_water=water, is_land=not water)
        tile['native_type']['domain'] = 'sea' if water else 'land'
        tile['native_height_band'] = {'below_coast': water, 'below_ocean': water, 'below_trench': False}
        tile['imported'].update(source_elevation=tile['elevation']['center'], source_water=water, source_corners=[tile['elevation'][c] for c in sea.height.CORNERS])
    actor = before['units'][-1]; actor.update(x=8, y=8, movement=4.0)
    detail = before['terrain_trace']['unit_details']['u8']
    detail.update(definition_id='SeaFormers', movement_kind='sea', can_terraform=True, home_base_id=1,
                  work={'action': '', 'work_units': 0}, terraforming_recovery={'active': False, 'x': 0, 'y': 0}, automation={'version': 2, 'epoch': 0})
    detail['quotes']['E']['destination'] = {'x': 10, 'y': 8}
    for i in range(7):
        before['terrain_trace']['base_details'][f'b{i + 1}']['production'] = {'choice_id': 'FORMERS', 'minerals': 4 if i == 0 else 0, 'last_processed_turn': 1}
    after = copy.deepcopy(before)
    after['units'][-1]['movement'] = 0.0
    after['terrain_trace']['unit_details']['u8']['moved_this_turn'] = True
    after['terrain_trace']['unit_details']['u8']['quotes']['E'].update(allowed_now=False, reason='Unit is out of moves')
    after['terrain_trace']['player_details']['p0']['energy']['credits'] = 9
    after['terrain_trace']['player_details']['p0']['energy_revision'] = 2
    for name, tile in after['terrain_trace']['tiles'].items():
        changed = False
        for corner in sea.height.CORNERS:
            if sea.vertex(tile['x'], tile['y'], corner, 16) in touched_vertices:
                tile['elevation'][corner] = 55; changed = True
        if changed:
            tile['terrain_epoch'] = 1
            tile['canonical'].update(active=True, elevation=tile['elevation']['center'], is_water=tile['is_water'])
    target = after['terrain_trace']['tiles']['8,8']
    target['elevation']['center'] = -500; target['canonical']['elevation'] = -500
    target['imported'].update(active=False, source_corners=None, source_elevation=None, source_water=None)
    target['native_height_band']['below_ocean'] = False
    # Model the known radius3 source identity order without constructing AFTER
    # from the implementation under test.
    queue, seen, baseline = [(8, 8, 0)], {(8, 8)}, []
    for x, y, distance in queue:
        tile = tiles[f'{x},{y}']
        # Native getter identity precedes the observer's four additions.
        baseline.append({key: copy.deepcopy(value) for key, value in tile.items() if key not in sea.EXTRA_TILE_FIELDS})
        if distance < 3:
            for dx, dy in offsets.values():
                point = ((x + dx) % 16, y + dy)
                if point not in seen:
                    seen.add(point); queue.append((*point, distance + 1))
    identity = {'unit_id': 8, 'owner': 0, 'definition': 'SeaFormers', 'health': 1.0, 'movement': 4.0, 'moved': False,
                'order': 'NO_ORDERS', 'work': detail['work'], 'recovery': detail['terraforming_recovery'], 'automation': detail['automation'], 'home': 1}
    quote = {'version': 1, 'supported': True, 'reason': '', 'action': 'raise', 'resuming': False, 'paid_fee': 0,
             'mode': 'functional_approximation', 'policy': sea.POLICY, 'fee_policy': sea.FEE_POLICY, 'unit_id': 8, 'owner': 0,
             'turn': 1, 'x': 8, 'y': 8, 'source_elevation': -1460, 'source_water': True, 'destination_elevation': -500,
             'destination_water': True, 'base_fee': 1, 'fee': 1, 'credits': 10,
             'plan': [{'x': 8, 'y': 8, 'canonical': {'elevation': -500, 'is_water': True}}],
             'unit_identity': json.dumps(identity), 'terrain_identity': json.dumps({'version': 1, 'policy': sea.POLICY, 'fee_policy': sea.FEE_POLICY, 'tiles': baseline})}
    inputs = {'actor': 8, 'definition': 'SeaFormers', 'can_terraform': True, 'policy': {'version': 1, 'ignore_technologies': True},
              'starting_credits': 10, 'faction_bonus': 0, 'energy': copy.deepcopy(before['terrain_trace']['player_details']['p0']['energy']), 'raise_rule': {'sea': {'id': 'raise', 'source_row': 16,
              'name': 'Raise Sea Floor', 'order': 'Terraform UP', 'turns': 1, 'enabled': True}}}
    changed = []
    for kind, value, line in records:
        if kind == 'TH_INPUTS': value = copy.deepcopy(inputs)
        if kind == 'TH_NATIVE':
            i = value['query'] - 1; value['world'] = copy.deepcopy(after if i == 5 else before)
            value['ui'].update(selected=8 if i < 5 else None, x=8, y=8, movement=4.0 if i < 5 else 0.0, movement_bits=1082130432 if i < 5 else 0)
            if i > 0: value['ui']['height_presentation']['quote'] = copy.deepcopy(quote)
            if value['ui']['dialog'] is not None:
                value['ui']['dialog'] = {'fee': 1, 'reserves': 10, 'caption': 'Planetary Ecologist',
                    'source_lines': ['It will cost $NUM0 credits to {raise} this area;', 'our current reserves are $NUM1 credits.'],
                    'lines': ['It will cost 1 credits to raise this area;', 'our current reserves are 10 credits.'],
                    'source_choices': ['Cancel action.', 'Expend $NUM0 credits.'], 'choices': ['Cancel action.', 'Expend 1 credits.']}
        if kind == 'TH_RECEIPT': value['event_id'] = 'model-height-accepted'
        changed.append((kind, value, line + 100 if kind in ('TH_NATIVE', 'TH_TRACE', 'TH_RECEIPT') else line))
    changed.append(('TH_EXIT_REQUEST', None, max(line for _, _, line in changed) + 1))
    report.update(native_input=copy.deepcopy(inputs), actual_sea_row={'id': 'raise', 'label': 'Terraform UP', 'enabled': True},
                  expected_effect_from_live_quote=copy.deepcopy(quote), traversal={'home_port_before': copy.deepcopy(detail['quotes']['E'])})
    for item, packet in zip(report['native_snapshots'], [v for k, v, _ in changed if k == 'TH_NATIVE']): item['observation'] = sea.height.node_projection(packet)
    report['height_receipt'] = copy.deepcopy(next(v for k, v, _ in changed if k == 'TH_RECEIPT'))
    recipe = {'id': 'SeaFormers', 'choice': 'SEA_FORMERS', 'movement_type': 'water', 'chassis_cost': 2, 'weapon_cost': 6, 'armor_cost': 1, 'rows': 5, 'weapon_mode': 9}
    states = [{'base_id': i + 1, 'owner': i, 'population': 1, 'production': {'choice_id': 'FORMERS', 'minerals': 4 if i == 0 else 0, 'last_processed_turn': 1}} for i in range(7)]
    setup = {'actor': 8, 'home_id': 1, 'base_states': states, 'declared': {'recipe': recipe, 'resumed_choice': 'FORMERS'}}
    account = {'observed_choice_cost': 40, 'requested_stock': 43, 'source_recipe': recipe, 'actual_prefill': {'choice_id': 'SEA_FORMERS', 'minerals': 43, 'last_processed_turn': 0}, 'owner': 0, 'turn': 1, 'base_id': 1}
    preturn = {'turn': 1, 'home_id': 1, 'bases': [dict(row, eligible=i == 0, intake={'MINERALS': 1, 'NUTRIENTS': 2}, consumption={'MINERALS': 0, 'NUTRIENTS': 2},
        production={'choice_id': 'SEA_FORMERS' if i == 0 else 'FORMERS', 'minerals': 43 if i == 0 else 0, 'last_processed_turn': 0 if i == 0 else 1}) for i, row in enumerate(states)]}
    birth = {'production': {'choice_id': '', 'minerals': 4, 'last_processed_turn': 1}, 'unit_id': 8, 'home_id': 1, 'home_population': 1,
             'definition': 'SeaFormers', 'is_water': True, 'can_terraform': True, 'x': 8, 'y': 8, 'health': 1.0, 'movement': 4.0}
    prefix = [('TH_SEA_ACCOUNTING', account, 1), ('TH_SEA_PRETURN', preturn, 2), ('TH_SEA_BIRTH', birth, 3)]
    for i in range(9):
        name = 'process_base_production' if i == 0 else ('process_base_growth' if i < 8 else 'set_base_production')
        data = {'turn_id': 1, 'minerals': 1} if i == 0 else ({'turn_id': 1} if i < 8 else {'choice_id': 'FORMERS'})
        prefix.append(('TH_RECEIPT', {'name': name, 'event_id': f'model-bootstrap-{i}', 'success': True, 'caller': 0, 'data': data}, i + 4))
    prefix.append(('TH_SEA_SETUP', setup, 13)); report['sea_setup'] = copy.deepcopy(setup)
    return prefix + changed, report


class DomainMutations:
    def setUp(self): self.records, self.report = copy.deepcopy(self.original)
    def packets(self): return [v for k, v, _ in self.records if k == 'TH_NATIVE']
    def quote(self): return self.packets()[1]['ui']['height_presentation']['quote']
    def sync(self):
        for item, packet in zip(self.report['native_snapshots'], self.packets()): item['observation'] = sea.height.node_projection(packet)
        self.report['native_input'] = sea.height.node_projection(next(v for k, v, _ in self.records if k == 'TH_INPUTS'))
        self.report['expected_effect_from_live_quote'] = sea.height.node_projection(self.quote())
        self.report['height_receipt'] = next(v for k, v, _ in self.records if k == 'TH_RECEIPT' and v['name'] == 'unit_terraform')
    def reject(self):
        self.sync()
        with self.assertRaises((AssertionError, KeyError, TypeError)): sea.audit_records(self.records, self.report)
    def set_quote(self, key, value):
        for packet in self.packets()[1:]: packet['ui']['height_presentation']['quote'][key] = copy.deepcopy(value)
    def test_valid_typed_world_is_readonly(self):
        before = copy.deepcopy((self.records, self.report)); result = sea.audit_records(self.records, self.report)
        self.assertEqual(result['native_float_fields'], 96); self.assertEqual(result['fee'], 1)
        self.assertEqual(result['per_world'], {'players': 7, 'units': 8, 'bases': 7, 'tiles': 128})
        self.assertEqual(result['browser_cases_audited'], 0); self.assertTrue(sea.height.equal(before, (self.records, self.report)))
    def test_coherent_foreign_actor_and_remote_position_are_rejected(self):
        # All six native worlds and their reported copies agree. A matching
        # report must not turn a foreign actor or remote position into payer0.
        for field, value in [('owner', 'p1'), ('x', 10), ('y', 10)]:
            self.setUp()
            for packet in self.packets():
                next(unit for unit in packet['world']['units'] if unit['raw_id'] == 8)[field] = value
            self.reject()
    def test_coherent_funding_cannot_contradict_native_energy(self):
        for field, value in [('starting_credits', 999), ('faction_bonus', 3),
                             ('energy', {'credits': 123, 'initialized': True, 'last_income_turn': 0})]:
            self.setUp()
            next(value for kind, value, _ in self.records if kind == 'TH_INPUTS')[field] = copy.deepcopy(value)
            self.reject()
    def test_coherent_uninitialized_or_precredited_energy_is_not_the_authored_input(self):
        for field, value in [('initialized', False), ('last_income_turn', 1), ('last_income_turn', False)]:
            self.setUp()
            for packet in self.packets():
                owner = next(player['id'] for player in packet['world']['players'] if player['raw_id'] == 0)
                packet['world']['terrain_trace']['player_details'][owner]['energy'][field] = value
            next(row for kind, row, _ in self.records if kind == 'TH_INPUTS')['energy'][field] = value
            self.reject()
    def test_query_carrier_stays_inside_each_native_checkpoint(self):
        for query in (1, 6):
            self.setUp()
            fence = self.report['native_snapshots'][query - 1]['query_after_native_key']
            index = next(i for i, (kind, value, _) in enumerate(self.records)
                         if kind == 'TH_TRACE' and any(event['seq'] == fence for event in value['events']))
            kind, value, _ = self.records[index]
            # Last query must precede the real exit marker, not merely appear
            # somewhere after its native snapshot. The first must follow its
            # own Native packet, not an earlier carrier.
            boundary = next(line for kind, _, line in self.records if kind == 'TH_EXIT_REQUEST') if query == 6 else next(line for kind, value, line in self.records if kind == 'TH_NATIVE' and value['query'] == query)
            self.records[index] = kind, value, boundary + 1 if query == 6 else boundary - 1
            self.reject()
    def test_wrong_land_domain_actor_fee_or_source_policy_rejects(self):
        for key, value in [('source_water', False), ('destination_water', False), ('unit_id', 1), ('owner', 1), ('action', 'lower'), ('fee', 2), ('credits', 9), ('destination_elevation', -1500), ('policy', 'unknown')]:
            self.setUp(); self.set_quote(key, value); self.reject()
    def test_quote_plan_and_terrain_epoch_are_not_the_oracle(self):
        self.set_quote('plan', [{'x': 8, 'y': 8, 'canonical': {'elevation': -600, 'is_water': True}}]); self.reject()
        self.setUp(); identity = json.loads(self.quote()['terrain_identity']); identity['tiles'][0]['terrain_epoch'] += 1
        self.set_quote('terrain_identity', json.dumps(identity)); self.reject()
    def test_wrong_native_unit_identity_and_metadata(self):
        identity = json.loads(self.quote()['unit_identity']); identity['definition'] = 'Formers'; self.set_quote('unit_identity', json.dumps(identity)); self.reject()
        self.setUp(); next(v for k, v, _ in self.records if k == 'TH_INPUTS')['raise_rule']['sea']['name'] = 'Raise Land'; self.reject()
    def test_geometry_within_range_still_must_equal_source_mean(self):
        self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']['elevation']['left'] += 1; self.reject()
    def test_epoch_canonical_neighbor_and_band_exact_values(self):
        for change in ('epoch', 'center', 'band'):
            self.setUp(); tile = self.packets()[-1]['world']['terrain_trace']['tiles']['8,8']
            if change == 'epoch': tile['terrain_epoch'] += 1
            if change == 'center': tile['canonical']['elevation'] = -600
            if change == 'band': tile['native_height_band']['below_ocean'] = True
            self.reject()
    def test_other_owners_unknown_fields_and_signed_zero_unchanged(self):
        self.packets()[-1]['world']['units'][0]['health'] = 0.5; self.reject()
        self.setUp(); self.packets()[-1]['world']['terrain_trace']['player_details'][next(p['id'] for p in self.packets()[0]['world']['players'] if p['raw_id'] == 1)]['extra'] = 'unexpected'; self.reject()
        self.setUp()
        for row in self.packets(): row['world']['terrain_trace']['tiles']['0,0']['extra_signed_zero'] = -0.0
        self.packets()[-1]['world']['terrain_trace']['tiles']['0,0']['extra_signed_zero'] = 0.0; self.reject()
    def test_float_token_and_roundtrip_bits_are_required(self):
        self.packets()[-1]['world']['units'][-1]['movement'] = 0; self.reject()
        self.setUp()
        for row in self.packets(): row['world']['units'][0]['health'] = 0.1
        self.reject()
    def test_first_five_quote_cancel_draft_are_pure(self):
        self.packets()[2]['world']['units'][0]['health'] = 0.5; self.reject()
    def test_bool_revision_or_source_policy_is_not_native_int(self):
        for row in self.packets()[:5]: row['world']['terrain_trace']['player_details'][next(p['id'] for p in row['world']['players'] if p['raw_id'] == 0)]['energy_revision'] = True
        self.reject()
    def test_modal_source_choice_and_receipt_binding(self):
        self.packets()[1]['ui']['dialog']['choices'][1] = 'Expend 2 credits.'; self.reject()
        self.setUp(); next(v for k, v, _ in self.records if k == 'TH_RECEIPT' and v['name'] == 'unit_terraform')['data']['unit_id'] = 1; self.reject()
    def test_missing_foreign_player_or_tile(self):
        for row in self.packets(): row['world']['players'].pop()
        self.reject()


class BootstrapMutations:
    def setUp(self): self.records, self.report = copy.deepcopy(self.original)
    def row(self, kind): return next(v for k, v, _ in self.records if k == kind)
    def reject(self):
        self.report['sea_setup'] = sea.height.node_projection(self.row('TH_SEA_SETUP'))
        with self.assertRaises((AssertionError, KeyError, TypeError)): sea.validate_bootstrap(self.records, self.report)
    def test_valid_accounting(self):
        result = sea.validate_bootstrap(self.records, self.report)
        self.assertEqual((result['native_choice_cost'], result['native_prefill'], result['income'], result['overflow']), (40, 43, 1, 4))
    def test_native_price_prefill_recipe_and_credit_not_assumed(self):
        for key, value in [('observed_choice_cost', 80), ('requested_stock', 83)]:
            self.setUp(); self.row('TH_SEA_ACCOUNTING')[key] = value; self.reject()
        self.setUp(); self.row('TH_SEA_PRETURN')['bases'][0]['intake']['MINERALS'] = True; self.reject()
    def test_wrong_base_identity_clock_or_overflow(self):
        self.row('TH_SEA_SETUP')['base_states'][-1]['base_id'] = 90; self.reject()
        self.setUp(); self.row('TH_SEA_PRETURN')['bases'][1]['production']['last_processed_turn'] = 0; self.reject()
        self.setUp(); self.row('TH_SEA_BIRTH')['production']['minerals'] = 3; self.reject()
    def test_missing_growth_or_early_resumption_is_not_ready(self):
        self.records.pop(next(i for i, (k, v, _) in enumerate(self.records) if k == 'TH_RECEIPT' and v['name'] == 'process_base_growth')); self.reject()
        self.setUp(); index = next(i for i, (k, v, _) in enumerate(self.records) if k == 'TH_RECEIPT' and v['name'] == 'set_base_production')
        kind, value, _ = self.records[index]; self.records[index] = kind, value, 0; self.reject()


class PublicSeaDomainTests(DomainMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.original = model()

class PublicSeaParserTests(unittest.TestCase):
    def test_exit_marker_is_retained_for_the_last_query_interval(self):
        self.assertEqual(sea.parse_records(b'prefix\nTH_EXIT_REQUEST\n'), [('TH_EXIT_REQUEST', None, 1)])

class PublicSeaBootstrapTests(BootstrapMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.original = model()


@unittest.skipUnless(os.environ.get('TERRAFORM_SEA_HEIGHT_CAPTURE'), 'Private retained capture is separate from public checks')
class RetainedSeaDomainTests(DomainMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = Path(os.environ['TERRAFORM_SEA_HEIGHT_CAPTURE']); cls.original = sea.parse_records((directory / 'application.log').read_bytes()), json.loads((directory / 'report.json').read_bytes())
    def test_full_retained_artifact_source_geometry_and_external_proof(self):
        result = sea.audit_artifacts(Path(os.environ['TERRAFORM_SEA_HEIGHT_CAPTURE']), Path(os.environ['TERRAFORM_SEA_SOURCE_ROOT']))
        self.assertEqual(result['changed_fields'], 71)
        self.assertEqual(result['browser_cases_audited'], 0)
        self.assertEqual(result['complete_browser_cases_audited'], 0)
        self.assertEqual(result['bounded_state_receipt_cases_audited'], 1)
        self.assertEqual(result['status'], 'partial-readonly-bounded-state-receipt-audit')
        self.assertFalse(result['finalization']['exact_callback_message_identity']['supported'])
        self.assertEqual(result['raw_sha256'], '191a6ffcf96f896ad8b7a0e009446bb406092133229461497492d6e6ccd7bb98')
        self.assertEqual({item['native_Int_height'] for item in result['source_vertex_means']}, {38, 42, 43, 47})

@unittest.skipUnless(os.environ.get('TERRAFORM_SEA_HEIGHT_CAPTURE'), 'Private retained capture is separate from public checks')
class RetainedSeaBootstrapTests(BootstrapMutations, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = Path(os.environ['TERRAFORM_SEA_HEIGHT_CAPTURE']); cls.original = sea.parse_records((directory / 'application.log').read_bytes()), json.loads((directory / 'report.json').read_bytes())


if __name__ == '__main__': unittest.main()
