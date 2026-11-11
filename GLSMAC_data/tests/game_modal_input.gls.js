// GLSMAC regression coverage, not original-game parity. Production game UI,
// menus, popup definitions and bottom bar initialize without display assets.
// Keyboard delivery models Container::ProcessEvent's child-first consumption;
// clear models Container::Clear removing both children and local handlers.
const behavior = #include('./_behavior');
const mocks = #include('./_ui_mocks');

const fixture = () => {
	const f = {};
	f.view = mocks.display();
	const decorate = (node) => {
		if (!#is_defined(node.width)) { node.width = 1024; }
		if (!#is_defined(node.height)) { node.height = 768; }

		for (kind of ['area', 'panel', 'window', 'surface', 'text', 'input', 'button', 'scrollview', 'listview', 'choicelist', 'widget', 'sound']) {
			const tag = kind;
			const create = node[tag];
			if (#typeof(create) != 'Callable') { continue; }
			node[tag] = (props) => { const child = create(props); decorate(child); return child; };
		}
	};
	decorate(f.view.root);
	const root_events = mocks.events();
	f.view.root.on = root_events.on; f.view.root.off = root_events.off;
	f.view.root.emit = root_events.emit; f.view.root.handler_count = root_events.count;
	const clear = f.view.root.clear;
	f.view.root.clear = () => { root_events.clear(); clear(); };

	f.view.ui.get_width = () => { return 1024; };
	f.game = mocks.events(); f.map = mocks.events(); f.glsmac = mocks.events();
	// Native Wrappable::Trigger snapshots handlers before callbacks can register
	// additional listeners. start_ui registers more handlers on the same game.
	f.game.emit = (name, data) => {
		const snapshot = [] + f.game.handlers;
		let result = false;
		for (handler of snapshot) {
			if (handler.active && handler.name == name) { result = handler.callback(data); }
		}
		return result;
	};
	f.state = { exits: 0, resets: 0, orders: [], results: [] };
	f.glsmac.exit = () => { f.state.exits = f.state.exits + 1; };
	f.glsmac.reset = () => { f.state.resets = f.state.resets + 1; };
	f.glsmac.load_smac_text = #include('./_ingame_menu_text_fixture');
	f.game.get_map = () => { return f.map; };
	f.game.get_um = () => { return {}; };
	f.game.get_year = () => { return 2101; };
	f.game.get_player = () => { return {get_energy_state: () => { return {credits: 0}; }}; };
	f.game.event = (name, data) => { f.state.orders :+ name; };
	const m = {};
	m.ui = f.view.ui; m.root = f.view.root; m.glsmac = f.glsmac;
	#include('../default/ui/parts/game/game')(m);
	const configured = {}; configured.game = f.game;
	f.glsmac.emit('configure_game', configured);
	f.start = () => { f.game.emit('start_ui', {}); };
	f.start();
	f.popup = #include('../default/ui/parts/game/popup/popup');
	f.menu = #include('../default/ui/parts/game/menu/menu');
	f.finish_animation = () => {
		for (let tick = 0; tick < 15; tick++) {
			for (timer of f.view.timers) {
				if (timer.interval == 10) { timer.tick(); }
			}
		}
	};
	f.key = (code, modifiers) => {
		const e = { code: code, modifiers: modifiers };
		// Modal windows consume keyboard input before root shortcuts in native
		// Container::ProcessEvent. Explicit delivery has no hit-testing claims.
		if (f.popup.is_shown()) { return f.popup.popup.el.emit('keydown', e) == true; }
		return f.view.root.emit('keydown', e) == true;
	};
	return f;
};

const f = fixture();

behavior.scenario('game UI initializes its real popup menu and bottom bar', () => {
	test.assert(!f.popup.is_shown());
	test.assert(f.view.find('button', 'text', 'MENU').handler_count('click') == 1);
	test.assert(f.view.root.handler_count('keydown') == 2, 'Quit and research shortcuts each own one root registration');
	test.assert(f.view.find('button', 'text', 'TURN COMPLETE').handler_count('click') == 1);
});
behavior.scenario('Escape cancels a dialog once before root quit handling', () => {
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	test.assert(f.popup.popup.id == 'turn_confirmation', 'Dialog shown before Escape');
	test.assert(f.key('ESCAPE', {}), 'Escape consumed');
	test.assert(f.popup.popup.id == 'turn_confirmation', 'Original dialog stays current during exit');
	test.assert(f.popup.popup_hiding, 'Cancel starts exit animation');
	f.finish_animation();
	test.assert(f.state.results == [false] && !f.popup.is_shown());
	test.assert(f.state.exits == 0 && f.state.resets == 0);
	test.assert(f.view.find('sound', 'sound', 'CPU please don\'t go.wav').play_count() == 0);
});
behavior.scenario('Escape closes an initialized base screen without opening quit', () => {
	f.state.results = [];
	f.popup.show('base_screen', (result) => { f.state.results :+ result; });
	f.finish_animation();
	test.assert(f.key('ESCAPE', {}));
	f.key('ESCAPE', {});
	f.finish_animation();
	test.assert(f.state.results == [false] && !f.popup.is_shown());
	test.assert(f.state.exits == 0 && f.state.resets == 0);
});
behavior.scenario('Ctrl Shift Q cannot replace a pending turn-confirmation result', () => {
	f.state.results = [];
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	test.assert(f.key('Q', { ctrl: true, shift: true }));
	test.assert(f.popup.popup.id == 'turn_confirmation' && f.state.results == []);
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.key('Q', { ctrl: true, shift: true });
	f.finish_animation();
	test.assert(f.state.results == [true] && !f.popup.is_shown());
	test.assert(f.state.exits == 0 && f.state.resets == 0);
});
behavior.scenario('canceling a dialog restores usable turn controls', () => {
	f.view.find('button', 'text', 'TURN COMPLETE').emit('click', {});
	f.finish_animation();
	f.key('ESCAPE', {});
	f.finish_animation();
	test.assert(f.state.orders == [] && !f.popup.is_shown());
	f.view.find('button', 'text', 'TURN COMPLETE').emit('click', {});
	f.finish_animation();
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.finish_animation();
	test.assert(f.state.orders == ['complete_turn']);
	f.game.emit('turn_status', { status: 'active' });
});
behavior.scenario('quit menu retains its exit result when restart shortcut arrives', () => {
	f.menu.open('left_menu_game');
	f.view.find('button', 'text', 'Quit').emit('click', {});
	f.finish_animation();
	test.assert(f.popup.popup.id == 'please_dont_go');
	test.assert(f.key('Q', { ctrl: true, shift: true }));
	f.view.find('button', 'text', 'Yes, that\'s an order mister!').emit('click', {});
	f.finish_animation();
	test.assert(f.state.exits == 1 && f.state.resets == 0);
});
behavior.scenario('restart shortcut retains its reset result and supports cancellation', () => {
	f.key('Q', { ctrl: true, shift: true });
	f.finish_animation();
	f.key('ESCAPE', {});
	f.finish_animation();
	test.assert(!f.popup.is_shown() && f.state.resets == 0 && f.state.exits == 1);
	f.key('Q', { ctrl: true, shift: true });
	f.finish_animation();
	f.view.find('button', 'text', 'Yes, that\'s an order mister!').emit('click', {});
	f.finish_animation();
	test.assert(f.state.resets == 1 && f.state.exits == 1);
});
behavior.scenario('repeated start_ui replaces root handlers instead of accumulating them', () => {
	for (let i = 0; i < 3; i++) {
		f.start();
		test.assert(f.view.root.handler_count('keydown') == 2);
	}
	test.assert(f.key('ESCAPE', {}));
	f.finish_animation();
	test.assert(f.popup.popup.id == 'please_dont_go');
	test.assert(f.view.find('sound', 'sound', 'CPU please don\'t go.wav').play_count() == 1);
});
behavior.scenario('restarting UI detaches old map preview and resize subscriptions', () => {
	const unit_previews = f.map.count('unit_preview');
	const base_previews = f.map.count('base_preview');
	const resize = f.view.ui.count('resize');
	f.start();
	test.assert(f.map.count('unit_preview') == unit_previews, 'Old unit-preview handlers must be detached');
	test.assert(f.map.count('base_preview') == base_previews, 'Old base-preview handlers must be detached');
	test.assert(f.view.ui.count('resize') == resize, 'Old popup-resize handlers must be detached');
});
behavior.scenario('restarting UI cancels animations owned by the old popup', () => {
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	test.assert(f.popup.sliding_timer != null);
	f.start();
	let running = 0;
	for (timer of f.view.timers) {
		if (timer.interval == 10 && timer.running) { running++; }
	}
	test.assert(running == 0, 'Old popup animations must stop when their UI is destroyed');
	test.assert(!f.popup.is_shown());
});
behavior.scenario('UI restart discards an old exit animation without delivering its result', () => {
	f.state.results = [];
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	test.assert(f.popup.popup_hiding && f.state.results == []);
	const exit = f.popup.sliding_timer;
	f.start();
	test.assert(!exit.tick(), 'Destroyed popup cannot resume its pending exit');
	f.finish_animation();
	test.assert(f.state.results == [] && !f.popup.is_shown());
});

behavior.scenario('turn confirmation cannot submit after delivered wait and active status transitions', () => {
	f.start(); f.state.orders = []; f.state.results = [];
	const turn = f.view.find('button', 'text', 'TURN COMPLETE');
	turn.emit('click', {}); f.finish_animation();
	f.game.emit('turn_status', { status: 'please_wait' });
	test.assert(turn.text == 'PLEASE WAIT' && f.popup.is_shown());
	f.game.emit('turn_status', { status: 'active' });
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.finish_animation();
	test.assert(f.state.orders == [] && !f.popup.is_shown(), 'An earlier confirmation cannot act on a restored active turn');
	test.assert(turn.text == 'TURN COMPLETE', 'Stale confirmation cannot replace the newer native status');
	turn.emit('click', {}); f.finish_animation();
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.finish_animation();
	test.assert(f.state.orders == ['complete_turn'] && turn.text == 'PLEASE WAIT', 'A fresh confirmation remains usable exactly once');
});

behavior.scenario('delivered mission year invalidates an open confirmation without losing the next dialog', () => {
	f.start(); f.state.orders = [];
	const turn = f.view.find('button', 'text', 'TURN COMPLETE');
	turn.emit('click', {}); f.finish_animation();
	f.game.emit('turn', { year: 2102 });
	test.assert(f.view.find('text', 'text', 'Mission Year 2102').text == 'Mission Year 2102');
	f.view.find('button', 'text', 'Yes, end the turn.').emit('click', {});
	f.finish_animation();
	test.assert(f.state.orders == [] && turn.text == 'TURN COMPLETE', 'An old-year response cannot complete the new turn');
	turn.emit('click', {}); f.finish_animation();
	test.assert(f.popup.popup.id == 'turn_confirmation' && !f.popup.popup_hiding);
	f.key('ESCAPE', {}); f.finish_animation();
	test.assert(f.state.orders == [] && !f.popup.is_shown(), 'New-year cancellation leaves the real turn control usable');
});

behavior.scenario('modal research and restart shortcuts leave its content and decision owned by the dialog', () => {
	f.start(); f.state.orders = []; f.state.results = [];
	const exits = f.state.exits; const resets = f.state.resets;
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	const window = f.popup.popup.el;
	const speech = f.view.find('sound', 'sound', 'CPU please don\'t go.wav');
	for (input of [{code: 'F2', modifiers: {}}, {code: 'R', modifiers: {shift: true}}, {code: 'Q', modifiers: {ctrl: true, shift: true}}, {code: 'TAB', modifiers: {}}]) {
		test.assert(f.key(input.code, input.modifiers), 'Modal owns the explicitly delivered key before root shortcuts');
		test.assert(f.popup.popup.el == window && window.is_visible() && !f.popup.popup_hiding);
		test.assert(f.state.results == [] && f.state.orders == []);
	}
	test.assert(f.view.find('text', 'text', 'Do you really want to end the turn now?').is_visible());
	test.assert(speech.play_count() == 0 && f.state.exits == exits && f.state.resets == resets);
	f.key('ESCAPE', {}); f.finish_animation();
	test.assert(f.state.results == [false] && f.view.root.handler_count('keydown') == 2);
});

behavior.scenario('saved controls from before UI restart cannot decide a successor dialog', () => {
	f.start(); f.state.orders = []; f.state.results = [];
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	const old_window = f.popup.popup.el;
	const old_yes = f.view.find('button', 'text', 'Yes, end the turn.');
	const old_handlers = old_yes.get_handlers(); const old_click = old_handlers[0].callback;
	const resize = f.view.ui.count('resize');
	f.start();
	test.assert(old_window.is_removed() && old_yes.handler_count('click') == 0);
	test.assert(!old_yes.emit('click', {}) && !old_window.emit('keydown', {code: 'ESCAPE', modifiers: {}}));
	f.popup.show('turn_confirmation', (result) => { f.state.results :+ result; });
	f.finish_animation();
	const successor = f.popup.popup.el;
	old_click({});
	test.assert(f.popup.popup.el == successor && successor != old_window && !f.popup.popup_hiding, 'Retained old callback cannot hide the current presentation');
	test.assert(f.state.results == [] && f.state.orders == [] && f.view.ui.count('resize') == resize);
	f.key('ESCAPE', {}); f.finish_animation();
	test.assert(f.state.results == [false] && !f.popup.is_shown(), 'Only the current presentation delivers a result');
});
