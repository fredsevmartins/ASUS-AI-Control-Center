// Optional file-only rendered-material audit; no server or runtime adapters.
import assert from 'node:assert/strict';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {writeFile,mkdir} from 'node:fs/promises';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dir=process.env.AI_MANAGER_MATERIAL_ARTIFACTS||path.join(os.tmpdir(),'asus-ai-liquid-materials');
let browser;
try {
let playwright;
try { playwright=await import(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE?pathToFileURL(path.resolve(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE)).href:'playwright'); }
catch { throw Object.assign(Error('Provisioned Playwright module unavailable.'),{blocked:true}); }
try { browser=await playwright.firefox.launch({headless:true,...(process.env.AI_MANAGER_VISUAL_EXECUTABLE?{executablePath:process.env.AI_MANAGER_VISUAL_EXECUTABLE}:{})}); }
catch { throw Object.assign(Error('Provisioned Firefox could not launch.'),{blocked:true}); }
await mkdir(dir,{recursive:true});
const network=[],errors=[];
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await context.route('**/*',route=>{const url=new URL(route.request().url());if(url.protocol==='file:'&&path.dirname(fileURLToPath(url))===path.join(root,'web'))return route.continue();network.push(url.protocol);return route.abort();});
const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(root,'web/index.html')).href+'?demo=1');await page.locator('.model-card').first().waitFor();
await page.evaluate(async()=>{
 demoState.storage=[
  {name:'ASUS System',online:true,total:2000*1073741824,free:1350*1073741824},
  {name:'NAS Model Library',online:true,total:16000*1073741824,free:10500*1073741824},
  {name:'NAS Archive',online:true,total:8000*1073741824,free:6200*1073741824},
  {name:'External NVMe',online:false}
 ];
 demoEvents.push({operation:'Inventory',stage:'Observed',model:'Representative fixture',time:'12:30:00',detail:'Synthetic observation; no runtime or NAS access.'},{operation:'Details',stage:'Inspected',model:'qwen3:8b',time:'12:29:55',detail:'Representative read-only metadata inspection.'});
 await update();
});
const records=[];
for(const theme of ['light','dark']) {
 if(theme==='dark')await page.locator('#theme-btn').click();
 for(const section of ['dashboard','models','details','library','workspaces','activity','settings']) {
  if(section==='details'){await page.locator('[data-details-key="qwen3:8b"]').click();await page.waitForFunction(()=>document.querySelector('#details-content').textContent.includes('Representative'));}
  else await page.locator(`.nav-item[data-page="${section}"]`).click();
  await page.evaluate(()=>window.scrollTo(0,0));
  const sample=await page.evaluate(({section,theme})=>{
   const root=section==='details'?document.querySelector('.details-dialog'):document.body;
   const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const texts=[];let n;
   while(n=walker.nextNode()){
    if(!n.textContent.trim())continue;const e=n.parentElement,s=getComputedStyle(e);
    if(e.closest('script,style,noscript,[hidden],button:disabled')||s.visibility==='hidden')continue;
    const range=document.createRange();range.selectNodeContents(n);
    for(const r of range.getClientRects())if(r.width>2&&r.height>2&&r.top>=0&&r.bottom<=innerHeight){
     const hit=document.elementFromPoint(r.x+r.width*.5,r.y+r.height*.5);if(!hit||!(e===hit||e.contains(hit)))continue;
     texts.push({text:n.textContent.trim().slice(0,90),color:s.color,fontSize:s.fontSize,fontWeight:s.fontWeight,x:r.x,y:r.y,width:r.width,height:r.height});
    }
   }
   const materials=['.sidebar','.overview-instruments','.panel','.model-card','.workspace-card','.modal-card'].flatMap(selector=>[...document.querySelectorAll(selector)].filter(e=>e.getClientRects().length).map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {selector,background:s.backgroundColor,blur:s.backdropFilter,shadow:s.boxShadow,x:r.x,y:r.y,width:r.width,height:r.height};}));
   return {section,theme,texts,materials};
  },{section,theme});
  for(const material of sample.materials){
   assert(material.background.startsWith('rgba(')&&parseFloat(material.background.split(',').at(-1))<1,`${material.selector}: translucent fill delivered`);
   assert(material.blur.includes('blur('),`${material.selector}: backdrop enhancement delivered`);
  }
  const hidden=await page.addStyleTag({content:'* { -webkit-text-fill-color:transparent!important; text-shadow:none!important; }'});
  sample.image=`${section}-${theme}-background.png`;await page.screenshot({path:dir+'/'+sample.image});await hidden.evaluate(e=>e.remove());
  records.push(sample);
  if(section==='details')await page.locator('#details-close').click();
 }
}
assert.deepEqual(network,[]);assert.deepEqual(errors,[]);
await writeFile(dir+'/samples.json',JSON.stringify(records,null,2));
console.log('Rendered surface samples: '+records.length);
}catch(error){console.error(`${error.blocked?'BLOCKED':'FAIL'}: ${error.message}`);process.exitCode=error.blocked?2:1;}finally{await browser?.close();}
