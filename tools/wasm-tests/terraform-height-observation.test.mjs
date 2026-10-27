// Protocol/presentation tests only; synthetic packets are never candidate
// gameplay or original-game evidence.
import assert from 'node:assert/strict';
import {test} from 'node:test';
import {HeightPresentation,completedHeightKey,verifyHeightCapture,nativeHeightWorld} from './terraform-height-observation.mjs';
const edge=(seq,kind,data,target='node')=>({seq,kind,data,target});

test('height key receipt links raw SDL ingress to normalized completed dispatch',()=>{
  const input=[edge(3,'input.ingress',{ingress:7,type:'keydown',keycode:112,scancode:19,mod:192}),
    edge(4,'input.dispatch',{ingress:7,phase:'begin',type:'keydown',code:'P',modifiers:6}),
    edge(5,'input.dispatch',{ingress:7,phase:'end',handled:true})];
  assert.equal(completedHeightKey(input,2,'P',6).ingress.seq,3);
  assert.equal(completedHeightKey(input,3,'P',6),null);
  assert.equal(completedHeightKey(input.slice(0,2),2,'P',6),null);
  assert.equal(completedHeightKey(input,2,'P',2),null);
  const wrong=structuredClone(input);wrong[2].data.ingress=8;assert.equal(completedHeightKey(wrong,2,'P',6),null);
});

test('height close requires actual hide after the processed input fence',()=>{
  const view=new HeightPresentation();
  view.ingest({enabled:true,dropped:0,events:[edge(1,'node.create',{tag:'$window',parent:null},'dialog'),edge(2,'semantic.role',{role:'dialog',source:'game.popup.terraforming_height'},'dialog'),edge(3,'node.show',{},'dialog')]});
  assert.equal(view.dialog(),'dialog');assert.equal(view.hiddenAfter('dialog',3),false);
  view.ingest({enabled:true,dropped:0,events:[edge(4,'node.hide',{},'dialog')]});
  assert.equal(view.hiddenAfter('dialog',3),true);assert.equal(view.hiddenAfter('dialog',4),false);
  assert.throws(()=>view.dialog());
  view.ingest({enabled:true,dropped:0,events:[edge(5,'node.show',{},'dialog')]});
  assert.equal(view.hiddenAfter('dialog',3),false);
});

test('button geometry comes from one actual native label and finite effective bounds',()=>{
  const view=new HeightPresentation();
  const node=(id,seq)=>[edge(seq,'node.create',{tag:'$button',parent:null},id),edge(seq+1,'node.show',{},id),edge(seq+2,'node.property',{key:'text',value:'MENU'},id),edge(seq+3,'semantic.geometry',{area:'effective',left:12,top:14,right:80,bottom:32},id)];
  view.ingest({enabled:true,dropped:0,events:node('menu',1)});
  assert.deepEqual(view.textButton('MENU',{width:100,height:100}).bounds,{area:'effective',left:12,top:14,right:80,bottom:32});
  assert.throws(()=>view.textButton('MENU',{width:60,height:100}));
  view.ingest({enabled:true,dropped:0,events:node('other',5)});assert.throws(()=>view.textButton('MENU',{width:100,height:100}));
});

function capture(){return{query:1,query_owner:{query:1,actor:8,owner:0,turn:1,session:2,dialog_generation:3,scope:'height'},ui:{actor:8,owner:0,turn:1,session:2,dialog_generation:3,modal:true},world:{players:Array.from({length:7},(_,id)=>({id})),units:Array.from({length:8},(_,id)=>({id})),bases:Array.from({length:7},(_,id)=>({id})),terrain_trace:{policy:{version:1,ignore_technologies:true},tiles:Object.fromEntries(Array.from({length:128},(_,id)=>[String(id),{opaque:'retained'}])),ui:{native:'retained'}}}};}

test('full height capture rejects stale owner/session/query and missing player/tile coverage',()=>{
  const key={end:{data:{handled:true}}};verifyHeightCapture(capture(),0,key);
  for(const mutate of [r=>r.query_owner.session++,r=>r.query_owner.owner++,r=>r.world.players.pop(),r=>delete r.world.terrain_trace.tiles['127'],r=>r.query_owner.scope='root']){
    const row=capture();mutate(row);assert.throws(()=>verifyHeightCapture(row,0,key));
  }
  assert.throws(()=>verifyHeightCapture(capture(),1,key));
  assert.throws(()=>verifyHeightCapture(capture(),0,{end:{data:{handled:false}}}));
});

test('native-only projection removes only UI and preserves every unknown native field',()=>{
  const row=capture();row.world.unrecognized={float:-0,fields:[1,'unchanged',null]};
  const native=nativeHeightWorld(row);assert.equal(native.terrain_trace.ui,undefined);
  assert.ok(Object.is(native.unrecognized.float,-0));assert.deepEqual(native.unrecognized.fields,row.world.unrecognized.fields);
  assert.equal(row.world.terrain_trace.ui.native,'retained');
});
