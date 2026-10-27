// Declared candidate inputs only. No work/payment effect is applied here.
// This is NOT the restricted land-only initial_production opening API.
return (game) => {
 let project = null;
 for (rule of game.get('starting_unit_rules')) {
  if (rule.weapon_mode == 9 && rule.prerequisite != 'Disable' && (!#is_defined(rule.movement_type) || rule.movement_type == 'land')) {
   if (project != null) { throw Error('Ambiguous source land worker project'); } project = rule;
  }
 }
 const sea = game.get('sea_former_rule');
 if (project == null || !#is_defined(sea) || sea == null) { throw Error('Installed land/Sea Former recipe is missing'); }
 if (sea.weapon_mode != 9 || sea.movement_type != 'water' || sea.application_recipe != 'foil-terraform-module-v1' || sea.source_components.chassis != 3 || sea.source_components.prototype != null) { throw Error('Unexpected installed Foil composition'); }
 const declared = {version:1,recipe:#clone(sea),resumed_choice:project.choice + '',port:{x:10,y:8},launch:{x:8,y:8},
  production_input:'existing native restore_production before FirstTurn; source sea price plus3 authored minerals; real turn event supplies actual current intake',
  stock_extra:3,restored:null};
 game.set('sea_browser_setup',declared);
 let home = null;
 game.get_bm().on('base_spawn',(e) => {
  const base = e.base;
  if (base.get_size() == 0) { base.create_pop({type:'DOCTOR'}); }
  if (base.get_owner().id == game.get_player().id) {
   if (home != null || base.get_tile().x != 10 || base.get_tile().y != 8) { throw Error('Ambiguous authored coastal producer'); }
   home = base;
   let choice = null;
   for (row of base.get_owner().get_production_choices()) { if (row.id == sea.choice) { if (choice != null) { throw Error('Duplicate Sea production choice'); } choice = row; } }
   if (choice == null || choice.type != 'unit' || choice.unit_id != sea.id || choice.population_cost != 0 || #typeof(choice.cost) != 'Int' || choice.cost <= 0) { throw Error('Native source Sea production choice unavailable'); }
   const cost = choice.cost; const stock = cost + 3;
   // Explicit authored input, before the first live observation. No treasury,
   // technology, generated map, production cost or completion guard is changed.
   base.restore_production({choice_id:sea.choice,minerals:stock,last_processed_turn:0},'');
   declared.restored = {choice_id:sea.choice,cost:cost,minerals:stock,last_processed_turn:0,population:#sizeof(base.get_pops())};
   game.set('sea_browser_setup',declared);
  }
 });
 let index = 0;
 for (player of game.get_players()) {
  const local = player.id == game.get_player().id;
  const tile = game.get_tm().get_tile(local ? 10 : index * 2,local ? 8 : 2);
  const funding = game.get('energy_rules').starting_credits + player.get_faction().economy_bonuses.starting_energy;
  game.event('initialize_energy',{player_id:player.id + 0,credits:funding});
  game.event('add_production_choice',{player:player,id:project.choice,data:{type:'unit',id:project.id,cost:project.rows * 10,cost_rows:project.rows,population_cost:project.population}});
  if (local) {
   game.event('add_production_choice',{player:player,id:sea.choice,data:{type:'unit',id:sea.id,cost:sea.rows * 10,cost_rows:sea.rows,population_cost:sea.population}});
   game.event('spawn_base',{owner:player,tile:tile,facilities:['HEADQUARTERS']});
  } else { game.event('spawn_base',{owner:player,tile:tile,facilities:['HEADQUARTERS'],production_choice:project.choice}); }
  game.event('spawn_unit',{type:'ScoutPatrol',owner:player,tile:tile,morale:2,health:1.0}); index++;
 }
 if (index != 7) { throw Error('Seven native participants are required'); }
 // bases.gls registered its ordinary turn listener first: it queues real
 // process_base_production, then growth. Queue the normal project selection
 // afterward so the complete trace's existing verified project vocabulary is
 // retained; no empty/native project is projected to a fabricated source ID.
 game.on('turn',() => {
  if (game.get_turn() == 1) {
   if (home == null || declared.restored == null) { throw Error('Authored Sea producer did not initialize'); }
   game.event('set_base_production',{base:home,choice_id:project.choice});
  }
 });
};
