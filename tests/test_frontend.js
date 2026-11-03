'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const setPage = source.match(/function setPage\(p\)\{[^\n]+\}/)[0];
let visible = false, drawn = false;
const sessionHistory = [{time: 1, memory: 42}];
const page = {id: 'performance', classList: {toggle: (name, value) => { visible = value; }}};
const element = {textContent: ''};
const context = {activePage: '', pages: {performance: ['Performance', 'Performance', 'Details']},
  $$: selector => selector === '.page' ? [page] : [],
  $: () => element, renderPerformance: () => {},
  state: {history: sessionHistory},
  drawCharts: () => { assert(visible, 'chart must be visible before drawing'); drawn = true; }};
vm.runInNewContext(setPage + "\nsetPage('performance');", context);
assert(drawn, 'opening Performance should draw its chart');
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
const canvas = {id:'performance-chart', dataset: {}, width: 0, height: 250, getClientRects: () => [1],
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
vm.runInNewContext("chartSelection['performance-chart']=1700000010", chartContext);
chartContext.drawChart(canvas, history);
assert(descriptions.textContent.includes('40.0 GiB used'));
assert(labels.some(x => x.includes('40.0 GiB used')), 'selected sample tooltip must be rendered');
console.log('Memory timeline regressions passed');

// Pointer and keyboard selection use the same observed samples.
const handlers = {}, overviewHandlers = {}, overviewDescription = {textContent:''};
canvas.addEventListener = (type, handler) => { handlers[type] = handler; };
const overview = {...canvas, id:'memory-chart', dataset:{}, addEventListener: (type, handler) => { overviewHandlers[type] = handler; }};
canvas.getBoundingClientRect = () => ({width:400, left:0});
overview.getBoundingClientRect = () => ({width:400, left:0});
const controlsSource = source.slice(source.indexOf('function drawCharts()'), source.indexOf('function renderPerformance()'));
chartContext.window.addEventListener = noop;
chartContext.state.history = history;
// The dashboard chart is not visible in this simulated Performance view.
chartContext.$ = selector => selector === '#performance-chart' ? canvas : selector === '#memory-chart' ? overview : selector === '#timeline-selection' ? descriptions : selector === '#overview-timeline-selection' ? overviewDescription : selector === '#chart-note' ? {textContent:''} : null;
vm.runInNewContext(controlsSource, chartContext);
overviewHandlers.pointermove({clientX:385});
assert(overviewDescription.textContent.includes('40.0 GiB used'), 'Overview tooltip uses the selected sample');
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
for (const id of ['overview-memory-gauge','overview-gpu-gauge','overview-cpu-gauge','performance-memory-gauge','performance-gpu-gauge','performance-cpu-gauge']) {
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
  assert.strictEqual(cards['performance-cpu-gauge'].fields['.gauge-value'].textContent,percent.toFixed(1));
  assert.strictEqual(cards['overview-cpu-gauge'].fields['.gauge-value'].textContent,percent.toFixed(1));
  assert.strictEqual(cards['overview-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: 53°C');
  assert.strictEqual(cards['performance-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: 53°C');
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
assert.strictEqual(cards['performance-gpu-gauge'].fields['.gauge-detail'].textContent,'GPU temperature: Unavailable');
assert.strictEqual(gaugeContext.gaugePercent(null),null);
assert.strictEqual(gaugeContext.gaugePercent(Infinity),null);
const css = fs.readFileSync('web/style.css','utf8');
assert(gaugeContext.gaugeMarkup('test','Test').includes('viewBox="0 0 240 140"'), 'gauge should use scalable vector graphics');
assert(css.includes('.gauge-compact .gauge-visual,.gauge-compact .gauge-scale{width:min(100%,190px)}'), 'Overview gauges must be compact');
assert(css.includes('body.dark .gauge-card'), 'gauge colors must support dark mode');
assert(css.includes('prefers-reduced-motion:reduce') && css.includes('.gauge-animated .gauge-arc{transition:none}'));
assert(css.includes('grid-template-columns:repeat(auto-fit,minmax(220px,1fr))') && css.includes('.gauge-grid{grid-template-columns:1fr}'), 'gauges must have responsive layouts');
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
