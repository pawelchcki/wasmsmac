// Functional application checks from installed identities, complete named flags
// and documented player rules. Not original recorded-comparison pass counts.
const behavior = #include('./_behavior'); const fixture = #include('./_terraform_primitives_fixture');
const command = #include('../default/game/event/unit_terraform');
for (water of [false,true]) {
	for (action of ['farm','soil_enricher','mine','solar','forest','road','mag_tube','bunker','airbase','sensor','remove_fungus','plant_fungus','level','condenser','mirror','borehole','aquifer']) {
		if (!water || action == 'farm' || action == 'mine' || action == 'solar' || action == 'remove_fungus' || action == 'plant_fungus') {
			behavior.scenario('technology-free actual work completes ' + action + ' on ' + (water ? 'sea' : 'land') + ' and native receipt restores it', () => {
				const f = fixture(action,water); const tm = f.game.get_tm();
				const before = f.snapshot(); const terrain = f.terrain_snapshot(); const energy = f.owner.get_energy_state();
				const expected = tm.get_terrain_state(2,2);
				if (action == 'level') { expected.rockiness = 2; }
				else if (action == 'remove_fungus') { expected.features.xenofungus = false; expected.features_raw = expected.features_raw - 4; }
				else if (action == 'plant_fungus') { expected.features.xenofungus = true; expected.features_raw = expected.features_raw + 4; }
				else if (action == 'aquifer') { expected.features.river = true; }
				else { expected.terraforming[action] = true; }
				if (action == 'condenser') { expected.moisture = #min(3,expected.moisture + 1); }
				const result = f.command(action); const actual = tm.get_terrain_state(2,2);
				if (action != 'level' && action != 'remove_fungus' && action != 'plant_fungus' && action != 'aquifer') {
					test.assert(actual.terraforming[action]);
					if (#is_defined(actual.terraforming_owners)) { test.assert(actual.terraforming_owners[action] == f.owner.id); }
				}
				else { test.assert(actual.rockiness == expected.rockiness && actual.features == expected.features); }
				test.assert(actual.elevation == expected.elevation && actual.is_water == expected.is_water && actual.moisture == expected.moisture && actual.bonus == expected.bonus);
				test.assert(f.former.get_order() == 'NO_ORDERS' && f.former.get_terraforming().work_units == 0 && f.former.movement == 0.0 && f.former.moved_this_turn);
				test.assert(f.owner.get_energy_state() == energy, 'Tech waiver never creates a resource fee or alters research');
				f.with_write(() => { command.rollback(result); });
				test.assert(f.snapshot() == before && f.terrain_snapshot() == terrain);
			});
		}
	}
}
behavior.scenario('source-disabled sea rows and editor-only Monolith remain unavailable under the technology waiver', () => {
	for (action of ['soil_enricher','forest','road','mag_tube','bunker','airbase','sensor','level','monolith']) {
		const f = fixture(action,true); const before = f.snapshot(); const terrain = f.terrain_snapshot(); let rejected = false;
		try { f.command(action); } catch { : (error) => { rejected = true; } }
		test.assert(rejected && f.snapshot() == before && f.terrain_snapshot() == terrain);
	}
});
behavior.scenario('sea resource improvement rejects deep water before any work or movement debit', () => {
	const f = fixture('farm',true); f.with_write(() => { f.game.get_tm().apply_terrain([{x:2,y:2,canonical:{elevation:(0-1500),is_water:true}}],[]); });
	const before = f.snapshot(); const terrain = f.terrain_snapshot(); let rejected = false;
	try { f.command('farm'); } catch { : (error) => { rejected = true; } }
	test.assert(rejected && f.snapshot() == before && f.terrain_snapshot() == terrain && f.former.movement == 4.0);
});
