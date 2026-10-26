const behavior = #include('./_behavior');
const fixture = #include('./_base_operations_fixture');
const unchanged = (f, before) => {
 const after = f.snapshot();
 test.assert(#sizeof(after.players) == 7 && #sizeof(after.identities) == 7 && #sizeof(after.bases) == #sizeof(before.bases));
 test.assert(after == before, 'Report controls preserve all seven owners, identities, units, bases, stores, jobs and research');
};
behavior.scenario('delayed management acknowledgement rejection retries without inventing city mutations', () => {
 const f = fixture(); const before = f.snapshot(); f.defer = true; f.open_menu(); f.double_click();
 test.assert(!f.popup.is_shown() && #sizeof(f.requests) == 1 && f.list.management_pending != null);
 const initial_token = f.requests[0].data.request_token;
 f.events.select_base(f.base); f.flush();
 test.assert(#sizeof(f.requests) == 1 && f.list.management_pending.request_token == initial_token, 'Ordinary repeated base selection retains its existing command');
 const pending = f.requests[0]; const wrong = {name: pending.name, caller: f.game.get_player().id, success: true};
 wrong.data = {} + pending.data; wrong.data.request_token = wrong.data.request_token + 1;
 f.events.emit('event_result', wrong); test.assert(f.list.management_pending != null && !f.popup.is_shown());
 f.delivered = 1; f.deliver(0, false);
 test.assert(f.popup.popup.id == 'base_operations' && f.row().el.border == 'rgb(0,235,0),1'); unchanged(f, before);
 f.double_click(); test.assert(#sizeof(f.requests) == 2 && !f.popup.is_shown());
 f.delivered = 2; f.deliver(1, true); test.assert(f.popup.popup.id == 'base_screen'); unchanged(f, before);
 f.escape(); f.escape();
 // The map menu remains usable while the first native receipt is delayed.
 // Reopening creates a different report session even for the same city/turn.
 f.open_menu(); f.double_click(); test.assert(#sizeof(f.requests) == 3 && !f.popup.is_shown());
 const old_token = f.requests[2].data.request_token;
 f.open_menu(); f.double_click();
 test.assert(#sizeof(f.requests) == 4, 'A reopened report must request its own native acknowledgement');
 test.assert(f.requests[3].data.request_token != old_token);
 f.delivered = 3; f.deliver(2, true);
 test.assert(!f.popup.is_shown() && f.list.management_pending != null, 'Old receipt cannot open or discard the new report session'); unchanged(f, before);
 f.delivered = 4; f.deliver(3, true);
 test.assert(f.popup.popup.id == 'base_screen' && f.management.base == f.base, 'Current receipt opens the city for the reopened report'); unchanged(f, before);
 f.escape(); test.assert(f.popup.popup.id == 'base_operations' && f.row().el.border == 'rgb(0,235,0),1');
 f.escape(); unchanged(f, before); f.view.root.remove();
});
behavior.scenario('removed and replaced report callbacks cannot operate a successor or bypass another modal', () => {
 const f = fixture(); f.open_menu(); const old = f.row().el.get_handlers();
 f.escape(); f.open_menu(); const current = f.report.generation;
 for (entry of old) { if (entry.name == 'click') { entry.callback({}); entry.callback({}); } }
 test.assert(f.report.generation == current && f.controller.session.selected == null && #sizeof(f.requests) == 0);
 f.popup.show('turn_confirmation');
 for (entry of old) { if (entry.name == 'click') { entry.callback({}); } }
 test.assert(f.popup.popup.id == 'turn_confirmation' && #sizeof(f.requests) == 0);
 f.popup.clear(); f.open_menu(); const saved = f.row().el.get_handlers(); const before = f.snapshot();
 f.view.root.remove();
 for (entry of saved) { if (entry.name == 'click') { entry.callback({}); entry.callback({}); } }
 test.assert(#sizeof(f.requests) == 0); unchanged(f, before);
});
behavior.scenario('late native acknowledgement cannot replace another modal or a newer report session', () => {
 const f = fixture(); f.defer = true; f.open_menu(); f.double_click();
 f.popup.show('turn_confirmation'); f.delivered = 1; f.deliver(0, true);
 test.assert(f.popup.popup.id == 'turn_confirmation' && f.list.management_pending == null);
 f.popup.clear(); f.open_menu(); f.double_click(); f.controller.open();
 test.assert(f.popup.popup.id == 'base_operations'); const generation = f.report.generation;
 f.delivered = 2; f.deliver(1, true);
 test.assert(f.popup.popup.id == 'base_operations' && f.report.generation == generation);
 f.escape(); f.view.root.remove();
});
behavior.scenario('single clicks outside cadence remain selection only and report cleanup stops owned timers', () => {
 const f = fixture(); f.open_menu(); const before = f.snapshot();
 f.row().el.emit('click', {});
 for (timer of f.view.timers) { if (timer.interval == 400 && timer.running) { timer.tick(); } }
 f.row().el.emit('click', {});
 test.assert(f.popup.popup.id == 'base_operations' && #sizeof(f.requests) == 0);
 f.report.close.emit('click', {}); test.assert(!f.popup.is_shown());
 for (timer of f.view.timers) { if (timer.interval == 400) { test.assert(!timer.running); } }
 unchanged(f, before); f.view.root.remove();
});
behavior.scenario('owned city membership is live and retired row callbacks cannot open removed or foreign cities', () => {
 const f = fixture(); let foreign = null;
 for (base of f.game.bm.get_bases()) { if (base.get_owner().id != f.game.get_player().id) { foreign = base; } }
 f.open_menu(); test.assert(!f.controller.select(foreign.id) && #sizeof(f.report.rows) == 1);
 const saved = f.row().el.get_handlers(); const id = f.base.id + 0;
 f.native.with_write(() => { f.game.bm.despawn_base(id); });
 f.controller.refresh(); test.assert(#sizeof(f.report.rows) == 0);
 const before = f.snapshot();
 for (entry of saved) { if (entry.name == 'click') { entry.callback({}); entry.callback({}); } }
 test.assert(#sizeof(f.requests) == 0 && f.controller.session.selected == null);
 f.escape(); unchanged(f, before); f.view.root.remove();
});
