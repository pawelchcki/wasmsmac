// Actual native city quote domains and immutable source-row identity.
// No browser, installed artwork, original-game or per-base UI-filter claim.
const behavior = #include('./_behavior');
const reader = #include('./_unit_workshop_reader');
const fixture = () => {
 const f = test.founding_fixture(); f.configure('flat_arid_world'); f.add_worker(0);
 f.with_write(() => {
  f.game.um.define_unit('ObserverSeaFormer',{name:'Synthetic Sea Worker',morale:'SYNTHETIC',type:'static',movement_type:'water',movement_per_turn:4,can_terraform:true,
   combat:{kind:'civilian',offense:0,defense:1,reactor:1},render:{type:'sprite',file:'synthetic.pcx',x:0,y:0,w:1,h:1,cx:0,cy:0}});
  f.owner.add_production_choice('A_LAND',{type:'unit',id:'ColonyPod',cost:30,cost_rows:3,population_cost:1});
  f.owner.add_production_choice('B_SEA',{type:'unit',id:'ObserverSeaFormer',cost:40,cost_rows:4,population_cost:0});
  f.owner.add_production_choice('C_LAND',{type:'unit',id:'ColonyPod',cost:30,cost_rows:3,population_cost:1});
 });
 f.choices = () => { const choices = []; for (choice of f.owner.get_production_choices()) { if (choice.type == 'unit') { choices :+ #clone(choice); } } return choices; };
 return f;
};
behavior.scenario('inland native global inventory retains rejected Sea quote and continues to later land design without mutation',() => {
 const f = fixture(); const inventory = f.choices(); const before = f.snapshot(); const inspect = f.inspect();
 const result = reader.quote_choices(f.base,inventory);
 test.assert(result.ids == ['A_LAND','B_SEA','C_LAND']);
 test.assert(result.by_id.A_LAND == {accepted:true,loss:0,reason:null});
 test.assert(result.by_id.B_SEA == {accepted:false,loss:null,reason:'Sea worker requires an unlocked friendly launch tile'});
 test.assert(result.by_id.C_LAND == {accepted:true,loss:0,reason:null},'The meaningful post-catch path must reach the design after Sea rejection');
 test.assert(f.choices() == inventory && f.snapshot() == before && f.inspect() == inspect,'Read-only collection changes no recipe or native world/update state');
});
behavior.scenario('the same globally visible Sea recipe quote is accepted in actual native coastal context without mutation',() => {
 const f = fixture(); f.configure('sea_worker_coast'); const before = f.snapshot(); const inspect = f.inspect();
 const result = reader.quote_choices(f.base,f.choices());
 test.assert(result.ids == ['A_LAND','B_SEA','C_LAND']);
 test.assert(result.by_id.B_SEA == {accepted:true,loss:0,reason:null});
 test.assert(result.by_id.A_LAND.accepted && result.by_id.C_LAND.accepted);
 test.assert(f.snapshot() == before && f.inspect() == inspect);
});
behavior.scenario('native-loaded source linkage follows a shifted Terraforming role rather than a synthetic fixed weapon ordinal',() => {
 const source = #include('./_startup_unit_rules_fixture'); const document = test.parse_smac_text(source.source,'rules');
 const weapons = [['Decoy','DECOY','1','0','1','-1','None']];
 for (row of document.rows('WEAPONS')) { weapons :+ #clone(row); }
 const rules = #include('../default/game/unit_rules').parse({rows:(block) => { return block == 'WEAPONS' ? weapons : document.rows(block); }});
 const rule = rules.definitions[1]; const before = #clone(weapons);
 const profile = reader.weapon_profile(rule,document.rows('UNITS'),weapons);
 test.assert(profile.weapon_index == 3 && profile.weapon_index == rule.source_components.weapon);
 test.assert(profile.unit_weapon == 'Terraformer' && profile.weapon_shortname == profile.unit_weapon && profile.weapon_mode == 9);
 test.assert(profile.prototype == 1 && weapons == before);
 const wrong = #clone(rule); wrong.source_components.weapon = 0; let rejected = false;
 try { reader.weapon_profile(wrong,document.rows('UNITS'),weapons); } catch { : (failure) => { rejected = true; } }
 test.assert(rejected,'A mismatched actual source row must reject instead of replacing the expected role');
});
