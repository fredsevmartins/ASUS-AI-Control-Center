// Optional real-browser acceptance. Requires an existing Playwright installation
// and browser binary. No downloads, live API calls, model operations or NAS reads.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdir, writeFile} from 'node:fs/promises';
import {createInterface} from 'node:readline';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
import os from 'node:os';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const checks=[];
const token='browser-fixture-only-not-a-live-session';
let child,browser,context;
const artifactDir=process.env.AI_MANAGER_E2E_ARTIFACTS||path.join(os.tmpdir(),'asus-ai-browser-evidence');

try {
  let playwright;
  try {playwright=await import(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE ? pathToFileURL(path.resolve(process.env.AI_MANAGER_E2E_PLAYWRIGHT_MODULE)).href : 'playwright');}
  catch {throw Object.assign(Error('Playwright is not installed; no browser tests ran.'),{blocked:true});}
  child=spawn('python3',['-u','tests/browser_server.py'],{cwd:root,stdio:['ignore','pipe','pipe']});
  let serverDenied=false;
  child.stderr.on('data',data=>{if(String(data).includes('PermissionError'))serverDenied=true;});
  const port=await new Promise((resolve,reject)=>{
    const lines=createInterface({input:child.stdout});
    const timer=setTimeout(()=>reject(Object.assign(Error('Fixture server startup timed out.'),{blocked:true})),5000);
    child.once('error',()=>{clearTimeout(timer);reject(Object.assign(Error('Fixture server could not start.'),{blocked:true}));});
    child.once('exit',()=>{clearTimeout(timer);reject(Object.assign(Error(serverDenied?'Loopback socket access denied.':'Fixture server exited before startup.'),{blocked:true}));});
    lines.once('line',line=>{clearTimeout(timer);resolve(JSON.parse(line).port);});
  });
  const origin=`http://127.0.0.1:${port}`;
  const name=process.env.AI_MANAGER_E2E_BROWSER||'chromium';
  assert(['chromium','firefox'].includes(name),'Select chromium or firefox');
  try {browser=await playwright[name].launch({headless:true});}
  catch {throw Object.assign(Error('The requested Playwright browser could not launch; no rendered checks passed.'),{blocked:true});}
  context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:2,hasTouch:true,reducedMotion:'reduce'});
  const page=await context.newPage(),errors=[],requests=[],external=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('request',request=>{const url=new URL(request.url());requests.push(url.pathname);});
  await page.route('**/*',route=>{
    if(new URL(route.request().url()).origin===origin)return route.continue();
    external.push('unexpected external request');return route.abort();
  });
  await page.goto(`${origin}/?token=${token}&demo=1`);
  await page.locator('#model-cards .model-card').first().waitFor();
  assert.equal(await page.locator('#demo-banner').isVisible(),true);
  checks.push('Authenticated fixture document; explicit demo mode');
  assert.equal((await context.request.get(origin+'/api/status')).status(),403);
  assert.equal((await context.request.get(origin+'/api/status',{headers:{'X-Session-Token':token,Origin:'http://invalid.example'}})).status(),403);
  checks.push('Session and Origin rejection over real HTTP');

  for(const section of ['dashboard','models','library','workspaces','activity','settings']){
    await page.locator(`.nav-item[data-page="${section}"]`).click();
    assert.equal(await page.locator('#'+section).isVisible(),true);
  }
  assert.equal(await page.locator('[data-page="performance"]').count(),0);
  // Complete visual matrix before simulated lifecycle changes alter the fixture.
  await mkdir(artifactDir,{recursive:true});
  for (const theme of ['light','dark']) {
    if ((await page.locator('body').getAttribute('class')||'').includes('dark') !== (theme==='dark')) await page.locator('#theme-btn').click();
    for (const width of [1440,1024,768,390,320]) {
      await page.setViewportSize({width,height:1000});
      for (const section of ['dashboard','models','library','workspaces','activity','settings']) {
        await page.locator(`.nav-item[data-page="${section}"]`).click();
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${section} overflow at ${theme}/${width}`);
        await page.screenshot({path:path.join(artifactDir,`fixture-${section}-${theme}-${width}.png`),fullPage:true});
      }
      await page.locator('.nav-item[data-page="models"]').click();
      await page.locator('#model-search').fill('qwen');
      await page.screenshot({path:path.join(artifactDir,`fixture-search-${theme}-${width}.png`),fullPage:true});
      await page.locator('#model-search').fill('no matching model');
      await page.screenshot({path:path.join(artifactDir,`fixture-empty-${theme}-${width}.png`),fullPage:true});
      await page.locator('#model-search').fill('');
      await page.locator('[data-details-key="qwen3:8b"]').click();
      await page.waitForFunction(()=>document.querySelector('#details-content')?.textContent.includes('Representative'));
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(artifactDir,`fixture-details-${theme}-${width}.png`),fullPage:false});
      await page.locator('#details-close').press('Escape');
      await page.locator('.model-action[data-id="qwen3:8b"][data-action="switch"]').click();
      await page.evaluate(()=>window.scrollTo(0,0));
      await page.screenshot({path:path.join(artifactDir,`fixture-confirmation-${theme}-${width}.png`),fullPage:false});
      await page.locator('#modal-cancel').click();
    }
  }
  checks.push('Six-page screenshot matrix, search, empty, details and confirmation: both themes at five widths');
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.nav-item[data-page="settings"]').click();
  assert.equal(await page.locator('#workspace-grid article.workspace-card').count(),6);
  await page.locator('.nav-item[data-page="workspaces"]').click();
  assert.equal(await page.locator('#workspace-grid').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length),3);
  await page.locator('.nav-item[data-page="settings"]').click();
  await page.locator('#settings-theme').click();
  checks.push('All six sections, fixture library/activity and informational workspaces');
  await page.locator('.nav-item[data-page="dashboard"]').click();
  for (const theme of ['light','dark']) {
    if ((await page.locator('body').getAttribute('class')||'').includes('dark') !== (theme==='dark')) await page.locator('#theme-btn').click();
    for (const width of [1440,1024,768,390,320]) {
      await page.setViewportSize({width,height:1000});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`Overview overflow at ${theme}/${width}`);
      const columns=await page.locator('.overview-records').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
      assert.equal(columns,width>1250?4:width>600?2:1,`${theme}/${width}: monitoring strip columns`);
      const strip=await page.locator('.overview-records > article').evaluateAll(items=>items.map(el=>({top:el.getBoundingClientRect().top,height:el.getBoundingClientRect().height,scroll:el.scrollHeight,client:el.clientHeight})));
      assert.equal(strip.length,4);
      assert(strip.every(item=>item.scroll<=item.client+1),'strip must not clip content');
      if(width===1440) assert(strip.every(item=>Math.abs(item.top-strip[0].top)<1),'four modules share a desktop row');
      assert.equal(await page.locator('#hardware-details .detail-row').count(),4);
      for (const selector of ['#theme-btn','#refresh-btn','.quick-grid button']) {
        if(width<=720) assert(await page.locator(selector).first().evaluate(el=>el.getBoundingClientRect().height)>=44,'narrow controls have 44px targets');
      }
      for (const instrument of ['memory','gpu','cpu']) assert(await page.locator(`#overview-${instrument}-gauge svg`).isVisible());
      assert(await page.locator('#loaded-main').isVisible());
      assert.equal(await page.locator('#memory-chart').evaluate(el=>el.getBoundingClientRect().height),184);
      for (const selector of ['.overview-instruments','.overview-history','.overview-runtime','.overview-storage','.overview-shortcuts']) {
        const surface=await page.locator('#dashboard '+selector).evaluate(el=>{const s=getComputedStyle(el);return {radius:parseFloat(s.borderTopLeftRadius),shadow:s.boxShadow,background:s.backgroundColor,border:s.borderTopStyle};});
        assert(surface.radius>=16 && surface.shadow!=='none' && surface.background!=='rgba(0, 0, 0, 0)' && surface.border!=='none',`${theme}/${width}: ${selector} lacks surface depth`);
      }
    }
    await page.setViewportSize({width:1440,height:1000});
    await mkdir(artifactDir,{recursive:true});
    await page.screenshot({path:path.join(artifactDir,`fixture-overview-${theme}.png`),fullPage:true});
  }
  assert.equal(await page.locator('.gauge-arc').first().evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
  await page.locator('#memory-chart').focus();
  await page.locator('#memory-chart').press('End');
  assert((await page.locator('#overview-timeline-selection').textContent()).includes('GiB'));
  assert.equal(await page.locator('#runtime-summary .status-line').count(),2);
  assert.equal(await page.locator('#storage-summary progress').count(),1);
  for (const destination of ['models','library','activity']) {
    await page.locator(`#dashboard .quick-grid [data-link="${destination}"]`).click();
    assert(await page.locator('#'+destination).isVisible());
    await page.locator('.nav-item[data-page="dashboard"]').click();
  }
  for (const destination of ['models','library']) {
    await page.locator(`#dashboard .overview-records [data-link="${destination}"]`).click();
    assert(await page.locator('#'+destination).isVisible());
    await page.locator('.nav-item[data-page="dashboard"]').click();
  }
  await page.setViewportSize({width:1440,height:1000});
  checks.push('Overview light/dark responsive gauges, compact history keyboard selection, storage and all five navigation links');
  await page.locator('.nav-item[data-page="models"]').click();
  await page.locator('#model-search').fill('does not exist');
  assert.equal(await page.locator('.empty-state').isVisible(),true);
  await page.locator('#model-search').fill('');
  await page.locator('[data-filter="loaded"]').click();
  assert.equal(await page.locator('#model-cards .model-card').count(),2);
  await page.locator('[data-filter="all"]').click();
  assert.equal(await page.locator('.model-list-row').count(),0);
  const details=page.locator('[data-details-key="qwen3:8b"]');
  await details.click();
  assert(await page.locator('#details-modal').isVisible());
  await page.waitForFunction(()=>document.querySelector('#details-content')?.textContent.includes('Representative'));
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(artifactDir,'fixture-model-details.png'),fullPage:false});
  await page.locator('#details-close').press('Tab');
  assert(await page.locator('#details-content').evaluate(el=>el===document.activeElement));
  await page.locator('#details-content').press('Shift+Tab');
  assert(await page.locator('#details-close').evaluate(el=>el===document.activeElement));
  await page.locator('#details-close').press('Escape');
  assert(await details.evaluate(el=>el===document.activeElement));
  checks.push('Search, filters, empty state and metadata provenance/details');

  await mkdir(artifactDir,{recursive:true});
  for(const theme of ['light','dark']){
    if((await page.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark'))await page.locator('#theme-btn').click();
    for(const width of [1440,390,320]){
      await page.setViewportSize({width,height:1000});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),`Horizontal overflow at ${theme}/${width}`);
      const columns=await page.locator('#model-cards').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
      assert.equal(columns,width===1440?3:1,`Model grid columns at ${theme}/${width}`);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.screenshot({path:path.join(artifactDir,`fixture-models-${theme}.png`),fullPage:true});
  }
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(artifactDir,'fixture-models-mobile.png'),fullPage:true});
  checks.push('Light/dark, 1440/390/320 widths, high-DPI and reduced-motion emulation');
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.nav-item[data-page="dashboard"]').click();
  const chart=page.locator('#memory-chart');
  await chart.tap({position:{x:100,y:50}});
  await chart.focus();await chart.press('End');
  assert((await page.locator('#overview-timeline-selection').textContent()).includes('GiB'));
  const initial=await chart.getAttribute('height');
  await page.locator('#theme-btn').click();await page.locator('#theme-btn').click();
  assert.equal(await chart.getAttribute('height'),initial);
  assert.equal(await page.locator('#overview-memory-gauge .gauge-value').textContent(),'52.0');
  assert.equal(await page.locator('#overview-gpu-gauge .gauge-value').textContent(),'28.0');
  assert.equal(await page.locator('#storage-summary progress').count(),1);
  await page.screenshot({path:path.join(artifactDir,'fixture-overview-telemetry.png'),fullPage:true});
  checks.push('Gauges, timeline keyboard selection, stable high-DPI canvas and storage progress');

  await page.locator('.nav-item[data-page="models"]').click();
  const switchButton=page.locator('.model-action[data-id="qwen3:8b"][data-action="switch"]');
  await switchButton.click();
  assert.equal(await page.locator('#modal-cancel').evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.locator('#app').evaluate(el=>el.inert),true);
  assert.equal(await page.locator('.stop-checkbox:checked').count(),0);
  assert.equal(await page.locator('#modal-accept').isDisabled(),true);
  await page.locator('#modal-cancel').press('Escape');
  assert.equal(await switchButton.evaluate(el=>el===document.activeElement),true);
  await switchButton.click();
  await page.locator('.stop-checkbox[data-id="sglang"]').check();
  await page.waitForFunction(()=>document.querySelector('#modal-plan')?.textContent.includes('Simulated model state update'));
  await page.locator('#risk-ack').check();
  await page.locator('#modal-accept').focus();await page.locator('#modal-accept').press('Tab');
  assert.equal(await page.locator('.stop-checkbox').first().evaluate(el=>el===document.activeElement),true);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.join(artifactDir,'fixture-confirmation.png'),fullPage:false});
  await page.locator('#modal-accept').click();
  await page.waitForFunction(()=>document.querySelector('#operation-status')?.textContent.includes('Simulated operation complete'));
  assert.equal(await page.locator('.model-action[data-id="sglang"][data-action="load"]').count(),1);
  assert.equal(await page.locator('.model-action[data-id="nomic-embed-text"][data-action="unload"]').count(),1);
  checks.push('Cancel/Escape/focus return, modal Tab trap, explicit stops/risk acknowledgement and simulated switch');

  await page.locator('#demo-failure').click();
  await page.locator('.model-action[data-id="sglang"][data-action="load"]').click();
  await page.waitForFunction(()=>document.querySelector('#modal-plan')?.textContent.includes('Simulated model state update'));
  await page.locator('#risk-ack').check();await page.locator('#modal-accept').click();
  await page.waitForFunction(()=>document.querySelector('#operation-status')?.textContent.includes('Simulated load failed'));
  await page.screenshot({path:path.join(artifactDir,'fixture-failure.png'),fullPage:true});
  await page.locator('.nav-item[data-page="activity"]').click();
  assert((await page.locator('#activity-list').textContent()).includes('Failed'));
  checks.push('Simulated failure retention and Activity feedback');
  // A separate page exercises the live-mode connection error with every API
  // request aborted in the browser; the fixture backend cannot reach runtimes.
  const offline=await context.newPage();
  await offline.route('**/api/**',route=>route.abort());
  await offline.goto(`${origin}/?token=${token}`);
  await offline.waitForFunction(()=>document.querySelector('#system-state')?.textContent==='Connection unavailable');
  await offline.locator('.nav-item[data-page="models"]').click();
  assert.equal(await offline.locator('.model-action').count(),0);
  await offline.screenshot({path:path.join(artifactDir,'fixture-unavailable.png'),fullPage:true});
  await offline.close();
  checks.push('Connection failure disables model actions');
  assert.deepEqual(external,[]);
  assert.equal(requests.some(p=>p.startsWith('/api/')),false,'Demo must make no API requests');
  assert.deepEqual(errors,[],'Browser JavaScript or CSP errors');
  const evidence={classification:'PASS_FIXTURE_BROWSER_ONLY',browser:name,checks,liveRuntimeValidated:false};
  await writeFile(path.join(artifactDir,'results.json'),JSON.stringify(evidence,null,2)+'\n');
  console.log(`PASS: ${checks.length} fixture browser acceptance groups. Evidence: ${artifactDir}`);
} catch(error) {
  console.error(`${error.blocked?'BLOCKED':'FAIL'}: ${error.message}`);
  process.exitCode=error.blocked?2:1;
} finally {
  await context?.close();await browser?.close();
  if(child){child.kill('SIGTERM');await new Promise(resolve=>{if(child.exitCode!==null)return resolve();child.once('exit',resolve);});}
}
