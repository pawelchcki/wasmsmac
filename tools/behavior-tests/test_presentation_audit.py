"""Accounting audits use synthetic candidate evidence, never original answers."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from protocol import ProtocolError
from state_trace.presentation import CLOCK, DOMAINS
from state_trace.presentation_audit import audit_capture, main
from state_trace.presentation_projector import project_capture
from test_presentation_projector import fixture


def evidence():
    inputs, capture, _ = fixture()
    capture.update(schema='glsmac.presentation.raw.v1', clock=deepcopy(CLOCK), coverage={})
    capture['capture'] = dict(terminal_drain_observed=True, ended_at='atomic-native-seal',
                              final_event_sequence=len(capture['batches'][0]['events']),
                              final_quiet_observed=True)
    return capture, project_capture(capture, inputs)


def resequence(projection):
    sequence = 0
    for state in [point['state']['presentation'] for point in projection['checkpoints']] + [projection['diagnostics']['tail_presentation']]:
        for event in state['events']:
            sequence += 1
            event['seq'] = sequence


class AuditTests(unittest.TestCase):
    def test_reconciles_all_events_births_retirements_and_unknown_transients(self):
        capture, projection = evidence()
        report = audit_capture(capture, projection)
        self.assertTrue(report['valid'])
        self.assertTrue(report['transport_complete'])
        self.assertFalse(report['semantic_understood'])
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['checkpoints'][0]['native_birth_count'], 10)
        self.assertEqual(report['checkpoints'][0]['native_retired_count'], 1)
        self.assertEqual(report['checkpoints'][0]['native_live_nodes'], 9)
        self.assertEqual(report['checkpoints'][0]['raw_prefix_event_count'], len(capture['batches'][0]['events']))
        self.assertIsNotNone(report['unknown_objects']['n9']['retirement_sequence'])
        self.assertTrue(any(event['target'] == 'n9' for event in report['unknown_events']))
        self.assertTrue(any(event['kind'] == 'node.opaque' for event in report['unmapped_fields']))
        self.assertEqual(set(report['coverage']), set(DOMAINS))
        self.assertTrue(all(not channel['complete'] and channel['missing_capability_reasons']
                            for channel in report['coverage'].values()))
        self.assertFalse(report['exhaustive_coverage_complete'])
        self.assertFalse(report['rendered_output_observed'])
        self.assertEqual(report, audit_capture(deepcopy(capture), deepcopy(projection)))

    def test_quiet_and_true_declarations_cannot_promote_coverage(self):
        capture, projection = evidence()
        capture['coverage'] = {name: True for name in DOMAINS}
        projection['checkpoints'][0]['coverage'] = {'presentation.' + name: True for name in DOMAINS}
        projection['diagnostics']['coverage_complete'] = True
        report = audit_capture(capture, projection)
        self.assertFalse(report['exhaustive_coverage_complete'])
        self.assertEqual(report['status'], 'incomplete')
        self.assertTrue(all(report['declared_checkpoint_coverage']['ready'].values()))
        self.assertTrue(all(not value['complete'] for value in report['coverage'].values()))

    def test_no_channel_events_does_not_prove_complete_channel(self):
        inputs = dict(fixture={'requested_coverage': list(DOMAINS)},
                      actions=[dict(id='launch', kind='launch')], checkpoints=[dict(id='done', after_action='launch')])
        rows = [dict(seq=1, target='trace', kind='semantic.protocol', data={'version': 2}),
                dict(seq=2, target='trace', kind='trace.checkpoint', data={'checkpoint': 1, 'action': 1})]
        capture = dict(schema='glsmac.presentation.raw.v1', batches=[dict(enabled=True, dropped=0, events=rows)],
                       input_checkpoints=[dict(id='done', after_action='launch', checkpoint=1)])
        report = audit_capture(capture, project_capture(capture, inputs))
        self.assertTrue(report['semantic_understood'])
        self.assertFalse(report['transport_complete'])
        self.assertTrue(all(not channel['complete'] for channel in report['coverage'].values()))

    def test_unsealed_prefix_is_valid_but_transport_incomplete(self):
        capture, projection = evidence()
        capture['capture'].update(terminal_drain_observed=False, ended_at='last-periodic-drain-only')
        report = audit_capture(capture, projection)
        self.assertFalse(report['transport_complete'])
        self.assertTrue(report['transport_gaps'])

    def test_dropped_gapped_disabled_and_incorrect_final_sequence_rejected(self):
        for corruption in ('loss', 'gap', 'disabled', 'final-sequence', 'seal'):
            capture, projection = evidence()
            if corruption == 'loss': capture['batches'][0]['dropped'] = 1
            elif corruption == 'gap': capture['batches'][0]['events'][3]['seq'] += 1
            elif corruption == 'disabled': capture['batches'][0]['enabled'] = False
            elif corruption == 'final-sequence': capture['capture']['final_event_sequence'] -= 1
            elif corruption == 'seal': capture['capture']['ended_at'] = 'periodic'
            with self.subTest(corruption=corruption), self.assertRaises(ProtocolError):
                audit_capture(capture, projection)

    def test_observation_omission_duplication_payload_change_and_disposition_domain_rejected(self):
        for corruption in ('omit', 'duplicate', 'payload', 'domain', 'identity', 'order'):
            capture, projection = evidence()
            events = projection['checkpoints'][0]['state']['presentation']['events']
            index = next(i for i, event in enumerate(events) if event['kind'] == 'observed')
            if corruption == 'omit': del events[index]
            elif corruption == 'duplicate': events.insert(index, deepcopy(events[index]))
            elif corruption == 'payload': events[index]['fields']['data']['version'] = 99
            elif corruption == 'domain': events[index]['domain'] = 'unknown'
            elif corruption == 'identity': events[index]['object_id'] = 'candidate-birth:wrong'
            elif corruption == 'order': events[index]['fields']['raw_sequence'] += 1
            resequence(projection)
            with self.subTest(corruption=corruption), self.assertRaises(ProtocolError):
                audit_capture(capture, projection)

    def test_birth_retirement_count_and_retired_unknown_omission_rejected(self):
        for corruption in ('birth', 'retirement', 'missing-birth', 'extra-birth', 'count', 'unknown', 'observed-count', 'final-watermark'):
            capture, projection = evidence()
            diag = projection['diagnostics']
            if corruption == 'birth': diag['dispositions']['n9']['birth_sequence'] += 1
            elif corruption == 'retirement': diag['dispositions']['n9']['retirement_sequence'] = None
            elif corruption == 'missing-birth': del diag['dispositions']['n9']
            elif corruption == 'extra-birth': diag['dispositions']['invented'] = deepcopy(diag['dispositions']['n9'])
            elif corruption == 'count': diag['counts']['unknown'] -= 1
            elif corruption == 'unknown': del diag['unknown_inventory']['n9']
            elif corruption == 'observed-count': diag['observed_events'] -= 1
            elif corruption == 'final-watermark': diag['source_final_sequence'] -= 1
            with self.subTest(corruption=corruption), self.assertRaises(ProtocolError):
                audit_capture(capture, projection)

    def test_semantic_snapshot_and_hidden_logical_birth_rejected(self):
        capture, projection = evidence()
        projection['checkpoints'][0]['state']['presentation']['objects']['candidate-birth:n1']['text'] = 'invented'
        with self.assertRaisesRegex(ProtocolError, 'snapshot differs'):
            audit_capture(capture, projection)
        capture, projection = evidence()
        identity = 'candidate-birth:n2'
        state = projection['checkpoints'][0]['state']['presentation']
        state['events'] = [event for event in state['events'] if not (event['object_id'] == identity and event['kind'] != 'observed')]
        del state['objects'][identity]
        del projection['diagnostics']['tail_presentation']['objects'][identity]
        resequence(projection)
        with self.assertRaisesRegex(ProtocolError, 'logical birth'):
            audit_capture(capture, projection)

    def test_logical_animation_media_and_retired_unknown_audio_are_distinct(self):
        inputs, capture, _ = fixture()
        rows = capture['batches'][0]['events']
        rows[-2:-2] = [
            dict(kind='media.create', target='animation', data=dict(type='animation', source='synthetic',
                 duration_ms=100, frame_count=2, x=0, y=0, z=0, evidence='native-registration', history='from-construction')),
            dict(kind='media.start', target='animation', data=dict(evidence='scene-instance')),
            dict(kind='media.frame', target='animation', data=dict(evidence='scene-instance', frame_index=0, scene_instance_id=1, present=True)),
            dict(kind='media.create', target='audio', data=dict(type='audio', source='synthetic.wav')),
            dict(kind='media.destroy', target='audio', data=dict(evidence='request'))]
        for sequence, event in enumerate(rows, 1): event['seq'] = sequence
        capture['schema'] = 'glsmac.presentation.raw.v1'
        report = audit_capture(capture, project_capture(capture, inputs))
        self.assertEqual(report['checkpoints'][0]['native_live_media'], 1)
        self.assertEqual(report['checkpoints'][0]['semantic_live_media'], 1)
        self.assertNotIn('animation', report['unknown_objects'])
        self.assertIsNotNone(report['unknown_objects']['audio']['retirement_sequence'])
        self.assertEqual(report['raw_event_kinds']['media.frame'], 1)
        self.assertFalse(report['coverage']['animation.frames']['complete'])
        self.assertFalse(report['rendered_output_observed'])

    def test_multi_checkpoint_prefix_counts_and_tail_preserve_all_events(self):
        inputs, capture, add = fixture()
        first_boundary = len(capture['batches'][0]['events'])
        add('node.create', 'transient', parent='n1', tag='$unexpected')
        add('node.destroy', 'transient')
        add('trace.checkpoint', action=1, checkpoint=2)
        second_boundary = len(capture['batches'][0]['events'])
        capture['input_checkpoints'].append(dict(id='later', after_action='launch', checkpoint=2))
        inputs['checkpoints'].append(dict(id='later', after_action='launch'))
        add('node.create', 'tail', parent='n1', tag='$unexpected')
        add('node.destroy', 'tail')
        capture['schema'] = 'glsmac.presentation.raw.v1'
        projection = project_capture(capture, inputs)
        report = audit_capture(capture, projection)
        self.assertEqual([point['raw_prefix_event_count'] for point in report['checkpoints']], [first_boundary, second_boundary])
        self.assertEqual(report['checkpoints'][1]['raw_interval_event_count'], 3)
        self.assertEqual(report['tail']['raw_interval_event_count'], 2)
        self.assertEqual(report['tail']['native_birth_count'], 12)
        self.assertEqual(report['tail']['native_retired_count'], 3)
        self.assertIn('tail', report['unknown_objects'])
        del projection['diagnostics']['tail_presentation']['events'][-1]
        with self.assertRaises(ProtocolError): audit_capture(capture, projection)

    def test_changed_or_omitted_checkpoint_watermark_and_tail_rejected(self):
        for corruption in ('omit', 'watermark', 'tail'):
            capture, projection = evidence()
            if corruption == 'omit': capture['input_checkpoints'] = []
            elif corruption == 'watermark': capture['input_checkpoints'][0]['watermark'] = 1
            elif corruption == 'tail': projection['diagnostics']['raw_tail'] = [{'invented': True}]
            with self.subTest(corruption=corruption), self.assertRaises(ProtocolError):
                audit_capture(capture, projection)

    def test_immutable_prefix_top_level_watermark_must_match_last_fence(self):
        capture, projection = evidence()
        capture['capture'].update(terminal_drain_observed=False, ended_at='acknowledged-input-barrier')
        capture['checkpoint'] = dict(id='ready', after_action='launch', watermark=len(capture['batches'][0]['events']))
        report = audit_capture(capture, projection)
        self.assertFalse(report['transport_complete'])
        self.assertEqual(report['checkpoint_prefix'], capture['checkpoint'])
        capture['checkpoint']['watermark'] -= 1
        with self.assertRaisesRegex(ProtocolError, 'prefix identity/watermark'):
            audit_capture(capture, projection)

    def test_raw_observation_json_types_are_not_coerced(self):
        capture, projection = evidence()
        observed = next(event for event in projection['checkpoints'][0]['state']['presentation']['events']
                        if event['kind'] == 'observed' and event['fields']['kind'] == 'trace.protocol')
        observed['fields']['data']['version'] = True
        with self.assertRaisesRegex(ProtocolError, 'raw payload differs'):
            audit_capture(capture, projection)

    def test_tail_only_logical_unavailable_fields_prevent_semantic_understanding(self):
        inputs = dict(fixture={'requested_coverage': list(DOMAINS)},
                      actions=[dict(id='launch', kind='launch')],
                      checkpoints=[dict(id='done', after_action='launch')])
        rows = [dict(seq=1, target='trace', kind='semantic.protocol', data={'version': 2}),
                dict(seq=2, target='trace', kind='trace.checkpoint', data={'checkpoint': 1, 'action': 1})]
        capture = dict(schema='glsmac.presentation.raw.v1', batches=[dict(enabled=True, dropped=0, events=rows)],
                       input_checkpoints=[dict(id='done', after_action='launch', checkpoint=1)])
        self.assertTrue(audit_capture(capture, project_capture(capture, inputs))['semantic_understood'])
        rows.extend([
            dict(seq=3, target='tail-widget', kind='node.create', data={'parent': None, 'tag': '$button'}),
            dict(seq=4, target='tail-widget', kind='semantic.role',
                 data={'role': 'button', 'source': '', 'constructor': True})])
        report = audit_capture(capture, project_capture(capture, inputs))
        self.assertFalse(report['unknown_events'])
        self.assertFalse(report['unknown_objects'])
        self.assertFalse(report['semantic_understood'])
        self.assertTrue(report['unavailable_fields'])
        self.assertTrue(all(field['checkpoint'] == 'terminal-tail' and field['identity'] == 'candidate-birth:tail-widget'
                            for field in report['unavailable_fields']))

    def test_cli_diagnostic_complete_gate_and_stale_result_replacement(self):
        capture, projection = evidence()
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            raw, semantic, output = [directory / name for name in ('raw.json', 'semantic.json', 'audit.json')]
            raw.write_text(json.dumps(capture)); semantic.write_text(json.dumps(projection))
            args = ['--capture', str(raw), '--projection', str(semantic), '--output', str(output)]
            self.assertEqual(main(args), 0)
            self.assertEqual(main(args + ['--require-complete']), 1)
            self.assertEqual(json.loads(output.read_text())['status'], 'incomplete')
            raw.write_text('{}')
            self.assertEqual(main(args), 2)
            report = json.loads(output.read_text())
            self.assertFalse(report['valid'])
            self.assertEqual(report['status'], 'invalid')
            self.assertNotIn('checkpoints', report)


if __name__ == '__main__':
    unittest.main()
