// Read-only application observation and declared initial selection. Input uses
// real SDL/pointer delivery; no production callback is called by this fixture.
#main((glsmac) => {
 #include('game/game')(glsmac); #include('ui/ui')(glsmac);
 const menu = #include('ui/parts/game/menu/menu');
 const preview = #include('ui/parts/game/bottom_bar/object_preview');
 const popup = #include('ui/parts/game/popup/popup');
 const terrain_observer = #include('../tests/_terrain_trace_observer');
 glsmac.on('configure_game',(configured) => {
  const game = configured.game; let actor = null; let armed = false; let focus_pending = false; let serial = 0;
  const proxy = {}; proxy.um = game.get_um(); proxy.bm = game.get_bm();
  for (field of ['get_um','get_bm','get_tm','get_players','get_player','get_turn','get_settings','get','is_started','is_turn_complete','get_research_state','get_research_science']) { proxy[field] = game[field]; }
  proxy.technologies = game.technologies;
  game.on('event_result',(e) => {
   #print('TF_RESULT|' + e.name + '|' + #to_string(e.success) + '|' + #json_text_exact(e.data));
   #print('TF_RECEIPT|' + #json_text_exact({name:e.name,event_id:e.event_id,caller:e.caller,success:e.success,data:e.data}));
   if (!e.success) { #print('TF_ERROR|event-rejected'); }
  });
  game.on('tile_target',(e) => {
   const base = e.tile.get_base(); const id = base == null ? null : base.id + 0;
   const owner = base == null ? null : base.get_owner().id + 0;
   #print('TF_TILE|' + #json_text_exact({x:e.tile.x + 0,y:e.tile.y + 0,base_id:id,base_owner:owner})); return false;
  });
  game.on('error',() => { #print('TF_ERROR|native-game'); });
  game.on('start_ui',() => {
   glsmac.ui.presentation_trace_start(); glsmac.ui.presentation_trace_inputs_start();
   for (unit of game.get_tm().get_tile(8,8).get_units()) { if (unit.owner == game.get_player().id && unit.get_def().can_terraform) { actor = unit; } }
   if (actor == null || !actor.get_def().can_terraform) { throw Error('Missing source-capable worker'); }
   const observer = terrain_observer(proxy,() => {
    return {selected:preview.selected_unit_id,pending:preview.order_pending == null ? null : #clone(preview.order_pending),order_label:preview.order_label == null ? null : preview.order_label.text + '',
     movement_label:preview.movement_label == null ? null : preview.movement_label.text + '',work_progress:preview.work_progress_label == null ? null : preview.work_progress_label.text + '',target:preview.terraforming_target.snapshot(),modal:popup.is_shown()};
   });
   const observe = () => {
    const movement = actor.movement;
    #print('TF_STATE|' + #to_string(serial) + '|' + #json_text_exact({selected:preview.selected_unit_id,actor:actor.id,owner:game.get_player().id + 0,
     order:actor.get_order(),work:actor.get_terraforming(),movement:movement,policy:game.get_settings().global.rules.get_terraforming_policy(),
     pending:preview.order_pending,target:preview.terraforming_target.snapshot(),modal:popup.is_shown(),root:menu.menus.left_menu.is_open,
     plan:actor.get_automation(),pending_native:game.has_pending_actions(game.get_player().id),
     tile_locked:actor.get_tile().is_locked(),x:actor.get_tile().x + 0,y:actor.get_tile().y + 0,
     height_presentation:preview.height_presentation}));
    serial++;
    const root = menu.menus.left_menu;
    if (root.is_open) {
     const header = root.items[5].el;
     #print('TF_POINT|header|' + #to_string(root.el.left + header.width / 2) + '|' + #to_string(glsmac.ui.get_height() - root.el.bottom - root.el.height + header.top + header.height / 2));
    }
    const child = menu.menus.left_menu_terraform;
    if (#is_defined(child) && child.is_open) {
     const rows = [];
     for (row of child.items) {
      const entry = row.entry;
      if (#is_defined(entry.terraform_action)) {
       rows :+ {id:entry.terraform_action + '',label:row.el.text + '',enabled:row.el.color != 'black',
        x:child.el.left + row.el.width / 2,y:child.el.top + row.el.top + row.el.height / 2};
      }
     }
     #print('TF_ROWS|' + #json_text_exact(rows));
    }
   };
   glsmac.ui.root.on('keydown',(e) => {
     if (e.modifiers != {ctrl:true,alt:true}) { return false; }
     if (e.code == 'K') {
      game.select_unit(actor); armed = true; focus_pending = true; return true;
     }
     if (e.code == 'P') { #print('TF_NATIVE|' + #json_text_exact(observer.read())); return true; }
     if (e.code == 'I') { #print('TF_INPUT|' + #json_text_exact(glsmac.ui.presentation_trace_drain())); return true; }
     if (e.code == 'Q') { glsmac.exit(); return true; }
     return false;
    });
   #print('TF_READY');
   glsmac.ui.root.timer(200,() => {
    if (focus_pending && preview.selected_unit_id == actor.id) {
     const owned = []; for (base of game.get_bm().get_bases()) { if (base.get_owner().id == game.get_player().id) { owned :+ base; } }
     if (#sizeof(owned) != 1) { throw Error('Expected one local target city'); }
     const point = glsmac.focus_owned_base(owned[0].id); focus_pending = false;
     #print('TF_BASE_POINT|' + #json_text_exact(point));
    }
    if (armed) { observe(); } return true;
   });
  });
 }); glsmac.run();
});
