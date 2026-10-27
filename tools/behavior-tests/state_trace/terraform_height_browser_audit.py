"""Read-only audit of the bounded land-height browser capture, not a new run."""
import argparse
import copy
import hashlib
import json
import struct
import re
import math
from pathlib import Path

CHECKPOINTS = ('before-height', 'raise-quote', 'raise-cancel', 'raise-reopened',
               'raise-payment-draft', 'raise-paid-completion')
SCOPES = ('root', 'height', 'root', 'height', 'height', 'root')
STAGES = (None, 'pending-consent', 'cancelled', 'pending-consent', 'pending-consent', 'submitted')
BANDS = ('below_coast', 'below_ocean', 'below_trench')
CORNERS = ('left', 'top', 'right', 'bottom')


def equal(a, b):
    """Native JSON preserves integral Float tokens and the sign of zero."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return struct.pack('>d', a) == struct.pack('>d', b)
    return a == b


def node_projection(value):
    """Report JSON folds integral JS Numbers; it never proves native types."""
    if isinstance(value, dict):
        return {k: node_projection(v) for k, v in value.items()}
    if isinstance(value, list):
        return [node_projection(v) for v in value]
    if type(value) is float and value.is_integer():
        return int(value)
    return value


def parse_records(raw):
    records = []
    for line_number, line in enumerate(raw.decode('utf8').splitlines()):
        for kind in ('TH_NATIVE', 'TH_RECEIPT', 'TH_INPUTS', 'TH_TRACE'):
            marker = kind + '|'
            if marker in line:
                value = json.loads(line.split(marker, 1)[1])  # malformed packets fail closed
                if kind == 'TH_TRACE':
                    value = json.loads(value)
                records.append((kind, value, line_number))
                break
    return records


def world(row):
    result = copy.deepcopy(row['world'])
    del result['terrain_trace']['ui']
    return result


def diffs(a, b, path=()):
    if type(a) is not type(b):
        return [(path, a, b)]
    if isinstance(a, dict):
        assert a.keys() == b.keys(), (path, 'key delta')
        return [d for k in a for d in diffs(a[k], b[k], path + (k,))]
    if isinstance(a, list):
        assert len(a) == len(b), (path, 'list length delta')
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diffs(x, y, path + (i,))]
    return [] if equal(a, b) else [(path, a, b)]


def validate_coverage(state):
    assert type(state['width']) is int and state['width'] == 16
    assert type(state['height']) is int and state['height'] == 16
    counts = {name: len(state[name]) for name in ('players', 'units', 'bases')}
    assert counts == {'players': 7, 'units': 8, 'bases': 7}, counts
    ids = {}
    for name in counts:
        rows = state[name]
        assert all(type(row['raw_id']) is int for row in rows)
        assert len({row['raw_id'] for row in rows}) == len(rows), (name, 'duplicate native identity')
        ids[name] = {row['id'] for row in rows}
        assert len(ids[name]) == len(rows), (name, 'duplicate logical identity')
    assert {row['raw_id'] for row in state['players']} == set(range(7))
    assert {row['owner'] for row in state['units']} == ids['players']
    assert {row['owner'] for row in state['bases']} == ids['players']
    trace = state['terrain_trace']
    for name, detail in [('players', 'player_details'), ('units', 'unit_details'), ('bases', 'base_details')]:
        assert set(trace[detail]) == ids[name], (name, 'incomplete native details')
    tiles = trace['tiles']
    expected = {f'{x},{y}' for y in range(16) for x in range(y % 2, 16, 2)}
    assert set(tiles) == expected, 'Incomplete native map coordinates'
    for key, tile in tiles.items():
        assert type(tile['x']) is int and type(tile['y']) is int
        assert key == f"{tile['x']},{tile['y']}"
    counts['tiles'] = len(tiles)
    return counts


def validate_sequence(records, report):
    inputs = [value for kind, value, _ in records if kind == 'TH_INPUTS']
    assert len(inputs) == 1
    policy = inputs[0]['policy']
    assert equal(policy, {'version': 1, 'ignore_technologies': True}), 'Different actual native input policy'
    native = [(value, line) for kind, value, line in records if kind == 'TH_NATIVE']
    assert len(native) == len(CHECKPOINTS)
    reported = report['native_snapshots']
    assert len(reported) == len(CHECKPOINTS)
    events = {event['seq']: event for kind, value, _ in records if kind == 'TH_TRACE' for event in value['events']}
    packets = []
    actor, owner, turn = native[0][0]['ui']['actor'], native[0][0]['ui']['owner'], native[0][0]['ui']['turn']
    assert all(type(v) is int for v in (actor, owner, turn))
    assert (actor, owner, turn) == (8, 0, 1), 'Different declared actor/owner/turn'
    prior_fence = -1
    for i, ((row, _), item) in enumerate(zip(native, reported)):
        ui, request = row['ui'], row['query_owner']
        assert type(row['query']) is int and row['query'] == i + 1
        assert item['checkpoint'] == CHECKPOINTS[i]
        assert equal(item['observation'], node_projection(row)), 'Report observation is not the retained raw packet'
        assert request['query'] == row['query'] and type(request['query']) is int
        for key in ('actor', 'owner', 'turn', 'session', 'dialog_generation'):
            assert type(ui[key]) is int and type(request[key]) is int
            assert request[key] == ui[key], ('stale request', i, key)
        assert (ui['actor'], ui['owner'], ui['turn']) == (actor, owner, turn)
        assert request['scope'] == SCOPES[i]
        assert ui['height_stage'] == STAGES[i]
        assert ui['modal'] is (SCOPES[i] == 'height')
        assert ui['popup_id'] == ('terraforming_height' if ui['modal'] else None)
        assert ui['sliding'] is False and ui['hiding'] is False
        assert ui['native_pending'] is False and ui['tile_locked'] is False and ui['pending'] is None
        assert type(ui['choice']) is int and ui['choice'] == (1 if i >= 4 else 0)
        assert ui['dialog_generation'] == (0, 1, 2, 3, 3, 4)[i]
        assert ui['session'] == (0 if i == 0 else 1)
        presentation = ui['height_presentation']
        assert (presentation is None) if i == 0 else (presentation['stage'] == STAGES[i])
        assert type(row['world']['turn']) is int and row['world']['turn'] == turn
        assert equal(row['world']['terrain_trace']['policy'], policy), 'Native world policy differs from actual input policy'
        validate_coverage(row['world'])
        fence = item['query_after_native_key']
        assert type(fence) is int and fence > prior_fence
        end = events[fence]
        assert end['kind'] == 'input.dispatch' and end['data']['phase'] == 'end' and end['data']['handled'] is True
        ingress_id = end['data']['ingress']
        begins = [e for e in events.values() if prior_fence < e['seq'] < fence and e['kind'] == 'input.dispatch'
                  and e['data'].get('phase') == 'begin' and e['data'].get('ingress') == ingress_id]
        assert len(begins) == 1
        begin = begins[0]
        assert begin['data']['type'] == 'keydown' and begin['data']['code'] == 'P' and begin['data']['modifiers'] == 6
        ingress = [e for e in events.values() if prior_fence < e['seq'] < begin['seq'] and e['kind'] == 'input.ingress'
                   and e['data'].get('type') == 'keydown' and e['data'].get('ingress') == ingress_id]
        assert len(ingress) == 1
        prior_fence = fence
        packets.append(row)
    return packets, native


def expected_paid_world(base, after, quote, actor_id, payer):
    expected = copy.deepcopy(base)
    actor = next(row for row in expected['units'] if row['id'] == actor_id)
    actor['movement'] = 0.0
    actor['order'] = 'NO_ORDERS'
    detail = expected['terrain_trace']['unit_details'][actor_id]
    detail['moved_this_turn'] = True
    for value in detail['quotes'].values():
        if value is not None:
            value['allowed_now'] = False
            value['reason'] = 'Unit is out of moves'
    energy = expected['terrain_trace']['player_details'][payer]
    assert type(quote['fee']) is int and 0 < quote['fee'] <= energy['energy']['credits']
    energy['energy']['credits'] -= quote['fee']
    energy['energy_revision'] += 1
    patches = {}
    for patch in quote['plan']:
        assert set(patch) == {'x', 'y', 'canonical'}
        assert set(patch['canonical']) == {'elevation', 'is_water'}
        assert type(patch['x']) is int and type(patch['y']) is int
        assert type(patch['canonical']['elevation']) is int and patch['canonical']['is_water'] is False
        key = f"{patch['x']},{patch['y']}"
        assert key not in patches and key in base['terrain_trace']['tiles']
        patches[key] = patch
    assert patches
    region = set(patches)
    for key in patches:
        for point in base['terrain_trace']['tiles'][key]['neighbors'].values():
            if point is not None:
                region.add(f"{point['x']},{point['y']}")
    for key in region:
        old, observed = base['terrain_trace']['tiles'][key], after['terrain_trace']['tiles'][key]
        target = expected['terrain_trace']['tiles'][key]
        geometry_changed = any(not equal(old['elevation'][name], observed['elevation'][name]) for name in CORNERS)
        patch = patches.get(key)
        if patch is None and not geometry_changed:
            continue
        if geometry_changed:
            for name in CORNERS:
                value = observed['elevation'][name]
                assert type(value) is int and -3500 <= value <= 3500
                target['elevation'][name] = value  # observed geometry only, never a numeric mesh-fidelity claim
        assert type(old['terrain_epoch']) is int
        target['terrain_epoch'] = old['terrain_epoch'] + 1
        target['canonical'].update(active=True,
                                   elevation=patch['canonical']['elevation'] if patch else old['elevation']['center'],
                                   is_water=patch['canonical']['is_water'] if patch else old['is_water'])
        if patch:
            elevation, water = patch['canonical']['elevation'], patch['canonical']['is_water']
            target['elevation']['center'] = elevation
            target['is_water'], target['is_land'] = water, not water
            target['native_type']['domain'] = 'sea' if water else 'land'
            target['imported'].update(active=False, source_corners=None, source_elevation=None, source_water=None)
            for name, limit in zip(BANDS, (0, -1000, -2000)):
                target['native_height_band'][name] = elevation < limit
    assert equal(after, expected), ('Unexpected exact native paid-world field/value/type', diffs(expected, after)[:8])
    return patches, region


def audit_records(records, report):
    """Callable read-only semantic audit; input mutation tests need no engine."""
    packets, native = validate_sequence(records, report)
    base, after = world(packets[0]), world(packets[-1])
    quote = packets[1]['ui']['height_presentation']['quote']
    assert all(equal(world(row), base) for row in packets[:5]), 'Quote/cancel/draft changed the native world'
    for row in packets[2:]:
        assert equal(row['ui']['height_presentation']['quote'], quote), 'Quote intent changed'
    inputs = [value for kind, value, _ in records if kind == 'TH_INPUTS']
    assert len(inputs) == 1 and equal(report['native_input'], node_projection(inputs[0]))
    assert inputs[0]['actor'] == 8 and inputs[0]['can_terraform'] is True
    assert inputs[0]['raise_rule']['turns'] == 1
    for key in ('version', 'unit_id', 'owner', 'turn', 'x', 'y', 'source_elevation', 'destination_elevation', 'fee', 'base_fee', 'paid_fee', 'credits'):
        assert type(quote[key]) is int, ('Native quote Int required', key)
    assert quote['supported'] is True and quote['action'] == 'raise' and quote['resuming'] is False and quote['paid_fee'] == 0
    assert quote['version'] == 1 and quote['mode'] == 'functional_approximation'
    assert quote['policy'] == 'application.band-slope-height.v1' and quote['fee_policy'] == 'application.band-fee.v1'
    assert (quote['unit_id'], quote['owner'], quote['turn'], quote['x'], quote['y']) == (8, 0, 1, 8, 8)
    actor = next(row for row in base['units'] if row['raw_id'] == quote['unit_id'])
    actor_id, actor_idx = actor['id'], base['units'].index(actor)
    payer_row = next(row for row in base['players'] if row['raw_id'] == quote['owner'])
    payer = payer_row['id']
    source = base['terrain_trace']['tiles'][f"{quote['x']},{quote['y']}"]
    assert type(quote['source_elevation']) is int and equal(quote['source_elevation'], source['elevation']['center'])
    assert quote['source_water'] is False and source['is_water'] is False and quote['destination_water'] is False
    assert quote['destination_elevation'] == (quote['source_elevation'] // 1000 + 1) * 1000 + 500
    assert quote['base_fee'] == max(1, quote['source_elevation'] // 1000 + 2) ** 2
    # This is the bounded unmodified Gaian case, not a general faction fee oracle.
    assert payer_row['faction'] == 'GAIANS' and quote['fee'] == quote['base_fee']
    assert quote['credits'] == base['terrain_trace']['player_details'][payer]['energy']['credits']
    for row in (packets[1], packets[3], packets[4]):
        assert row['ui']['dialog']['fee'] == quote['fee'] and row['ui']['dialog']['reserves'] == quote['credits']
    patches, region = expected_paid_world(base, after, quote, actor_id, payer)
    assert patches[f"{quote['x']},{quote['y']}"]['canonical']['elevation'] == quote['destination_elevation']
    receipts = [(value, line) for kind, value, line in records if kind == 'TH_RECEIPT' and value['name'] == 'unit_terraform']
    assert len(receipts) == 1
    receipt, receipt_line = receipts[0]
    assert equal(receipt, report['height_receipt']), 'Reported receipt is not the actual raw receipt'
    assert native[4][1] < receipt_line < native[5][1], 'Payment ACK is outside draft/complete sequence'
    assert type(receipt['event_id']) is str and receipt['event_id']
    assert receipt['success'] is True and type(receipt['caller']) is int and receipt['caller'] == quote['owner']
    assert receipt['data'] == {'unit_id': quote['unit_id'], 'action': 'raise', 'confirmed_height': True}
    assert type(receipt['data']['unit_id']) is int
    changes, categories = diffs(base, after), {}
    for path, _, _ in changes:
        category = None
        if path == ('units', actor_idx, 'movement'): category = 'actor actual MP'
        if path[:3] == ('terrain_trace', 'player_details', payer): category = 'payer fee/revision'
        if path[:3] == ('terrain_trace', 'unit_details', actor_id):
            category = 'actor moved flag' if path[3:] == ('moved_this_turn',) else 'actor exhausted movement preflight'
        if len(path) >= 4 and path[:2] == ('terrain_trace', 'tiles') and path[2] in region:
            key, tail = path[2], path[3:]
            if tail == ('terrain_epoch',): category = 'affected tile epoch'
            if len(tail) == 2 and tail[0] == 'elevation' and tail[1] in CORNERS: category = 'adjacent shared geometry (observed only)'
            if len(tail) == 2 and tail[0] == 'canonical' and tail[1] in ('active', 'elevation', 'is_water'): category = 'native canonical write/pin'
            if key in patches:
                if tail == ('elevation', 'center'): category = 'quoted gameplay elevation'
                if len(tail) == 2 and tail[0] == 'imported': category = 'edited imported source retirement'
                if tail in [('is_land',), ('is_water',), ('native_type', 'domain')]: category = 'quoted gameplay domain'
                if len(tail) == 2 and tail[0] == 'native_height_band' and tail[1] in BANDS: category = 'derived native below-coast band'
        assert category is not None, path
        categories[category] = categories.get(category, 0) + 1
    f32 = []
    for row in packets:
        for unit in row['world']['units']:
            for key in ('movement', 'health'):
                value = unit[key]
                assert type(value) is float and struct.unpack('>f', struct.pack('>f', value))[0] == value
                f32.append({'query': row['query'], 'unit': unit['raw_id'], 'field': key, 'type': 'native Float token',
                            'f32_bits': struct.pack('>f', value).hex(), 'f64_bits': struct.pack('>d', value).hex()})
        ui = row['ui']
        assert type(ui['movement']) is float and type(ui['movement_bits']) is int
        assert int.from_bytes(struct.pack('>f', ui['movement']), 'big') == ui['movement_bits']
        assert equal(ui['movement'], next(unit['movement'] for unit in row['world']['units'] if unit['raw_id'] == ui['actor']))
    assert packets[0]['ui']['movement_bits'] == 1065353216 and packets[-1]['ui']['movement_bits'] == 0
    return {'status': 'passed-readonly-audit', 'native_cases_added': 0, 'browser_cases_audited': 0, 'native_capture_field_cases_audited': 1,
            'typed_pure_checkpoints': 5, 'complete_worlds': len(packets), 'per_world': validate_coverage(base),
            'parsed_native_world_changed_fields': len(changes), 'allowed_diff_categories': categories,
            'native_float_unit_fields_checked': len(f32), 'unit_float_bits': f32,
            'actor_movement_bits': [row['ui']['movement_bits'] for row in packets],
            'quote': {**{key: quote[key] for key in ('fee', 'credits', 'source_elevation', 'destination_elevation', 'source_water', 'destination_water', 'policy', 'fee_policy', 'mode')}, 'patches': len(quote['plan'])},
            'payer_before': base['terrain_trace']['player_details'][payer]['energy'], 'payer_after': after['terrain_trace']['player_details'][payer]['energy'],
            'payer_revision_before': base['terrain_trace']['player_details'][payer]['energy_revision'], 'payer_revision_after': after['terrain_trace']['player_details'][payer]['energy_revision']}


# Historical kind-less envelope is accepted only as this explicitly identified
# immutable capture, never as a generic fallback for absent/unknown schemas.
LEGACY_PREFLIGHT_SHA256 = '791b078abf2949ddb1fb2efcd322b05dc41198e6114f31aa1ad2816375264622'
LEGACY_KEYS = {'candidate_executed', 'phase', 'prior_attempt', 'head', 'native_tree', 'default_tree',
               'original_rules_sha256', 'executed_rules_sha256', 'override_table', 'source_sha256',
               'runtime', 'seed_requested', 'browser_budget_ms', 'tracked_diff'}
V1_KEYS = {'version', 'kind', 'candidate_executed', 'phase', 'head', 'native_tree', 'default_tree',
           'runtime', 'original_rules_sha256', 'executed_rules_sha256', 'override_table', 'source_sha256',
           'input_sha256', 'production_default_sha256', 'declared_map', 'seed_requested',
           'browser_budget_ms', 'native_policy_observation'}
FATAL = re.compile(r'TH_ERROR|Unhandled exception|Uncaught|Unsupported image format|Assertion failed|Aborted\(|RuntimeError:|(?:worker|Pthread[^\n]*) sent an error!|\[Error\]', re.I)


def validate_preflight(directory, preflight, preflight_bytes, report, native_input):
    assert equal(json.loads(preflight_bytes), preflight), 'Preflight object is not its supplied bytes'
    digest = hashlib.sha256(preflight_bytes).hexdigest()
    if 'kind' not in preflight:
        assert set(preflight) == LEGACY_KEYS and preflight['phase'] == 'prelaunch-input-binding'
        assert type(preflight['prior_attempt']) is str and preflight['prior_attempt']
        assert preflight['tracked_diff'] == ''
        assert digest == LEGACY_PREFLIGHT_SHA256, 'Unrecognized kind-less preflight; not the genuine retained legacy record'
        schema = 'historical-prelaunch-input-binding:791b078a'
        driver_key = 'tools/wasm-tests/terraform-height-browser.test.mjs'
    else:
        assert preflight['kind'] == 'terraform-height-producer-preflight.v1', 'Unknown preflight schema'
        assert set(preflight) == V1_KEYS
        assert type(preflight['version']) is int and preflight['version'] == 1
        assert preflight['phase'] == 'before-native-launch'
        assert report['preflight_sha256'] == digest
        assert preflight['production_default_sha256'] == report['production_default_sha256']
        assert preflight['native_policy_observation'] == 'not available before launch; require actual TH_INPUTS and every retained native world in the auditor'
        source = preflight['input_sha256']
        assert source['main'] == report['observer_sha256'] and source['world'] == report['world_input_sha256']
        assert source['helpers'] == report['observer_helpers_sha256']
        map_bytes = (directory / 'fixture-map.MP').read_bytes()
        assert hashlib.sha256(map_bytes).hexdigest() == source['map']
        assert map_bytes[:11] == b'TERRANMAP\0\x1a'
        assert equal(preflight['declared_map'], {'width': int.from_bytes(map_bytes[15:19], 'little'),
            'height': int.from_bytes(map_bytes[19:23], 'little'), 'tiles': int.from_bytes(map_bytes[35:39], 'little'), 'bytes': len(map_bytes)})
        assert preflight['declared_map']['width'] == 16 and preflight['declared_map']['height'] == 16 and preflight['declared_map']['tiles'] == 128
        schema = preflight['kind']
        driver_key = 'executed_node_driver'
    assert preflight['candidate_executed'] is False
    assert preflight['seed_requested'] == report['seed_requested'] == '1651011033:1377505029:3019448108:3247278135'
    assert type(preflight['browser_budget_ms']) is int and preflight['browser_budget_ms'] == 180000
    assert preflight['head'] == report['host_head'] and preflight['native_tree'] == report['native_source_tree'] and preflight['default_tree'] == report['default_tree']
    assert preflight['runtime'] == {'js': report['runtime_js_sha256'], 'wasm': report['runtime_wasm_sha256']}
    assert preflight['original_rules_sha256'] == report['source_override']['original_sha256']
    assert preflight['executed_rules_sha256'] == report['source_override']['rate_one_sha256']
    files = preflight['source_sha256']
    shared = {'browser-log-cursor.mjs', 'browser-native-log-hook.mjs', 'runtime-fetch-barrier.mjs', 'terraform-browser-geometry.mjs', 'terraform-browser-pointer.mjs'}
    assert set(report['shared_helpers_sha256']) == shared
    common_sources = {'tools/wasm-tests/' + name for name in shared} | {'tools/wasm-tests/terraform-height-observation.mjs', 'tools/wasm-tests/fixtures/terraform-height-main.gls.js', 'tools/wasm-tests/terraform-browser-inputs.mjs'}
    expected_sources = common_sources | ({'tools/wasm-tests/terraform-height-browser.test.mjs'} if 'kind' not in preflight else {'executed_node_driver', 'preflight_producer', 'tools/wasm-tests/fixtures/terraform-controls-world.gls.js', 'GLSMAC_data/tests/_state_trace_observer.gls.js', 'GLSMAC_data/tests/_terrain_trace_observer.gls.js', 'GLSMAC_data/tests/_terraform_cooperation_observer.gls.js'})
    assert set(files) == expected_sources
    assert all(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) for value in files.values())
    assert files[driver_key] == report['driver_sha256']
    assert files['tools/wasm-tests/terraform-height-observation.mjs'] == report['height_observation_sha256']
    assert files['tools/wasm-tests/fixtures/terraform-height-main.gls.js'] == report['observer_sha256']
    for name, digest in report['shared_helpers_sha256'].items():
        assert files['tools/wasm-tests/' + name] == digest, ('Executed helper mismatch', name)
    for name, field in [('fixture-main.gls.js', 'observer_sha256'), ('fixture-world.gls.js', 'world_input_sha256')]:
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == report[field]
    rows = preflight['override_table']
    assert len(rows) == 20
    legacy = 'kind' not in preflight
    for i, row in enumerate(rows):
        assert type(row['source_row' if legacy else 'row']) is int and row['source_row' if legacy else 'row'] == i
        assert row['field'] == 'shared_turns' and type(row['field_index']) is int and row['field_index'] == 4
        assert row['applies_to'] == ['land', 'sea']
        assert row['new'] == ('1' if legacy else 1) and type(row['new']) is (str if legacy else int)
        assert type(row['old']) is (str if legacy else int)
    raised = rows[16]
    rule = native_input['raise_rule']
    assert type(rule['source_row']) is int and rule['source_row'] == 16 and rule['id'] == 'raise'
    assert type(rule['turns']) is int and type(rule['sea']['turns']) is int and rule['turns'] == 1 and rule['sea']['turns'] == 1
    assert raised['name' if legacy else 'land_name'] == rule['name']
    assert raised['sea_name'] == rule['sea']['name']
    assert raised['prerequisite_unchanged' if legacy else 'land_prerequisite'] == rule['prerequisite']
    if not legacy:
        assert raised['sea_prerequisite'] == rule['sea']['prerequisite']
    return schema


def utf16_length(text):
    return len(text.encode('utf-16-le', 'surrogatepass')) // 2


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_finalization(report, raw, chunks, records):
    text = raw.decode('utf8')
    assert report['status'] == 'passed' and type(report['native_raw_exit_code']) is int and report['native_raw_exit_code'] == 0
    assert equal(report['native_exit'], {'body_state': 'exited', 'status_text': 'GLSMAC exited (0).', 'raw_code': 0})
    assert report['browser_errors'] == [] and report['errors'] == []
    for name in ('log_capture_error', 'hook_capture_error', 'browser_close_error', 'final_artifact_error'):
        assert report.get(name) is None, (name, report.get(name))
    assert FATAL.search(text) is None, 'Fatal error in complete sealed raw, including final suffix'
    transport = report['log_transport']
    assert transport['sealed'] is True and transport['partial'] is False
    assert transport['settled_failure'] is None and transport['unread_tail'] is False
    digest = hashlib.sha256(raw).hexdigest()
    assert transport['raw_sha256'] == transport['joined_chunk_sha256'] == digest
    assert type(transport['retained_utf8']) is int and transport['retained_utf8'] == len(raw)
    assert type(transport['retained_utf16']) is int and transport['retained_utf16'] == utf16_length(text)
    offset = 0
    for chunk in chunks:
        assert type(chunk['start_utf16']) is int and type(chunk['end_utf16']) is int
        assert chunk['start_utf16'] == offset and chunk['end_utf16'] == offset + utf16_length(chunk['text'])
        offset = chunk['end_utf16']
    joined = ''.join(chunk['text'] for chunk in chunks)
    # JSONL may divide one UTF16 surrogate pair; combine it losslessly before
    # UTF8 comparison, rather than encoding each half independently.
    joined = joined.encode('utf-16-le', 'surrogatepass').decode('utf-16-le')
    assert joined.encode('utf8') == raw and offset == utf16_length(text)
    text16 = text.encode('utf-16-le')
    read_offset = 0
    for read in transport['reads']:
        assert type(read['start_utf16']) is int and type(read['end_utf16']) is int
        assert read['start_utf16'] == read_offset and read['end_utf16'] >= read_offset
        assert type(read['transferred_utf16']) is int and read['transferred_utf16'] == read['end_utf16'] - read_offset
        fragment = text16[read_offset * 2:read['end_utf16'] * 2].decode('utf-16-le', 'surrogatepass')
        assert type(read['transferred_utf8']) is int and read['transferred_utf8'] == len(fragment.encode('utf8', 'surrogatepass'))
        read_offset = read['end_utf16']
    assert read_offset == offset
    config = report['native_log_configuration']
    assert type(config['installations']) is int and config['installations'] == 1
    barrier, callbacks = config['barrier'], config['callbacks']
    assert barrier['kind'] == 'main' and barrier['continued'] is True and barrier['before_unmodified_runtime_response'] is True
    assert finite_number(barrier['continuation_acknowledged_node_ms'])
    assert barrier['ack']['installed_before_runtime_capture'] is True
    assert callbacks['installed_before_runtime_capture'] is True
    assert callbacks['original_source'] == barrier['ack']['original_source']
    assert hashlib.sha256(callbacks['original_source'].encode()).hexdigest() == config['original_log_source_sha256']
    for name in ('stdout_source', 'stderr_source'):
        assert callbacks[name] == barrier['ack'][name]
    first = callbacks['first_callback']
    assert first['sequence'] == 1 and type(first['sequence']) is int
    assert first['runtime_out_bound'] is True and first['runtime_err_bound'] is True and first['runtime_callMain_present'] is True
    assert callbacks['initial_utf16'] == utf16_length(callbacks['initial_text'])
    assert text.startswith(callbacks['initial_text'])
    position = utf16_length(callbacks['initial_text'])
    text16 = text.encode('utf-16-le')
    assert callbacks['calls']
    for i, call in enumerate(callbacks['calls']):
        assert type(call['sequence']) is int and call['sequence'] == i + 1
        assert call['channel'] in ('stdout', 'stderr')
        assert call['runtime_out_bound'] is True and call['runtime_err_bound'] is True and call['runtime_callMain_present'] is True
        assert type(call['before_utf16']) is int and type(call['after_utf16']) is int
        assert position <= call['before_utf16'] < call['after_utf16'] <= offset
        assert call['message_utf16'] == call['after_utf16'] - call['before_utf16'] - 1
        position = call['after_utf16']
    assert all(equal(first[key], value) for key, value in callbacks['calls'][0].items())
    assert first['message'] == text16[first['before_utf16'] * 2:(first['after_utf16'] - 1) * 2].decode('utf-16-le')
    workers = config['worker_requests']
    assert len(workers) == 8, 'This pinned v6 runtime requires all eight actual pthread continuations'
    assert len({worker['fetch_id'] for worker in workers}) == len(workers)
    assert len({worker['target_id'] for worker in workers}) == len(workers)
    assert all(event['kind'] != 'rejected' for event in config['protocol_events'])
    for role in [barrier] + workers:
        assert role['continued'] is True and finite_number(role['continuation_acknowledged_node_ms'])
        if role is not barrier:
            assert role['kind'] == 'worker' and role['continued_without_frame_lookup'] is True
            assert role['frame_id'] == barrier['frame_id'] and role['network_id'] == role['target_id']
        acknowledgements = [event for event in config['protocol_events'] if event['kind'] == 'continue-acknowledged'
                            and all(event['role'].get(key) == role[key] for key in ('kind', 'fetch_id', 'network_id', 'frame_id'))]
        assert len(acknowledgements) == 1, 'No exact actual CDP continuation ACK'
    events = [event for kind, value, _ in records if kind == 'TH_TRACE' for event in value['events']]
    last_query = report['native_snapshots'][-1]['query_after_native_key']
    qbegins = [event for event in events if event['seq'] > last_query and event['kind'] == 'input.dispatch'
               and event['data'].get('phase') == 'begin' and event['data'].get('type') == 'keydown'
               and event['data'].get('code') == 'Q' and event['data'].get('modifiers') == 6]
    assert len(qbegins) == 1
    begin = qbegins[0]
    assert any(event['seq'] > last_query and event['seq'] < begin['seq'] and event['kind'] == 'input.ingress'
               and event['data'].get('type') == 'keydown' and event['data'].get('ingress') == begin['data']['ingress'] for event in events)
    assert any(event['seq'] > begin['seq'] and event['kind'] == 'input.dispatch' and event['data'].get('phase') == 'end'
               and event['data'].get('ingress') == begin['data']['ingress'] and event['data'].get('handled') is True for event in events)
    exit_lines = [i for i, line in enumerate(text.splitlines()) if 'TH_EXIT_REQUEST' in line]
    last_native_line = max(line for kind, _, line in records if kind == 'TH_NATIVE')
    assert len(exit_lines) == 1 and exit_lines[0] > last_native_line
    return {'sealed_complete': True, 'native_exit_verified': True, 'actual_main_ack': True,
            'actual_worker_acks': len(workers), 'actual_exit_key_and_request': True, 'full_raw_fatal_scan': 'clean'}


LEGACY_OUTER_SHA256 = '6ab902e12ee6a6d0f3a4a4f52868a0bf5232a00ea408475ddbba1afd2850673d'
LEGACY_CAPTURE_BINDINGS = {
    'raw_sha256': '7877baed15b88c2700f3042fe5c31f64c6ee66517dcef04541c1ced832bad473',
    'report_sha256': '7f196c8f5de67e76355f3f49cff0ac20a4a4f3ef35fc7021c90d993f73f76f3c',
    'preflight_sha256': LEGACY_PREFLIGHT_SHA256,
    'host_head': 'bc8a3e4a113456cce2ada80e7a56d0872911d8a0',
}


def validate_external_exit(path, native_exit, capture_bindings):
    if not path.exists():
        return {'supported': False, 'reason': 'External Node process completion not supplied; never inferred from native status or TAP'}
    encoded = path.read_bytes()
    digest = hashlib.sha256(encoded).hexdigest()
    data = json.loads(encoded)
    if 'kind' not in data:
        assert digest == LEGACY_OUTER_SHA256, 'Unknown kind-less external process witness'
        assert data['tool_session_id'] == 40314 and data['tool_completion_chunk_id'] == '0ae251'
        assert equal(capture_bindings, LEGACY_CAPTURE_BINDINGS), 'Historical outer completion belongs to a different capture'
    else:
        assert data['kind'] == 'terraform-height-external-process-outcome.v1', 'Unknown external outcome schema'
        assert equal(data['capture_bindings'], capture_bindings), 'External completion belongs to a different capture'
    assert type(data['version']) is int and data['version'] == 1
    assert data['status'] == 'exited' and type(data['raw_process_exit']) is int and data['raw_process_exit'] == 0
    assert type(data['tool_session_id']) is int and type(data['tool_completion_chunk_id']) is str and data['tool_completion_chunk_id']
    assert type(data['command']) is str and 'node --test' in data['command'] and 'terraform-height-browser.test.mjs' in data['command']
    assert type(data['source']) is str and data['source']
    completion = data['tool_completion_result']
    assert type(completion['exit_code']) is int and completion['exit_code'] == 0
    assert completion['chunk_id'] == data['tool_completion_chunk_id']
    assert data['browser_server_driver_reaped'] is True and equal(data['native_exit'], native_exit)
    return {'supported': True, 'external_raw_exit_code': 0, 'tool_session_id': data['tool_session_id'],
            'completion_chunk_id': data['tool_completion_chunk_id'], 'artifact_sha256': digest}


def audit_artifacts(directory, outer_outcome=None):
    directory = Path(directory)
    raw = (directory / 'application.log').read_bytes()
    report_bytes, preflight_bytes = (directory / 'report.json').read_bytes(), (directory / 'preflight.json').read_bytes()
    report, preflight = json.loads(report_bytes), json.loads(preflight_bytes)
    records = parse_records(raw)
    result = audit_records(records, report)
    native_input = next(value for kind, value, _ in records if kind == 'TH_INPUTS')
    schema = validate_preflight(directory, preflight, preflight_bytes, report, native_input)
    chunks = [json.loads(line) for line in (directory / 'application-log-chunks.jsonl').read_text().splitlines() if line]
    finalization = validate_finalization(report, raw, chunks, records)
    bindings = {'raw_sha256': hashlib.sha256(raw).hexdigest(), 'report_sha256': hashlib.sha256(report_bytes).hexdigest(),
                'preflight_sha256': hashlib.sha256(preflight_bytes).hexdigest(), 'host_head': report['host_head']}
    external = validate_external_exit(Path(outer_outcome) if outer_outcome else directory / 'raw-outcome.json', report['native_exit'], bindings)
    assert external['supported'], 'Full browser audit requires genuine external Node completion; native-field-only audit adds no browser case credit'
    result['browser_cases_audited'] = 1
    result.update(raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw), report_sha256=hashlib.sha256(report_bytes).hexdigest(),
                  preflight_sha256=hashlib.sha256(preflight_bytes).hexdigest(), source_audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  preflight_schema=schema, finalization=finalization, external_node_exit=external)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--outer-outcome', type=Path, help='Genuine external process-completion witness; defaults to artifacts/raw-outcome.json, required for full browser audit')
    parser.add_argument('--output', type=Path, help='Optional separate derived audit output; never rewrites raw capture/report')
    args = parser.parse_args()
    directory = args.artifacts
    result = audit_artifacts(directory, args.outer_outcome)
    (args.output or directory / 'raw-typed-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'unit_float_bits'}, indent=2))


if __name__ == '__main__':
    main()
