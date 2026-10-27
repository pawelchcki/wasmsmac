// Candidate-only normal movement. No original oracle, duration/pose override or C++ seam.
import {declaredTerrain} from './terraform-browser-inputs.mjs';
import {stackOrderWorld} from './unit-stack-order-browser-fixture.mjs';
export const movementWorld=stackOrderWorld;
export function movementTerrain(){
  const bytes=declaredTerrain();const offset=15+0xaa4;
  // Actual SMACMap parser: altitude3/contour60 selects constant +10 rather
  // than coordinate-dependent contour64 jitter. No native terrain mutation.
  for(let i=0;i<128;i++)bytes[offset+i*44+1]=60;
  return bytes;
}
export const movementBudgets=Object.freeze({node_ms:180000,observation_ms:120000,outer_seconds:190,
  term_seconds:3,kill_wait_seconds:5,cleanup_seconds:8,postkill_seconds:2,census_calls:32,sample_delay_ms:10});
export const movementMain=String.raw`#main((glsmac) => {
 #include('game/game')(glsmac); #include('ui/ui')(glsmac);
 const preview = #include('ui/parts/game/bottom_bar/object_preview');
 const terrain_observer = #include('../tests/_terrain_trace_observer');
 glsmac.on('configure_game',(configured) => {
  const game = configured.game;
  game.on('start_ui',() => {
   if (#typeof(glsmac.get_unit_body_census) != 'Callable') { throw Error('Census API unavailable'); }
   const proxy = {}; proxy.um = game.get_um(); proxy.bm = game.get_bm();
   for (field of ['get_um','get_bm','get_tm','get_players','get_player','get_turn','get_settings','get','is_started','is_turn_complete','get_research_state','get_research_science']) { proxy[field] = game[field]; }
   proxy.technologies = game.technologies;
   // No read_ui callback: full Native worlds do not absorb transient frontend UI.
   const observer = terrain_observer(proxy,null);
   let a = null; let b = null; let city_id = null; const owners = [];
   const owner = game.get_player().id + 0;
   for (player of game.get_players()) { owners :+ player.id + 0; }
   for (unit of game.get_tm().get_tile(8,8).get_units()) {
    if (unit.owner == owner && unit.def == 'ScoutPatrol') {
     if (unit.morale == 2) { if (a != null) { throw Error('Ambiguous A'); } a = unit.id + 0; }
     if (unit.morale == 1) { if (b != null) { throw Error('Ambiguous B'); } b = unit.id + 0; }
    }
   }
   for (base of game.get_bm().get_bases()) { if (base.get_owner().id == owner) { if (city_id != null) { throw Error('Ambiguous readiness city'); } city_id = base.id + 0; } }
   if (a == null || b == null || city_id == null || #sizeof(owners) != 7) { throw Error('Missing movement world'); }
   let seq = 0; let phase = 'ready'; let submit_seq = null; let receipt_seq = null;
   let selection_fence = null; let tile_seq = null; let preview_seq = null;
   let reads = 0; let sampled = 0; let pending_ticks = 0; let ticks = 0;
   let failed = false;
   const emit = (kind,row) => { seq++; row.seq = seq; #print('UM_' + kind + '|' + #json_text_exact(row)); return seq; };
   const abort = (reason) => { #print('UM_UNSUPPORTED|' + reason); glsmac.exit(); };
   game.on('error',() => { failed = true; });
   game.on('tile_select',(e) => { tile_seq = emit('EVENT',{kind:'tile-select',x:e.tile.x + 0,y:e.tile.y + 0}); });
   game.get_map().on('unit_preview',(e) => {
    // Only immutable native identity metadata; no mutable unit/tile/MP reads.
    const id = e.unit == null ? null : e.unit.id + 0;
    const serial = emit('EVENT',{kind:'native-unit-preview',unit_id:id});
    if (id == a) { preview_seq = serial; }
   });
   game.on('event_result',(e) => {
    if (#typeof(e.name) != 'String' || #typeof(e.event_id) != 'String' || #typeof(e.caller) != 'Int' || #typeof(e.success) != 'Bool') { throw Error('Native receipt types'); }
    const serial = emit('RECEIPT',{name:e.name + '',event_id:e.event_id + '',caller:e.caller + 0,success:e.success});
    if (submit_seq != null) {
     if (e.name != 'move_unit' || !e.success || e.caller != owner || receipt_seq != null) { throw Error('Unexpected post-submit receipt'); }
     receipt_seq = serial;
    }
   });
   const pending = () => {
    const values = [];
    for (id of owners) { values :+ {owner_id:id,pending:game.has_pending_actions(id)}; }
    return values;
   };
   const clear = (values) => { let result = true; for (row of values) { if (row.pending) { result = false; } } return result; };
   const capture = (label) => {
    const checkpoint = {label:label}; checkpoint.world = observer.read(); const scalars = [];
    for (entry of checkpoint.world.units) {
     const unit = game.get_um().get_unit(entry.raw_id);
     scalars :+ {unit_id:unit.id + 0,owner_id:unit.owner + 0,id_type:#typeof(unit.id),owner_type:#typeof(unit.owner),health_type:#typeof(unit.health),health_bits:#float_bits(unit.health),movement_type:#typeof(unit.movement),movement_bits:#float_bits(unit.movement)};
    }
    checkpoint.native_unit_scalars = scalars; checkpoint.state = {}; checkpoint.pending = pending();
    emit('CHECKPOINT',checkpoint); // All Native FloatPtr data serialized immediately.
   };
   const validate_input = () => {
    const actor = game.get_um().get_unit(a); const target = game.get_tm().get_tile(10,8);
    if (actor.owner != owner || actor.get_tile().x != 8 || actor.get_tile().y != 8 || actor.movement != 1.0 || actor.health != 1.0 || actor.moved_this_turn || actor.get_order() != 'NO_ORDERS' || actor.get_terraforming().active || actor.get_automation().command != '' || actor.get_terraforming_recovery().active) { throw Error('Controlled A is not idle'); }
    if (target.get_base() != null || #sizeof(target.get_units()) != 0 || actor.get_tile().get_base() != null) { throw Error('Controlled route occupied'); }
    const points = [{x:8,y:8},{x:10,y:8}];
    for (point of points) {
     const center = game.get_tm().get_terrain_state(point.x,point.y); const neighborhood = [];
     neighborhood :+ point;
     for (direction in center.neighbors) { const neighbor = center.neighbors[direction]; if (neighbor != null) { neighborhood :+ neighbor; } }
     for (position of neighborhood) {
      const state = game.get_tm().get_terrain_state(position.x,position.y);
      if (state.is_water || game.get_tm().get_tile(position.x,position.y).is_locked() || state.rockiness != 1 || state.features.river || state.features.xenofungus || state.terraforming.road || state.terraforming.mag_tube) { throw Error('Controlled route is not clear dry flat land'); }
      for (height in state.elevation) { if (state.elevation[height] != 10) { throw Error('Controlled Native height is not ten'); } }
     }
    }
    const quote = observer.quote(actor,target);
    if (!quote.allowed_now || quote.reason != null || quote.policy_quote_version != 1 || quote.policy_quote.road_rate != 0 || quote.policy_quote.base_cost != 1.0 || quote.policy_quote.after_cost != 0.0 || quote.policy_quote.total_cost != 1.0 || quote.quoted_step_cost_mp != 1.0) { throw Error('Controlled normal movement cost unavailable'); }
   };
   const census = (stage) => {
    if (reads >= 32) { throw Error('Census call cap exceeded'); } reads++;
    const payload = glsmac.get_unit_body_census(game);
    if (#typeof(payload) != 'String') { throw Error('Census is not a Native String'); }
    return emit('CENSUS',{ordinal:reads,stage:stage,payload:payload});
   };
   glsmac.ui.root.timer(100,() => {
    ticks++; if (failed || ticks >= 600) { abort('readiness-limit'); return false; }
    if (phase == 'ready') {
     let ready = false;
     try { glsmac.focus_owned_base(city_id); ready = true; } catch { : (e) => { if (ticks == 1) { #print('UM_READINESS_WAIT|' + e.reason); } } }
     if (ready) { phase = 'warm'; selection_fence = seq; game.select_tile(game.get_tm().get_tile(8,8)); }
    } else {
     if (phase == 'warm' && tile_seq != null && preview_seq != null && selection_fence < tile_seq && tile_seq < preview_seq && preview.rendered_unit_id == a && preview.selected_unit_id == null) { phase = 'deferred'; }
     else {
      if (phase == 'deferred') {
       const initial_pending = pending(); if (!clear(initial_pending)) { throw Error('Initial pending actions'); }
       if (preview.preview == null || preview.preview.data.unit.id != a) { throw Error('Missing mounted native A'); }
       emit('READY',{a:a,b:b,owner:owner,selection_fence:selection_fence,tile_seq:tile_seq,preview_seq:preview_seq,mounted_unit_id:preview.preview.data.unit.id + 0});
       validate_input(); capture('before'); census('baseline');
       submit_seq = emit('SUBMIT',{name:'move_unit',a:a,owner:owner,x:10,y:8});
       const data = {}; data.unit = game.get_um().get_unit(a); data.tile = game.get_tm().get_tile(10,8);
       game.event('move_unit',data); phase = 'sampling';
       glsmac.ui.root.timer(10,() => {
        if (failed) { abort('native-game-error'); return false; }
        if (phase == 'sampling') {
         if (sampled < 29) { sampled++; census('sample'); }
         // Runtime trigger is fixed sample budget + accepted apply, NOT decoded
         // coordinates. Offline strict JSON validation must prove two actual
         // endpoint callbacks precede the first pending query; absent => incomplete.
         if (sampled == 29 && receipt_seq != null) { phase = 'pending'; }
         else { pending_ticks++; if (pending_ticks >= 600) { abort('receipt-limit'); return false; } }
        } else {
         if (phase == 'pending') {
          pending_ticks++; if (pending_ticks >= 600) { abort('pending-limit'); return false; }
          const values = pending(); const serial = emit('PENDING',{stage:'poll',values:values});
          if (clear(values)) { phase = 'settled'; }
         } else {
          if (phase == 'settled') {
           const values = pending(); if (!clear(values)) { throw Error('New pending action at capture'); }
           emit('PENDING',{stage:'capture',values:values}); census('settled'); capture('after'); phase = 'confirm';
          } else {
           if (phase != 'confirm') { throw Error('Unexpected movement observer phase'); }
           const values = pending(); if (!clear(values)) { throw Error('New pending action at confirmation'); }
           emit('PENDING',{stage:'confirm',values:values}); census('confirm');
           emit('RESULT',{schema:'application.unit-body-movement-observation.v1',a:a,b:b,owner:owner,reads:reads,sampled:sampled,submit_seq:submit_seq,receipt_seq:receipt_seq,physical_inputs:0,move_commands:1});
           phase = 'done'; glsmac.exit(); return false;
          }
         }
        }
        return true;
       }); return false;
      }
     }
    }
    return true;
   });
  });
 }); glsmac.run();
});`;
