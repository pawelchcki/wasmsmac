// Primitive effect planning from installed TERRAIN identities and the supplied
// player manual (pp46–50). Exact runtime comparisons still define measured
// agreement; this module does not invent height contours, fees or river routes.
const simple = ['farm','soil_enricher','mine','solar','forest','road','mag_tube','bunker','airbase','sensor','remove_fungus','plant_fungus','level'];
const additional = ['mine','solar','forest','condenser','mirror','borehole','sensor','bunker','airbase'];
const contains = (items,value) => { for (item of items) { if (item == value) { return true; } } return false; };
const supports = (action) => { return contains(simple,action); };
const validate = (game,unit,action) => {
	if (!supports(action)) { return 'Terraforming effect is not implemented'; }
	const tile = unit.get_tile(); const data = game.get_tm().get_terrain_state(tile.x,tile.y);
	if (tile.get_base() != null) { return 'Terraforming a base tile is not supported'; }
	if (tile.is_water != unit.is_water) { return 'Worker must occupy its compatible terrain'; }
	if (tile.is_water && (action == 'farm' || action == 'mine' || action == 'solar') && data.elevation.center < (0-1000)) { return 'Sea improvements require an ocean shelf'; }
	if (action == 'remove_fungus') { if (!data.features.xenofungus) { return 'There is no fungus to remove'; } return; }
	if (action == 'plant_fungus') { if (data.features.xenofungus) { return 'Fungus already exists'; } return; }
	if (action == 'level') { if (tile.rockiness <= 1) { return 'Terrain is already level'; } return; }
	if (data.terraforming[action]) { return 'Improvement already exists'; }
	if (action == 'soil_enricher' && !data.terraforming.farm) { return 'Soil enrichment requires a farm'; }
	if (action == 'mag_tube' && !data.terraforming.road) { return 'A mag tube requires a road'; }
	if (action == 'farm' && tile.is_land && tile.rockiness >= 3) { return 'A farm requires non-rocky terrain'; }
	if ((action == 'farm' || action == 'mine' || action == 'solar') && (data.features.xenofungus || data.features.monolith)) { return 'Clear fungus and avoid monoliths before resource improvements'; }
	if (action == 'forest' && data.features.xenofungus) { return 'Clear fungus before planting a forest'; }
};
const replacements = (data,action) => {
	const result = [];
	if (contains(additional,action) || action == 'plant_fungus') {
		for (name of additional) { if (name != action && data.terraforming[name]) { result :+ name; } }
	}
	if (action == 'farm' || action == 'soil_enricher') {
		for (name of ['forest','condenser','borehole']) { if (data.terraforming[name]) { result :+ name; } }
	}
	if (action == 'forest' || action == 'plant_fungus') {
		for (name of ['farm','soil_enricher']) { if (data.terraforming[name]) { result :+ name; } }
	}
	return result;
};
return {
	supports:supports,
	validate:validate,
	replacements:(game,unit,action) => { const tile = unit.get_tile(); return replacements(game.get_tm().get_terrain_state(tile.x,tile.y),action); },
	plan:(game,unit,action) => {
		const reason = validate(game,unit,action); if (#is_defined(reason)) { throw Error(reason); }
		const tile = unit.get_tile(); const data = game.get_tm().get_terrain_state(tile.x,tile.y);
		const patch = {x:tile.x + 0,y:tile.y + 0};
		if (action == 'level') { patch.rockiness = tile.rockiness - 1; }
		else if (action == 'remove_fungus') { data.features.xenofungus = false; patch.features = data.features; }
		else {
			for (name of replacements(data,action)) { data.terraforming[name] = false; }
			if (action == 'plant_fungus') { data.features.xenofungus = true; patch.features = data.features; }
			else { data.terraforming[action] = true; }
			patch.terraforming = data.terraforming;
		}
		return [patch];
	},
};
