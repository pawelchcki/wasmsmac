import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import {RuntimeFetchEvidence} from './runtime-fetch-barrier.mjs';
const actual=JSON.parse(readFileSync(new URL('./fixtures/runtime-request-observations.json',import.meta.url)));
const normalize=e=>({requestId:e.request_id,request:{url:e.url},type:e.type,frameId:e.frame_id,loaderId:e.loader_id,initiator:e.initiator});
const main=normalize(actual.main),worker=normalize(actual.worker);
const pause=(event,id)=>({requestId:id,networkId:event.requestId,request:{url:event.request.url},resourceType:event.type,frameId:event.frameId});
function fixture(){const bootstrap=main.initiator.stack.callFrames[0].url;const e=new RuntimeFetchEvidence(main.request.url,bootstrap);e.frameNavigated({id:main.frameId,loaderId:main.loaderId,url:new URL('/',bootstrap).href});return e;}
function install(e){e.networkRequest(main);const p=pause(main,'declared-Fetch-main');const role=e.classify(p);e.consume(p,role);return role;}
test('actual main and dedicated-worker Network/Target records link by exact declared Fetch networkId',()=>{
 const e=fixture();assert.equal(install(e).kind,'main');e.targetCreated(actual.target);e.networkRequest(worker);
 const p=pause(worker,'declared-Fetch-worker');const role=e.classify(p);assert.equal(role.kind,'worker');assert.equal(role.network_id,actual.target.targetId);e.consume(p,role);
 assert.throws(()=>e.classify(p),/already consumed/);
 assert.throws(()=>e.classify({...p,requestId:'different-pause-same-network'}),/already consumed/);
});
test('Network, frame and target event ordering waits for positive evidence, never same-URL FIFO',()=>{
 const e=new RuntimeFetchEvidence(main.request.url,main.initiator.stack.callFrames[0].url),p=pause(main,'main');assert.equal(e.classify(p),null);
 e.networkRequest(main);assert.equal(e.classify(p),null);e.frameNavigated({id:main.frameId,loaderId:main.loaderId,url:'declared'});e.consume(p,e.classify(p));
 const wp=pause(worker,'worker');e.networkRequest(worker);assert.equal(e.classify(wp),null);
 e.targetCreated({...actual.target,targetId:'different-worker-same-url',url:worker.request.url});assert.equal(e.classify(wp),null);
 e.targetCreated(actual.target);assert.equal(e.classify(wp).target_id,actual.target.targetId);
});
test('missing IDs, wrong frames/targets and unknown initiators cannot authorize main installation',()=>{
 for(const kind of ['missing-id','subframe','wrong-parent','shared-worker','unknown']){
  const e=fixture();install(e);e.networkRequest(worker);const p=pause(worker,'worker');
  if(kind==='missing-id')delete p.networkId;
  if(kind==='subframe')p.frameId='foreign-frame';
  if(kind==='wrong-parent')e.targetCreated({...actual.target,parentFrameId:'foreign-frame'});
  if(kind==='shared-worker')e.targetCreated({...actual.target,type:'shared_worker'});
  if(kind==='unknown'){assert.equal(e.classify(p),null);assert.throws(()=>e.consume(p,{kind:'worker'}));continue;}
  assert.throws(()=>e.classify(p));
 }
});
test('destroyed targets, navigation and repeated main runtime fail closed',()=>{
 const e=fixture();install(e);e.networkRequest(worker);e.targetCreated(actual.target);e.targetDestroyed(actual.target.targetId);
 e.targetChanged(actual.target);assert.throws(()=>e.classify(pause(worker,'worker')),/destroyed/);assert.throws(()=>e.targetCreated(actual.target),/resurrected/);
 const reload={...main,requestId:'second-main'};e.networkRequest(reload);assert.throws(()=>e.classify(pause(reload,'reload')),/only once/);
 const changed=fixture();install(changed);changed.networkRequest(worker);changed.targetCreated(actual.target);changed.frameNavigated({id:main.frameId,loaderId:'new-document',url:'declared'});assert.throws(()=>changed.classify(pause(worker,'old-worker')),/Navigation invalidates/);
});
