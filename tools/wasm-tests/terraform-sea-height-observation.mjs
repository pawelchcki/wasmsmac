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

