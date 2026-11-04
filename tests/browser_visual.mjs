// File-only visual fixture for environments that deny loopback sockets.
// Explicit Demo Mode, blocked HTTP(S), no backend process or live adapters.
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const artifacts=process.env.AI_MANAGER_VISUAL_ARTIFACTS||path.join(os.tmpdir(),'asus-ai-midnight-visual');
const name=process.env.AI_MANAGER_E2E_BROWSER||'firefox';
const checks=[],errors=[],network=[];
let browser;
try {
  let playwright;
  try { playwright=await import(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE ? pathToFileURL(path.resolve(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE)).href : 'playwright'); }
  catch { throw Object.assign(Error('Provisioned Playwright module unavailable.'),{blocked:true}); }
  assert(['firefox','chromium'].includes(name));
  try { browser=await playwright[name].launch({headless:true,...(name==='chromium'?{chromiumSandbox:true}:{}),...(process.env.AI_MANAGER_VISUAL_EXECUTABLE?{executablePath:process.env.AI_MANAGER_VISUAL_EXECUTABLE}:{})}); }
  catch { throw Object.assign(Error('Provisioned browser could not launch.'),{blocked:true}); }
  const context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1,reducedMotion:'reduce'});
  await context.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.protocol==='file:' && path.dirname(fileURLToPath(url))===path.join(root,'web')) return route.continue();
    network.push(url.protocol); return route.abort();
  });
  const page=await context.newPage();page.setDefaultTimeout(10000);
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(root,'web/index.html')).href+'?demo=1');
  await page.locator('#model-cards .model-card').first().waitFor();
  assert(await page.locator('#demo-banner').isVisible());
  // Synthetic full storage inventory exercises all four observations, including offline.
  await page.evaluate(async()=>{
    demoState.storage=[
      {name:'ASUS System',online:true,total:2000*1073741824,free:1350*1073741824},
      {name:'NAS Model Library',online:true,total:16000*1073741824,free:10500*1073741824},
      {name:'NAS Archive',online:true,total:8000*1073741824,free:6200*1073741824},
      {name:'External NVMe',online:false}
    ];
    demoEvents.push({operation:'Inventory',stage:'Observed',model:'Representative fixture',time:'12:30:00',detail:'Synthetic observation; no runtime or NAS access.'}, {operation:'Details',stage:'Inspected',model:'qwen3:8b',time:'12:29:55',detail:'Representative read-only metadata inspection.'});
    await update();
  });
  await mkdir(artifacts,{recursive:true});
  const measures=[];
  for(const theme of ['light','dark']) {
    if((await page.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark')) await page.locator('#theme-btn').click();
    for(const width of [1440,1024,390,320]) {
      const height={1440:960,1024:768,390:844,320:720}[width];
      await page.setViewportSize({width,height});
      for(const section of ['dashboard','models','library','workspaces','activity','settings']) {
        await page.locator(`.nav-item[data-page="${section}"]`).click();
        // Stable top-of-document capture, after canvas and fonts are ready.
        await page.evaluate(async()=>{await document.fonts.ready;window.scrollTo(0,0);});
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${theme}/${width}/${section}: overflow`);
        await page.screenshot({path:path.join(artifacts,`${section}-${theme}-${width}.png`),fullPage:true,animations:'disabled'});
        if(section==='dashboard') {
          const measurement=await page.locator('.overview-records').evaluate(el=>({
            columns:getComputedStyle(el).gridTemplateColumns.split(' ').length,
            items:[...el.children].map(item=>({top:item.getBoundingClientRect().top,height:item.getBoundingClientRect().height,clipped:item.scrollHeight>item.clientHeight+1}))
          }));
          assert.equal(measurement.columns,width>1250?4:width>600?2:1);
          assert.equal(measurement.items.length,4);assert(measurement.items.every(item=>!item.clipped));
          if(width===1440) {
            assert(measurement.items.every(item=>Math.abs(item.top-measurement.items[0].top)<1));
            assert(measurement.items.every(item=>item.height<=180),'synthetic four-disk strip stays compact without clipping');
            const headings=await page.locator('.gauge-heading').evaluateAll(items=>items.map(el=>el.getBoundingClientRect().top));
            assert(Math.max(...headings)-Math.min(...headings)<1,'gauge headings align');
          }
          const gauges=await page.locator('.gauge-card').evaluateAll(items=>items.map(el=>({caption:el.querySelector('.gauge-percent').getBoundingClientRect().bottom,scale:el.querySelector('.gauge-scale').getBoundingClientRect().top})));
          assert(gauges.every(g=>g.caption<=g.scale),'gauge captions and scale have separate space');
          measures.push({theme,width,...measurement});
          assert.equal(await page.locator('#hardware-details .detail-row').count(),4);
          assert.equal(await page.locator('#storage-summary .disk-line').count(),4);
          assert.equal(await page.locator('#storage-summary progress').count(),3);
          assert((await page.locator('#storage-summary').innerText()).includes('OFFLINE'));
          for(const gauge of ['memory','gpu','cpu'])assert(await page.locator(`#overview-${gauge}-gauge svg`).isVisible());
          for(const selector of ['.overview-instruments','.overview-history','.overview-records > .panel']) {
            const style=await page.locator(selector).first().evaluate(el=>{const s=getComputedStyle(el);return {shadow:s.boxShadow,radius:parseFloat(s.borderRadius),image:s.backgroundImage};});
            assert(style.shadow!=='none'&&style.radius>=16&&style.image.includes('gradient'),`${selector}: material depth`);
          }
          assert.equal(await page.locator('#memory-chart').evaluate(el=>el.getBoundingClientRect().height),184);
          await page.locator('#memory-chart').focus();await page.locator('#memory-chart').press('End');
          assert((await page.locator('#overview-timeline-selection').innerText()).includes('GiB'));
          assert.equal(await page.locator('.gauge-arc').first().evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
        }
        if(section==='models') {
          assert.equal(await page.locator('#model-cards').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length),width>1100?3:width>720?2:1);
          await page.locator('[data-details-key="qwen3:8b"]').click();
          await page.waitForFunction(()=>document.querySelector('#details-content')?.textContent.includes('Representative'));
          assert(await page.locator('#app').evaluate(el=>el.inert));
          await page.locator('#details-close').press('Tab');assert(await page.locator('#details-content').evaluate(el=>el===document.activeElement));
          await page.evaluate(()=>window.scrollTo(0,0));
          await page.screenshot({path:path.join(artifacts,`details-${theme}-${width}.png`),fullPage:false,animations:'disabled'});
          await page.locator('#details-content').press('Escape');
          assert(await page.locator('[data-details-key="qwen3:8b"]').evaluate(el=>el===document.activeElement));
          await page.locator('.model-action[data-id="qwen3:8b"][data-action="switch"]').click();
          assert(await page.locator('#modal-accept').isDisabled());
          await page.screenshot({path:path.join(artifacts,`confirmation-${theme}-${width}.png`),fullPage:false,animations:'disabled'});
          await page.locator('#modal-cancel').press('Escape');
          await page.locator('#model-search').fill('no such model');assert(await page.locator('.empty-state').isVisible());await page.locator('#model-search').fill('');
          await page.locator('[data-filter="loaded"]').click();assert.equal(await page.locator('#model-cards .model-card').count(),2);await page.locator('[data-filter="all"]').click();
        }
        if(section==='workspaces')assert.equal(await page.locator('article.workspace-card').count(),6);
      }
    }
  }
  checks.push('Six pages and read-only Details: both themes at 1440/1024/390/320px; no horizontal overflow');
  checks.push('Four/two/one monitoring columns, four storage observations, no clipped strip content, four hardware readings');
  checks.push('Memory/GPU/CPU gauges, fixed-height history, keyboard inspection, reduced motion');
  checks.push('Compact model grid, search/filters, Details Tab/Escape/focus restoration, six workspaces');
  // Confirm the existing protective dialog remains usable; never accept a lifecycle operation.
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.nav-item[data-page="models"]').click();
  await page.locator('.model-action[data-id="qwen3:8b"][data-action="switch"]').click();
  assert.equal(await page.locator('.stop-checkbox:checked').count(),0);assert(await page.locator('#modal-accept').isDisabled());
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(artifacts,'confirmation-dark-1440.png'),fullPage:false});
  await page.locator('#modal-cancel').press('Escape');
  checks.push('Protected confirmation opens readably; explicit stop/risk gates retained; cancelled without mutation');
  assert.deepEqual(network,[],'No HTTP, runtime, NAS or external asset requests');assert.deepEqual(errors,[]);
  await writeFile(path.join(artifacts,'results.json'),JSON.stringify({classification:'PASS_FILE_DEMO_VISUAL_CHECKS',browser:name,checks,measures,httpSecurityVerified:false,liveRuntimeValidated:false,visualReviewRequired:true},null,2)+'\n');
  console.log(`PASS: ${checks.length} file-only visual browser groups. Evidence: ${artifacts}`);
} catch(error) {
  console.error(`${error.blocked?'BLOCKED':'FAIL'}: ${error.message}`);process.exitCode=error.blocked?2:1;
} finally { await browser?.close(); }
