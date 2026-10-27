// Actual native accepted-income undo lifetime; no original economy claim.
const behavior = #include('./_behavior');
const shipped = #include('../default/game/event/credit_energy_income');
const income = #include('../default/game/energy_income');
const fixture = () => {
 const f = test.natural_startup_fixture(16,16,'flat-arid'); const game = f.game;
 #include('./_natural_startup_mechanics')(f);
 game.on('configure',(e) => { game.get_tm().on('get_tile_resources',(tile) => { return {NUTRIENTS:2,MINERALS:1,ENERGY:7}; }); });
 f.initialize_single_player('GAIANS','Citizen'); f.start_world();
 test.assert(#sizeof(game.get_players()) == 7 && #sizeof(game.get_bm().get_bases()) == 7);
 f.receipt = null; f.results = [];
 game.register_event('energy_journal_income',{validate:shipped.validate,apply:(e) => { f.receipt = shipped.apply(e); return f.receipt; },rollback:shipped.rollback});
 game.on('event_result',(e) => { if (e.name == 'energy_journal_income') { f.results :+ {name:e.name + '',success:e.success == true}; } });
 f.with_write(() => { for (player of game.get_players()) { if (!game.is_turn_complete(player.id)) { game.complete_turn(player.id); } } });
 return f;
};
behavior.scenario('accepted genuine completed-turn income retires its native undo authority',() => {
 const f = fixture(); const game = f.game; const player = game.get_player(); const before = player.get_energy_state();
 const amount = income.income(game,player.id);
 test.assert(amount > 0 && before.last_income_turn < game.get_turn());
 game.event('energy_journal_income',{player_id:player.id + 0,turn_id:game.get_turn() + 0,income:amount,expected_balance:before.credits}); f.process_events();
 const after = player.get_energy_state();
 test.assert(f.results == [{name:'energy_journal_income',success:true}]);
 test.assert(after.credits == before.credits + amount && after.last_income_turn == game.get_turn());
 let usable = true; try { player.validate_energy_rollback(f.receipt.token); } catch { : (error) => { usable = false; } }
 #print('ENERGY_RECEIPT_PROOF|' + #json_text_exact({owner:player.id + 0,turn:game.get_turn() + 0,before:before,after:after,amount:amount,receipt:f.receipt.token + 0,accepted:true,receipt_usable_after_acceptance:usable}));
 // This old-API assertion proves a retained accepted record before any new
 // count seam is accessed; missing observation APIs cannot supply the red.
 test.assert(!usable,'An accepted income event no longer owns reversible treasury history');
});
