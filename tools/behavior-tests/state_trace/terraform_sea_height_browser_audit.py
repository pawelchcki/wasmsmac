"""Read-only, typed audit of the bounded installed-source Sea Raise capture."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import struct
import subprocess
from pathlib import Path

SHARED = Path(__file__).with_name('terraform_height_browser_audit.py')
spec = importlib.util.spec_from_file_location('height_capture_audit', SHARED)
height = importlib.util.module_from_spec(spec)
spec.loader.exec_module(height)
HEAD = '7d26149abbaa028b3d685f3503df7c8e195fbdec'
NATIVE = '115032ffc7f53ff7f0c3a9f997da12674e25e643'
DEFAULT = '25ef18d3222f553507291d412330262169b2e418'
JS = 'e71036c9365a3ac87bf818e7eb49fb2344077a15aa6836371a436572cedf7f82'
WASM = 'b2c7fa273042f2407335169eb4fca51f131f1f30656301d7b7573a201b28f5b7'
POLICY = 'application.band-slope-height.v1'
FEE_POLICY = 'application.band-fee.v1'
DIRECTIONS = ('W', 'NW', 'N', 'NE', 'E', 'SE', 'S', 'SW')
EXTRA_TILE_FIELDS = {'resources', 'locked', 'native_type', 'native_height_band'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_records(raw):
    kinds = ('TH_NATIVE', 'TH_RECEIPT', 'TH_INPUTS', 'TH_TRACE', 'TH_HEADERS', 'TH_ROWS',
             'TH_SEA_DECLARED', 'TH_SEA_ACCOUNTING', 'TH_SEA_PRETURN', 'TH_SEA_BIRTH', 'TH_SEA_SETUP')
    records = []
    for line_number, line in enumerate(raw.decode('utf8').splitlines()):
        if 'TH_EXIT_REQUEST' in line:
            records.append(('TH_EXIT_REQUEST', None, line_number))
        for kind in kinds:
            if kind + '|' in line:
                value = json.loads(line.split(kind + '|', 1)[1])
                if kind == 'TH_TRACE': value = json.loads(value)
                records.append((kind, value, line_number))
                break
    return records


def one(records, kind):
    rows = [(value, line) for name, value, line in records if name == kind]
    assert len(rows) == 1, kind
    return rows[0]


def source_plan(before, actor):
    """Existing GSE band/slope policy, computed from BEFORE centers/topology."""
    tiles = before['terrain_trace']['tiles']
    start = (actor['x'], actor['y'])
    initial = tiles[f'{start[0]},{start[1]}']
    assert type(initial['elevation']['center']) is int and initial['is_water'] is True
    destination = (initial['elevation']['center'] // 1000 + 1) * 1000 + 500
    assert -3500 <= destination < 0
    queue, seen, baseline, patches = [(*start, 0)], {start}, [], []
    for x, y, distance in queue:
        state = tiles[f'{x},{y}']
        bound = destination - distance * 1000
        if state['elevation']['center'] < bound:
            assert state['is_water'] is (bound < 0), 'This case does not support a land/sea conversion'
            patches.append({'x': x, 'y': y, 'canonical': {'elevation': bound, 'is_water': bound < 0}})
        baseline.append({key: copy.deepcopy(value) for key, value in state.items() if key not in EXTRA_TILE_FIELDS})
        if distance < 7 and destination - (distance + 1) * 1000 >= -3500:
            for direction in DIRECTIONS:
                point = state['neighbors'][direction]
                if point is not None and (point['x'], point['y']) not in seen:
                    seen.add((point['x'], point['y']))
                    queue.append((point['x'], point['y'], distance + 1))
    assert patches == [{'x': 8, 'y': 8, 'canonical': {'elevation': -500, 'is_water': True}}], 'Different bounded authored effect'
    fee = max(1, initial['elevation']['center'] // 1000 + 2) ** 2
    return patches, baseline, destination, fee


def vertex(x, y, corner, width):
    dx, dy = {'left': (-1, 0), 'top': (0, -1), 'right': (1, 0), 'bottom': (0, 1)}[corner]
    return ((x + dx) % width, y + dy)


def cpp_div(numerator, denominator):
    return (abs(numerator) // denominator) * (-1 if numerator < 0 else 1)


def expected_paid_world(before, patches, fee, actor_id, payer):
    """No AFTER/quote values enter the expected world or shared-vertex mean."""
    expected = copy.deepcopy(before)
    actor = next(row for row in expected['units'] if row['id'] == actor_id)
    actor['movement'] = 0.0
    actor['order'] = 'NO_ORDERS'
    detail = expected['terrain_trace']['unit_details'][actor_id]
    detail['moved_this_turn'] = True
    for quote in detail['quotes'].values():
        if quote is not None: quote.update(allowed_now=False, reason='Unit is out of moves')
    energy = expected['terrain_trace']['player_details'][payer]
    assert type(energy['energy_revision']) is int
    energy['energy']['credits'] -= fee
    energy['energy_revision'] += 1
    tiles = before['terrain_trace']['tiles']
    patch_map = {(p['x'], p['y']): p['canonical'] for p in patches}
    changed_vertices = {}
    for x, y in patch_map:
        # This is deliberately an interior case. No unproved polar alias model.
        assert 2 <= x < before['width'] - 2 and 2 <= y < before['height'] - 2
        for corner in height.CORNERS:
            key = vertex(x, y, corner, before['width'])
            incident = [tile for tile in tiles.values() if any(vertex(tile['x'], tile['y'], c, before['width']) == key for c in height.CORNERS)]
            assert len(incident) == 4
            total = sum(patch_map.get((tile['x'], tile['y']), {}).get('elevation', tile['elevation']['center']) for tile in incident)
            changed_vertices[key] = cpp_div(total, len(incident))
    affected = []
    for name, old in tiles.items():
        target = expected['terrain_trace']['tiles'][name]
        geometry_changed = False
        for corner in height.CORNERS:
            point = vertex(old['x'], old['y'], corner, before['width'])
            if point in changed_vertices:
                value = changed_vertices[point]
                assert type(value) is int
                geometry_changed |= value != old['elevation'][corner]
                target['elevation'][corner] = value
        patch = patch_map.get((old['x'], old['y']))
        if patch is None and not geometry_changed: continue
        affected.append(name)
        target['terrain_epoch'] = old['terrain_epoch'] + 1
        target['canonical'].update(active=True, elevation=patch['elevation'] if patch else old['elevation']['center'],
                                   is_water=patch['is_water'] if patch else old['is_water'])
        if patch:
            target['elevation']['center'] = patch['elevation']
            target['is_water'], target['is_land'] = patch['is_water'], not patch['is_water']
            target['native_type']['domain'] = 'sea' if patch['is_water'] else 'land'
            target['imported'].update(active=False, source_corners=None, source_elevation=None, source_water=None)
            for band, threshold in zip(height.BANDS, (0, -1000, -2000)):
                target['native_height_band'][band] = patch['elevation'] < threshold
    assert len(affected) == 9
    return expected, affected, changed_vertices


def audit_records(records, report):
    packets, native = height.validate_sequence(records, report)
    before, after = height.world(packets[0]), height.world(packets[-1])
    assert all(height.equal(height.world(row), before) for row in packets[:5]), 'Quote/Cancel/draft changed native state'
    inputs, _ = one(records, 'TH_INPUTS')
    assert height.equal(report['native_input'], height.node_projection(inputs))
    assert type(inputs['actor']) is int and inputs['actor'] == 8 and inputs['definition'] == 'SeaFormers' and inputs['can_terraform'] is True
    rule = inputs['raise_rule']['sea']
    assert rule['id'] == 'raise' and rule['source_row'] == 16 and rule['name'] == 'Raise Sea Floor' and rule['order'] == 'Terraform UP'
    assert type(rule['turns']) is int and rule['turns'] == 1 and rule['enabled'] is True
    actor = next(row for row in before['units'] if row['raw_id'] == 8)
    owner = next(row for row in before['players'] if row['raw_id'] == 0)
    assert actor['owner'] == owner['id'] and owner['faction'] == 'GAIANS'
    assert (actor['x'], actor['y']) == (8, 8)
    assert all(height.equal(row['ui']['x'], actor['x']) and height.equal(row['ui']['y'], actor['y']) for row in packets)
    detail = before['terrain_trace']['unit_details'][actor['id']]
    assert detail['definition_id'] == 'SeaFormers' and detail['movement_kind'] == 'sea' and detail['can_terraform'] is True and detail['home_base_id'] == 1
    assert all(row['ui']['selected'] == 8 for row in packets[:5])
    patches, baseline, destination, fee = source_plan(before, actor)
    quote = packets[1]['ui']['height_presentation']['quote']
    for row in packets[2:]: assert height.equal(row['ui']['height_presentation']['quote'], quote)
    expected_fields = {'version': 1, 'supported': True, 'action': 'raise', 'resuming': False, 'paid_fee': 0,
                       'mode': 'functional_approximation', 'policy': POLICY, 'fee_policy': FEE_POLICY,
                       'unit_id': 8, 'owner': 0, 'turn': before['turn'], 'x': 8, 'y': 8,
                       'source_elevation': before['terrain_trace']['tiles']['8,8']['elevation']['center'], 'source_water': True,
                       'destination_elevation': destination, 'destination_water': True, 'base_fee': fee, 'fee': fee,
                       'credits': before['terrain_trace']['player_details'][owner['id']]['energy']['credits'], 'plan': patches}
    assert set(quote) == set(expected_fields) | {'reason', 'terrain_identity', 'unit_identity'} and quote['reason'] == ''
    for name, value in expected_fields.items(): assert height.equal(quote[name], value), ('Quote differs from BEFORE/source policy', name)
    assert not any(name in quote for name in ('name', 'sea')), 'No invented quote name echo'
    terrain_identity = json.loads(quote['terrain_identity'])
    assert height.equal(terrain_identity, {'version': 1, 'policy': POLICY, 'fee_policy': FEE_POLICY, 'tiles': baseline})
    identity = {'unit_id': 8, 'owner': 0, 'definition': 'SeaFormers', 'health': actor['health'], 'movement': actor['movement'],
                'moved': detail['moved_this_turn'], 'order': actor['order'], 'work': detail['work'], 'recovery': detail['terraforming_recovery'],
                'automation': detail['automation'], 'home': detail['home_base_id']}
    assert height.equal(json.loads(quote['unit_identity']), identity)
    assert type(fee) is int and fee == 1
    assert height.equal(inputs['starting_credits'], 10) and height.equal(inputs['faction_bonus'], 0) and quote['credits'] == 10
    assert height.equal(inputs['energy'], before['terrain_trace']['player_details'][owner['id']]['energy'])
    for row in (packets[1], packets[3], packets[4]):
        dialog = row['ui']['dialog']
        assert dialog['fee'] == fee and dialog['reserves'] == quote['credits']
        assert dialog['caption'] == 'Planetary Ecologist'
        assert dialog['source_lines'] == ['It will cost $NUM0 credits to {raise} this area;', 'our current reserves are $NUM1 credits.']
        assert dialog['lines'] == [f'It will cost {fee} credits to raise this area;', f'our current reserves are {quote["credits"]} credits.']
        assert dialog['source_choices'] == ['Cancel action.', 'Expend $NUM0 credits.']
        assert dialog['choices'] == ['Cancel action.', f'Expend {fee} credits.']
    expected, affected, vertices = expected_paid_world(before, patches, fee, actor['id'], owner['id'])
    assert height.equal(after, expected), ('Unexpected full typed native change', height.diffs(expected, after)[:8])
    assert height.equal(report['expected_effect_from_live_quote'], height.node_projection(quote))
    assert height.equal(report['actual_sea_row'], {'id': 'raise', 'label': rule['order'], 'enabled': True})
    port = [value for value in detail['quotes'].values() if value is not None and value['destination'] == {'x': 10, 'y': 8}]
    assert len(port) == 1 and port[0]['allowed_now'] is True
    assert height.equal(report['traversal']['home_port_before'], height.node_projection(port[0]))
    receipts = [(v, line) for k, v, line in records if k == 'TH_RECEIPT' and v['name'] == 'unit_terraform']
    assert len(receipts) == 1
    receipt, receipt_line = receipts[0]
    assert native[4][1] < receipt_line < native[5][1]
    assert height.equal(receipt, report['height_receipt']) and type(receipt['event_id']) is str and receipt['event_id']
    assert receipt['name'] == 'unit_terraform' and receipt['success'] is True and type(receipt['caller']) is int and receipt['caller'] == 0
    assert height.equal(receipt['data'], {'unit_id': 8, 'action': 'raise', 'confirmed_height': True})
    f32 = []
    for row in packets:
        for unit in row['world']['units']:
            for name in ('movement', 'health'):
                value = unit[name]
                assert type(value) is float and height.equal(value, struct.unpack('>f', struct.pack('>f', value))[0])
                f32.append({'query': row['query'], 'unit': unit['raw_id'], 'field': name, 'f32': struct.pack('>f', value).hex(), 'f64': struct.pack('>d', value).hex()})
        movement = row['ui']['movement']
        assert type(movement) is float and type(row['ui']['movement_bits']) is int
        assert int.from_bytes(struct.pack('>f', movement), 'big') == row['ui']['movement_bits']
        assert height.equal(movement, next(unit['movement'] for unit in row['world']['units'] if unit['raw_id'] == 8))
    assert [row['ui']['movement_bits'] for row in packets] == [1082130432] * 5 + [0]
    return {'status': 'passed-readonly-native-audit', 'native_cases_added': 0, 'browser_cases_audited': 0,
            'worlds': len(packets), 'per_world': height.validate_coverage(before), 'pure_worlds': 5,
            'changed_fields': len(height.diffs(before, after)), 'canonical_patches': patches, 'affected_tiles': affected,
            'source_vertex_means': [{'vertex': list(key), 'native_Int_height': value} for key, value in vertices.items()],
            'fee': fee, 'energy_before': quote['credits'], 'energy_after': quote['credits'] - fee,
            'revision_before': before['terrain_trace']['player_details'][owner['id']]['energy_revision'],
            'revision_after': after['terrain_trace']['player_details'][owner['id']]['energy_revision'],
            'native_float_fields': len(f32), 'unit_float_bits': f32,
            'actor_movement_bits': [row['ui']['movement_bits'] for row in packets], 'selection': [row['ui']['selected'] for row in packets],
            'scope': 'source application policy/corner Int consistency; no original or typed render-mesh vertex claim'}


def validate_bootstrap(records, report):
    accounting, accounting_line = one(records, 'TH_SEA_ACCOUNTING')
    preturn, preturn_line = one(records, 'TH_SEA_PRETURN')
    birth, birth_line = one(records, 'TH_SEA_BIRTH')
    setup, setup_line = one(records, 'TH_SEA_SETUP')
    assert height.equal(report['sea_setup'], height.node_projection(setup))
    declared = setup['declared']; recipe = declared['recipe']
    # Existing installed application recipe: triad0 pricing, Foil cost2,
    # basic Formers weapon6/armor1/reactor1; Load Map/Gaian mineral factor8.
    for name, value in [('chassis_cost', 2), ('weapon_cost', 6), ('armor_cost', 1), ('rows', 5), ('weapon_mode', 9)]:
        assert type(recipe[name]) is int and recipe[name] == value
    rows = max(2, ((recipe['chassis_cost'] + 1) * recipe['weapon_cost'] + recipe['chassis_cost']) // 4)
    cost = rows * 8
    assert recipe['id'] == 'SeaFormers' and recipe['movement_type'] == 'water' and cost == 40
    assert height.equal(accounting['observed_choice_cost'], cost) and height.equal(accounting['requested_stock'], cost + 3)
    assert height.equal(accounting['actual_prefill'], {'choice_id': recipe['choice'], 'minerals': cost + 3, 'last_processed_turn': 0})
    assert height.equal(accounting['source_recipe'], recipe)
    assert height.equal(accounting['owner'], 0) and height.equal(accounting['turn'], 1)
    assert height.equal(accounting['base_id'], 1) and height.equal(setup['home_id'], 1)
    assert accounting_line < preturn_line < birth_line < setup_line
    assert setup_line < next(line for kind, _, line in records if kind == 'TH_NATIVE')
    assert preturn['turn'] == 1 and preturn['home_id'] == 1
    assert len(preturn['bases']) == len(setup['base_states']) == 7
    mapping = lambda values: sorted((v['base_id'], v['owner']) for v in values)
    assert mapping(preturn['bases']) == mapping(setup['base_states']) == [(i + 1, i) for i in range(7)]
    credits = []
    for row in preturn['bases']:
        local = row['owner'] == 0
        assert height.equal(row['population'], 1) and row['eligible'] is local
        assert height.equal(row['intake']['MINERALS'], 1) and height.equal(row['consumption']['MINERALS'], 0)
        assert height.equal(row['intake']['NUTRIENTS'], 2) and height.equal(row['consumption']['NUTRIENTS'], 2)
        assert height.equal(row['production'], {'choice_id': recipe['choice'] if local else declared['resumed_choice'], 'minerals': cost + 3 if local else 0, 'last_processed_turn': 0 if local else 1})
        if local: credits.append(max(0, row['intake']['MINERALS'] - row['consumption']['MINERALS']))
    assert credits == [1]
    overflow = cost + 3 + credits[0] - cost
    assert height.equal(birth['production'], {'choice_id': '', 'minerals': overflow, 'last_processed_turn': 1})
    assert all(height.equal(value, expected) for value, expected in [(birth['unit_id'], 8), (setup['actor'], 8), (birth['home_id'], 1), (birth['home_population'], 1)])
    assert birth['definition'] == 'SeaFormers' and birth['is_water'] is True and birth['can_terraform'] is True and (birth['x'], birth['y']) == (8, 8)
    assert type(birth['movement']) is float and birth['movement'] == 4.0 and type(birth['health']) is float and birth['health'] == 1.0
    production = [(v, line) for k, v, line in records if k == 'TH_RECEIPT' and v['name'] == 'process_base_production']
    growth = [(v, line) for k, v, line in records if k == 'TH_RECEIPT' and v['name'] == 'process_base_growth']
    resumed = [(v, line) for k, v, line in records if k == 'TH_RECEIPT' and v['name'] == 'set_base_production']
    assert len(production) == len(resumed) == 1 and len(growth) == 7
    assert birth_line < production[0][1] < growth[0][1] and all(line < resumed[0][1] < setup_line for _, line in growth)
    results = production + growth + resumed
    assert all(v['success'] is True and type(v['caller']) is int and v['caller'] == 0 and type(v['event_id']) is str for v, _ in results)
    assert len({v['event_id'] for v, _ in results}) == 9
    all_ids = [value['event_id'] for kind, value, _ in records if kind == 'TH_RECEIPT']
    assert all(type(value) is str and value for value in all_ids) and len(set(all_ids)) == len(all_ids)
    assert all(type(v['data']['turn_id']) is int and v['data']['turn_id'] == 1 for v, _ in production + growth)
    assert height.equal(production[0][0]['data']['minerals'], credits[0]) and resumed[0][0]['data']['choice_id'] == declared['resumed_choice']
    baseline = next(value for kind, value, _ in records if kind == 'TH_NATIVE')['world']
    native_owners = {player['id']: player['raw_id'] for player in baseline['players']}
    assert sorted((base['raw_id'], native_owners[base['owner']]) for base in baseline['bases']) == mapping(setup['base_states'])
    for row in setup['base_states']:
        assert height.equal(row['population'], 1)
        assert height.equal(row['production'], {'choice_id': declared['resumed_choice'], 'minerals': overflow if row['owner'] == 0 else 0, 'last_processed_turn': 1})
        base = next(base for base in baseline['bases'] if base['raw_id'] == row['base_id'])
        assert height.equal(baseline['terrain_trace']['base_details'][base['id']]['production'], row['production'])
    return {'native_choice_cost': cost, 'native_prefill': cost + 3, 'income': credits[0], 'overflow': overflow,
            'production_receipts': 1, 'growth_receipts': 7, 'scope': 'scalar receipts plus all-seven source/current-turn state; no fabricated per-base ACK echo'}


def validate_provenance(directory, report, source_root):
    preflight = json.loads((directory / 'preflight.json').read_bytes())
    assert preflight['kind'] == 'terraform-sea-height-preflight.v3' and preflight['candidate_executed'] is False
    assert preflight['head'] == report['host_head'] == HEAD
    assert preflight['native_tree'] == report['native_source_tree'] == NATIVE
    assert preflight['default_tree'] == report['default_tree'] == DEFAULT
    assert preflight['runtime']['GLSMAC.js'] == report['runtime_js_sha256'] == JS
    assert preflight['runtime']['GLSMAC.wasm'] == report['runtime_wasm_sha256'] == WASM
    assert preflight['browser_budget_ms'] == 180000 and preflight['native_timeout_override'] is None
    assert preflight['sea_menu_contract_version'] == report['sea_menu_contract_version'] == 3
    assert digest(directory / 'preflight.py') == preflight['preflight_producer_sha256']
    assert preflight['seed_requested'] == report['seed_requested'] == '1651011033:1377505029:3019448108:3247278135'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source_root, text=True).strip() == HEAD
    assert subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=source_root, text=True) == ''
    files = preflight['source_sha256']
    for name, value in {**files, **preflight['default_source_sha256']}.items(): assert digest(source_root / name) == value
    assert len(files) == 18 and len(preflight['default_source_sha256']) == 220
    mapping = {'driver_sha256': 'terraform-sea-height-browser.test.mjs', 'height_observation_sha256': 'terraform-height-observation.mjs',
               'sea_observation_sha256': 'terraform-sea-height-observation.mjs', 'sea_input_sha256': 'terraform-sea-height-inputs.mjs',
               'observer_sha256': 'fixtures/terraform-sea-height-main.gls.js', 'world_input_sha256': 'fixtures/terraform-sea-height-world.gls.js'}
    for name, file in mapping.items(): assert report[name] == files['tools/wasm-tests/' + file]
    for name, value in report['shared_helpers_sha256'].items(): assert value == files['tools/wasm-tests/' + name]
    assert digest(directory / 'fixture-main.gls.js') == report['observer_sha256'] and digest(directory / 'fixture-world.gls.js') == report['world_input_sha256']
    assert digest(directory / 'declared-map.MP') == report['map_sha256'] == preflight['inputs']['map_sha256']
    assert report['source_override']['original_sha256'] == preflight['inputs']['original_rules_sha256'] == 'bb01e3ac23793da0a46713f4851d65e63b599c24aef8300ffe45e7e57b332c42'
    assert report['source_override']['rate_one_sha256'] == preflight['inputs']['executed_rules_sha256'] == '7abf62aa4f4f562aaa86c785b67b7af2320e122cbda7901287ee3ed0ab4c5bd0'
    assert height.equal(report['source_override']['rows'], preflight['inputs']['override_table']) and len(report['source_override']['rows']) == 20
    for row in report['source_override']['rows']:
        assert row['field_index'] == 4 and row['new'] == 1 and row['applies_to'] == ['land', 'sea']
    return preflight


def validate_outer(directory, report, raw):
    # One genuine retained external receipt, not a fallback for new captures.
    assert digest(directory / 'raw-outcome.json') == '95ef0e7d413ffd9c11787d9034c56fd8e2eace4323c4e552d9c92a55a2c13da3'
    outcome = json.loads((directory / 'raw-outcome.json').read_bytes())
    completion = json.loads((directory / 'external-completion.json').read_bytes())
    assert outcome['kind'] == 'sea-height-v3-genuine-external-outcome' and outcome['status'] == 'exited'
    assert type(outcome['actual_os_node_exit_code']) is int and outcome['actual_os_node_exit_code'] == 0 and outcome['actual_node_wait_returned'] is True
    assert outcome['external_tool_completion'] == {'session_id': 52401, 'chunk_id': '60a1a5', 'exit_code': 0}
    assert outcome['source_head'] == HEAD and outcome['report_sha256'] == digest(directory / 'report.json')
    assert outcome['preflight_sha256'] == digest(directory / 'preflight.json') and outcome['raw_sha256'] == hashlib.sha256(raw).hexdigest()
    assert height.equal(outcome['native_exit'], report['native_exit'])
    for field in ('owned_group_absent', 'browser_server_driver_reaped', 'postpins_match', 'temporary_dependency_link_removed'): assert outcome[field] is True
    assert outcome['forced_cleanup'] is False and outcome['actual_external_driver_exit_code'] == 0
    assert completion['actual_wait_returned'] is True and type(completion['actual_os_node_exit_code']) is int and completion['actual_os_node_exit_code'] == 0
    assert completion['owned_group_absent'] is True and completion['forced_cleanup'] is False and completion['outer_timed_out'] is False
    assert outcome['external_completion_sha256'] == digest(directory / 'external-completion.json')
    assert outcome['external_driver_sha256'] == completion['external_driver_sha256'] == digest(directory / 'run-once.py')
    return {'external_node_os_exit': 0, 'native_app_exit': 0, 'tool_session': 52401, 'tool_chunk': '60a1a5',
            'raw_outcome_sha256': digest(directory / 'raw-outcome.json'), 'owned_reaped_without_forced_cleanup': True}


def audit_artifacts(directory, source_root):
    directory, source_root = Path(directory), Path(source_root)
    raw = (directory / 'application.log').read_bytes()
    records = parse_records(raw)
    report = json.loads((directory / 'report.json').read_bytes())
    result = audit_records(records, report)
    result['bootstrap'] = validate_bootstrap(records, report)
    validate_provenance(directory, report, source_root)
    chunks = [json.loads(line) for line in (directory / 'application-log-chunks.jsonl').read_text().splitlines() if line]
    result['finalization'] = height.validate_finalization(report, raw, chunks, records)
    result['pointer_route'] = height.validate_pointer_route(records, report)
    result['external_exit'] = validate_outer(directory, report, raw)
    expected_frames = ['before-height', 'raise-quote', 'raise-cancel', 'raise-payment-draft', 'raise-paid-completion']
    assert [frame['name'] for frame in report['captures']] == expected_frames
    # Playwright's element screenshot rounds the fractional document clip
    # outward (coreBundle Helper.enclosingIntRect), unlike native viewport size.
    box = report['processed_pointers'][0]['canvas_css_rect']
    clip = tuple(math.ceil(box[axis] + box[size] - 1e-3) - math.floor(box[axis] + 1e-3)
                 for axis, size in [('x', 'width'), ('y', 'height')])
    assert clip == (report['rendered_readiness']['width'], report['rendered_readiness']['height'])
    for frame in report['captures']:
        path = directory / (frame['name'] + '.png')
        assert digest(path) == frame['sha256'] and struct.unpack('>II', path.read_bytes()[16:24]) == clip
    result.update(status='passed-readonly-full-sea-browser-audit', browser_cases_audited=1, raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(),
                  report_sha256=digest(directory / 'report.json'), preflight_sha256=digest(directory / 'preflight.json'),
                  auditor_sha256=digest(__file__), shared_height_auditor_sha256=digest(SHARED), frames=5,
                  native_viewport={'width': 1024, 'height': 768}, png_clip_dimensions=list(clip),
                  unsupported=['original height/price/wording parity', 'numeric render-mesh vertices/resident Z/facing/tool frames/audio/animation',
                               'fixed camera (only viewport fixed)', 'Sea water-to-land/coast/stranded worker/lower scenarios', 'actual movement (traversal quotes only)'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--source-root', required=True, type=Path, help='Unmodified actual7d frozen source checkout')
    parser.add_argument('--output', required=True, type=Path, help='NEW derived result; original report/raw are never rewritten')
    args = parser.parse_args()
    assert not args.output.exists(), 'Keep each previous derived result immutable'
    result = audit_artifacts(args.artifacts, args.source_root)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'unit_float_bits'}, indent=2))


if __name__ == '__main__': main()
