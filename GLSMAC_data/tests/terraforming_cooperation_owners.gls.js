// Same live seven-owner application world. These are authored workers/rates,
// actual native transactions and pure observation, not original AI/UI parity.
const behavior = #include('./_behavior'); const work = #include('../default/game/terraforming');
const command = #include('../default/game/event/unit_terraform');
const scene = {f:null,pairs:[],third:null,last:'',inventory:''};
const order = (unit) => {
 const e = {caller:unit.owner + 0,data:{unit_id:unit.id + 0,action:'farm',replace_existing:true}}; e.game = scene.f.game;
 const error = command.validate(e); if (#is_defined(error)) { throw Error(error); }
 scene.f.with_write(() => { e.applied = command.apply(e); }); return e;
};
const setup = () => {
 const f = test.natural_startup_fixture(16,16,'flat-arid'); scene.f = f;
 #include('./_natural_startup_mechanics')(f); f.initialize_single_player('GAIANS','Citizen'); f.start_world();
 const game = f.game; game.get_settings().global.rules.set_terraforming_ignore_technologies(true);
 const rows = test.parse_smac_text(#include('./_terraform_action_source'),'rules').rows('TERRAIN'); rows[0][4] = '5';
 game.set('terraforming_rules',#include('../default/game/terraforming_rules').parse({rows:(block) => { return rows; }}));
 test.assert(#sizeof(game.get_players()) == 7 && game.get_player().id == 0);
 for (player of game.get_players()) {
  let location = null; const tm = game.get_tm();
  for (let y = 2; y < 14; y++) {
   for (let x = 2 + y % 2; x < 14; x = x + 2) {
    const tile = tm.get_tile(x,y);
    if (location == null && tile.is_land && tile.get_base() == null && #sizeof(tile.get_units()) == 0 && tile.rockiness < 3) { location = tile; }
   }
  }
  test.assert(location != null);
  const pair = {owner:player.id + 0};
  f.with_write(() => {
   const data = {def:'Formers',health:1.0,morale:2}; data.owner = player; data.tile = location;
   pair.first = game.get_um().spawn_unit(data); pair.second = game.get_um().spawn_unit(data);
   if (player.id == 1) { scene.third = game.get_um().spawn_unit(data); }
  });
  scene.pairs :+ pair;
 }
 for (pair of scene.pairs) { order(pair.first); order(pair.second); }
};
const read = (label,total,stale_owner) => {
 const f = scene.f; const before = f.audit_snapshot(); const inventory = #json_text_exact(f.audit_inspect());
 const cache = {}; const records = [];
 for (pair of scene.pairs) {
  const unit = f.game.get_um().get_unit(pair.first.id); const own = unit.get_terraforming();
  const cohort = work.cohort_state(f.game,unit,cache);
  test.assert(unit.owner == pair.owner && unit.get_terraforming_schema_version() == 2 && own.job.owner == pair.owner && own.work_units == 2);
  if (pair.owner == stale_owner) { test.assert(cohort == null); }
  else {
   test.assert(cohort != null && cohort.own_work_units == 2 && cohort.cohort_work_units == (pair.owner == 1 ? total : 4));
   let previous = 0;
   for (participant of cohort.participants) {
    test.assert(participant.unit_id > previous); previous = participant.unit_id;
    const peer = f.game.get_um().get_unit(participant.unit_id);
    test.assert(peer.owner == pair.owner && peer.get_terraforming().work_units == participant.work_units);
   }
  }
  records :+ {owner:pair.owner,unit_id:unit.id + 0,native_work:own,cohort:cohort};
 }
 test.assert(#sizeof(records) == 7 && f.audit_snapshot() == before && #json_text_exact(f.audit_inspect()) == inventory,
  'Every local/opponent cohort read preserves the complete native world RNG and queues');
 #print('COOPERATIVE_OWNERS|' + label + '|' + #json_text_exact(records));
};
const first_read = () => { read('first',4,(0-1)); };
const next_contribution = () => { order(scene.third); };
const second_read = () => { read('fresh-after-real-peer-work',6,(0-1)); };
const change_terrain = () => {
 const tm = scene.f.game.get_tm();
 for (pair of scene.pairs) {
  if (pair.owner == 2) {
   const tile = pair.first.get_tile(); const state = tm.get_terrain_state(tile.x,tile.y);
   scene.f.with_write(() => { tm.apply_terrain([{x:tile.x + 0,y:tile.y + 0,moisture:state.moisture == 1 ? 2 : 1}],[]); });
  }
 }
};
const final_read = () => {
 read('fresh-after-terrain-change',6,2);
 scene.last = scene.f.audit_snapshot(); scene.inventory = #json_text_exact(scene.f.audit_inspect());
};
test.after_stages('seven-owner-no-implicit-progress',() => {
 test.assert(scene.f.audit_snapshot() == scene.last && #json_text_exact(scene.f.audit_inspect()) == scene.inventory);
});
behavior.scenario_staged('actual local and all six opponent cohorts are observed without local selection gates',[
 {label:'setup-and-native-work',run:setup},{label:'first-full-owner-read',run:first_read},
 {label:'real-peer-contribution',run:next_contribution},{label:'fresh-work-read',run:second_read},
 {label:'native-terrain-change',run:change_terrain},{label:'fresh-terrain-read',run:final_read},
]);
