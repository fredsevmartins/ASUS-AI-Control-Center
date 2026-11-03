'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const setPage = source.match(/function setPage\(p\)\{[^\n]+\}/)[0];
let visible = false, drawn = false;
const sessionHistory = [{time: 1, memory: 42}];
const page = {id: 'dashboard', classList: {toggle: (name, value) => { visible = value; }}};
const element = {textContent: ''};
const context = {activePage: '', pages: {dashboard: ['Overview', 'Workstation', 'Telemetry']},
  $$: selector => selector === '.page' ? [page] : [],
  $: () => element, renderPerformance: () => {},
  state: {history: sessionHistory},
  drawCharts: () => { assert(visible, 'chart must be visible before drawing'); drawn = true; }};
vm.runInNewContext(setPage + "\nsetPage('dashboard');", context);
assert(drawn, 'opening Overview should draw its chart');
assert.strictEqual(context.state.history, sessionHistory, 'navigation must preserve history');
assert(source.includes('setInterval(update,5000)'), 'status must refresh every five seconds');
console.log('Frontend navigation regression passed');

// Exercise calculation and markup without a server or live storage.
const storageSource = source.slice(source.indexOf('function storagePercent('), source.indexOf('function statusSummary('));
const escapeSource = source.match(/function escapeHTML\(s\)\{[^\n]+\}/)[0];
const gibSource = source.match(/function gib\(n\)\{[^\n]+\}/)[0];
const storageContext = {state: {storage: []}};
vm.runInNewContext(escapeSource + gibSource + storageSource, storageContext);
for (const [total, free, expected] of [[100,100,0], [1892.3,1806.6,85.7/1892.3*100], [100,50,50], [100,0,100]]) {
  assert(Math.abs(storageContext.storagePercent(total,free)-expected)<1e-9);
  storageContext.state.storage = [{name:'Test', online:true, total, free}];
  const markup = storageContext.storageRows();
  const value = Number(markup.match(/value="([^"]+)"/)[1]);
  assert(Math.abs(value-expected)<1e-9, `wrong value: ${markup}`);
  assert(!markup.includes('style='), 'capacity must not rely on blocked inline styles');
}
for (const [total, free] of [[0,0], [-1,0], [100,-1], [100,101], [NaN,1], [100,Infinity], [null,0]]) {
  assert.strictEqual(storageContext.storagePercent(total,free), null);
  storageContext.state.storage = [{name:'Test', online:true, total, free}];
  assert(storageContext.storageRows().includes('Unavailable'));
  assert(!storageContext.storageRows().includes('<progress'));
}
storageContext.state.storage = [{name:'Test', online:false}];
assert(!storageContext.storageRows().includes('<progress'));
console.log('Storage utilization regressions passed');

// Exercise chart drawing, labels, empty state and repeated high-DPI redraws.
const chartSource = source.slice(source.indexOf('const chartSelection'), source.indexOf('function drawCharts()'));
const noop = () => {}, labels = [], lines = [], descriptions = {textContent:''};
const ctx = {scale: noop, clearRect: noop, beginPath: noop, moveTo: noop, lineTo: (x,y) => lines.push([x,y]),
  stroke: noop, closePath: noop, fill: noop, arc: noop, fillRect: noop,
  save: noop, restore: noop, translate: noop, rotate: noop,
  fillText: text => labels.push(text), measureText: text => ({width: text.length*6})};
const canvas = {id:'memory-chart', dataset: {}, width: 0, height: 250, getClientRects: () => [1],
  getBoundingClientRect: () => ({width: 400}),
  getAttribute: function (name) { return name === 'height' ? String(this.height) : null; },
  getContext: () => ctx};
const chartContext = {window: {devicePixelRatio: 2}, $: () => descriptions,
  document: {body: {classList: {contains: () => false}}}, state: {memory: {total: 100*1073741824}}};
vm.runInNewContext(gibSource + chartSource, chartContext);
chartContext.drawChart(canvas, []);
assert(labels.includes('Waiting for memory samples'));
const history = [{time:1700000000,memory:30*1073741824},{time:1700000010,memory:40*1073741824}];
chartContext.drawChart(canvas, history);
assert.strictEqual(canvas.height, 500);
for (let tick=0; tick<=128; tick+=16) assert(labels.includes(String(tick)), `missing tick ${tick}`);
assert(labels.includes('Used Memory (GiB)') && labels.includes('Time'));
// With a 250px canvas, the chart spans y=16..202. Values are plotted in GiB on a fixed 128 GiB scale.
assert(lines.some(([x,y]) => x===385 && Math.abs(y-(202-40/128*186))<1e-9));
// Different total memory and canvas width must not alter the fixed-scale mapping.
chartContext.state.memory.total = 64*1073741824;
canvas.getBoundingClientRect = () => ({width:300});
lines.length=0;
chartContext.drawChart(canvas,history);
assert(lines.some(([x,y]) => x===285 && Math.abs(y-(202-40/128*186))<1e-9));
canvas.getBoundingClientRect = () => ({width:400});
chartContext.document.body.classList.contains = () => true;
labels.length=0; chartContext.drawChart(canvas,history);
assert(labels.includes('128') && labels.includes('Used Memory (GiB)'), 'dark theme must draw the same axes');
chartContext.document.body.classList.contains = () => false;
assert(labels.includes(chartContext.chartTime(history[0].time)) && labels.includes(chartContext.chartTime(history[1].time)));
chartContext.drawChart(canvas, history);
assert.strictEqual(canvas.height, 500, 'redraw must not rescale previous backing height');
assert.strictEqual(chartContext.chartSamples([{time:1,memory:-1}]).length, 0);
lines.length=0;
chartContext.drawChart(canvas,[{time:1,memory:0},{time:2,memory:128*1073741824}]);
assert(lines.some(([x,y])=>x===385 && y===16), '128 GiB must map to the top tick');
chartContext.drawChart(canvas,[{time:1,memory:129*1073741824}]);
assert(descriptions.textContent.includes('Values above 128 GiB are clipped'));
chartContext.drawChart(canvas, history);
const localTime = new Date(history[0].time*1000);
const expectedTime = [localTime.getHours(),localTime.getMinutes(),localTime.getSeconds()].map(x=>String(x).padStart(2,'0')).join(':');
assert.strictEqual(chartContext.chartTime(history[0].time), expectedTime);
vm.runInNewContext("chartSelection['memory-chart']=1700000010", chartContext);
chartContext.drawChart(canvas, history);
assert(descriptions.textContent.includes('40.0 GiB used'));
assert(labels.some(x => x.includes('40.0 GiB used')), 'selected sample tooltip must be rendered');
console.log('Memory timeline regressions passed');

// Pointer and keyboard selection use the same observed samples.
const handlers = {};
canvas.addEventListener = (type, handler) => { handlers[type] = handler; };
canvas.getBoundingClientRect = () => ({width:400, left:0});
const controlsSource = source.slice(source.indexOf('function drawCharts()'), source.indexOf('function renderHardware()'));
chartContext.window.addEventListener = noop;
chartContext.state.history = history;
chartContext.$ = selector => selector === '#memory-chart' ? canvas : selector === '#overview-timeline-selection' ? descriptions : selector === '#chart-note' ? {textContent:''} : null;
vm.runInNewContext(controlsSource, chartContext);
handlers.pointermove({clientX:385});
assert(descriptions.textContent.includes('40.0 GiB used'));
let prevented = false;
handlers.keydown({key:'ArrowLeft', preventDefault:()=>{prevented=true;}});
assert(prevented && descriptions.textContent.includes('30.0 GiB used'));
handlers.pointerleave({pointerType:'touch'});
assert(descriptions.textContent.includes('30.0 GiB used'), 'touch selection remains visible');
handlers.pointerleave({pointerType:'mouse'});
assert(descriptions.textContent.includes('2 samples'));
console.log('Timeline interaction regressions passed');

// Gauges use telemetry only; invalid values never become plausible measurements.
const gaugeSource = source.slice(source.indexOf('function gaugePercent('), source.indexOf('initGauges();'));
const cards = {};
for (const id of ['overview-memory-gauge','overview-gpu-gauge','overview-cpu-gauge']) {
  const fields = {};
  for (const selector of ['.gauge-arc','.gauge-value','.gauge-unit','.gauge-percent','.gauge-detail','.gauge-accessible']) fields[selector] = {textContent:'',style:{}};
  cards[id] = {fields, dataset:{}, classList:{toggle:noop}, querySelector:selector=>fields[selector]};
}
const gaugeContext = {document:{getElementById:id=>cards[id]}};
vm.runInNewContext(gibSource + gaugeSource, gaugeContext);
const unit = 1073741824;
for (const percent of [0,50,100]) {
  gaugeContext.renderGauges({total:120*unit,used:120*unit*percent/100,available:120*unit*(100-percent)/100},{load:percent,temp:53},percent);
  const card = cards['overview-memory-gauge'];
  assert.strictEqual(card.fields['.gauge-value'].textContent,(120*percent/100).toFixed(1));
  assert.strictEqual(card.fields['.gauge-percent'].textContent,`${percent.toFixed(1)}% used`);
  assert.strictEqual(card.fields['.gauge-detail'].textContent,`120.0 GiB total · ${(120*(100-percent)/100).toFixed(1)} GiB available`);
  assert.strictEqual(card.fields['.gauge-arc'].style.strokeDashoffset,String(100-percent));
  assert.strictEqual(card.fields['.gauge-arc'].style.visibility,percent ? 'visible' : 'hidden');
  assert.strictEqual(cards['overview-cpu-gauge'].fields['.gauge-value'].textContent,percent.toFixed(1));
  assert.strictEqual(cards['overview-cpu-gauge'].fields['.gauge-value'].textContent,percent.toFixed(1));
  assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: 53°C');
  assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: 53°C');
}
for (const reading of [null, {total:0,used:0}, {total:100,used:-1}, {total:100,used:101}, {total:100,used:NaN}, {total:Infinity,used:1}]) {
  gaugeContext.renderGauges(reading,{load:-1,temp:NaN},101);
  for (const card of Object.values(cards)) {
    assert.strictEqual(card.fields['.gauge-value'].textContent,'—');
    assert.strictEqual(card.fields['.gauge-arc'].style.visibility,'hidden');
    assert(card.fields['.gauge-accessible'].textContent.includes('unavailable'));
  }
}
gaugeContext.renderGauges({total:120*unit,used:40*unit,available:null},{load:NaN,temp:0},null);
assert(cards['overview-memory-gauge'].fields['.gauge-detail'].textContent.includes('Available memory unavailable'));
assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-value'].textContent,'—');
assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: 0°C');
gaugeContext.renderGauges({total:120*unit,used:40*unit,available:80*unit},{load:50,temp:NaN},40);
assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: Unavailable');
assert.strictEqual(gaugeContext.gaugePercent(null),null);
assert.strictEqual(gaugeContext.gaugePercent(Infinity),null);
const css = fs.readFileSync('web/style.css','utf8');
assert(gaugeContext.gaugeMarkup('test','Test').includes('viewBox="0 0 240 140"'), 'gauge should use scalable vector graphics');
assert(css.includes('width:min(100%,310px)') && css.includes('width:min(100%,220px)'), 'Memory remains the larger instrument');
assert(css.includes('body.dark .gauge-card'), 'gauge colors must support dark mode');
assert(css.includes('prefers-reduced-motion:reduce') && css.includes('.gauge-animated .gauge-arc{transition:none}'));
assert(css.includes('@media(max-width:1100px)') && css.includes('@media(max-width:600px)') && css.includes('#overview-memory-gauge { grid-column:1/-1; }'), 'instruments reflow at narrower widths');
console.log('Telemetry gauge regressions passed');

const gpuSource = source.match(/function gpuValues\(\)\{[^\n]+\}/)[0];
const gpuContext = {state:{gpu:'GPU: 27% utilization · 0°C'}};
vm.runInNewContext(gpuSource, gpuContext);
assert.strictEqual(gpuContext.gpuValues().load,27);
assert.strictEqual(gpuContext.gpuValues().temp,0);
gpuContext.state.gpu='GPU: 27.5% utilization · 46.5°C';
assert.strictEqual(gpuContext.gpuValues().load,27.5);
assert.strictEqual(gpuContext.gpuValues().temp,46.5);
gpuContext.state.gpu='GPU telemetry unavailable';
assert(Number.isNaN(gpuContext.gpuValues().load));
assert(Number.isNaN(gpuContext.gpuValues().temp));
const html = fs.readFileSync('web/index.html','utf8');
assert(html.includes('id="overview-gpu-gauge"') && html.includes('id="overview-cpu-gauge"'));
assert(html.includes('id="loaded-main"'), 'model count remains available');
console.log('Overview telemetry regressions passed');

// The empty Activity view must respect style-src 'self'; failed refreshes stay
// visible in the section and use textContent rather than rendering error HTML.
const activityElement={innerHTML:'',textContent:''};
const activityContext={$:()=>activityElement,request:async()=>[]};
const activitySource=source.match(/async function refreshActivity\(\)\{[^\n]+\}/)[0];
vm.runInNewContext(escapeSource+activitySource,activityContext);
(async()=>{
  await activityContext.refreshActivity();
  assert(activityElement.innerHTML.includes('No operations recorded'));
  assert(!activityElement.innerHTML.includes('style='),'Activity must not emit CSP-blocked inline style');
  activityContext.request=async()=>{throw Error('<offline>');};
  await activityContext.refreshActivity();
  assert(activityElement.textContent.includes('Activity unavailable: <offline>'));
  assert(activityElement.textContent.includes('Refresh to retry'));
  console.log('Activity CSP and persistent error regressions passed');
})().catch(error=>{console.error(error);process.exitCode=1;});

// Theme state must be announced consistently from either appearance control,
// including restoration of the existing browser-local preference.
const themeSource = source.slice(source.indexOf("$('#theme-btn').onclick="), source.indexOf('function storagePercent('));
for (const savedTheme of ['light', 'dark']) {
  let dark = false;
  const attributes = new Map();
  const controls = Object.fromEntries(['#theme-btn', '#settings-theme'].map(id => [id, {
    setAttribute: (key, value) => attributes.set(id + key, value)
  }]));
  const stored = new Map([['ai-manager-theme', savedTheme]]);
  vm.runInNewContext(themeSource, {
    $: id => controls[id], drawCharts: () => {},
    document: {body: {classList: {
      contains: () => dark, add: () => { dark = true; }, toggle: () => { dark = !dark; }
    }}},
    localStorage: {getItem: key => stored.get(key), setItem: (key, value) => stored.set(key, value)}
  });
  for (const expected of [savedTheme === 'dark', savedTheme !== 'dark']) {
    assert.equal(attributes.get('#theme-btnaria-pressed'), String(expected));
    assert.equal(attributes.get('#settings-themearia-pressed'), String(expected));
    if (expected === (savedTheme === 'dark')) controls['#theme-btn'].onclick();
  }
  assert.equal(stored.get('ai-manager-theme'), savedTheme === 'dark' ? 'light' : 'dark');
}
console.log('Appearance preference and accessible toggle state regressions passed');

// Utilization thresholds remain visual indicators, including exact boundaries.
{
  const fs = require('fs'), vm = require('vm'), assert = require('assert');
  const src = fs.readFileSync('web/app.js', 'utf8');
  const code = src.slice(src.indexOf('function gaugePercent('), src.indexOf('function memoryGaugeReading(')) + src.slice(src.indexOf('function gaugeBand('), src.indexOf('function gaugeMarkup('));
  const ctx = {}; vm.createContext(ctx); vm.runInContext(code, ctx);
  for (const [value, band] of [[null,'unavailable'],[-1,'unavailable'],[0,'low'],[59.9,'low'],[60,'medium'],[84.9,'medium'],[85,'high'],[100,'high'],[101,'unavailable']]) assert.equal(ctx.gaugeBand(value), band);
  const css = fs.readFileSync('web/style.css','utf8');
  assert(css.includes('data-band=low') && css.includes('data-band=medium') && css.includes('data-band=high') && css.includes('body.dark'));
  assert(css.includes('repeat(3,minmax(0,1fr))') && css.includes('repeat(2,minmax(0,1fr))'));
}

const destinations=[...html.matchAll(/class="nav-item[^"]*" data-page="([^"]+)"/g)].map(m=>m[1]);
assert.deepStrictEqual(destinations,['dashboard','models','library','workspaces','activity','settings']);
assert(!html.includes('id="performance"') && !source.includes('performance-chart'));
assert(html.includes('id="hardware-details"') && html.includes('id="storage-summary"'));
assert(!html.includes('registered-library'), 'Library avoids duplicating Model Manager');
vm.runInNewContext(setPage + "\nsetPage('performance');", context);
assert.strictEqual(context.activePage,'dashboard','retired routes return to Overview');
const workspaceTarget={innerHTML:''};
vm.runInNewContext(source.slice(source.indexOf('const presets='),source.indexOf('\n',source.indexOf('const presets='))), {$:()=>workspaceTarget});
assert.strictEqual((workspaceTarget.innerHTML.match(/<article class="workspace-card">/g)||[]).length,6);
assert(!workspaceTarget.innerHTML.includes('<details'), 'workspace cards show their requirements without expansion');
console.log('Six-page navigation, consolidated telemetry, simplified Library and workspace cards passed');
// Simplified inventory retains evidence and escapes discovered metadata.
const libraryElements={'#nas-summary':{textContent:''},'#library-content':{innerHTML:''}};
const libraryContext={libraryView:'groups',library:{status:'Synthetic fixture',files:[],groups:[{name:'<asset>',category:'Language',files:2,bytes:1073741824,formats:['safetensors'],classification:'Requires additional configuration',compatibility_hint:{value:'<hint>',confidence:'low'},missing_components:['<missing shard>']}]},$:id=>libraryElements[id]};
vm.runInNewContext(escapeSource+gibSource+source.match(/function renderLibrary\(\)\{[^\n]+\}/)[0],libraryContext);
libraryContext.renderLibrary();
const assetMarkup=libraryElements['#library-content'].innerHTML;
assert(assetMarkup.includes('<details class="asset-evidence"><summary>Asset details</summary>'));
for(const evidence of ['&lt;asset&gt;','&lt;hint&gt;','&lt;missing shard&gt;','No executable adapter','low','2 asset file(s)'])assert(assetMarkup.includes(evidence));
assert(!assetMarkup.includes('<button'), 'NAS assets cannot initiate model operations');
libraryContext.libraryView='files';libraryContext.renderLibrary();
assert(libraryElements['#library-content'].innerHTML.includes('No model weights'));
console.log('Simplified Library evidence, escaping and empty-state regressions passed');

// Source contracts are deliberately separate from computed browser acceptance.
assert.equal((css.match(/:root\s*\{/g)||[]).length,1,'one light token authority');
assert.equal((css.match(/body\.dark\s*\{/g)||[]).length,1,'one dark token authority');
for(const token of ['--bg:#f5f7fa','--bg:#0b1120','--surface:#172235','--blue:#407bbd','--ink:#222831','--ink:#f1f5f9']) assert(css.includes(token),token);
for(const token of ['--nav-glass:','--instrument-glass:','--material:','--dialog-glass:','--reflection:','--panel-shadow:','--modal-shadow:']) assert(css.includes(token),token);
assert(css.includes('prefers-reduced-transparency:reduce') && css.includes('@supports not'), 'solid material fallbacks');
assert(css.includes('.overview-records { display:grid; grid-template-columns:repeat(4,minmax(0,1fr))'));
assert(css.includes('@media(max-width:1250px)') && css.includes('.overview-records { grid-template-columns:repeat(2,minmax(0,1fr)); }'));
assert(css.includes('.overview-records { grid-template-columns:1fr; }'));
assert(!/emerald|#e9f0ef|#087653|master-detail|#performance/.test(css),'obsolete presentation layers removed');
assert(source.includes("ctx.strokeStyle = dark ? '#74b5e8' : '#407bbd'"),'blue history in both themes');
const telemetryTarget={innerHTML:''};
const hardwareContext={state:{memory:{used:52*unit,available:76*unit},cpu:14},gpuValues:()=>({temp:46}),$:()=>telemetryTarget};
vm.runInNewContext(gibSource+source.match(/function renderHardware\(\)\{[^\n]+\}/)[0],hardwareContext);
hardwareContext.renderHardware();
assert.equal((telemetryTarget.innerHTML.match(/class="detail-row"/g)||[]).length,4);
for(const text of ['Memory in use','52.0 GiB','Available memory','76.0 GiB','GPU temperature','46°C','CPU utilization','14%']) assert(telemetryTarget.innerHTML.includes(text));
hardwareContext.state.memory.available=null;hardwareContext.state.cpu=null;hardwareContext.gpuValues=()=>({temp:NaN});
hardwareContext.renderHardware();assert(telemetryTarget.innerHTML.includes('Unavailable') && telemetryTarget.innerHTML.includes('Collecting…'));
const runtimeContext={state:{models:[{runtime:'SGLang',loaded:true},{runtime:'Ollama',loaded:false}],errors:[]}};
vm.runInNewContext(escapeSource+source.match(/function statusSummary\(\)\{[^\n]+\}/)[0],runtimeContext);
for(const text of ['SGLang','Ollama','1 registered · 1 loaded','1 registered · 0 loaded','ACTIVE','IDLE']) assert(runtimeContext.statusSummary().includes(text));
runtimeContext.state.errors=['Ollama unavailable: synthetic fixture'];assert(runtimeContext.statusSummary().includes('UNKNOWN'));
storageContext.state.storage=['ASUS system','NAS model library','NAS archive','External NVMe'].map((name,i)=>({name,online:i!==3,total:100*unit,free:40*unit}));
const disks=storageContext.storageRows();
assert.equal((disks.match(/class="disk-line"/g)||[]).length,4);assert.equal((disks.match(/<progress/g)||[]).length,3);
for(const text of ['ASUS system','NAS model library','NAS archive','External NVMe','OFFLINE','ONLINE','60.0% used']) assert(disks.includes(text));
assert(assetMarkup.includes('library-compatibility'),'collection compatibility visible without disclosure');
console.log('Midnight glass, responsive strip, telemetry, runtime and storage source contracts passed');
