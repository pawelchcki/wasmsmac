"""Declared transport corruption tests; these do not execute or emulate a game."""
from copy import deepcopy
import json
import unittest

from protocol import ProtocolError
from state_trace import terrain_capture as capture
from state_trace import terrain_observation as terrain
from test_terrain_observation import packet


def declared_transport():
    state = packet(); owners = [row['id'] for row in state['players']]
    # Declared transport uses the probe's complete 16x16 staggered world.
    first = deepcopy(state['terrain_trace']['tiles']['0,0']); tiles = {}
    for y in range(16):
        for x in range(y % 2, 16, 2):
            tile = deepcopy(first); tile.update(x=x, y=y, width=16, height=16)
            tiles[f'{x},{y}'] = tile
    state.update(width=16, height=16); state['terrain_trace']['tiles'] = tiles
    trace = state['terrain_trace']
    for key, tile in trace['tiles'].items():
        other = dict(x=1, y=1) if key == '0,0' else dict(x=0, y=0)
        tile['neighbors'] = {direction: deepcopy(other) for direction in terrain.DIRECTIONS}
    identities = list(capture.ACTORS) + ['other:' + str(i) for i in range(6)]
    for raw_id, identity in enumerate(identities):
        owner = owners[0] if raw_id < 3 else owners[raw_id - 2]
        state['units'].append(dict(id=identity, raw_id=raw_id, owner=owner, x=0, y=0,
                                   prototype='declared', movement=1.0, health=1.0, order=''))
        trace['unit_details'][identity] = dict(definition_id=capture.ACTORS.get(identity, 'Declared'),
            morale_set='declared', movement_kind='land', nominal_mp_per_turn=1.0,
            can_terraform=identity == 'former', moved_this_turn=False,
            work=dict(action='', work_units=0, required_work=0, last_turn=0, previous_work_units=0,
                      previous_movement=0.0, previous_moved=False, active=False, tile_x=0, tile_y=0),
            combat={}, quotes={})
    for raw_id, owner in enumerate(owners):
        identity = 'base:' + str(raw_id)
        state['bases'].append(dict(id=identity, raw_id=raw_id, owner=owner, x=0, y=0, population=1))
        trace['base_details'][identity] = dict(name='Declared', production={}, intake={}, consumption={},
            nutrients_present=False, nutrients=None, citizens=[dict(id=raw_id, type='Declared', worked_tile=None)],
            worked_tiles=[], facilities={})

    def quote_units(snapshot):
        for unit in snapshot['units']:
            source = dict(x=unit['x'], y=unit['y']); destination = dict(x=1-unit['x'], y=1-unit['y'])
            detail = snapshot['terrain_trace']['unit_details'][unit['id']]
            detail['quotes'] = {direction: dict(source=deepcopy(source), destination=deepcopy(destination),
                movement_kind='land', nominal_mp_per_turn=1.0, allowed_now=unit['movement'] > 0.0,
                reason=None if unit['movement'] > 0.0 else 'Out of moves',
                quoted_step_cost_mp=1.0, zero_cost_quote=False, quoted_tiles_per_turn=1.0,
                policy_quote=dict(road_rate=0, base_cost=1.0, after_cost=0.0, total_cost=1.0)) for direction in terrain.DIRECTIONS}
    quote_units(state)
    stages = {'initial': deepcopy(state)}; movements = []
    for actor in capture.ACTORS:
        before = deepcopy(state); stages[actor + '-before'] = before
        unit = next(row for row in state['units'] if row['id'] == actor)
        old_detail = before['terrain_trace']['unit_details'][actor]
        unit.update(x=1, y=1, movement=0.0)
        state['terrain_trace']['unit_details'][actor]['moved_this_turn'] = True
        quote_units(state)
        stages[actor + '-during'] = deepcopy(state); stages[actor + '-after'] = deepcopy(state)
        movements.append(dict(unit_id=actor, source=dict(x=0, y=0), destination=dict(x=1, y=1),
            movement_before=1.0, movement_after=0.0, actual_debit_mp=1.0, movement_successful=True,
            actual_step_count=1, before_checkpoint=actor+'-before', after_checkpoint=actor+'-after',
            quote=deepcopy(old_detail['quotes']['E'])))
    return stages, movements


def wire(stages, movements, *, omit=(), duplicate=None, native_missing=False):
    lines = []
    for stage, state in stages.items():
        if stage in omit: continue
        bookkeeping = dict(unit_ids=[row['raw_id'] for row in state['units']],
                           base_ids=[row['raw_id'] for row in state['bases']], dangling_unit_updates=0)
        if native_missing: bookkeeping['unit_ids'].pop()
        lines += ['TERRAIN_NATIVE|' + stage + '|' + json.dumps(bookkeeping),
                  'TERRAIN_STEP_JSON|' + stage + '|' + json.dumps(state)]
    if duplicate: lines.append('TERRAIN_STEP_JSON|' + duplicate + '|' + json.dumps(stages[duplicate]))
    lines += ['TERRAIN_JSON|' + json.dumps(stages['initial'])]
    lines += ['TERRAIN_MOVEMENT|' + json.dumps(row) for row in movements]
    lines += ['TERRAIN_OBSERVATION_COMPLETE', 'BEHAVIOR_SUMMARY 1 50', 'All tests passed.']
    return '\n'.join(lines)


class TerrainCaptureTests(unittest.TestCase):
    def test_declared_packet_audit_has_zero_original_matches_and_no_full_actions_claim(self):
        report = capture.audit(wire(*declared_transport()))
        self.assertEqual(report['checkpoint_count'], 10)
        self.assertEqual(report['players_per_checkpoint'], 7)
        self.assertEqual(report['actual_movement_commands'], 3)
        self.assertFalse(report['original_comparison_executed'])
        self.assertEqual(report['original_matches'], 0)
        self.assertFalse(report['full_action_inventory_complete'])
        self.assertIn('runtime lacks native canonical_height capability', report['unsupported'])

    def test_missing_duplicate_native_registration_and_empty_results_fail_closed(self):
        stages, moves = declared_transport()
        logs = [wire(stages, moves, omit=('native-during',)), wire(stages, moves, duplicate='former-after'),
                wire(stages, moves, native_missing=True), wire(stages, []),
                wire(stages, moves).replace('TERRAIN_OBSERVATION_COMPLETE', '')]
        for log in logs:
            with self.subTest(log=log[-150:]), self.assertRaises(ProtocolError): capture.audit(log)

    def test_later_opponent_change_and_false_debit_are_not_hidden_by_summaries(self):
        for change in ('opponent', 'debit', 'position', 'result', 'ability', 'quote'):
            stages, moves = declared_transport()
            if change == 'opponent': stages['conventional-after']['terrain_trace']['player_details']['player:7']['energy']['credits'] = 99
            elif change == 'debit': moves[-1]['actual_debit_mp'] = 0.5
            elif change == 'position': moves[-1]['destination'] = dict(x=0, y=0)
            elif change == 'result': moves[-1]['actual_step_count'] = False
            elif change == 'ability': stages['native-before']['terrain_trace']['unit_details']['native']['can_terraform'] = True
            else: moves[-1]['quote']['policy_quote']['total_cost'] = 2.0
            with self.subTest(change=change), self.assertRaises(ProtocolError): capture.audit(wire(stages, moves))


if __name__ == '__main__': unittest.main()
