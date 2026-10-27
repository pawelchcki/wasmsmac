// Test-only adaptation of the audited Workshop presentation/query contract.
// Inputs come exclusively from actual native packets, never layout estimates.
import assert from 'node:assert/strict';
import {TerraformGeometry} from './terraform-browser-geometry.mjs';

export class HeightPresentation extends TerraformGeometry {
  constructor(){super();this.hidden=new Map();}
  ingest(packet){
    super.ingest(packet);
    for(const event of packet.events){
      const node=this.nodes.get(event.target);
      if(event.kind==='node.create'&&node&&node.visible===undefined)node.visible=false;
      if(event.kind==='node.show'){if(node)node.visible=true;this.hidden.delete(event.target);}
      if(event.kind==='node.hide'){if(node)node.visible=false;this.hidden.set(event.target,event.seq);}
      if(event.kind==='node.destroy')this.hidden.delete(event.target);
    }
  }
  within(id,ancestor){const seen=new Set();while(id!=null&&!seen.has(id)){if(id===ancestor)return true;seen.add(id);id=this.nodes.get(id)?.parent;}return false;}
  visible(id){const seen=new Set();while(id!=null&&!seen.has(id)){const node=this.nodes.get(id);if(!node||node.visible===false)return false;seen.add(id);id=node.parent;}return id==null;}
  hiddenAfter(id,fence){return this.nodes.has(id)&&!this.visible(id)&&(this.hidden.get(id)??0)>fence;}
  dialog(){const rows=[...this.nodes].filter(([id,node])=>node.role==='dialog'&&node.source==='game.popup.terraforming_height'&&this.visible(id));assert.equal(rows.length,1);return rows[0][0];}
  choice(index,label,viewport){
    const target=this.button('terraform-height-choice',String(index),label,viewport);
    assert.ok(this.visible(target.id)&&this.within(target.id,this.dialog()));return target;
  }
  ok(viewport){const target=this.button('terraform-height-ok','confirm','OK',viewport);assert.ok(this.visible(target.id)&&this.within(target.id,this.dialog()));return target;}
  textButton(label,viewport){
    const rows=[...this.nodes].filter(([id,node])=>node.tag==='$button'&&node.properties.text===label&&this.visible(id));
    assert.equal(rows.length,1,`Exactly one actual visible button ${label}`);
    const [id,node]=rows[0],bounds=node.effective;assert.ok(bounds);
    for(const key of ['left','top','right','bottom'])assert.ok(Number.isFinite(bounds[key]));
    assert.ok(bounds.left>=0&&bounds.top>=0&&bounds.right<=viewport.width&&bounds.bottom<=viewport.height);
    assert.ok(bounds.right>bounds.left&&bounds.bottom>bounds.top);
    return{id,label,bounds:structuredClone(bounds),x:(bounds.left+bounds.right)/2,y:(bounds.top+bounds.bottom)/2};
  }
}

// Raw SDL ingress carries keycode/scancode/mod; normalized code/modifiers
// belong to native dispatch only. The exact ingress ID links the two records.
export function completedHeightKey(events,fence,code,modifiers){
  for(const begin of events.filter(e=>e.seq>fence&&e.kind==='input.dispatch'&&e.data.phase==='begin'&&e.data.type==='keydown'&&e.data.code===code&&e.data.modifiers===modifiers)){
    const ingress=events.find(e=>e.seq>fence&&e.seq<begin.seq&&e.kind==='input.ingress'&&e.data.type==='keydown'&&e.data.ingress===begin.data.ingress);
    const end=events.find(e=>e.seq>begin.seq&&e.kind==='input.dispatch'&&e.data.phase==='end'&&e.data.ingress===begin.data.ingress);
    if(ingress&&end)return{ingress,begin,end};
  }
  return null;
}

export function nativeHeightWorld(record){const world=structuredClone(record.world);delete world.terrain_trace.ui;return world;}

export function verifyHeightCapture(record,previousQuery,key){
  assert.equal(record.query,previousQuery+1);assert.equal(key.end.data.handled,true);
  assert.equal(record.query_owner.query,record.query);assert.equal(record.query_owner.actor,record.ui.actor);
  assert.equal(record.query_owner.owner,record.ui.owner);assert.equal(record.query_owner.turn,record.ui.turn);
  assert.equal(record.query_owner.session,record.ui.session);assert.equal(record.query_owner.dialog_generation,record.ui.dialog_generation);
  assert.equal(record.query_owner.scope,record.ui.modal?'height':'root');
  assert.equal(record.world.players.length,7);assert.equal(record.world.units.length,8);assert.equal(record.world.bases.length,7);
  assert.equal(Object.keys(record.world.terrain_trace.tiles).length,128);
  assert.deepEqual(record.world.terrain_trace.policy,{version:1,ignore_technologies:true});
}
