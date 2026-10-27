// Synthetic inputs and read-only observation. No original-game oracle, copied
// artwork, production callback replacement or hand-authored layout coordinates.
export const workshopWorld=String.raw`return (game) => {
 const rules = game.get('starting_unit_rules');
 let initial = null;
 for (rule of rules) { if (rule.id == 'ScoutPatrol') { initial = rule.choice + ''; } }
 if (initial == null) { throw Error('Workshop fixture needs the actual source Scout recipe'); }
 game.get_bm().on('base_spawn',(e) => { if (e.base.get_size() == 0) { e.base.create_pop({type:'DOCTOR'}); } });
 let index = 0;
 for (player of game.get_players()) {
  const tile = game.get_tm().get_tile(index * 2,2);
  const credits = game.get('energy_rules').starting_credits + player.get_faction().economy_bonuses.starting_energy;
  game.event('initialize_energy',{player_id:player.id + 0,credits:credits});
  // Explicit fixture inventory: registered source recipes; no technology,
  // component, price or prototype arithmetic is replaced by the test.
  for (rule of rules) {
   game.event('add_production_choice',{player:player,id:rule.choice,
    data:{type:'unit',id:rule.id,cost:rule.rows * 10,cost_rows:rule.rows,population_cost:rule.population}});
  }
  const sea = game.get('sea_former_rule');
  if (sea != null) { game.event('add_production_choice',{player:player,id:sea.choice,
   data:{type:'unit',id:sea.id,cost:sea.rows * 10,cost_rows:sea.rows,population_cost:sea.population}}); }
  game.event('spawn_base',{owner:player,tile:tile,facilities:['HEADQUARTERS'],production_choice:initial});
  game.event('spawn_unit',{type:'ScoutPatrol',owner:player,tile:tile,morale:2,health:1.0}); index++;
 }
 if (index != 7) { throw Error('Workshop browser fixture requires seven native owners'); }
 game.event('spawn_unit',{type:'Formers',owner:game.get_player(),tile:game.get_tm().get_tile(8,8),morale:2,health:1.0});
};`;

export const workshopMain=String.raw`#main((glsmac) => {
 #include('game/game')(glsmac); #include('ui/ui')(glsmac);
 const screen = #include('ui/parts/game/popup/base_screen');
 const popup = #include('ui/parts/game/popup/popup');
 const terrain_observer = #include('../tests/_terrain_trace_observer');
 glsmac.on('configure_game',(configured) => {
  const game = configured.game; const receipts = [];
  game.on('event_result',(e) => {
   if (#typeof(e.name) != 'String' || #typeof(e.event_id) != 'String' || #typeof(e.caller) != 'Int' || #typeof(e.success) != 'Bool') {
    throw Error('Unexpected native event receipt scalar types');
   }
   if (#sizeof(receipts) == 0) { #print('WS_RECEIPT_TYPES|' + #json_text_exact({name:#typeof(e.name),event_id:#typeof(e.event_id),caller:#typeof(e.caller),success:#typeof(e.success)})); }
   // Opaque native transaction token, distinct from Int entity handles and
   // source definition/production String IDs. Preserve the complete token.
   const row = {name:e.name + '',event_id:e.event_id + '',caller:e.caller + 0,success:e.success == true};
   receipts :+ row; #print('WS_RECEIPT|' + #json_text_exact(row));
   if (!e.success) { #print('WS_ERROR|event-rejected'); }
  });
  game.on('error',() => { #print('WS_ERROR|native-game'); });
  game.on('start_ui',() => {
   const proxy = {}; proxy.um = game.get_um(); proxy.bm = game.get_bm();
   for (field of ['get_um','get_bm','get_tm','get_players','get_player','get_turn','get_settings','get','is_started','is_turn_complete','get_research_state','get_research_science']) { proxy[field] = game[field]; }
   proxy.technologies = game.technologies;
   glsmac.ui.presentation_trace_start(); glsmac.ui.presentation_trace_inputs_start();
   // A separate declared pixel control loads the same installed component
   // through the normal asset loader. It never supplies an input target or
   // replaces any Workshop widget, model, renderer or palette.
   const pixel_control = glsmac.ui.root.panel({align:'top right',right:8,top:8,width:100,height:75,background:'black',zindex:0.92});
   const pixel_surface = pixel_control.surface({left:0,top:0,width:100,height:75,background:'VT.cvr'});
   pixel_surface.presentation_role('workshop-pixel-control','VT.cvr');
   let base_id = null;
   for (base of game.get_bm().get_bases()) { if (base.get_owner().id == game.get_player().id) { if (base_id != null) { throw Error('Expected exactly one local browser city'); } base_id = base.id + 0; } }
   if (base_id == null) { throw Error('Missing local browser city'); }
   const find_base = () => { for (base of game.get_bm().get_bases()) { if (base.id == base_id) { return base; } } throw Error('Browser city retired'); };
   const read_ui = () => {
    const result = {base_open:screen.is_open,base_id:screen.base_id,production_open:screen.production_selection != null,
     popup_sliding:popup.sliding_timer != null,popup_hiding:popup.popup_hiding,
     draft:screen.production_choices == null ? null : screen.production_choices.value + '',
     workshop_open:screen.workshop != null && screen.workshop.dialog != null,workshop_selected:null,workshop_token:null,
     viewport:{width:glsmac.ui.get_width(),height:glsmac.ui.get_height()},receipts:#sizeof(receipts),choices:[],rules:[],switch_losses:{}};
    if (result.workshop_open) {
     const dialog = screen.workshop.dialog;
     result.workshop_selected = dialog.choices == null ? null : dialog.choices.value + '';
     result.workshop_token = screen.workshop.session.token + 0;
    }
    const base = find_base(); const owner = base.get_owner();
    for (choice of owner.get_production_choices()) {
     if (choice.type == 'unit') {
      result.choices :+ {id:choice.id + '',unit_id:choice.unit_id + '',name:choice.name + '',cost:choice.cost + 0};
      result.switch_losses[choice.id] = base.get_production_switch_loss(choice.id);
     }
    }
    for (rule of game.get('starting_unit_rules')) { result.rules :+ #clone(rule); }
    const sea = game.get('sea_former_rule'); if (sea != null) { result.rules :+ #clone(sea); }
    return result;
   };
   const observer = terrain_observer(proxy,read_ui);
   let query = 0; let pending_query = null; let exit_requested = false; let refresh_armed = false; let refresh_wait = 0;
   let watched_base = null; let watched_workshop = null; let tagged_production = null; let watch_serial = 0;
   const watch = (frame,scope) => {
    watch_serial++; const token = watch_serial;
    #print('WS_WINDOW|' + #json_text_exact({kind:'attached',scope:scope,token:token}));
    // Both actual Window handlers already return true unconditionally.
    // Wrappable runs its ordered callback copy to completion. Returning true
    // here preserves that result for EVERY ordinary key; no callback is replaced.
    frame.on('keydown',(e) => {
     if (e.modifiers == {ctrl:true,alt:true}) {
      if (e.code == 'P') { query++; pending_query = query; }
      if (e.code == 'J') { refresh_armed = true; #print('WS_ARMED|' + #to_string(token)); }
      if (e.code == 'Q') { exit_requested = true; }
     }
     return true;
    });
    frame.on('remove',() => {
     #print('WS_WINDOW|' + #json_text_exact({kind:'removed',scope:scope,token:token}));
     if (scope == 'base' && watched_base == frame) { watched_base = null; }
     if (scope == 'workshop' && watched_workshop == frame) { watched_workshop = null; }
    });
   };
   let focused = false; let focus_attempts = 0; let serial = 0; let last_ui = '';
   glsmac.ui.root.timer(100,() => {
    if (!focused) {
     focus_attempts++;
     try { const point = glsmac.focus_owned_base(base_id); focused = true; #print('WS_BASE_POINT|' + #json_text_exact(point)); }
     catch { : (e) => { if (focus_attempts == 1) { #print('WS_FOCUS_WAIT|' + e.reason); } } }
     if (!focused && focus_attempts >= 600) { throw Error('Rendered city never became focusable within startup budget'); }
    }
    if (screen.is_open && popup.popups.base_screen.el != watched_base) {
     watched_base = popup.popups.base_screen.el; watch(watched_base,'base');
    }
    const workshop = screen.workshop == null ? null : screen.workshop.dialog;
    if (workshop != null && workshop.frame != watched_workshop) {
     watched_workshop = workshop.frame; watch(watched_workshop,'workshop');
     if (workshop.choices != null) { workshop.choices.presentation_role('workshop-list','designs'); }
    }
    if (screen.production_choices != null && screen.production_choices != tagged_production) {
     tagged_production = screen.production_choices; tagged_production.presentation_role('workshop-list','production');
    }
    const ui = read_ui(); const ui_text = #json_text_exact(ui);
    if (ui_text != last_ui) { serial++; last_ui = ui_text; #print('WS_STATE|' + #json_text_exact({serial:serial,ui:ui})); }
    if (pending_query != null) {
     const requested = pending_query; pending_query = null;
     // This owned timer executes after the query key callback/dispatch returns.
     // Read the live world now; never reuse a snapshot taken before mouseup.
     #print('WS_NATIVE|' + #json_text_exact({query:requested,serial:serial,ui:ui,world:observer.read()}));
    }
    if (refresh_armed && workshop != null) {
     refresh_wait++;
     if (refresh_wait >= 3) {
      refresh_armed = false; refresh_wait = 0;
      #print('WS_CONTEXT|' + #json_text_exact({kind:'native-select-same-base',base_id:base_id}));
      // Declared fixture invalidation through the actual native frontend path;
      // do not call screen.set(), hide(), choose() or any production callback.
      game.select_base(find_base());
     }
    }
    #print('WS_TRACE|' + #json_text_exact(glsmac.ui.presentation_trace_drain()));
    if (exit_requested) { #print('WS_EXIT_REQUEST'); glsmac.exit(); return false; }
    return true;
   });
   #print('WS_READY');
  });
 }); glsmac.run();
});`;
