const behavior = #include('./_behavior');
behavior.scenario('a real native long river is rejected before accepting work',() => {
 const f = #include('./_aquifer_capacity_fixture')(); const game = f.game; const tm = game.get_tm();
 const before = f.audit_snapshot(); const inventory = f.audit_inspect();
 const route = #include('../default/game/terraforming_effects').plan(game,f.former,'aquifer');
 test.assert(#sizeof(route) == 4190,'Actual production source must traverse the declared native corridor');
 let native_rejected = false; let native_reason = '';
 try { tm.validate_terrain(route,[f.former.id + 0]); }
 catch { : (error) => { native_rejected = true; native_reason = error.reason + ''; } }
 test.assert(native_rejected && f.audit_snapshot() == before && f.audit_inspect() == inventory);
 const event = {caller:game.get_player().id + 0,data:{unit_id:f.former.id + 0,action:'aquifer'}}; event.game = game;
 const reason = #include('../default/game/event/unit_terraform').validate(event);
 #print('AQUIFER_CAP_BASELINE|' + #json_text_exact({native_route_patches:#sizeof(route),native_rejected:native_rejected,native_reason:native_reason,
  source_accepted: !#is_defined(reason),source_reason:#is_defined(reason) ? reason : null,inventory:inventory}));
 test.assert(f.audit_snapshot() == before && f.audit_inspect() == inventory && f.former.movement == 1.0 && !f.former.get_terraforming().active,
  'Capacity discovery and preflight preserve the complete native graph, RNG, work and movement');
 test.assert(#is_defined(reason),'An unpublishable river must be rejected before its work is accepted');
});
