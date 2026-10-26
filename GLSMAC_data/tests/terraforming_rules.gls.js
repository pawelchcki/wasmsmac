// Installed action declarations, independent of original work-trace evidence.
const behavior = #include('./_behavior');
const consumer = #include('../default/game/terraforming_rules');
const source = '#TERRAIN\nFarm,None,Kelp Farm,None,4,Cultivate $STR0,f,F\n' +
	'Soil,None,Soil,Disable,8,Construct $STR0,f,F\nMine,None,Platform,None,8,Construct $STR0,M,M\n' +
	'Solar,None,Harness,None,4,Construct $STR0,S,S\nForest,None,...,Disable,4,Plant $STR0,F,Shift+F\n' +
	'Road,None,Road,Disable,1,Build $STR0,R,R\n#END\n';
const fixture = () => {
	const document = test.parse_smac_text(source, 'rules'); const rows = document.rows('TERRAIN');
	const result = {}; result.rows = rows; result.document = {rows: (block) => { test.assert(block == 'TERRAIN'); return rows; }};
	return result;
};
const change = (f, row, column, value) => { const entry = f.rows[row]; entry[column] = value; };

behavior.scenario('installed action rows provide independent names rates prerequisites and order labels', () => {
	const rules = consumer.parse(test.parse_smac_text(source, 'rules'));
	test.assert(rules.road.turns == 1 && rules.farm.turns == 4 && rules.mine.turns == 8 && rules.forest.turns == 4);
	test.assert(rules.farm.name == 'Farm' && rules.farm.prerequisite == 'None' && rules.farm.order == 'Cultivate Farm');
	test.assert(rules.road.order == 'Build Road' && rules.forest.order == 'Plant Forest');
});

behavior.scenario('edited source rates and names replace default action metadata without changing action IDs', () => {
	const f = fixture(); change(f, 0, 4, '2'); change(f, 2, 4, '3'); change(f, 4, 4, '2'); change(f, 5, 4, '3');
	change(f, 0, 0, 'Synthetic field'); change(f, 0, 1, 'SyntheticTech'); change(f, 0, 5, 'Prepare $STR0');
	const rules = consumer.parse(f.document);
	test.assert(rules.road.turns == 3 && rules.farm.turns == 2 && rules.mine.turns == 3 && rules.forest.turns == 2);
	test.assert(rules.farm.name == 'Synthetic field' && rules.farm.prerequisite == 'SyntheticTech' && rules.farm.order == 'Prepare Synthetic field');
});

let index = 0;
for (invalid of [[0, 4, '0'], [0, 4, '65'], [0, 4, '4.0'], [0, 4, '04'], [0, 0, ''], [0, 1, ''], [0, 5, '$STR1']]) {
	behavior.scenario('unsupported installed terraforming declaration fails before configuration ' + #to_string(index), () => {
		const f = fixture(); change(f, invalid[0], invalid[1], invalid[2]); let caught = false;
		try { consumer.parse(f.document); } catch { : (e) => { caught = true; } }
		test.assert(caught);
	}); index++;
}

const complete_source = '#TERRAIN\n' +
	'Farm,None,Kelp Farm,None,4,Cultivate $STR0,f,F\n' +
	'Soil Enricher,EcoEng2,Soil Enricher,Disable,8,Construct $STR0,f,F\n' +
	'Mine,None,Mining Platform,None,8,Construct $STR0,M,M\n' +
	'Solar Collector,None,Tidal Harness,None,4,Construct $STR0,S,S\n' +
	'Forest,None,...,Disable,4,Plant $STR0,F,Shift+F\n' +
	'Road,None,Road,Disable,1,Build $STR0,R,R\n' +
	'Mag Tube,Magnets,Mag Tube,Disable,3,Build $STR0,R,R\n' +
	'Bunker,MilAlg,Bunker,Disable,5,Construct $STR0,K,K\n' +
	'Airbase,DocAir,Airbase,Disable,10,Construct $STR0,.,.\n' +
	'Sensor Array,None,Sensor Array,Disable,4,Construct $STR0,O,O\n' +
	'Fungus,None,Sea Fungus,None,6,Remove $STR0,F,F\n' +
	'Fungus,EcoEng,Sea Fungus,EcoEng,6,Plant $STR0,F,Ctrl+F\n' +
	'Condenser,EcoEng,Condenser,Disable,12,Construct $STR0,N,N\n' +
	'Echelon Mirror,EcoEng,Echelon Mirror,Disable,12,Construct $STR0,E,Shift+E\n' +
	'Thermal Borehole,EcoEng,Thermal Borehole,Disable,24,Construct $STR0,B,Shift+B\n' +
	'Aquifer,EcoEng,Aquifer,Disable,18,Drill to $STR0,Q,Q\n' +
	'Raise Land,EnvEcon,Raise Sea Floor,EnvEcon,12,Terraform UP,],]]\n' +
	'Lower Land,EnvEcon,Lower Sea Floor,EnvEcon,12,Terraform DOWN,[,[[\n' +
	'Level Terrain,None,Level Terrain,Disable,8,Terraform LEVEL,_,_\n' +
	'Monolith,Disable,Monolith,Disable,8,Place Monolith,?,?\n#END\n';

behavior.scenario('complete installed terrain vocabulary has nineteen land and seven sea declarations', () => {
	const rules = consumer.parse(test.parse_smac_text(complete_source, 'complete terrain'));
	let land = 0; let sea = 0;
	for (entry of consumer.entries) {
		const ordinary = consumer.for_tile(rules, {is_water: false}, entry.id);
		const ocean = consumer.for_tile(rules, {is_water: true}, entry.id);
		test.assert(ordinary.id == entry.id && ocean.id == entry.id && ordinary.source_row == entry.row);
		if (ordinary.enabled) { land++; } if (ocean.enabled) { sea++; }
	}
	test.assert(land == 19 && sea == 7);
	test.assert(rules.raise.order == 'Terraform UP' && rules.lower.sea.name == 'Lower Sea Floor');
	test.assert(rules.farm.sea.order == 'Cultivate Kelp Farm' && rules.mine.sea.order == 'Construct Mining Platform');
	test.assert(!rules.monolith.enabled && !rules.monolith.sea.enabled);
	test.assert(consumer.for_tile(rules, {is_water: false}, 'unknown') == null);
});

behavior.scenario('sea variant consumes its independent names and prerequisites without changing work identity', () => {
	const doc = test.parse_smac_text(complete_source, 'edited terrain'); const rows = doc.rows('TERRAIN');
	const row = rows[0]; row[2] = 'Authored sea field'; row[3] = 'AuthoredSeaTech'; row[4] = '11';
	const rules = consumer.parse({rows: (block) => { return rows; }});
	test.assert(rules.farm.name == 'Farm' && rules.farm.prerequisite == 'None');
	test.assert(rules.farm.sea.name == 'Authored sea field' && rules.farm.sea.prerequisite == 'AuthoredSeaTech');
	test.assert(rules.farm.turns == 11 && rules.farm.sea.turns == 11 && rules.farm.sea.id == 'farm');
});
