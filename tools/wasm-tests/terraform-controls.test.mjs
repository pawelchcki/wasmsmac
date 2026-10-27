// Installed-data application proof, separate from original visual agreement.
import assert from 'node:assert/strict';
import {spawn,execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, readdirSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {chromium} from 'playwright';
import {PNG} from 'pngjs';
import {fixtureSources} from './terraform-browser-inputs.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const scriptsRoot = process.env.WASM_SCRIPTS_ROOT || root;
const build = process.env.WASM_APP_DIR || `${root}build/wasm-release/bin`;
const assets = process.env.SMAC_ASSETS_DIR;
const artifacts = process.env.TERRAFORM_CONTROLS_ARTIFACTS_DIR || `${root}tools/wasm-tests/build/artifacts/terraform-controls`;
const hash = value => createHash('sha256').update(value).digest('hex');
const initialSeed='1651011033:1377505029:3019448108:3247278135';

function terrain() {
  const width=16, height=16, count=width*height/2, offset=15+0xaa4;
  const aw=Math.ceil(width/5), ah=Math.ceil(height/5), ac=Math.floor((aw+1)/2)*ah;
  const bytes=Buffer.alloc(offset+count*44+ac);
  bytes.write('TERRANMAP\0\x1a',0,'binary'); bytes.writeUInt32LE(5,11);
  for (const [at,value] of [[0,width],[4,height],[20,count],[0xa24,aw],[0xa28,ah],[0xa2c,ac]]) bytes.writeUInt32LE(value,15+at);
  for (let i=0;i<count;++i) { bytes[offset+i*44]=96; bytes[offset+i*44+1]=64; }
  return bytes;
}

const {world,main}=fixtureSources(scriptsRoot,{water:false});

test('complete Terraform menu and actual target pointer lifecycle preserve seven-owner world', {
  skip: !assets && 'Requires installed SMAC assets', timeout: 180000,
}, async t => {
  mkdirSync(artifacts,{recursive:true});
  const scripts=Object.fromEntries(readdirSync(`${scriptsRoot}/GLSMAC_data/default`,{recursive:true}).filter(n=>n.endsWith('.gls.js')).sort()
    .map(n=>[`GLSMAC_data/default/${n}`,readFileSync(`${scriptsRoot}/GLSMAC_data/default/${n}`,'utf8')]));
  const observer=readFileSync(`${scriptsRoot}/GLSMAC_data/tests/_state_trace_observer.gls.js`,'utf8');
  const terrainObserver=readFileSync(`${scriptsRoot}/GLSMAC_data/tests/_terrain_trace_observer.gls.js`,'utf8');
  const cooperationObserver=readFileSync(`${scriptsRoot}/GLSMAC_data/tests/_terraform_cooperation_observer.gls.js`,'utf8');
  const report={version:1,scope:'source-declared Terraform controls and native pointer target application invariants',
    original_visual_agreement:'unsupported', original_passing_cases:0,
    candidate_executed:false,status:'running',
    host_head:execFileSync('git',['rev-parse','HEAD'],{cwd:scriptsRoot,encoding:'utf8'}).trim(),
    native_source_tree:execFileSync('git',['rev-parse','HEAD:src'],{cwd:scriptsRoot,encoding:'utf8'}).trim(),
    initial_seed_requested:initialSeed,seed_binding:'existing Game.Start quickstart-seed path; no public live RNG-state getter',
    scripts_sha256:hash(JSON.stringify(scripts)),runtime_sha256:hash(readFileSync(`${build}/GLSMAC.wasm`)),
    runtime_js_sha256:hash(readFileSync(`${build}/GLSMAC.js`)),
    fixture_sha256:hash(world+main+observer+terrainObserver+cooperationObserver),
    scripts_root:scriptsRoot,fixture_sources:{world:hash(world),main:hash(main),state_observer:hash(observer),terrain_observer:hash(terrainObserver),cooperation_observer:hash(cooperationObserver)},
    declared_input:{world:'all-seven nonempty controlled16x16',normal_policy:'default-ignore-technologies',source_rates:'unchanged-installed',unit_ownership:'actual-local-native-player'},native_snapshots:[],
    web_sha256:Object.fromEntries(['index.html','bootstrap.js','asset-store.js'].map(name=>[name,hash(readFileSync(`${build}/${name}`))])),
    component_sha256:hash(readFileSync(`${assets}/VT.cvr`)), captures:[]};
  const server=spawn('python3',['tools/serve-wasm.py',build,'--port','0','--assets',assets],{cwd:root});
  t.after(()=>server.kill());
  const address=await new Promise((resolve,reject)=>{
    let log=''; const timer=setTimeout(()=>reject(Error(`Asset server timeout: ${log}`)),60000);
    server.stderr.on('data',d=>{log+=d;}); server.once('error',reject);
    server.once('exit',code=>{clearTimeout(timer);reject(Error(`Asset server exited ${code}: ${log}`));});
    server.stdout.on('data',data=>{const match=String(data).match(/http:\/\/127\.0\.0\.1:\d+/);if(match){clearTimeout(timer);resolve(match[0]);}});
  });
  const browser=await chromium.launch({headless:true,executablePath:process.env.WASM_BROWSER_EXECUTABLE||undefined,
    args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  const page=await browser.newPage({viewport:{width:1100,height:1000}}); page.setDefaultTimeout(60000);
  const errors=[]; page.on('pageerror',error=>errors.push(error.stack||String(error))); page.on('crash',()=>errors.push('Chromium crashed'));
  t.after(async()=>{try{if(report.status!=='passed')report.status='failed-or-incomplete';
    try{writeFileSync(`${artifacts}/application.log`,await page.locator('#log').textContent({timeout:1000}));}
    catch(error){report.log_capture_error=String(error);}
    if(report.status!=='passed'){try{await page.locator('#canvas').screenshot({path:`${artifacts}/failed-frame.png`,timeout:1000});}catch(error){report.frame_capture_error=String(error);}}
    writeFileSync(`${artifacts}/report.json`,JSON.stringify(report,null,2)+'\n');}finally{await browser.close();}});
  const fatal=/TF_ERROR|Unhandled exception|Uncaught|Unsupported image format|Assertion failed|Aborted\(|RuntimeError:|(?:worker|Pthread[^\n]*) sent an error!|\[Error\]/i;
  const waitLog=async marker=>{await page.waitForFunction(({marker,fatal})=>document.querySelector('#log').textContent.includes(marker)||new RegExp(fatal).test(document.querySelector('#log').textContent)||document.body.dataset.state==='failed',{marker,fatal:fatal.source});
    assert.doesNotMatch(await page.locator('#log').textContent(),fatal);assert.deepEqual(errors,[]);};
  await page.goto(address); await page.waitForFunction(()=>document.body.dataset.state==='ready');
  const manifest=await (await page.request.get(`${address}/assets/manifest.json`)).json();
  const entry=manifest.files.find(row=>row.path==='VT.cvr'); assert.ok(entry,'Real manifest must include the CVR resource');
  assert.equal(entry.sha256,report.component_sha256); report.manifest_id=manifest.id;
  await page.locator('#custom-maps').setInputFiles({name:'cvr-arid.MP',mimeType:'application/octet-stream',buffer:terrain()});
  await page.locator('#import-maps').click();
  await page.waitForFunction(()=>document.querySelector('#custom-map-list').textContent.includes('cvr-arid.MP'));
  await page.locator('#asset-source').selectOption('remote'); await page.locator('#asset-url').fill(`${address}/assets/manifest.json`);
  // Mount only application scripts and the synthetic world. CVR bytes enter
  // exclusively through the normal remote manifest/bridge/VFS product flow.
  await page.evaluate(({scripts,main,world,observer,terrainObserver,cooperationObserver,initialSeed})=>{
    for(const [name,source] of Object.entries(scripts)){const path=`/cvr-snapshot/${name}`;Module.FS.mkdirTree(path.slice(0,path.lastIndexOf('/')));Module.FS.writeFile(path,source);}
    Module.FS.mkdirTree('/cvr-snapshot/GLSMAC_data/tests');
    Module.FS.writeFile('/cvr-snapshot/GLSMAC_data/tests/_state_trace_observer.gls.js',observer);
    Module.FS.writeFile('/cvr-snapshot/GLSMAC_data/tests/_terrain_trace_observer.gls.js',terrainObserver);
    Module.FS.writeFile('/cvr-snapshot/GLSMAC_data/tests/_terraform_cooperation_observer.gls.js',cooperationObserver);
    Module.FS.writeFile('/cvr-snapshot/GLSMAC_data/default/browser_cvr_main.gls.js',main);
    Module.FS.writeFile('/cvr-snapshot/GLSMAC_data/default/game/world/browser_cvr.gls.js',world);
    const callMain=Module.callMain;
    Module.callMain=args=>callMain([...args,'--datapath','/cvr-snapshot/GLSMAC_data','--mainscript','browser_cvr_main','--worldscript','browser_cvr',
      '--quickstart','--quickstart-seed',initialSeed,'--quickstart-mapfile','/persist/glsmac/maps/cvr-arid.MP','--quickstart-faction','GAIANS']);
  },{scripts,main,world,observer,terrainObserver,cooperationObserver,initialSeed});
  report.candidate_executed=true; await page.locator('#start').click(); await waitLog('TF_READY');
  const log=async()=>{const value=await page.locator('#log').textContent();assert.doesNotMatch(value,fatal);assert.deepEqual(errors,[]);return value;};
  const fresh=async(prefix,action)=>{const before=(await log()).length;await action();await page.waitForFunction(({before,prefix,fatal})=>{const t=document.querySelector('#log').textContent;return t.slice(before).includes(prefix)||new RegExp(fatal).test(t);},{before,prefix,fatal:fatal.source});return(await log()).slice(before);};
  const lines=(text,prefix)=>text.split('\n').filter(line=>line.includes(prefix)).map(line=>line.slice(line.indexOf(prefix)+prefix.length).trim());
  const state=async()=>{const text=await fresh('TF_STATE|',async()=>{});const line=lines(text,'TF_STATE|').at(-1);return JSON.parse(line.slice(line.indexOf('|')+1));};
  const snapshot=async checkpoint=>{const text=await fresh('TF_NATIVE|',()=>page.keyboard.press('Control+Alt+p'));const value=JSON.parse(lines(text,'TF_NATIVE|').at(-1));report.native_snapshots.push({checkpoint,value});return value;};
  const nativeOnly=value=>{const copy=structuredClone(value);delete copy.terrain_trace.ui;return copy;};
  const point=async(x,y)=>{const box=await page.locator('#canvas').boundingBox();return{x:box.x+box.width*x/1024,y:box.y+box.height*y/768};};
  const click=async(x,y)=>{const p=await point(x,y);await page.mouse.click(p.x,p.y);};
  const setup=await fresh('TF_BASE_POINT|',()=>page.keyboard.press('Control+Alt+k'));
  const basePoint=JSON.parse(lines(setup,'TF_BASE_POINT|').at(-1));
  const selected=await state();assert.equal(selected.selected,selected.actor);
  // Native start_ui precedes browser rendering. Await actual nonblank HUD
  // pixels within the existing startup budget, without extra gameplay input.
  const startupDeadline=performance.now()+60000;let hud;report.rendered_readiness=[];
  do{const bytes=await page.locator('#canvas').screenshot();const frame=PNG.sync.read(bytes);
    let visible=0;const colors=new Set();
    for(let y=576;y<642;y++)for(let x=6;x<132;x++){const at=(y*frame.width+x)*4;const rgb=frame.data.subarray(at,at+3);if(rgb.some(v=>v!==0)){visible++;colors.add([...rgb].join(','));}}
    hud={visible,distinct_rgb:colors.size,width:frame.width,height:frame.height};report.rendered_readiness.push(hud);
    if(visible>100&&colors.size>3)break;
  }while(performance.now()<startupDeadline);
  assert.ok(hud.visible>100&&hud.distinct_rgb>3,'Actual production HUD must render before the first pointer input');
  const initial=await snapshot('before-controls');
  await page.locator('#canvas').screenshot({path:`${artifacts}/before-controls.png`});
  assert.equal(initial.players.length,7);assert.equal(initial.bases.length,7);assert.equal(initial.units.length,8);assert.equal(Object.keys(initial.terrain_trace.tiles).length,128);
  for(const player of initial.players){assert.ok(initial.bases.some(base=>base.owner===player.id));assert.ok(initial.units.some(unit=>unit.owner===player.id));}
  assert.deepEqual(initial.terrain_trace.policy,{version:1,ignore_technologies:true});
  await click(65,539);let text=await fresh('TF_POINT|header|',async()=>{});
  const header=lines(text,'TF_POINT|header|').at(-1).split('|').map(Number);await click(...header);
  text=await fresh('TF_ROWS|',async()=>{});const rows=JSON.parse(lines(text,'TF_ROWS|').at(-1));
  assert.equal(rows.length,29);assert.equal(new Set(rows.map(row=>row.id)).size,29);
  assert.ok(rows.find(row=>row.id==='soil_enricher'));assert.ok(rows.find(row=>row.id==='mag_tube'));
  assert.equal(rows.filter(row=>row.id==='monolith').length,0);
  for(const row of rows){assert.ok(row.x>=0&&row.x<=1024&&row.y>=0&&row.y<=768,`reachable ${row.id}`);}
  report.rows=rows;await page.locator('#canvas').screenshot({path:`${artifacts}/complete-menu.png`});
  const road=rows.find(row=>row.id==='road_to');assert.ok(road.enabled);await click(road.x,road.y);
  let current=await state();assert.equal(current.target.command,'road_to');assert.equal(current.modal,false);
  text=await fresh('TF_TILE|',()=>click(basePoint.x+100,basePoint.y+100));
  report.rejected_pointer=JSON.parse(lines(text,'TF_TILE|').at(-1));
  assert.notEqual(report.rejected_pointer.base_owner,selected.owner,'The declared rejection pointer must hit an empty or foreign-owned tile');
  current=await state();assert.ok(current.target,'Non-owned pointer must keep the owned-base picker active');
  await page.keyboard.press('Escape');current=await state();assert.equal(current.target,null);assert.equal(current.modal,false);
  let after=await snapshot('after-pointer-Escape');assert.deepEqual(nativeOnly(after),nativeOnly(initial),'Menu/non-owned target/Escape must preserve every observed owner/tile');
  await page.keyboard.press('Control+r');current=await state();assert.equal(current.target.command,'road_to');
  await page.keyboard.press('Tab');current=await state();assert.equal(current.target,null);assert.equal(current.modal,false);
  after=await snapshot('after-target-Tab');assert.deepEqual(nativeOnly(after),nativeOnly(initial),'Target Tab cancellation must preserve native state');
  await page.keyboard.press('Control+Alt+k');await page.waitForTimeout(300);
  await page.keyboard.press('Control+r');current=await state();assert.equal(current.target.command,'road_to');
  text=await fresh('TF_RESULT|unit_terraform_plan|true|',()=>click(basePoint.x,basePoint.y));
  const result=JSON.parse(lines(text,'TF_RESULT|unit_terraform_plan|true|').at(-1));
  assert.equal(result.command,'road_to');assert.equal(result.target_x,0);assert.equal(result.target_y,2);
  await page.waitForTimeout(300);current=await state();assert.equal(current.target,null);assert.equal(current.pending,null);
  report.final_state=current;await snapshot('after-owned-base-request');
  const ledger=await fresh('TF_INPUT|',()=>page.keyboard.press('Control+Alt+i'));
  report.input_ledger=JSON.parse(JSON.parse(lines(ledger,'TF_INPUT|').at(-1)));
  assert.equal(report.input_ledger.enabled,true);assert.equal(report.input_ledger.dropped,0,'Native input observer must remain complete');
  assert.ok(report.input_ledger.events.some(event=>event.kind==='input.ingress'),'Actual SDL input ingress must be recorded');
  assert.ok(report.input_ledger.events.some(event=>event.kind==='input.dispatch'),'Actual engine input dispatch must be recorded');
  report.native_guards='Seven actual owners/cities and complete128tile map unchanged for open/non-owned-click/Escape/Tab; owned-base pointer submitted one actual authoritative plan';
  report.unsupported=['full36actioneffects','heightquote/payment','sea-controls','originalvisualagreement','animation/audio','livebrowserRNGstate','typedfrontendmesh/facing/frame telemetry'];
  await page.locator('#canvas').screenshot({path:`${artifacts}/target-submitted.png`});
  await page.keyboard.press('Control+Alt+q');await page.waitForFunction(()=>document.body.dataset.state==='exited');assert.deepEqual(errors,[]);report.status='passed';
});
