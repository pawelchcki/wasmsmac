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
