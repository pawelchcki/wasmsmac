// Metadata-only tests: buffers below are synthetic protocol inputs, not a
// browser, native engine, installed-data result or substitute preflight record.
import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';
import {createHash} from 'node:crypto';
import {declaredTerrain,rateOneSource} from './terraform-browser-inputs.mjs';
import {buildHeightPreflight,writeHeightPreflight,terrainOverrideTable} from './terraform-height-preflight.mjs';
const hash=value=>createHash('sha256').update(value).digest('hex');
const data=()=>{
 const originalRules=Buffer.from('#TERRAIN\n'+Array.from({length:20},(_,i)=>`Land ${i},None,Sea ${i},Disable,12,Build,Help,R`).join('\n')+'\n#NEXT\n');
 return{source:{head:'a'.repeat(40),native_tree:'b'.repeat(40),default_tree:'c'.repeat(40),files:{executed_node_driver:'d'.repeat(64),'tools/wasm-tests/terraform-height-observation.mjs':'e'.repeat(64)},production_default_sha256:'f'.repeat(64)},
   runtimeJS:Buffer.from('not evaluated JS'),runtimeWasm:Buffer.from('not loaded WASM'),originalRules,executedRules:rateOneSource(originalRules),map:declaredTerrain(),main:'source-main',world:'source-world',helpers:{sample:'source-helper'},seed:'declared seed'};
};

test('preflight derives actual input hashes map dimensions and both-domain duration rows',()=>{
 const input=data(),record=buildHeightPreflight(input);
 assert.deepEqual(record.runtime,{js:hash(input.runtimeJS),wasm:hash(input.runtimeWasm)});
 assert.equal(record.input_sha256.world,hash(input.world));assert.equal(record.input_sha256.map,hash(input.map));
 assert.deepEqual(record.declared_map,{width:16,height:16,tiles:128,bytes:8379});
 assert.equal(record.candidate_executed,false);assert.equal(record.override_table.length,20);
 assert.deepEqual(record.override_table[16].applies_to,['land','sea']);
 assert.equal(record.override_table[16].sea_prerequisite,'Disable');assert.equal(record.override_table[16].old,12);
 assert.equal(record.native_policy_observation,'not available before launch; require actual TH_INPUTS and every retained native world in the auditor');
 assert.equal(record.policy,undefined,'Preflight cannot invent observed native policy');
});

test('fresh-directory preparation persists exactly the required reproducible artifacts',()=>{
 const folder=mkdtempSync(join(tmpdir(),'height-preflight-'));
 try{
  const input=data(),record=buildHeightPreflight(input),digest=writeHeightPreflight({artifacts:folder,record,...input});
  assert.equal(hash(readFileSync(join(folder,'preflight.json'))),digest);
  assert.deepEqual(JSON.parse(readFileSync(join(folder,'preflight.json'))),record);
  assert.equal(readFileSync(join(folder,'fixture-main.gls.js'),'utf8'),input.main);
  assert.equal(readFileSync(join(folder,'fixture-world.gls.js'),'utf8'),input.world);
  assert.deepEqual(readFileSync(join(folder,'fixture-map.MP')),input.map);
  assert.equal(writeHeightPreflight({artifacts:folder,record,...input}),digest,'Identical preparatory record is consumed unchanged');
  const different=structuredClone(record);different.runtime.js='0'.repeat(64);
  assert.throws(()=>writeHeightPreflight({artifacts:folder,record:different,...input}),/Refusing to overwrite/);
  writeFileSync(join(folder,'fixture-world.gls.js'),'historical source');
  assert.throws(()=>writeHeightPreflight({artifacts:folder,record,...input}),/Refusing to overwrite/);
 }finally{rmSync(folder,{recursive:true,force:true});}
});

test('actual producer snapshot mismatch rejects before artifact preparation',()=>{
 const input=data(),record=buildHeightPreflight(input),folder=mkdtempSync(join(tmpdir(),'height-preflight-'));
 const report={host_head:record.head,native_source_tree:record.native_tree,default_tree:record.default_tree,runtime_js_sha256:record.runtime.js,runtime_wasm_sha256:record.runtime.wasm,
  observer_sha256:record.input_sha256.main,world_input_sha256:record.input_sha256.world,observer_helpers_sha256:record.input_sha256.helpers,production_default_sha256:record.production_default_sha256,
  seed_requested:input.seed,driver_sha256:record.source_sha256.executed_node_driver,height_observation_sha256:record.source_sha256['tools/wasm-tests/terraform-height-observation.mjs'],shared_helpers_sha256:{},
  source_override:{original_sha256:record.original_rules_sha256,rate_one_sha256:record.executed_rules_sha256}};
 try{
  assert.doesNotThrow(()=>writeHeightPreflight({artifacts:folder,record,...input,report}));
  report.runtime_wasm_sha256='0'.repeat(64);assert.throws(()=>writeHeightPreflight({artifacts:folder,record,...input,report}),/capture snapshot/);
 }finally{rmSync(folder,{recursive:true,force:true});}
});

test('preflight refuses non-duration rule changes instead of fabricating provenance',()=>{
 const input=data();const changed=Buffer.from(input.executedRules.toString().replace('Sea 16','invented sea name'));
 assert.throws(()=>terrainOverrideTable(input.originalRules,changed));
 const malformed=data();malformed.map=Buffer.from(malformed.map);malformed.map[0]=0;
 assert.throws(()=>buildHeightPreflight(malformed));
});
