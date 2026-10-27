// Metadata preparation only: reads declared source/runtime/input bytes without
// evaluating scripts, loading WASM, creating a browser, or claiming native state.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {existsSync,mkdirSync,readFileSync,readdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {declaredTerrain,fixtureSources,rateOneSource} from './terraform-browser-inputs.mjs';
const sha=value=>createHash('sha256').update(value).digest('hex');

export function terrainOverrideTable(original,executed){
  const rows=bytes=>{let active=false;const out=[];
    for(const[line,text]of bytes.toString('latin1').split('\n').entries()){
      const trimmed=text.trim();if(trimmed==='#TERRAIN'){active=true;continue;}
      if(active&&trimmed.startsWith('#'))break;
      if(active&&trimmed&&!trimmed.startsWith(';'))out.push({line:line+1,fields:text.split(';')[0].trimEnd().split(',').map(field=>field.trim())});
    }return out;};
  const before=rows(original),after=rows(executed);assert.equal(before.length,20);assert.equal(after.length,20);
  return before.map((row,index)=>{
    const next=after[index];assert.equal(row.line,next.line);assert.equal(row.fields.length,next.fields.length);
    for(let field=0;field<row.fields.length;field++)if(field!==4)assert.equal(row.fields[field],next.fields[field],'Only shared duration input may change');
    assert.match(row.fields[4],/^\d+$/);assert.equal(next.fields[4],'1');
    return{row:index,line:row.line,land_name:row.fields[0],land_prerequisite:row.fields[1],sea_name:row.fields[2],sea_prerequisite:row.fields[3],
      field:'shared_turns',field_index:4,old:Number(row.fields[4]),new:1,applies_to:['land','sea']};
  });
}

export function buildHeightPreflight({source,runtimeJS,runtimeWasm,originalRules,executedRules,map,main,world,helpers,seed}){
  assert.ok(Buffer.isBuffer(map));assert.equal(map.subarray(0,11).toString('binary'),'TERRANMAP\0\x1a');
  for(const key of ['head','native_tree','default_tree'])assert.match(source[key],/^[0-9a-f]{40}$/);
  const width=map.readUInt32LE(15),height=map.readUInt32LE(19),tiles=map.readUInt32LE(35);
  return{version:1,kind:'terraform-height-producer-preflight.v1',candidate_executed:false,phase:'before-native-launch',
    head:source.head,native_tree:source.native_tree,default_tree:source.default_tree,
    runtime:{js:sha(runtimeJS),wasm:sha(runtimeWasm)},original_rules_sha256:sha(originalRules),executed_rules_sha256:sha(executedRules),
    override_table:terrainOverrideTable(originalRules,executedRules),source_sha256:source.files,
    input_sha256:{main:sha(main),world:sha(world),helpers:sha(JSON.stringify(helpers)),map:sha(map)},
    production_default_sha256:source.production_default_sha256,
    declared_map:{width,height,tiles,bytes:map.length},seed_requested:seed,browser_budget_ms:180000,
    native_policy_observation:'not available before launch; require actual TH_INPUTS and every retained native world in the auditor'};
}

export function loadHeightPreflight({scriptsRoot,build,assets,seed,driverPath=resolve(scriptsRoot,'tools/wasm-tests/terraform-height-browser.test.mjs')}){
  const read=name=>readFileSync(resolve(scriptsRoot,name));
  const main=read('tools/wasm-tests/fixtures/terraform-height-main.gls.js'),world=fixtureSources(scriptsRoot,{water:false}).world;
  const names=['_state_trace_observer','_terrain_trace_observer','_terraform_cooperation_observer'];
  const helpers=Object.fromEntries(names.map(name=>[name,read(`GLSMAC_data/tests/${name}.gls.js`).toString('utf8')]));
  const files=Object.fromEntries(['tools/wasm-tests/terraform-height-observation.mjs','tools/wasm-tests/terraform-browser-inputs.mjs',
    'tools/wasm-tests/fixtures/terraform-height-main.gls.js','tools/wasm-tests/fixtures/terraform-controls-world.gls.js',
    'tools/wasm-tests/browser-log-cursor.mjs','tools/wasm-tests/browser-native-log-hook.mjs','tools/wasm-tests/runtime-fetch-barrier.mjs',
    'tools/wasm-tests/terraform-browser-geometry.mjs','tools/wasm-tests/terraform-browser-pointer.mjs',
    ...names.map(name=>`GLSMAC_data/tests/${name}.gls.js`)].map(name=>[name,sha(read(name))]));
  assert.equal(files['tools/wasm-tests/terraform-browser-inputs.mjs'],sha(readFileSync(new URL('terraform-browser-inputs.mjs',import.meta.url))),'Executed input helper differs from declared source root');
  files['executed_node_driver']=sha(readFileSync(driverPath));files['preflight_producer']=sha(readFileSync(fileURLToPath(import.meta.url)));
  const scripts=Object.fromEntries(readdirSync(resolve(scriptsRoot,'GLSMAC_data/default'),{recursive:true}).filter(name=>name.endsWith('.gls.js')).sort()
    .map(name=>[`GLSMAC_data/default/${name}`,read(`GLSMAC_data/default/${name}`).toString('utf8')]));
  const rev=ref=>execFileSync('git',['rev-parse',ref],{cwd:scriptsRoot,encoding:'utf8'}).trim();
  const originalRules=readFileSync(resolve(assets,'alphax.txt')),executedRules=rateOneSource(originalRules),map=declaredTerrain();
  const record=buildHeightPreflight({source:{head:rev('HEAD'),native_tree:rev('HEAD:src'),default_tree:rev('HEAD:GLSMAC_data/default'),files,production_default_sha256:sha(JSON.stringify(scripts))},
    runtimeJS:readFileSync(resolve(build,'GLSMAC.js')),runtimeWasm:readFileSync(resolve(build,'GLSMAC.wasm')),originalRules,executedRules,map,main,world,helpers,seed});
  return{record,main,world,map};
}

export function writeHeightPreflight({artifacts,record,main,world,map,report}){
  if(report){
    for(const[reportKey,value]of Object.entries({host_head:record.head,native_source_tree:record.native_tree,default_tree:record.default_tree,
      runtime_js_sha256:record.runtime.js,runtime_wasm_sha256:record.runtime.wasm,observer_sha256:record.input_sha256.main,
      world_input_sha256:record.input_sha256.world,observer_helpers_sha256:record.input_sha256.helpers,
      production_default_sha256:record.production_default_sha256,seed_requested:record.seed_requested,driver_sha256:record.source_sha256.executed_node_driver}))assert.equal(report[reportKey],value,`Preflight differs from actual capture snapshot: ${reportKey}`);
    assert.equal(report.height_observation_sha256,record.source_sha256['tools/wasm-tests/terraform-height-observation.mjs']);
    for(const[name,digest]of Object.entries(report.shared_helpers_sha256))assert.equal(record.source_sha256[`tools/wasm-tests/${name}`],digest,`Executed shared helper differs: ${name}`);
    assert.equal(report.source_override.original_sha256,record.original_rules_sha256);assert.equal(report.source_override.rate_one_sha256,record.executed_rules_sha256);
  }
  mkdirSync(artifacts,{recursive:true});
  const text=JSON.stringify(record,null,2)+'\n';
  // An identical preparation may be consumed by the later capture. Never
  // relabel or overwrite a historical/different preflight or fixture artifact.
  for(const[name,bytes]of [['preflight.json',text],['fixture-main.gls.js',main],['fixture-world.gls.js',world],['fixture-map.MP',map]]){
    const path=resolve(artifacts,name),buffer=Buffer.from(bytes);
    if(existsSync(path))assert.deepEqual(readFileSync(path),buffer,`Refusing to overwrite different ${name}`);
    else writeFileSync(path,buffer,{flag:'wx'});
  }
  return sha(text);
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const args=process.argv.slice(2),options={};
  assert.equal(args.length%2,0,'Expected --scripts-root/--app-dir/--assets-dir/--artifacts-dir pairs');
  const keys={'--scripts-root':'scriptsRoot','--app-dir':'build','--assets-dir':'assets','--artifacts-dir':'artifacts'};
  for(let i=0;i<args.length;i+=2){assert.ok(keys[args[i]]);assert.equal(options[keys[args[i]]],undefined);options[keys[args[i]]]=resolve(args[i+1]);}
  for(const key of Object.values(keys))assert.ok(options[key],`Missing ${key}`);
  const prepared=loadHeightPreflight({...options,seed:'1651011033:1377505029:3019448108:3247278135'});
  const digest=writeHeightPreflight({...options,...prepared});
  console.log(JSON.stringify({candidate_executed:false,preflight_sha256:digest,path:resolve(options.artifacts,'preflight.json')}));
}
