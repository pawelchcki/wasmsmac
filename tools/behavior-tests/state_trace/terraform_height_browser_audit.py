"""Read-only audit of the bounded land-height browser capture, not a new run."""
import argparse
import copy
import hashlib
import json
import struct
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
    return {'status': 'passed-readonly-audit', 'native_cases_added': 0, 'browser_cases_audited': 1,
            'typed_pure_checkpoints': 5, 'complete_worlds': len(packets), 'per_world': validate_coverage(base),
            'parsed_native_world_changed_fields': len(changes), 'allowed_diff_categories': categories,
            'native_float_unit_fields_checked': len(f32), 'unit_float_bits': f32,
            'actor_movement_bits': [row['ui']['movement_bits'] for row in packets],
            'quote': {**{key: quote[key] for key in ('fee', 'credits', 'source_elevation', 'destination_elevation', 'source_water', 'destination_water', 'policy', 'fee_policy', 'mode')}, 'patches': len(quote['plan'])},
            'payer_before': base['terrain_trace']['player_details'][payer]['energy'], 'payer_after': after['terrain_trace']['player_details'][payer]['energy'],
            'payer_revision_before': base['terrain_trace']['player_details'][payer]['energy_revision'], 'payer_revision_after': after['terrain_trace']['player_details'][payer]['energy_revision']}


def audit_artifacts(directory):
    directory = Path(directory)
    raw = (directory / 'application.log').read_bytes()
    report_bytes, preflight_bytes = (directory / 'report.json').read_bytes(), (directory / 'preflight.json').read_bytes()
    report, preflight = json.loads(report_bytes), json.loads(preflight_bytes)
    result = audit_records(parse_records(raw), report)
    assert report['status'] == 'passed' and type(report['native_raw_exit_code']) is int and report['native_raw_exit_code'] == 0
    assert report['log_transport']['partial'] is False and report['log_transport']['settled_failure'] is None
    assert report['runtime_js_sha256'] == preflight['runtime']['js'] and report['runtime_wasm_sha256'] == preflight['runtime']['wasm']
    assert report['source_override']['original_sha256'] == preflight['original_rules_sha256'] and report['source_override']['rate_one_sha256'] == preflight['executed_rules_sha256']
    assert preflight['head'] == report['host_head'] and preflight['native_tree'] == report['native_source_tree'] and preflight['default_tree'] == report['default_tree']
    if preflight.get('kind') == 'terraform-height-producer-preflight.v1':
        assert preflight['version'] == 1 and preflight['candidate_executed'] is False and preflight['phase'] == 'before-native-launch'
        assert report['preflight_sha256'] == hashlib.sha256(preflight_bytes).hexdigest()
        assert preflight['seed_requested'] == report['seed_requested'] and preflight['browser_budget_ms'] == 180000
        assert preflight['production_default_sha256'] == report['production_default_sha256']
        for name, field in [('fixture-main.gls.js', 'main'), ('fixture-world.gls.js', 'world'), ('fixture-map.MP', 'map')]:
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == preflight['input_sha256'][field]
        assert preflight['input_sha256']['main'] == report['observer_sha256'] and preflight['input_sha256']['world'] == report['world_input_sha256']
        assert preflight['input_sha256']['helpers'] == report['observer_helpers_sha256']
    assert hashlib.sha256(raw).hexdigest() == report['log_transport']['raw_sha256']
    joined = ''.join(json.loads(line)['text'] for line in (directory / 'application-log-chunks.jsonl').read_text().splitlines() if line)
    assert joined.encode() == raw
    result.update(raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw), report_sha256=hashlib.sha256(report_bytes).hexdigest(),
                  preflight_sha256=hashlib.sha256(preflight_bytes).hexdigest(), source_audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--output', type=Path, help='Optional separate derived audit output; never rewrites raw capture/report')
    args = parser.parse_args()
    directory = args.artifacts
    result = audit_artifacts(directory)
    (args.output or directory / 'raw-typed-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'unit_float_bits'}, indent=2))


if __name__ == '__main__':
    main()
