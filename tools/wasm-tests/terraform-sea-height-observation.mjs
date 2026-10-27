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
  const rows=kind=>records.map((row,index)=>({...row,index})).filter(row=>row.kind===kind);
  const births=rows('TH_SEA_BIRTH'),accounting=rows('TH_SEA_ACCOUNTING'),turns=rows('TH_SEA_PRETURN');
  const receipts=rows('TH_RECEIPT'),productions=receipts.filter(row=>row.value.name==='process_base_production');
  const growth=receipts.filter(row=>row.value.name==='process_base_growth'),resumed=receipts.filter(row=>row.value.name==='set_base_production');
  assert.equal(births.length,1);assert.equal(accounting.length,1);assert.equal(turns.length,1);
  assert.equal(productions.length,1);assert.equal(growth.length,7);assert.equal(resumed.length,1);
  const birth=births[0].value,actual=accounting[0].value,preturn=turns[0].value;
  const recipe=setup.declared.recipe,restored=setup.declared.restored,resume=resumed[0].value;
  assert.equal(setup.declared.version,2);assert.equal(recipe.id,'SeaFormers');assert.equal(recipe.application_recipe,'foil-terraform-module-v1');
  assert.equal(recipe.weapon_mode,9);assert.equal(recipe.movement_type,'water');assert.equal(recipe.rows,5);
  assert.equal(recipe.source_components.chassis,3);assert.equal(recipe.source_components.prototype,null);
  assert.equal(restored.cost,40);assert.equal(restored.minerals,43);assert.equal(restored.last_processed_turn,0);assert.equal(restored.population,1);
  assert.equal(actual.version,2);assert.equal(actual.base_id,setup.home_id);assert.equal(actual.owner,0);assert.equal(actual.turn,1);
  assert.equal(actual.observed_choice_cost,40);assert.equal(actual.requested_stock,43);assert.equal(actual.population_cost,0);assert.equal(actual.population,1);
  assert.equal(actual.choice_id,recipe.choice);assert.deepEqual(actual.source_recipe,recipe);
  assert.deepEqual(actual.actual_prefill,{choice_id:recipe.choice,minerals:43,last_processed_turn:0});
  assert.ok(accounting[0].index<turns[0].index&&turns[0].index<births[0].index&&births[0].index<productions[0].index);
  const states=(list)=>{assert.equal(list.length,7);assert.equal(new Set(list.map(row=>row.base_id)).size,7);assert.deepEqual(list.map(row=>row.owner).sort((a,b)=>a-b),[0,1,2,3,4,5,6]);};
  assert.equal(preturn.version,2);assert.equal(preturn.turn,1);assert.equal(preturn.home_id,setup.home_id);states(preturn.bases);states(setup.base_states);
  const identities=list=>list.map(({base_id,owner})=>({base_id,owner})).sort((a,b)=>a.base_id-b.base_id);
  assert.deepEqual(identities(setup.base_states),identities(preturn.bases),'Production preserves each actual base ID and owner');
  assert.equal(Math.min(...preturn.bases.map(row=>row.base_id)),setup.home_id);
  for(const row of preturn.bases){
    const local=row.base_id===setup.home_id;assert.equal(row.owner===0,local);assert.equal(row.population,1);
    assert.deepEqual(row.production,{choice_id:local?recipe.choice:setup.declared.resumed_choice,minerals:local?43:0,last_processed_turn:local?0:1});
    assert.equal(row.eligible,local);assert.equal(row.intake.MINERALS,1);assert.equal(row.consumption.MINERALS,0);
    assert.equal(row.intake.NUTRIENTS,2);assert.equal(row.consumption.NUTRIENTS,2);
  }
  for(const row of setup.base_states){
    assert.equal(row.population,1);assert.equal(row.owner===0,row.base_id===setup.home_id);
    assert.deepEqual(row.production,{choice_id:setup.declared.resumed_choice,minerals:row.base_id===setup.home_id?4:0,last_processed_turn:1});
  }
  for(const row of [...productions,...growth]){
    assert.ok(row.index<resumed[0].index,'Current-turn work ACK precedes normal project resumption');
    assert.equal(row.value.success,true);assert.equal(row.value.caller,0);assert.equal(row.value.data.turn_id,1);
    assert.equal(typeof row.value.event_id,'string');assert.ok(row.value.event_id.length>0);
  }
  for(const row of growth)assert.ok(row.index>productions[0].index);
  assert.equal(productions[0].value.data.minerals,1);
  assert.equal(resume.success,true);assert.equal(resume.caller,0);assert.equal(resume.data.choice_id,setup.declared.resumed_choice);
  assert.equal(typeof resume.event_id,'string');assert.ok(resume.event_id.length>0);
  assert.equal(new Set([...productions,...growth,...resumed].map(row=>row.value.event_id)).size,9);
  assert.equal(birth.owner,0);assert.equal(birth.unit_id,setup.actor);assert.equal(birth.definition,recipe.id);
  assert.equal(birth.is_water,true);assert.equal(birth.can_terraform,true);assert.equal(birth.turn,1);
  assert.equal(birth.home_id,setup.home_id);assert.equal(birth.home_population,1);
  assert.equal(birth.x,8);assert.equal(birth.y,8);assert.equal(birth.movement,recipe.movement);assert.equal(birth.health,1);
  assert.deepEqual(birth.production,{choice_id:'',minerals:4,last_processed_turn:1});
  assert.deepEqual(setup.production,{choice_id:setup.declared.resumed_choice,minerals:4,last_processed_turn:1});
  return{accounting:structuredClone(actual),preturn:structuredClone(preturn),birth:structuredClone(birth),
    production_acknowledgements:productions.map(row=>structuredClone(row.value)),growth_acknowledgements:growth.map(row=>structuredClone(row.value)),
    resumption_acknowledgement:structuredClone(resume),scope:'installed source choice40+3 authored stock43; actual first-turn income1/overflow4; one eligible producer and six already-current projects; no city production UI claim'};
}
