// Full native allowed-diff audit for the authored sea-preserving Raise case.
// Shared observation/input/finalization helpers are reused unchanged.
import assert from 'node:assert/strict';
import {nativeHeightWorld} from './terraform-height-observation.mjs';

export function auditPaidSeaHeight(beforeRecord,afterRecord,quote){
  const before=nativeHeightWorld(beforeRecord),after=nativeHeightWorld(afterRecord),expected=structuredClone(before);
  const payer=before.players.find(row=>row.raw_id===quote.owner);assert.ok(payer);
  const actor=expected.units.find(row=>row.raw_id===quote.unit_id);assert.ok(actor);
  assert.equal(quote.source_water,true);assert.equal(quote.destination_water,true);
  actor.movement=0;actor.order='NO_ORDERS';
  const details=expected.terrain_trace.unit_details[actor.id];details.moved_this_turn=true;
  for(const value of Object.values(details.quotes))if(value!==null){value.allowed_now=false;value.reason='Unit is out of moves';}
  const energy=expected.terrain_trace.player_details[payer.id];
  assert.ok(Number.isSafeInteger(energy.energy_revision));
  energy.energy.credits-=quote.fee;energy.energy_revision++;
  const patches=new Map(quote.plan.map(patch=>[`${patch.x},${patch.y}`,patch]));
  assert.equal(patches.size,quote.plan.length);
  const region=new Set(patches.keys());
  for(const key of patches.keys())for(const point of Object.values(before.terrain_trace.tiles[key].neighbors))if(point!==null)region.add(`${point.x},${point.y}`);
  const geometryChanges=[];
  for(const key of region){
    const old=before.terrain_trace.tiles[key],actual=after.terrain_trace.tiles[key],target=expected.terrain_trace.tiles[key];assert.ok(old&&actual&&target);
    const geometryChanged=['left','top','right','bottom'].some(corner=>!Object.is(old.elevation[corner],actual.elevation[corner]));
    const patch=patches.get(key);
    if(!patch&&!geometryChanged)continue;
    // TerrainMutation.cpp renders shared vertices on the actual patch tiles
    // and their native adjacent tiles. Their numeric mesh fidelity is outside
    // this case; canonical centers/classes are still exact from the live plan.
    if(geometryChanged){
      for(const corner of ['left','top','right','bottom']){
        assert.ok(Number.isSafeInteger(actual.elevation[corner])&&actual.elevation[corner]>=-3500&&actual.elevation[corner]<=3500);
        target.elevation[corner]=actual.elevation[corner];
      }
      geometryChanges.push(key);
    }
    target.terrain_epoch=old.terrain_epoch+1;
    target.canonical.active=true;target.canonical.elevation=patch?patch.canonical.elevation:old.elevation.center;
    target.canonical.is_water=patch?patch.canonical.is_water:old.is_water;
    if(patch){
      assert.deepEqual(Object.keys(patch).sort(),['canonical','x','y'],'This sea-preserving case must not silently accept additional effect fields');
      target.elevation.center=patch.canonical.elevation;target.is_water=patch.canonical.is_water;target.is_land=!patch.canonical.is_water;
      target.native_type.domain=patch.canonical.is_water?'sea':'land';
      target.imported.active=false;target.imported.source_corners=null;target.imported.source_elevation=null;target.imported.source_water=null;
      target.native_height_band.below_coast=patch.canonical.elevation<0;
      target.native_height_band.below_ocean=patch.canonical.elevation<-1000;
      target.native_height_band.below_trench=patch.canonical.elevation<-2000;
    }
  }
  assert.deepEqual(after,expected,'Full native height world differs only at the actual payer fee/revision, actor MP/order, quoted canonical terrain and adjacent shared geometry');
  return{quoted_tiles:[...patches.keys()],adjacent_geometry_tiles:geometryChanges,payer:payer.id,actor:actor.id,scope:'exact full-world noninterference; shared corner values observed, no mesh-fidelity claim'};
}


// The birth witness reads the actual native production publication; receipts
// stay scalar-only. No nested base/unit echo is invented in event_result.
export function verifySeaBootstrap(records,setup){
  const births=records.map((row,index)=>({...row,index})).filter(row=>row.kind==='TH_SEA_BIRTH');
  const productions=records.map((row,index)=>({...row,index})).filter(row=>row.kind==='TH_RECEIPT'&&row.value.name==='process_base_production');
  const resumed=records.map((row,index)=>({...row,index})).filter(row=>row.kind==='TH_RECEIPT'&&row.value.name==='set_base_production');
  assert.equal(births.length,1);assert.equal(productions.length,7);assert.equal(resumed.length,1);
  const birth=births[0].value,recipe=setup.declared.recipe,restored=setup.declared.restored,resume=resumed[0].value;
  assert.equal(recipe.id,'SeaFormers');assert.equal(recipe.application_recipe,'foil-terraform-module-v1');
  assert.equal(recipe.weapon_mode,9);assert.equal(recipe.movement_type,'water');assert.equal(recipe.rows,8);
  assert.equal(recipe.source_components.chassis,3);assert.equal(recipe.source_components.prototype,null);
  assert.equal(restored.cost,80);assert.equal(restored.minerals,83);assert.equal(restored.last_processed_turn,0);assert.equal(restored.population,1);
  assert.ok(births[0].index<productions[0].index,'Actual production publication precedes its accepted result');
  for(const row of productions){
    assert.ok(row.index<resumed[0].index,'Every ordinary production ACK precedes project resumption');
    assert.equal(row.value.success,true);assert.equal(row.value.caller,0);assert.equal(row.value.data.turn_id,1);
    assert.equal(typeof row.value.event_id,'string');assert.ok(row.value.event_id.length>0);
  }
  // Native BM iterates ordered base IDs; the authored local producer must be
  // the first base. Its actual first-turn mineral input is a required witness,
  // not silently added to or subtracted from the declared83 stock.
  assert.equal(productions[0].value.data.minerals,0);
  assert.equal(resume.success,true);assert.equal(resume.caller,0);assert.equal(resume.data.choice_id,setup.declared.resumed_choice);
  assert.equal(typeof resume.event_id,'string');assert.ok(resume.event_id.length>0);
  assert.equal(new Set([...productions.map(row=>row.value.event_id),resume.event_id]).size,8);
  assert.equal(birth.owner,0);assert.equal(birth.unit_id,setup.actor);assert.equal(birth.definition,recipe.id);
  assert.equal(birth.is_water,true);assert.equal(birth.can_terraform,true);assert.equal(birth.turn,1);
  assert.equal(birth.home_id,setup.home_id);assert.equal(birth.home_population,1);
  assert.equal(birth.x,8);assert.equal(birth.y,8);assert.equal(birth.movement,recipe.movement);assert.equal(birth.health,1);
  assert.deepEqual(birth.production,{choice_id:'',minerals:3,last_processed_turn:1});
  assert.deepEqual(setup.production,{choice_id:setup.declared.resumed_choice,minerals:3,last_processed_turn:1});
  return{birth:structuredClone(birth),production_acknowledgements:productions.map(row=>structuredClone(row.value)),
    resumption_acknowledgement:structuredClone(resume),scope:'real production from authored83 stock; cost80/overflow3; no earned-income or city production UI claim'};
}
