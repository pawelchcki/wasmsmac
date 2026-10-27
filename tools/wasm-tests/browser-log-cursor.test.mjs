import assert from 'node:assert/strict';
import {test} from 'node:test';
import vm from 'node:vm';
import {BrowserLogCursor,readBrowserLogDelta} from './browser-log-cursor.mjs';

function fixture(){
 const element={textContent:''};const context=vm.createContext({document:{querySelector:()=>element},performance});
 const evaluate=vm.runInContext(`(${readBrowserLogDelta.toString()})`,context);
 return{element,context,page:{evaluate:async(fn,args)=>evaluate(args)}};
}
test('UTF-16 suffixes preserve Unicode, split surrogates and exact joined UTF-8 bytes',async()=>{
 const f=fixture(),r=new BrowserLogCursor(f.page);const chunks=['A\n','é漢','\ud83d','\ude00\n','tail'];
 for(const chunk of chunks){f.element.textContent+=chunk;const p=await r.read();assert.equal(p.text,chunk);}
 assert.equal(r.text,chunks.join(''));assert.deepEqual(Buffer.from(r.text),Buffer.from(chunks.join('')));
 assert.equal((await r.read()).text,'');assert.equal(r.reads.at(-1).transferred_utf16,0);
 assert.equal(r.reads.at(-1).end_utf16,chunks.join('').length);
});
test('concurrent polls are serialized and each original code unit transfers once',async()=>{
 const f=fixture(),r=new BrowserLogCursor(f.page);let active=0,max=0;const original=f.page.evaluate;
 f.page.evaluate=async(...args)=>{active++;max=Math.max(max,active);await new Promise(resolve=>setImmediate(resolve));const p=await original(...args);active--;return p;};
 f.element.textContent='one😀two';const packets=await Promise.all([r.read(),r.read(),r.read()]);
 assert.equal(max,1);assert.equal(packets.map(p=>p.text).join(''),'one😀two');
 assert.equal(r.reads.reduce((n,p)=>n+p.transferred_utf16,0),r.text.length);
});
test('rewrites, truncation, replacement, cursor reset and offset mismatch fail closed',async()=>{
 for(const kind of ['rewrite','truncate','replace','reset','offset']){
  const f=fixture(),r=new BrowserLogCursor(f.page);f.element.textContent='original\n';await r.read();
  if(kind==='rewrite')f.element.textContent='changed!\n';
  if(kind==='truncate')f.element.textContent='orig';
  if(kind==='replace')vm.runInContext('__terraformLogCursorV1.element={}',f.context);
  if(kind==='reset')vm.runInContext('delete globalThis.__terraformLogCursorV1',f.context);
  if(kind==='offset')vm.runInContext('__terraformLogCursorV1.text=""',f.context);
  await assert.rejects(r.read(),/rewritten|truncated|replaced|reset|offset/);assert.equal(r.text,'original\n');
  await assert.rejects(r.read());
 }
});
test('invalid transported offsets cannot silently drop or duplicate log text',async()=>{
 const r=new BrowserLogCursor({evaluate:async()=>({start:1,end:4,text:'abc'})});
 await assert.rejects(r.read(),/retained UTF-16 offset/);assert.equal(r.text,'');
});
test('lossless chunk artifacts preserve split Unicode and fresh marker offsets',async()=>{
 const f=fixture(),rows=[],r=new BrowserLogCursor(f.page,p=>rows.push(JSON.stringify({start_utf16:p.start,end_utf16:p.end,text:p.text})));
 for(const text of ['old TF_STATE|1|{}\n😀','\nTF_ST','ATE|2|{"x":"漢"}\n']){f.element.textContent+=text;await r.read();}
 const original=f.element.textContent;const restored=rows.map(line=>JSON.parse(line).text).join('');
 assert.equal(restored,original);assert.deepEqual(Buffer.from(restored),Buffer.from(original));
 const before='old TF_STATE|1|{}\n😀'.length;assert.equal(restored.slice(before).match(/TF_STATE\|/g).length,1);
 assert.equal(JSON.parse(rows[1]).start_utf16,before);
});
test('artifact I/O failure rejects the read while retaining received text in Node',async()=>{
 const f=fixture(),r=new BrowserLogCursor(f.page,()=>{throw Error('declared disk failure');});f.element.textContent='received\n';
 await assert.rejects(r.read(),/disk failure/);assert.equal(r.text,'received\n');await assert.rejects(r.read(),/disk failure/);
});
