// Actual native DOM regression: late epochs and real property-store ordering.
import assert from 'node:assert/strict';
import test from 'node:test';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {readFileSync,readdirSync,mkdirSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {chromium} from '../../wasm-tests/node_modules/playwright/index.mjs';
const root=fileURLToPath(new URL('../../../',import.meta.url));
const build=process.env.WASM_APP_DIR,assets=process.env.SMAC_ASSETS_DIR;
const hash=value=>createHash('sha256').update(value).digest('hex');

test('actual late UI epoch preserves focus/modal and records each property store in causal order',{
 skip:!build||!assets,timeout:120000,
},async t=>{
 const artifacts=process.env.PRESENTATION_ARTIFACTS||'/tmp/presentation-native-ui';mkdirSync(artifacts,{recursive:true});
 const production=Object.fromEntries(readdirSync(`${root}GLSMAC_data/default`,{recursive:true}).filter(name=>name.endsWith('.gls.js')).sort().map(name=>[name,readFileSync(`${root}GLSMAC_data/default/${name}`,'utf8')]));
 const scripts={...production};const marker='glsmac.run();';assert.equal(scripts['main.gls.js'].split(marker).length,2);
 scripts['main.gls.js']=scripts['main.gls.js'].replace(marker,marker+`
 glsmac.ui.root.timer(1000, () => {
  const ui = glsmac.ui;
  ui.presentation_trace_start();
  const input = ui.root.input({id: 'focus-before-trace', left: 20, top: 20, width: 240, height: 28, value: 'active', zindex: 0.999});
  const select = ui.root.select({id: 'modal-before-trace', left: 20, top: 70, width: 240, height: 28, zindex: 0.999,
   items: [['first', 'First choice'], ['second', 'Second choice']], itemheight: 24, itempadding: 1, value: 'first'});
  #print('UI_PROBE_READY');
  ui.root.timer(1500, () => {
   #print('UI_PROBE_BEFORE|' + ui.presentation_trace_drain());
   ui.presentation_trace_start();
   #print('UI_PROBE_BASELINE|' + ui.presentation_trace_drain());
   const text = ui.root.text({id: 'mutation-probe', left: 500, top: 30, text: 'first'});
   text.text = 'second';
   text.text = 'first';
   text.text = undefined;
   text.color = 'rgb(1,2,3)';
   #print('UI_PROBE_MUTATIONS|' + ui.presentation_trace_seal());
   #print('UI_PROBE_DONE');
   return false;
  });
  return false;
 });`);
 const server=spawn('python3',['tools/serve-wasm.py',build,'--port','0','--assets',assets],{cwd:root});let serverLog='';server.stderr.on('data',chunk=>serverLog+=chunk);t.after(()=>server.kill());
 const origin=await new Promise((resolve,reject)=>{let output='';const timer=setTimeout(()=>reject(Error(serverLog)),30000);server.on('error',reject);server.stdout.on('data',chunk=>{output+=chunk;const found=output.match(/http:\/\/127\.0\.0\.1:\d+/);if(found){clearTimeout(timer);resolve(found[0]);}});});
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});t.after(()=>browser.close());
 const page=await browser.newPage({viewport:{width:1100,height:1100}});const errors=[];page.on('pageerror',error=>errors.push(String(error)));
 await page.addInitScript(()=>{let module;window.__uiProbe=[];Object.defineProperty(window,'Module',{configurable:true,get:()=>module,set:value=>{module=value;const print=value.print;value.print=message=>{const text=String(message);const found=/(?:^|\]\s*)UI_PROBE_(BEFORE|BASELINE|MUTATIONS)\|(\{[^\r\n]*\})$/.exec(text);if(found){window.__uiProbe.push({phase:found[1],batch:JSON.parse(found[2])});}else print(message);};}});});
 try{
  await page.goto(origin);await page.waitForFunction(()=>document.body.dataset.state==='ready');await page.locator('#asset-source').selectOption('remote');await page.locator('#asset-url').fill(`${origin}/assets/manifest.json`);
  await page.evaluate(scripts=>{for(const [name,source]of Object.entries(scripts)){const path='/presentation-ui/GLSMAC_data/default/'+name;Module.FS.mkdirTree(path.slice(0,path.lastIndexOf('/')));Module.FS.writeFile(path,source);}const run=Module.callMain;Module.callMain=args=>run([...args,'--skipintro','--datapath','/presentation-ui/GLSMAC_data']);},scripts);
  await page.locator('#start').focus();await page.keyboard.press('Space');await page.waitForFunction(()=>document.body.dataset.state==='running');
  await page.waitForFunction(()=>document.querySelector('#log').textContent.includes('UI_PROBE_READY'));
  const canvas=await page.locator('#canvas').boundingBox();await page.mouse.click(canvas.x+120,canvas.y+83);
  await page.waitForFunction(()=>document.querySelector('#log').textContent.includes('UI_PROBE_DONE'));
  assert.deepEqual(errors,[]);assert.doesNotMatch(await page.locator('#log').textContent(),/FATAL ERROR|Unhandled exception|uncaught|Pthread .*sent an error!/i);
  const batches=await page.evaluate(()=>window.__uiProbe);writeFileSync(`${artifacts}/raw.json`,JSON.stringify(batches,null,2));
  const get=phase=>{const batch=batches.find(value=>value.phase===phase)?.batch;assert.ok(batch,phase);assert.equal(batch.dropped,0);return batch.events;};
  const before=get('BEFORE'),baseline=get('BASELINE'),events=get('MUTATIONS');
  const last=(values,kind)=>values.filter(event=>event.kind===kind).at(-1)?.data.node;
  const focus=last(before,'ui.focus'),modal=last(before,'ui.modal');assert.ok(focus,'fixture really focused a native input before restart');assert.ok(modal,'trusted click really opened native global singleton before restart');
  const created=baseline.filter(event=>event.kind==='node.create').map(event=>event.target);
  const target=id=>events.find(event=>event.kind==='node.property'&&event.data.key==='id'&&event.data.value===id)?.target;
  const text=target('mutation-probe');assert.ok(text);
  const properties=events.filter(event=>event.target===text&&event.kind==='node.property'&&event.data.key==='text');
  const propertyB=properties.find(event=>event.data.value==='second'),paintB=events.find(event=>event.target===text&&event.kind==='node.property'&&event.data.key==='rendered_text'&&event.data.value==='second');
  const unset=events.find(event=>event.target===text&&event.kind==='node.unset'&&event.data.key==='text'),empty=events.find(event=>event.target===text&&event.kind==='node.property'&&event.data.key==='rendered_text'&&event.data.value==='');
  const report={runtime_js_sha256:hash(readFileSync(`${build}/GLSMAC.js`)),runtime_wasm_sha256:hash(readFileSync(`${build}/GLSMAC.wasm`)),source_sha256:hash(JSON.stringify(production)),fixture_sha256:hash(JSON.stringify(scripts)),
   expected_focus:focus,expected_modal:modal,focus: last(baseline,'ui.focus')??null,modal:last(baseline,'ui.modal')??null,
   duplicate_births:created.length-new Set(created).size,text_property_values:properties.map(event=>event.data.value),nullable_records:events.filter(event=>event.target===text&&event.kind==='node.property'&&event.data.key==='color').length,
   store_before_paint:Boolean(propertyB&&paintB&&propertyB.seq<paintB.seq),unset_before_clear:Boolean(unset&&empty&&unset.seq<empty.seq)};
  writeFileSync(`${artifacts}/report.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report));
  assert.deepEqual({focus:report.focus,modal:report.modal,duplicate_births:report.duplicate_births,text_property_values:report.text_property_values,nullable_records:report.nullable_records,store_before_paint:report.store_before_paint,unset_before_clear:report.unset_before_clear},
   {focus,modal,duplicate_births:0,text_property_values:['first','second','first'],nullable_records:1,store_before_paint:true,unset_before_clear:true});
 }finally{writeFileSync(`${artifacts}/application.log`,await page.locator('#log').textContent().catch(()=>''));writeFileSync(`${artifacts}/server.log`,serverLog);}
});
