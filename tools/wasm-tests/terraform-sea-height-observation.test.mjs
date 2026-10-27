// Pure input/acceptance checks. No native execution or reference agreement.
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {declaredTerrain,rateOneSource} from './terraform-browser-inputs.mjs';
import {seaHeightTerrain,seaHeightInput,seaHeightOverrideManifest} from './terraform-sea-height-inputs.mjs';
import {auditPaidSeaHeight} from './terraform-sea-height-observation.mjs';

test('coastal map changes only the declared deep-water altitude and contour bytes',()=>{
  const base=declaredTerrain(),sea=seaHeightTerrain();assert.equal(sea.length,base.length);
  const offset=15+0xaa4+(8*16/2+8/2)*44;
  assert.deepEqual([...sea.keys()].filter(index=>sea[index]!==base[index]),[offset,offset+1]);
  assert.equal(sea[offset],32);assert.equal(sea[offset+1],30);
  const port=15+0xaa4+(8*16/2+10/2)*44;assert.equal(sea[port],96);
  assert.equal(seaHeightInput.port.x,10);assert.equal(seaHeightInput.actor.x,8);
  sea[offset]=0;assert.equal(seaHeightTerrain()[offset],32,'Each call owns fresh bytes');
});

test('override manifest distinguishes both source domains and rejects unrelated edits',()=>{
  const original=Buffer.from('#TERRAIN\n'+Array.from({length:20},(_,id)=>`Land ${id},None,Sea ${id},Disable,12,Build,Help,R ; unchanged`).join('\n')+'\n#NEXT\n','latin1');
  const changed=rateOneSource(original),rows=seaHeightOverrideManifest(original,changed);
  assert.equal(rows.length,20);assert.deepEqual(rows[16],{row:16,line:18,land_name:'Land 16',sea_name:'Sea 16',field_index:4,field:'shared_turns',old:12,new:1,applies_to:['land','sea']});
  assert.throws(()=>seaHeightOverrideManifest(original,Buffer.from(changed.toString('latin1').replace('Sea 16','invented'))));
  assert.throws(()=>seaHeightOverrideManifest(original,Buffer.from(changed.toString('latin1').replace(',1,Build',',2,Build'))));
});

function pair(){
  const tile={x:8,y:8,elevation:{center:-1460,left:-500,top:-500,right:-500,bottom:-500},neighbors:{E:{x:10,y:8}},terrain_epoch:0,
    canonical:{active:false,elevation:null,is_water:null,unknown:'retained'},imported:{active:true,source_corners:[-500,-500,-500,-500],source_elevation:-1460,source_water:true},
    is_land:false,is_water:true,native_type:{domain:'sea'},native_height_band:{below_coast:true,below_ocean:true,below_trench:false},resources:{payer:{energy:1}},unknown_native:'retained'};
  const port=structuredClone(tile);port.x=10;port.elevation.center=240;port.neighbors={W:{x:8,y:8}};
  port.is_land=true;port.is_water=false;port.native_type.domain='land';
  const world={players:[{id:'payer',raw_id:0},{id:'foreign',raw_id:1}],units:[{id:'actor',raw_id:8,movement:4,order:'NO_ORDERS',health:1,morale:1}],
    terrain_trace:{player_details:{payer:{energy:{credits:10,last_income_turn:0,initialized:true},energy_revision:1,unknown:'retained'},foreign:{energy:{credits:10},unknown:'retained'}},
      unit_details:{actor:{moved_this_turn:false,home_base_id:1,terraforming_recovery:{active:false,x:0,y:0},work:{action:'',work_units:0,unknown:'retained'},quotes:{E:{allowed_now:true,reason:null,cost:1}},combat:{defense:1},unknown:'retained'}},
      tiles:{'8,8':tile,'10,8':port},ui:{state:'changed independently'}}};
  const quote={owner:0,unit_id:8,fee:1,source_water:true,destination_water:true,plan:[{x:8,y:8,canonical:{elevation:-500,is_water:true}}]};
  const after=structuredClone(world);after.units[0].movement=0;after.terrain_trace.unit_details.actor.moved_this_turn=true;
  after.terrain_trace.unit_details.actor.quotes.E.allowed_now=false;after.terrain_trace.unit_details.actor.quotes.E.reason='Unit is out of moves';
  after.terrain_trace.player_details.payer.energy.credits=9;after.terrain_trace.player_details.payer.energy_revision=2;
  const changed=after.terrain_trace.tiles['8,8'];changed.elevation.center=-500;changed.terrain_epoch=1;
  Object.assign(changed.canonical,{active:true,elevation:-500,is_water:true});Object.assign(changed.imported,{active:false,source_corners:null,source_elevation:null,source_water:null});changed.native_height_band.below_ocean=false;
  return{before:{world},after:{world:after},quote};
}

test('sea audit checks the complete world while accepting exact quote fee budget and canonical changes',()=>{
  const p=pair();assert.deepEqual(auditPaidSeaHeight(p.before,p.after,p.quote).quoted_tiles,['8,8']);
  assert.equal(p.before.world.terrain_trace.tiles['8,8'].imported.active,true);
});

test('sea audit rejects unrelated ownership resources actor health home and recovery changes',()=>{
  for(const corrupt of [
    r=>r.world.units[0].health=0.5,
    r=>r.world.terrain_trace.unit_details.actor.home_base_id=2,
    r=>r.world.terrain_trace.unit_details.actor.terraforming_recovery.active=true,
    r=>r.world.terrain_trace.player_details.payer.unknown='changed',
    r=>r.world.terrain_trace.player_details.foreign.energy.credits=9,
    r=>r.world.terrain_trace.tiles['8,8'].resources.payer.energy=2,
    r=>r.world.terrain_trace.tiles['8,8'].canonical.unknown='changed',
    r=>r.world.terrain_trace.tiles['10,8'].is_water=true,
  ]){const p=pair();corrupt(p.after);assert.throws(()=>auditPaidSeaHeight(p.before,p.after,p.quote));}
});

test('sea-preserving case cannot silently expand to an emerged tile or feature replacement',()=>{
  const p=pair();p.quote.destination_water=false;assert.throws(()=>auditPaidSeaHeight(p.before,p.after,p.quote));
  const q=pair();q.quote.plan[0].terraforming={farm:false};assert.throws(()=>auditPaidSeaHeight(q.before,q.after,q.quote));
});

// Public protocol data, not claimed native outcomes. Live source bootstrap
// must supply every witness before the driver can call this acceptance check.
function bootstrap(){
  const recipe={id:'SeaFormers',choice:'SEA_FORMERS',application_recipe:'foil-terraform-module-v1',weapon_mode:9,movement_type:'water',movement:4,rows:5,source_components:{chassis:3,prototype:null}};
  const base_states=Array.from({length:7},(_,i)=>({base_id:i+1,owner:i,population:1,production:{choice_id:'FORMERS',minerals:i===0?4:0,last_processed_turn:1}}));
  const setup={actor:8,home_id:1,base_states,declared:{version:2,recipe,resumed_choice:'FORMERS',restored:{cost:40,minerals:43,last_processed_turn:0,population:1}},production:{choice_id:'FORMERS',minerals:4,last_processed_turn:1}};
  const actual={version:2,base_id:1,owner:0,turn:1,observed_choice_cost:40,requested_stock:43,population_cost:0,population:1,choice_id:'SEA_FORMERS',source_recipe:recipe,actual_prefill:{choice_id:'SEA_FORMERS',minerals:43,last_processed_turn:0}};
  const preturn={version:2,turn:1,home_id:1,bases:base_states.map((row,i)=>({...structuredClone(row),eligible:i===0,
    production:{choice_id:i===0?'SEA_FORMERS':'FORMERS',minerals:i===0?43:0,last_processed_turn:i===0?0:1},intake:{MINERALS:1,NUTRIENTS:2},consumption:{MINERALS:0,NUTRIENTS:2}}))};
  const birth={unit_id:8,owner:0,definition:'SeaFormers',is_water:true,can_terraform:true,turn:1,home_id:1,home_population:1,x:8,y:8,movement:4,health:1,production:{choice_id:'',minerals:4,last_processed_turn:1}};
  const records=[{kind:'TH_SEA_ACCOUNTING',value:actual},{kind:'TH_SEA_PRETURN',value:preturn},{kind:'TH_SEA_BIRTH',value:birth},
    {kind:'TH_RECEIPT',value:{name:'process_base_production',event_id:'0_61',caller:0,success:true,data:{turn_id:1,minerals:1}}},
    ...Array.from({length:7},(_,i)=>({kind:'TH_RECEIPT',value:{name:'process_base_growth',event_id:`0_${i+62}`,caller:0,success:true,data:{turn_id:1}}})),
    {kind:'TH_RECEIPT',value:{name:'set_base_production',event_id:'0_69',caller:0,success:true,data:{choice_id:'FORMERS'}}}];
  return{records,setup};
}

test('production bootstrap binds native publication to ordered current-turn ACKs and exact stock home launch',async()=>{
  const {verifySeaBootstrap}=await import('./terraform-sea-height-observation.mjs');
  const {records,setup}=bootstrap();const before=structuredClone({records,setup});
  assert.equal(verifySeaBootstrap(records,setup).production_acknowledgements.length,1);assert.deepEqual({records,setup},before);
});

test('production bootstrap rejects early resumption missing ACKs and undeclared stock/income changes',async()=>{
  const {verifySeaBootstrap}=await import('./terraform-sea-height-observation.mjs');
  for(const mutate of [
    r=>r.records.unshift(r.records.pop()),r=>r.records.splice(2,1),
    r=>r.records[3].value.data.minerals=0,r=>r.records[3].value.caller=1,r=>r.records[3].value.data.turn_id=2,
    r=>r.setup.declared.restored.cost=80,r=>r.setup.declared.restored.minerals=83,
    r=>r.records[2].value.production.minerals=3,r=>r.setup.production.minerals=3,
    r=>r.records[2].value.home_id=2,r=>r.records[2].value.x=10,r=>r.records[2].value.home_population=0,
    r=>r.setup.declared.recipe.weapon_mode=0,r=>r.setup.declared.recipe.source_components.chassis=0,
    r=>r.records[0].value.actual_prefill.minerals=42,r=>r.records[1].value.bases[1].production.last_processed_turn=0,
    r=>r.setup.base_states[6].production.last_processed_turn=0,
  ]){const row=bootstrap();mutate(row);assert.throws(()=>verifySeaBootstrap(row.records,row.setup));}
});

test('production bootstrap preserves the exact preturn base-to-owner mapping',async()=>{
  const {verifySeaBootstrap}=await import('./terraform-sea-height-observation.mjs');
  for(const mutate of [
    row=>row.setup.base_states[6].base_id=70,
    row=>row.records[1].value.bases[6].base_id=70,
    row=>{[row.setup.base_states[5].owner,row.setup.base_states[6].owner]=[6,5];},
  ]){
    const row=bootstrap();mutate(row);
    assert.throws(()=>verifySeaBootstrap(row.records,row.setup));
  }
  const reordered=bootstrap();reordered.setup.base_states.reverse();
  assert.equal(verifySeaBootstrap(reordered.records,reordered.setup).production_acknowledgements.length,1);
});
