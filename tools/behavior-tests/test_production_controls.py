"""Frozen original production phases, isolated inputs and complete roster contexts."""
from pathlib import Path
import json
import unittest
import compare
from protocol import ProtocolError
from ui.production_controls_contract import validate_input,validate_output
PHASES=('first_city_before_panels','ready_before_panels','after_operations','after_panel','after_social')

class ProductionControlTests(unittest.TestCase):
    def datasets(self):
        root=Path(__file__).parent/'ui'
        return root,[(name,compare.read_json(root/f'cases/initial-production-controls-{name}.json'),compare.read_json(root/f'observations/initial-production-controls-{name}.json')) for name in ('core','source')]

    def test_two_fresh_complete_original_runs_per_case(self):
        _,datasets=self.datasets()
        for _,suite,record in datasets:
            compare.validate_observations(record,suite);self.assertEqual(record['repeat'],2);self.assertEqual(len(suite['cases']),4)
            self.assertEqual(record['reference']['kind'],'original-executable')
            self.assertEqual(record['reference']['executable_sha256'],'01901cbf7196b0c5d0df9540a029520f5df8fd9a6b343deef8b5663872805fcf')
            for c,r in zip(suite['cases'],record['observations']):validate_input(c['input']);validate_output(r['output'])

    def test_only_declared_source_files_differ_from_stock(self):
        _,datasets=self.datasets()
        expected={'gaian-physics':{'gaians.txt'},'gaian-formers-cost-4':{'alphax.txt'},'gaian-formers-cost-8':{'alphax.txt'},'gaian-mineral-rule-12':{'alphax.txt'},'gaian-industry-minus-1':{'gaians.txt'}}
        for _,_,record in datasets:
            profiles=record['reference']['source_profiles_sha256'];stock=profiles['stock']
            for name,changed in expected.items():self.assertEqual({k for k in stock if stock[k]!=profiles[name][k]},changed)

    def test_first_observed_stock_precedes_panels_and_remains_unchanged(self):
        _,datasets=self.datasets()
        for _,_,record in datasets:
            for r in record['observations']:
                d=r['output'];first=d[PHASES[0]]
                for phase in PHASES:
                    n=d[phase];self.assertEqual((n['turn'],n['map_kind'],n['map_area_sqrt']),(1,0,40))
                    for field in ('raw_mineral_field','current_project_id','queue_size','industry_rating','mineral_rule_factor','city','owned_ids'):self.assertEqual(n[field],first[field])
                self.assertEqual(d['operations']['pair'][0],first['raw_mineral_field'])
                self.assertEqual(d['operations']['project'],d['panel']['project']);self.assertEqual(d['operations']['turns'],d['panel']['turns'])
                self.assertEqual(d['social_after']['industry'],first['industry_rating'])
                self.assertEqual(d['panel']['allocation'],dict(economy=50,psych=0,labs=50));self.assertEqual(d['panel']['labs_income'],1)

    def test_strict_projection_keeps_every_complete_context_separately(self):
        root,datasets=self.datasets()
        for name,_,record in datasets:
            expected={r['id']:r['output'] for r in record['observations']}
            for run in ('run-a','run-b'):
                full=compare.read_json(root/f'reference-archives/initial-production-controls-v2/{name}-{run}.json')
                for r in full['observations']:
                    d=json.loads(json.dumps(r['output']))
                    for phase in PHASES:
                        units=d[phase].pop('units');self.assertGreaterEqual(len(units),1)
                        self.assertTrue(all(set(u)=={'prototype_id','order_code','movement_spent','damage'} for u in units))
                    self.assertEqual(d,expected[r['id']])

    def test_unrecorded_profiles_are_outside_scope(self):
        base=dict(faction='GAIANS',difficulty='CITIZEN',text_profile='stock',world_width=40,world_height=80,map_route='load-map',research='directed',target_id=5)
        for change in (dict(difficulty='TRANSCEND'),dict(text_profile='gaian-formers-cost-3'),dict(world_width=80),dict(faction='HIVE',text_profile='gaian-physics')):
            with self.assertRaises(ProtocolError):validate_input(dict(base,**change))
