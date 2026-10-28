"""Adversarial coverage planning checks; no engine, assets or reference execution."""
from copy import deepcopy
from contextlib import redirect_stderr
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import lanes
from protocol import ProtocolError, canonical, decode_json, fingerprint
import stable_selection as selection


BASE = '1' * 40
HEAD = '2' * 40


class StableSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = selection.inventory()
        cls.profile = decode_json(selection.PROFILE.read_text())

    def request(self, changed):
        return dict(version=1, base_sha=BASE, head_sha=HEAD,
                    inventory_sha256=self.current['sha256'], changes=changed)

    def plan(self, changed, **kwargs):
        return selection.select(kwargs.get('profile', self.profile), kwargs.get('current', self.current),
                                kwargs.get('request', self.request(changed)), kwargs.get('head', HEAD), changed)

    def assert_complete(self, plan):
        self.assertTrue(plan['full_stable_fallback'])
        self.assertFalse(plan['candidate_executed'])
        self.assertFalse(plan['gate_satisfied'])
        self.assertTrue(plan['execution_required_before_merge'])
        for kind, expected in [('regression', 180), ('ui', 60), ('economy', 2), ('helper', 22)]:
            hot, stable = set(plan['always_hot'][kind]), set(plan['required_stable'][kind])
            self.assertFalse(hot & stable)
            self.assertEqual(len(hot | stable), expected)
            self.assertEqual(hot | stable, set(self.current['ids'][kind]))
        self.assertEqual(len(plan['always_hot']['regression']), 45)
        self.assertEqual(len(plan['required_stable']['regression']), 135)
        self.assertEqual(len(plan['always_hot']['ui']), 11)
        self.assertEqual(len(plan['required_stable']['ui']), 49)
        self.assertEqual(set(plan['required_stable_captures']['terraform_actions']), set(self.current['action_ids']))
        self.assertEqual(len(plan['required_stable_captures']['terraform_actions']), 36)
        self.assertEqual(len(plan['always_hot_captures']['startup_native']), 8)
        self.assertIn('world-single-player-setup', plan['always_hot']['regression'])
        self.assertEqual(set(plan['always_hot_captures']['terraform_actions']), {
            'land:road', 'land:raise', 'sea:farm', 'sea:lower', 'command:road_to', 'command:auto_former'})
        self.assertIn('pending-ui', plan['excluded_from_passing_totals'])

    def test_actual_catalog_union_and_pending_separation(self):
        plan = self.plan([dict(status='M', path='GLSMAC_data/default/game/terraforming.gls.js')])
        self.assert_complete(plan)
        old_hot = set(self.current['manifest']['kinds']['regression']['hot'])
        self.assertEqual(len(old_hot), 76)
        self.assertEqual(len(self.profile['moved_regression']), 31)
        self.assertEqual(set(plan['required_stable']['regression']) -
                         set(self.current['manifest']['kinds']['regression']['stable']),
                         set(self.profile['moved_regression']))
        self.assertNotIn('natural-first-city', plan['always_hot']['ui'])
        self.assertEqual(len(self.current['manifest']['kinds']['pending-ui']['hot']), 4)

    def test_every_area_example_keeps_full_required_coverage(self):
        examples = {
            'terraform-terrain-movement-orders': ['GLSMAC_data/default/game/terraforming_height.gls.js',
                'GLSMAC_data/default/game/movement_rules.gls.js', 'GLSMAC_data/default/game/event/unit_terraform.gls.js'],
            'production-growth-startup-factions': ['GLSMAC_data/default/game/computer_production.gls.js',
                'GLSMAC_data/default/game/faction_identity.gls.js', 'GLSMAC_data/default/ui/parts/mainmenu/steps/select_faction.gls.js'],
            'research-technology': ['GLSMAC_data/default/game/research.gls.js',
                'GLSMAC_data/default/game/technology_rules.gls.js', 'GLSMAC_data/default/game/event/set_research_target.gls.js'],
            'ui-unit-menu-modal-base-operations': ['GLSMAC_data/default/ui/parts/game/menu/unit_orders.gls.js',
                'GLSMAC_data/default/game/base_operations_dialog.gls.js'],
            'shared-engine-runtime-build-ci-harness-evidence': ['src/gc/Space.cpp', 'CMakeLists.txt',
                '.github/workflows/hot.yml', 'tools/behavior-tests/catalog.json',
                'tools/behavior-tests/ui/observations/new-public-record.json', 'GLSMAC_data/tests/new_case.gls.js'],
        }
        self.assertEqual(set(examples), set(self.profile['areas']))
        for area, paths in examples.items():
            for name in paths:
                with self.subTest(path=name):
                    plan = self.plan([dict(status='M', path=name)])
                    self.assertIn(area, plan['areas'])
                    self.assert_complete(plan)

    def test_unknown_new_file_empty_diff_and_ambiguous_dependency_never_skip(self):
        for changed in [[], [dict(status='A', path='new_feature/new_probe.py')],
                        [dict(status='M', path='GLSMAC_data/default/game/unknown_dependency.gls.js')]]:
            self.assert_complete(self.plan(changed))

    def test_renames_and_copies_account_for_both_sides_and_deletions(self):
        for status in ['R', 'C']:
            changed = [dict(status=status, old_path='src/gc/Space.cpp', path='misc/renamed.cpp')]
            plan = self.plan(changed)
            self.assert_complete(plan)
            self.assertEqual({r['path'] for r in plan['reasons']}, {'src/gc/Space.cpp', 'misc/renamed.cpp'})
            self.assertIn('shared-engine-runtime-build-ci-harness-evidence', plan['areas'])
        self.assert_complete(self.plan([dict(status='D', path='GLSMAC_data/default/game/research.gls.js')]))

    def test_order_is_deterministic_and_profile_and_inventory_are_bound(self):
        changed = [dict(status='M', path='src/gc/Space.cpp'), dict(status='A', path='some/new-file.txt')]
        self.assertEqual(self.plan(changed), self.plan(list(reversed(changed))))
        plan = self.plan(changed)
        self.assertEqual(plan['profile_sha256'], fingerprint(self.profile))
        self.assertEqual(plan['inventory_sha256'], self.current['sha256'])
        self.assertEqual((plan['base_sha'], plan['head_sha']), (BASE, HEAD))

    def test_omitted_changed_paths_and_stale_head_or_inventory_are_errors(self):
        changed = [dict(status='M', path='src/gc/Space.cpp')]
        bad = []
        for key, value in [('head_sha', BASE), ('inventory_sha256', '0'*64), ('version', True),
                           ('base_sha', '--help'), ('head_sha', HEAD.upper()), ('changes', [])]:
            request = self.request(changed); request[key] = value; bad.append(request)
        bad[-2]['head_sha'] = 'A' * 40
        for request in bad:
            with self.subTest(request=request), self.assertRaises(ProtocolError):
                self.plan(changed, request=request)
        with self.assertRaises(ProtocolError):
            self.plan(changed, head=BASE)

    def test_path_attacks_malformed_and_duplicate_changes_fail_closed(self):
        for name in ['', '/tmp/a', '../src/x', 'src/../x', 'src//x', './src/x', 'src/./x',
                     'src/x\nM\tinnocent', 'src/a\0b', 'src/a\tb', 'C:/src/x', 'src\\x',
                     'src/a b', 'src/\u202ex', 'src/*', 'src/[x]', '-x/../src']:
            with self.subTest(path=name), self.assertRaises(ProtocolError):
                self.plan([dict(status='M', path=name)])
        for changed in [None, {}, [{'status': 'U', 'path': 'src/a'}],
                        [{'status': 'M', 'path': 'src/a', 'old_path': 'src/b'}],
                        [{'status': 'R', 'path': 'src/a'}],
                        [{'status': 'R', 'path': 'src/a', 'old_path': '../bad'}],
                        [{'status': 'M', 'path': 'src/a'}]*2]:
            with self.subTest(changed=changed), self.assertRaises(ProtocolError):
                self.plan(changed)

    def test_stale_profile_new_unmapped_catalog_case_and_invalid_membership_reject(self):
        for key, value in [('version', 2), ('dependencies_reviewed', True), ('inventory_sha256', '0'*64),
                           ('hot_regression', self.profile['hot_regression'][:-1]),
                           ('moved_regression', self.profile['moved_regression'] + ['new-unmapped-case']),
                           ('all_actions', self.profile['all_actions'][:-1]),
                           ('hot_actions', ['sea:unknown']), ('areas', {}),
                           ('areas', {'bad-area': ['../src/*']})]:
            profile = deepcopy(self.profile); profile[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ProtocolError):
                self.plan([], profile=profile)
        current = deepcopy(self.current)
        current['ids']['regression'].append('new-unmapped-case')
        with self.assertRaises(ProtocolError):
            self.plan([], current=current)
        current = deepcopy(self.current); current['sha256'] = 'f' * 64
        with self.assertRaises(ProtocolError):
            self.plan([], current=current)

    def test_new_cases_in_real_input_inventory_change_fingerprint(self):
        original = lanes.read
        def altered(name):
            data = original(name)
            if str(name).endswith('ui/cases/initial-production-controls-core.json'):
                data = deepcopy(data)
                new_case = deepcopy(data['cases'][0]); new_case['id'] = 'new-case-not-in-profile'
                data['cases'].append(new_case)
            return data
        with patch.object(lanes, 'read', side_effect=altered):
            updated = selection.inventory()
        self.assertNotEqual(updated['sha256'], self.current['sha256'])
        with self.assertRaises(ProtocolError):
            self.plan([], current=updated)

    def test_git_nul_parser_preserves_both_rename_sides_and_rejects_truncation(self):
        self.assertEqual(selection.diff_records(b'R100\0src/a\0src/b\0M\0src/c\0'),
                         selection.changes([dict(status='R', old_path='src/a', path='src/b'), dict(status='M', path='src/c')]))
        self.assertEqual(selection.diff_records(b''), [])
        for raw in [b'M\0src/a', b'R100\0src/a\0', b'M\0../a\0', b'M\0src/\xff\0', b'U\0src/a\0']:
            with self.subTest(raw=raw), self.assertRaises(ProtocolError):
                selection.diff_records(raw)

    def test_duplicate_json_fields_never_silently_override_bindings(self):
        with self.assertRaises(ProtocolError):
            decode_json('{"version":1,"version":2}')

    def test_cli_checks_real_git_diff_and_removes_stale_report_on_error(self):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder); root = temp / 'checkout'; root.mkdir()
            directory = root / 'tools/behavior-tests'; directory.mkdir(parents=True)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()
            git('init', '-q'); git('config', 'user.name', 'Selector Test'); git('config', 'user.email', 'selector@example.invalid')
            (root/'file.txt').write_text('before'); git('add', '.'); git('commit', '-qm', 'base')
            base = git('rev-parse', 'HEAD')
            (root/'file.txt').write_text('after'); git('add', '.'); git('commit', '-qm', 'head')
            head = git('rev-parse', 'HEAD')
            request = self.request([dict(status='M', path='file.txt')]); request.update(base_sha=base, head_sha=head)
            source = temp / 'request.json'; source.write_text(canonical(request))
            profile = temp/'profile.json'; profile.write_text(canonical(self.profile))
            report = temp/'report.json'
            argv = ['--request', str(source), '--profile', str(profile), '--report', str(report)]
            with patch.object(selection, 'DIRECTORY', directory), patch.object(selection, 'inventory', return_value=self.current):
                self.assertEqual(selection.main(argv), 0)
                self.assert_complete(decode_json(report.read_text()))
                request['changes'] = []; source.write_text(canonical(request))
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(selection.main(argv), 2)
                self.assertFalse(report.exists())
                request['changes'] = [dict(status='M', path='file.txt')]; source.write_text(canonical(request))
                (root/'file.txt').write_text('uncommitted')
                report.write_text('stale plan')
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(selection.main(argv), 2)
                self.assertFalse(report.exists())


    def test_cli_parse_errors_clear_only_valid_report_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / 'report.json'
            for argv in (['--report', str(report)],
                         ['--request', str(Path(folder) / 'request.json'), '--report', str(report), '--unknown']):
                report.write_text('stale plan')
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    selection.main(argv)
                self.assertEqual(error.exception.code, 2)
                self.assertFalse(report.exists())

    def test_report_symlink_cannot_be_replaced_by_source_tree_output(self):
        with tempfile.TemporaryDirectory() as folder:
            temp = Path(folder); root = temp / 'checkout'; directory = root / 'tools/behavior-tests'
            directory.mkdir(parents=True)
            target = temp / 'outside-report.json'; target.write_text('keep existing target')
            link = root / 'report.json'; link.symlink_to(target)
            argv = ['--request', str(temp/'request.json'), '--report', str(link)]
            with patch.object(selection, 'DIRECTORY', directory), redirect_stderr(io.StringIO()):
                self.assertEqual(selection.main(argv), 2)
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(), 'keep existing target')

    def test_regression_case_and_helper_source_changes_invalidate_profile(self):
        original = Path.read_bytes
        for filename in ('unit_orders_controls.gls.js', '_colony_menu_controls_cases.gls.js'):
            # Included case factories matter even when the catalog/canonical
            # entrypoint itself did not change.
            existing = list((selection.DIRECTORY.parents[1]/'GLSMAC_data/tests').rglob(filename))
            if not existing and filename.startswith('_'):
                existing = list((selection.DIRECTORY.parents[1]/'GLSMAC_data/tests').glob('_colony_menu_controls*.gls.js'))
            self.assertTrue(existing)
            selected = existing[0]
            def altered(name):
                value = original(name)
                return value + b'\n// changed case input\n' if name == selected else value
            with patch.object(Path, 'read_bytes', altered):
                updated = selection.inventory()
            self.assertNotEqual(updated['sha256'], self.current['sha256'])
            with self.assertRaises(ProtocolError): self.plan([], current=updated)

    def test_real_git_unchanged_copy_keeps_both_source_and_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()
            git('init', '-q'); git('config', 'user.name', 'Selector Test'); git('config', 'user.email', 'selector@example.invalid')
            (root/'src').mkdir(); (root/'misc').mkdir()
            content = 'unique source content for copy classification\n' * 4
            (root/'src/mapped.cpp').write_text(content)
            git('add', '.'); git('commit', '-qm', 'base'); base = git('rev-parse', 'HEAD')
            (root/'misc/copied.cpp').write_text(content)
            git('add', '.'); git('commit', '-qm', 'copy'); head = git('rev-parse', 'HEAD')
            changed = selection.actual_changes(root, base, head)
            self.assertEqual(changed, [dict(status='C', old_path='src/mapped.cpp', path='misc/copied.cpp')])
            plan = self.plan(changed)
            self.assertEqual({row['path'] for row in plan['reasons']}, {'src/mapped.cpp', 'misc/copied.cpp'})
            self.assert_complete(plan)


if __name__ == '__main__':
    unittest.main()
