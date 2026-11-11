// Resizing must preserve the pending decision and finish the popup lifecycle.
const behavior = #include('./_behavior');
const mocks = #include('_ui_mocks');

behavior.scenario('confirmed popup delivers its result when resize interrupts exit', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	const enter = f.view.timers[0];
	for (let i = 0; i < 12; i++) { enter.tick(); }
	test.assert(!enter.running, 'entry animation finished');
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	test.assert(f.state.results == [] && f.view.running_timers() == 1, 'confirmed result awaits exit');
	f.view.ui.emit('resize', { height: 900 });
	test.assert(!f.module.is_shown() && f.view.running_timers() == 0, 'resize completed hide and stopped exit timer');
	test.assert(f.state.results == [true], 'confirmed result must be delivered despite resize');
});

behavior.scenario('resize completes cancellation once even after repeated input and resize', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	const enter = f.view.timers[0];
	for (let i = 0; i < 12; i++) { enter.tick(); }
	f.view.find('button', 'text', 'Cancel').emit('click', {});
	const exit = f.view.timers[1];
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.view.ui.emit('resize', { height: 900 });
	f.view.ui.emit('resize', { height: 768 });
	test.assert(f.state.results == [false], 'the first decision is delivered exactly once');
	test.assert(!exit.tick() && f.view.running_timers() == 0, 'old exit cannot repeat delivery');
});

behavior.scenario('resize during entry keeps the popup available for a later decision', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	const enter = f.view.timers[0];
	enter.tick();
	f.view.ui.emit('resize', { height: 900 });
	test.assert(f.module.is_shown() && f.state.results == [], 'entry resize cannot cancel or confirm');
	test.assert(!enter.tick() && f.view.running_timers() == 0, 'entry animation is stopped');
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	const exit = f.view.timers[1];
	for (let i = 0; i < 12; i++) { exit.tick(); }
	test.assert(f.state.results == [true] && !f.module.is_shown(), 'later confirmation still completes normally');
});

behavior.scenario('resize finishes a programmatic hide without inventing a decision', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	f.module.hide('turn_confirmation');
	f.view.ui.emit('resize', { height: 900 });
	test.assert(!f.module.is_shown() && f.view.running_timers() == 0, 'programmatic exit completes');
	test.assert(f.state.results == [], 'hide without a result cannot invoke the decision callback');
});

for (sliding of [false, true]) {
	behavior.scenario('completion callback can reopen the same popup with sliding ' + #to_string(sliding), () => {
		const f = mocks.game_popup(sliding);
		f.module.show('turn_confirmation', (result) => {
			f.state.results :+ result;
			f.show('turn_confirmation');
		});
		f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
		if (sliding) { f.view.ui.emit('resize', { height: 900 }); }
		test.assert(f.state.results == [true] && f.module.is_shown(), 'callback reopens after old state is cleared');
		f.view.find('button', 'text', 'Cancel').emit('click', {});
		if (sliding) { f.view.ui.emit('resize', { height: 768 }); }
		test.assert(f.state.results == [true, false] && !f.module.is_shown(), 'reopened callback survives old completion');
		test.assert(f.view.running_timers() == 0, 'both popup lifecycles released timers');
	});
}

behavior.scenario('repeated visible and hidden popup resize preserves content geometry and audio ownership', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	const enter = f.module.sliding_timer;
	const current = f.module.popups.turn_confirmation;
	const hidden = f.module.popups.please_dont_go;
	const up = f.view.find('sound', 'sound', 'menu up.wav');
	const down = f.view.find('sound', 'sound', 'menu down.wav');
	for (height of [900, 640, 1080, 768]) {
		f.view.ui.emit('resize', {height: height});
		test.assert(current.el.top == (height - f.module.bottombar_height - current.height) / 2);
		test.assert(hidden.el.top == (height - f.module.bottombar_height - hidden.height) / 2);
		test.assert(current.el.is_visible() && !hidden.el.is_visible() && !f.module.popup_hiding);
		test.assert(f.state.results == [] && f.view.running_timers() == 0);
	}
	test.assert(!enter.tick() && up.play_count() == 1 && down.play_count() == 0, 'Resize cannot replay transition sounds or the stopped entry');
	f.view.find('button', 'text', 'Cancel').emit('click', {});
	f.view.ui.emit('resize', {height: 900});
	f.view.ui.emit('resize', {height: 640});
	test.assert(f.state.results == [false] && !current.el.is_visible() && !hidden.el.is_visible());
	test.assert(up.play_count() == 1 && down.play_count() == 1 && f.view.running_timers() == 0);
});

behavior.scenario('duplicate show during exit cannot replace its decision callback or animation', () => {
	const f = mocks.game_popup(true);
	f.show('turn_confirmation');
	for (let i = 0; i < 12; i++) { f.view.timers[0].tick(); }
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	const exit = f.module.sliding_timer;
	let replacements = 0;
	f.module.show('turn_confirmation', (result) => { replacements++; });
	test.assert(f.module.sliding_timer == exit && f.module.popup_hiding && f.view.running_timers() == 1);
	test.assert(f.state.closed_menus == 1 && f.view.find('sound', 'sound', 'menu up.wav').play_count() == 1);
	f.view.ui.emit('resize', {height: 900});
	test.assert(f.state.results == [true] && replacements == 0 && !f.module.is_shown());
	test.assert(!exit.tick() && f.view.running_timers() == 0, 'Only the original pending decision is completed');
});

behavior.scenario('resize completion may open a different dialog without old cleanup hiding it', () => {
	const f = mocks.game_popup(true);
	f.module.show('turn_confirmation', (result) => {
		f.state.results :+ result;
		f.show('please_dont_go');
	});
	for (let i = 0; i < 12; i++) { f.view.timers[0].tick(); }
	const old_window = f.module.popup.el;
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	const exit = f.module.sliding_timer;
	f.view.ui.emit('resize', {height: 900});
	test.assert(f.state.results == [true] && f.module.popup.id == 'please_dont_go');
	test.assert(!old_window.is_visible() && f.module.popup.el.is_visible() && !f.module.popup_hiding);
	test.assert(!exit.tick() && f.view.running_timers() == 1, 'Only the replacement entry owns an animation');
	test.assert(f.view.find('sound', 'sound', 'CPU please don\'t go.wav').play_count() == 1);
	f.view.find('button', 'text', 'Oops, no, wait!').emit('click', {});
	f.view.ui.emit('resize', {height: 768});
	test.assert(f.state.results == [true, false] && !f.module.is_shown() && f.view.running_timers() == 0);
});
