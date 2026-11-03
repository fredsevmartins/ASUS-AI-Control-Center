'use strict';
const DEMO = new URLSearchParams(location.search).get('demo') === '1';
let modelFilter='all', connectionHealthy=false, submitting=false, modalTrigger=null, failNextDemo=false;
const TOKEN=document.querySelector('meta[name="session-token"]').content;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
let state=null, library=null, activePage='dashboard', libraryView='groups', modalData=null, lastOperation='';
const pages={dashboard:['Overview','Workstation Overview','Hardware, runtimes and storage in one place.'],models:['Model Manager','Model Manager','Manage local AI models with clear, deliberate actions.'],library:['Model Library','Model Library','Discover and inspect model assets on your NAS.'],performance:['Performance','Performance Center','An at-a-glance view of your local hardware.'],workspaces:['Workspaces','AI Workspaces','Purpose-built presets for your workflows.'],activity:['Activity','Activity','Inspect local operations and recovery attempts.'],settings:['Settings','Settings','Personalize your local control center.']};
function escapeHTML(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function gib(n){return Number.isFinite(n)?(n/1073741824).toFixed(1)+' GiB':'—';}
function pct(n,total){return total?Math.min(100,Math.max(0,100*n/total)):0;}
function toast(message,ms=5000){const x=$('#toast');x.textContent=message;x.style.display='block';clearTimeout(x._timer);x._timer=setTimeout(()=>x.style.display='none',ms);}
async function request(path,opts={}){if(DEMO)return demoRequest(path,opts);const r=await fetch(path,{...opts,headers:{'X-Session-Token':TOKEN,...opts.headers}});const d=await r.json();if(!r.ok)throw Error(d.error||`HTTP ${r.status}`);return d;}
function setPage(p){activePage=p;$$('.page').forEach(e=>e.classList.toggle('active',e.id===p));$$('.nav-item').forEach(e=>(e.classList.toggle('active',e.dataset.page===p),e.setAttribute('aria-current',e.dataset.page===p?'page':'false')));$('#breadcrumb').textContent=pages[p][0];$('#page-title').textContent=pages[p][1];$('#page-desc').textContent=pages[p][2];if(p==='library'&&!library)scanNAS();if(p==='activity')refreshActivity();if(p==='performance')renderPerformance();drawCharts();}
$$('.nav-item').forEach(b=>b.onclick=()=>setPage(b.dataset.page));$$('[data-link]').forEach(b=>b.onclick=()=>setPage(b.dataset.link));
$('#theme-btn').onclick=()=>{document.body.classList.toggle('dark');localStorage.setItem('ai-manager-theme',document.body.classList.contains('dark')?'dark':'light');drawCharts();};
if(localStorage.getItem('ai-manager-theme')==='dark')document.body.classList.add('dark');
function storagePercent(total, free) {
  if (!Number.isFinite(total) || !Number.isFinite(free) || total <= 0 || free < 0 || free > total) return null;
  return (total - free) / total * 100;
}
function storageRows() {
  return (state?.storage || []).map(d => {
    const progress = d.online ? storagePercent(d.total, d.free) : null;
    const size = progress === null ? 'Unavailable' : `${gib(d.total-d.free)} of ${gib(d.total)} · ${progress.toFixed(1)}% used`;
    return `<div class="disk-line"><div class="disk-info"><strong>${escapeHTML(d.name)}</strong><small>${escapeHTML(size)}</small>${progress === null ? '' : `<progress class="disk-track" max="100" value="${progress}" aria-label="${escapeHTML(d.name)} storage used"></progress>`}</div><span class="pill ${d.online ? '' : 'off'}">${d.online ? 'ONLINE' : 'OFFLINE'}</span></div>`;
  }).join('');
}
function statusSummary(){const names=['SGLang','Ollama'];return names.map(runtime=>{const matching=(state.models||[]).filter(m=>m.runtime===runtime),loaded=matching.filter(m=>m.loaded).length,unknown=matching.some(m=>m.uncertain)||(runtime==='Ollama'&&state.errors.some(e=>e.startsWith('Ollama unavailable:')));return `<div class="status-line"><div><strong>${runtime}</strong><small>${matching.length} registered · ${loaded} loaded</small></div><span class="pill ${loaded&&!unknown?'':'off'}">${unknown?'UNKNOWN':loaded?'ACTIVE':'IDLE'}</span></div>`}).join('')+(state.errors?.length?`<div class="note">${escapeHTML(state.errors.join(' · '))}</div>`:'');}
function gpuValues(){const text=state?.gpu||'';return {load:Number((text.match(/GPU:\s*(\d+)%/)||[])[1]),temp:Number((text.match(/(-?\d+)°C/)||[])[1])};}
function gaugePercent(value) {
  return Number.isFinite(value) && value >= 0 && value <= 100 ? value : null;
}
function memoryGaugeReading(memory) {
  if (!memory || !Number.isFinite(memory.total) || !Number.isFinite(memory.used) || memory.total <= 0 || memory.used < 0 || memory.used > memory.total) return null;
  return {percent: memory.used / memory.total * 100, used: memory.used, total: memory.total};
}
function gaugeMarkup(id, title) {
  return `<div class="gauge-heading"><h2>${title}</h2><span>TELEMETRY</span></div><div class="gauge-visual"><svg viewBox="0 0 240 140" aria-hidden="true" focusable="false"><defs><linearGradient id="${id}-gradient" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#5275df"/><stop offset="1" stop-color="#8964e8"/></linearGradient></defs><path class="gauge-track" d="M 24 118 A 96 96 0 0 1 216 118" pathLength="100"/><path class="gauge-arc" d="M 24 118 A 96 96 0 0 1 216 118" pathLength="100" stroke="url(#${id}-gradient)" stroke-dasharray="100 100"/></svg><div class="gauge-center"><strong class="gauge-value">—</strong><span class="gauge-unit"></span><small class="gauge-percent">Waiting for telemetry</small></div></div><div class="gauge-scale" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div><div class="gauge-detail">Telemetry unavailable</div><span class="gauge-accessible sr-only" role="status"></span>`;
}
function initGauges() {
  for (const [id,title] of [['overview-memory-gauge','Unified Memory'],['overview-gpu-gauge','GPU Utilization'],['overview-cpu-gauge','CPU Utilization'],['performance-memory-gauge','Unified Memory'],['performance-gpu-gauge','GPU Utilization'],['performance-cpu-gauge','CPU Utilization']]) {
    document.getElementById(id).innerHTML = gaugeMarkup(id,title);
  }
}
function updateGauge(id, title, percent, value, unit, detail) {
  const card = document.getElementById(id), valid = gaugePercent(percent) !== null;
  const arc = card.querySelector('.gauge-arc');
  card.querySelector('.gauge-value').textContent = valid ? value : '—';
  card.querySelector('.gauge-unit').textContent = valid ? unit : '';
  card.querySelector('.gauge-percent').textContent = valid ? `${percent.toFixed(1)}% ${title === 'Unified Memory' ? 'used' : 'utilization'}` : 'Unavailable';
  card.querySelector('.gauge-detail').textContent = detail || 'Telemetry unavailable';
  card.querySelector('.gauge-accessible').textContent = valid ? `${title}: ${value} ${unit}, ${percent.toFixed(1)} percent. ${detail}` : `${title}: telemetry unavailable. ${detail || ''}`;
  card.classList.toggle('gauge-animated', valid && card.dataset.hasValue === 'true');
  arc.style.strokeDashoffset = String(100-(valid ? percent : 0));
  arc.style.visibility = valid && percent > 0 ? 'visible' : 'hidden';
  card.dataset.hasValue = valid ? 'true' : 'false';
}
function renderGauges(memory, gpu, cpu) {
  const m = memoryGaugeReading(memory);
  const available = Number.isFinite(memory?.available) && memory.available >= 0 && Number.isFinite(memory?.total) && memory.available <= memory.total ? gib(memory.available) : null;
  const memoryDetail = m ? `${gib(m.total)} total · ${available === null ? 'Available memory unavailable' : available + ' available'}` : 'Telemetry unavailable';
  for (const id of ['overview-memory-gauge','performance-memory-gauge']) {
    updateGauge(id,'Unified Memory',m?.percent ?? null,m ? (m.used/1073741824).toFixed(1) : '', 'GiB', memoryDetail);
  }
  const temp = Number.isFinite(gpu?.temp) ? `${gpu.temp}°C` : 'Unavailable';
  const gpuDetail = `GPU temperature: ${temp}`;
  for (const [id,title,reading,detail] of [['overview-gpu-gauge','GPU Utilization',gpu?.load,gpuDetail],['performance-gpu-gauge','GPU Utilization',gpu?.load,gpuDetail],['overview-cpu-gauge','CPU Utilization',cpu,'System-wide utilization'],['performance-cpu-gauge','CPU Utilization',cpu,'System-wide utilization']]) {
    const value = gaugePercent(reading);
    updateGauge(id,title,value,value === null ? '' : value.toFixed(1),'%', value === null && title === 'CPU Utilization' ? 'Telemetry unavailable' : detail);
  }
}
initGauges();
function renderStatus(){if(!state)return;const g=gpuValues(),loaded=state.models.filter(x=>x.loaded).length;renderGauges(state.memory,g,state.cpu);
$('#loaded-main').textContent=loaded;$('#loaded-sub').textContent=`${state.models.length} registered models`;$('#runtime-summary').innerHTML=statusSummary();$('#storage-summary').innerHTML=storageRows();$('#system-state').textContent=state.operation.busy?`Running: ${state.operation.job}`:state.errors.length?'Some runtime checks unavailable':'Monitoring local system';$('#refresh-tag').textContent=`Updated ${new Date(state.time*1000).toLocaleTimeString()}`;$('#connection-dot').style.background=state.errors.length?'#db9d36':'#39cea2';renderModels();renderPerformance();drawCharts();
const current=JSON.stringify(state.operation);if(current!==lastOperation){if(lastOperation&&state.operation.error)toast('Operation failed: '+state.operation.error,9000);else if(lastOperation&&!state.operation.busy&&state.operation.message!=='Ready')toast(state.operation.message,7000);lastOperation=current;}}
function modelBlocked(model) {
  return !connectionHealthy || submitting || state.operation.busy || model.uncertain;
}
function renderModels(){
  if(!state){$('#operation-status').innerHTML='<strong>Waiting for workstation data</strong><span>If the connection is unavailable, use Refresh to reconnect. Model actions remain disabled.</span>';return;}
  const focus=document.activeElement;
  const focusKey=focus?.dataset.id, focusAction=focus?.dataset.action;
  const focusedDetail=focus?.tagName==='SUMMARY'?focus.parentElement.dataset.key:null;
  const expanded=new Set($$('#model-cards details[open]').map(e=>e.dataset.key));
  const search=($('#model-search').value||'').toLowerCase();
  const models=state.models.filter(m=>(m.name+' '+m.runtime).toLowerCase().includes(search)).filter(m=>modelFilter==='all'||(modelFilter==='loaded'&&m.loaded)||(modelFilter==='unloaded'&&!m.loaded&&!m.uncertain)||(modelFilter==='attention'&&m.uncertain));
  $('#model-count').textContent=`${models.length} of ${state.models.length}`;
  const mem=memoryGaugeReading(state.memory);
  $('#manager-capacity').innerHTML=`<div><strong>Unified memory</strong><span>${mem?gib(mem.used)+' used / '+gib(mem.total):'Unavailable'}</span></div>${mem?`<progress max="100" value="${mem.percent}" aria-label="System unified memory used"></progress>`:''}<span>System-wide · Not per-model allocation</span>`;
  const op=state.operation;
  $('#operation-status').classList.toggle('has-error',!!op.error||!connectionHealthy);
  $('#operation-status').innerHTML=!connectionHealthy?'<strong>Connection unavailable — model actions paused</strong><span>Use Refresh to reconnect before taking action.</span>':op.busy?`<strong>${escapeHTML(op.job||'Operation in progress')}</strong><progress aria-label="Operation in progress"></progress><span>Waiting for runtime confirmation. Completion percentage is unavailable.</span>`:op.error?`<strong>Operation failed</strong><span>${escapeHTML(op.error)}</span><span>Review Activity and refresh process state before retrying. Recovery is not guaranteed.</span>`:`<strong>${escapeHTML(op.message||'Ready')}</strong><span>${DEMO?'Simulation only':'Process monitoring connected'} · Inference readiness is not verified</span>`;
  $('#model-cards').innerHTML=models.length?models.map(m=>`<article class="model-card ${m.loaded?'is-loaded':''}"><div class="model-header"><span class="pill ${m.uncertain?'attention':m.loaded?'':'off'}">${m.uncertain?'Needs attention':m.loaded?'Loaded':'Unloaded'}</span><span class="runtime-label">${escapeHTML(m.runtime)}</span></div><h3>${escapeHTML(m.name)}</h3><p>${m.embedding?'Embedding model':'Registered inference model'}</p><dl class="model-facts"><div><dt>Runtime memory</dt><dd>${escapeHTML(m.memory||'Unavailable')}</dd></div><div><dt>Readiness</dt><dd>Not verified</dd></div></dl><details data-key="${escapeHTML(m.key)}" ${expanded.has(m.key)?'open':''}><summary>Model details</summary><dl><dt>Runtime identifier</dt><dd>${escapeHTML(m.key)}</dd><dt>Observed process state</dt><dd>${escapeHTML(m.status||(m.loaded?'Loaded':'Unloaded'))}</dd></dl><p>Memory is runtime-reported when available. Required capacity and connected clients are unknown.</p></details><div class="model-actions"><button class="${m.loaded?'secondary':'primary'} small model-action" data-id="${escapeHTML(m.key)}" data-action="${m.loaded?'unload':'load'}" ${modelBlocked(m)?'disabled':''}>${m.loaded?'Unload':'Load'} model</button>${!m.loaded?`<button class="secondary small model-action" data-id="${escapeHTML(m.key)}" data-action="switch" ${modelBlocked(m)?'disabled':''}>Switch to…</button>`:''}</div>${m.uncertain?'<p class="card-warning">Refresh process state before operating this model.</p>':''}</article>`).join(''):'<div class="empty-state"><h3>No models found</h3><p>Try another search or filter. If the inventory is empty, refresh and inspect runtime status in Overview.</p></div>';
  $$('.model-action').forEach(b=>b.onclick=()=>showModal(b.dataset.action,b.dataset.id));
  if(focusedDetail)$$('#model-cards details').find(d=>d.dataset.key===focusedDetail)?.querySelector('summary').focus();
  if(focusKey)$$('.model-action').find(b=>b.dataset.id===focusKey&&b.dataset.action===focusAction)?.focus();
}
$$('[data-filter]').forEach(b=>b.onclick=()=>{modelFilter=b.dataset.filter;$$('[data-filter]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b));});renderModels();});
$('#model-search').oninput=renderModels;
function showModal(action,id){if(!state||!connectionHealthy||submitting||state.operation.busy)return;const target=state.models.find(x=>x.key===id);if(!target||target.uncertain)return;modalTrigger={element:document.activeElement,key:id,action};modalData={action,target};$('#modal-title').textContent=action==='switch'?'Switch active model':`${action==='load'?'Load':'Unload'} model`;$('#modal-desc').textContent=action==='switch'?`Select the loaded models you explicitly agree to stop before loading ${target.name}. Any models left unchecked will remain active.`:`${action==='unload'?'Unloading may interrupt connected applications.':'This model will be loaded into unified memory.'} Confirm ${action} for ${target.name}.`;
$('#modal-options').innerHTML=action==='switch'?`<p>Models to unload (optional):</p>${state.models.filter(x=>x.loaded&&x.key!==id).map(x=>`<label class="check-line"><input type="checkbox" class="stop-checkbox" data-id="${escapeHTML(x.key)}"> ${escapeHTML(x.name)} (${escapeHTML(x.runtime)})</label>`).join('')}<small class="warning-text">If loading fails, recovery is attempted but is not guaranteed.</small>`:'<small>No other models will be changed.</small>';
$('#modal-accept').textContent=action==='switch'?'Confirm switch':'Confirm';$('#modal').classList.remove('modal-hidden');$('#app').inert=true;$('#modal-cancel').focus();}
function closeModal(){modalData=null;$('#modal').classList.add('modal-hidden');$('#app').inert=false;const trigger=$$('.model-action').find(b=>b.dataset.id===modalTrigger?.key&&b.dataset.action===modalTrigger?.action);if(trigger&&!trigger.disabled)trigger.focus();else if(modalTrigger?.element?.isConnected)modalTrigger.element.focus();else $('#model-search').focus();}
$('#modal-cancel').onclick=closeModal;$('#modal-backdrop').onclick=closeModal;
$('#modal').addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();closeModal();}
  if(e.key==='Tab'){const items=$$('#modal button, #modal input').filter(x=>!x.disabled);const first=items[0],last=items[items.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}
});
$('#modal-accept').onclick=async()=>{
  if(!modalData||submitting)return;
  const {action,target}=modalData,stops=$$('.stop-checkbox:checked').map(e=>e.dataset.id);
  if(!connectionHealthy||state.operation.busy||!state.models.some(m=>m.key===target.key&&!m.uncertain)){closeModal();toast('State changed. Refresh and review the model before retrying.');return;}
  submitting=true;closeModal();renderModels();
  try{await request('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,target:target.key,stops})});toast(DEMO?'Simulated operation started.':'Operation started. Status will update automatically.');await update();}
  catch(e){$('#operation-status').textContent='Request failed: '+e.message+'. Refresh state before retrying.';toast(e.message,8000);}
  finally{submitting=false;$$('.model-action').forEach(b=>{const m=state.models.find(m=>m.key===b.dataset.id);b.disabled=!m||modelBlocked(m);});}
};
let updating=false;
async function update(){if(updating)return;updating=true;try{state=await request('/api/status');connectionHealthy=true;renderStatus();if(DEMO){$('#refresh-tag').textContent='Simulated telemetry';$('#system-state').textContent='Prototype · No runtime connection';}}catch(e){connectionHealthy=false;renderGauges(null,null,null);$('#system-state').textContent='Connection unavailable';$('#refresh-tag').textContent='Telemetry stale';$('#connection-dot').style.background='#ed7272';renderModels();toast('Cannot reach local manager: '+e.message);}finally{updating=false;}}
$('#refresh-btn').onclick=update;
const chartSelection = {};
const GIB = 1024 ** 3, CHART_MAX_GIB = 128, CHART_LEFT = 75;
function chartSamples(history) {
  if (!Array.isArray(history)) return [];
  return history.filter(s => s && Number.isFinite(s.time) && Number.isFinite(s.memory) && s.memory >= 0 && Number.isFinite(new Date(s.time * 1000).getTime())).sort((a,b) => a.time-b.time);
}
function chartTime(timestamp) {
  const d = new Date(timestamp * 1000), pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
function drawChart(canvas, history) {
  if (!canvas || !canvas.getClientRects().length) return;
  const w = canvas.getBoundingClientRect().width, h = Number(canvas.dataset.chartHeight || canvas.getAttribute('height')) || 210;
  if (w <= 0) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.dataset.chartHeight = String(h);
  canvas.width = w*dpr; canvas.height = h*dpr;
  const ctx = canvas.getContext('2d'), dark = document.body.classList.contains('dark');
  const samples = chartSamples(history);
  const left = CHART_LEFT, right = Math.max(left+1, w-15), top = 16, bottom = h-48;
  ctx.scale(dpr,dpr); ctx.clearRect(0,0,w,h);
  ctx.font = '11px sans-serif'; ctx.fillStyle = dark ? '#c4c9d8' : '#49516a';
  ctx.textBaseline = 'middle'; ctx.textAlign = 'right';
  ctx.strokeStyle = dark ? '#525b70' : '#d4d8e2'; ctx.lineWidth = 1;
  for (let i=0; i<=8; i++) {
    const y = top+(bottom-top)*i/8;
    ctx.beginPath(); ctx.moveTo(left,y); ctx.lineTo(right,y); ctx.stroke();
    ctx.fillText(String(CHART_MAX_GIB-i*16), left-8, y);
  }
  ctx.save(); ctx.translate(12,(top+bottom)/2); ctx.rotate(-Math.PI/2);
  ctx.textAlign='center'; ctx.fillText('Used Memory (GiB)',0,0); ctx.restore();
  ctx.textAlign='center'; ctx.textBaseline='bottom'; ctx.fillText('Time',(left+right)/2,h-2);
  const selectionText = canvas.id === 'performance-chart' ? '#timeline-selection' : '#overview-timeline-selection';
  if (!samples.length) {
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('Waiting for memory samples', (left+right)/2, (top+bottom)/2);
    $(selectionText).textContent = 'Waiting for memory samples.';
    return;
  }
  const first = samples[0].time, last = samples[samples.length-1].time;
  const xFor = t => first === last ? (left+right)/2 : left+(t-first)/(last-first)*(right-left);
  const points = samples.map(s => ({x:xFor(s.time), y:bottom-Math.min(s.memory/GIB,CHART_MAX_GIB)/CHART_MAX_GIB*(bottom-top), sample:s}));
  ctx.textBaseline = 'top'; ctx.textAlign = first === last ? 'center' : 'left'; ctx.fillText(chartTime(first), first === last ? (left+right)/2 : left, bottom+10);
  if (first !== last) {ctx.textAlign='right'; ctx.fillText(chartTime(last), right, bottom+10);}
  ctx.beginPath(); points.forEach((p,i) => i ? ctx.lineTo(p.x,p.y) : ctx.moveTo(p.x,p.y));
  ctx.lineWidth = 2.5; ctx.strokeStyle = dark ? '#b8a5ff' : '#6046cf'; ctx.stroke();
  if (points.length === 1) {ctx.beginPath(); ctx.arc(points[0].x,points[0].y,3,0,2*Math.PI); ctx.fillStyle=ctx.strokeStyle; ctx.fill();}
  {
    const selected = points.find(p => p.sample.time === chartSelection[canvas.id]);
    const description = selected ? `${chartTime(selected.sample.time)} · ${gib(selected.sample.memory)} used${selected.sample.memory/GIB > CHART_MAX_GIB ? ' (above chart scale)' : ''}` : `${samples.length} samples.${samples.some(s => s.memory/GIB > CHART_MAX_GIB) ? ' Values above 128 GiB are clipped.' : ''} Hover, tap, or use arrow keys to inspect.`;
    $(selectionText).textContent = description;
    if (selected) {
      ctx.beginPath(); ctx.arc(selected.x,selected.y,4,0,2*Math.PI); ctx.fillStyle=dark?'#ded6ff':'#4932af'; ctx.fill();
      ctx.font='12px sans-serif'; const width=Math.min(w-8,ctx.measureText(description).width+16);
      const x=Math.max(4,Math.min(w-width-4,selected.x-width/2)), y=Math.max(2,selected.y-34);
      ctx.fillStyle=dark?'#f5f5fb':'#24243e'; ctx.fillRect(x,y,width,24);
      ctx.fillStyle=dark?'#171a2a':'#ffffff'; ctx.textBaseline='middle'; ctx.textAlign='center'; ctx.fillText(description,x+width/2,y+12,width-12);
    }
  }
}
function drawCharts(){if(!state)return;drawChart($('#memory-chart'),state.history);drawChart($('#performance-chart'),state.history);$('#chart-note').textContent=state.history.length+' samples in session';}
function setupTimeline(timeline) {
  function selectAt(clientX) {
    const samples = chartSamples(state?.history);
    if (!samples.length) return;
    const rect=timeline.getBoundingClientRect(), left=CHART_LEFT, right=Math.max(left+1,rect.width-15);
    const fraction=Math.max(0,Math.min(1,(clientX-rect.left-left)/(right-left)));
    const time=samples[0].time+fraction*(samples[samples.length-1].time-samples[0].time);
    chartSelection[timeline.id]=samples.reduce((a,b)=>Math.abs(b.time-time)<Math.abs(a.time-time)?b:a).time;
    drawCharts();
  }
  timeline.addEventListener('pointermove', e=>selectAt(e.clientX));
  timeline.addEventListener('pointerdown', e=>selectAt(e.clientX));
  timeline.addEventListener('pointerleave', e=>{if(e.pointerType==='mouse'){delete chartSelection[timeline.id];drawCharts();}});
  timeline.addEventListener('keydown', e=>{
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return;
    const samples=chartSamples(state?.history); if (!samples.length) return;
    e.preventDefault(); let i=samples.findIndex(s=>s.time===chartSelection[timeline.id]);
    if (e.key==='Home') i=0; else if (e.key==='End') i=samples.length-1;
    else if (i<0) i=e.key==='ArrowLeft'?samples.length-1:0;
    else i=Math.max(0,Math.min(samples.length-1,i+(e.key==='ArrowRight'?1:-1)));
    chartSelection[timeline.id]=samples[i].time; drawCharts();
  });
}
setupTimeline($('#memory-chart')); setupTimeline($('#performance-chart'));
window.addEventListener('resize',drawCharts);
function renderPerformance(){if(!state)return;const g=gpuValues();$('#hardware-details').innerHTML=[['Unified memory',gib(state.memory.total)],['Memory in use',gib(state.memory.used)],['Available memory',gib(state.memory.available)],['GPU utilization',Number.isFinite(g.load)?g.load+'%':'Unavailable'],['GPU temperature',Number.isFinite(g.temp)?g.temp+'°C':'Unavailable'],['CPU utilization',state.cpu===null?'Collecting…':state.cpu+'%']].map(([k,v])=>`<div class="detail-row"><span>${k}</span><strong>${v}</strong></div>`).join('');$('#storage-detail').innerHTML=storageRows();}
async function scanNAS(){try{$('#nas-summary').textContent='Scanning NAS metadata…';library=await request('/api/library');renderLibrary();}catch(e){$('#nas-summary').textContent='NAS scan failed: '+e.message;}}
function renderLibrary(){if(!library)return;const items=libraryView==='groups'?library.groups:library.files;$('#nas-summary').textContent=`${library.files.length} weight files · ${library.groups.length} collections · ${library.status}`;$('#library-content').innerHTML=items.length?items.map(x=>libraryView==='groups'?`<div class="library-item"><em>${escapeHTML(x.category)}</em><strong>${escapeHTML(x.name)}</strong><small>${x.files} weight file(s) · ${gib(x.bytes)} stored</small><small>Formats: ${escapeHTML(x.formats.join(', '))}</small><small>Asset group · Not automatically loadable</small></div>`:`<div class="library-item"><em>${escapeHTML(x.format)}</em><strong>${escapeHTML(x.path)}</strong><small>${gib(x.size)} · Stored on NAS</small></div>`).join(''):'<p>No model weights were discovered in the scanned directories.</p>';}
$('#scan-btn').onclick=scanNAS;$$('[data-library]').forEach(b=>b.onclick=()=>{$$('[data-library]').forEach(x=>x.classList.toggle('selected',x===b));libraryView=b.dataset.library;renderLibrary();});
const presets=[['⌘','Coding','Software engineering and code assistance','Suggested: Qwen3-Coder-Next'],['⌁','Scientific Research','Scientific reasoning and analysis','Suggested: reasoning-oriented LLM'],['✦','General AI','Everyday reasoning and productivity','Suggested: Qwen 3.8 / Qwen3.5'],['◩','Image Studio','Creative image workflows','Requires a compatible image runtime'],['▤','Video Studio','Generation and post-production','Requires a compatible video workflow'],['◉','Voice Studio','Text-to-speech and audio','Requires a compatible audio runtime']];$('#workspace-grid').innerHTML=presets.map(([icon,title,desc,note])=>`<article class="workspace-card glass"><div class="symbol">${icon}</div><h2>${title}</h2><p>${desc}</p><small>${note}</small></article>`).join('');
async function refreshActivity(){try{const events=await request('/api/activity');$('#activity-list').innerHTML=events.length?events.map(e=>`<div class="activity-entry"><i></i><div><strong>${escapeHTML(e.operation)} · ${escapeHTML(e.stage)}</strong><small>${escapeHTML(e.model||'System')} · ${escapeHTML(e.time||'')}</small>${e.detail?`<small>${escapeHTML(e.detail)}</small>`:''}</div></div>`).join(''):'<p style="color:var(--sub)">No operations recorded yet.</p>';}catch(e){toast(e.message);}}
$('#activity-refresh').onclick=refreshActivity;
const demoState={time:Date.now()/1000,memory:{total:128*1073741824,used:52*1073741824,available:76*1073741824},cpu:14,gpu:'GPU: 28% · 46°C',errors:[],storage:[{name:'Local storage',online:true,total:2000*1073741824,free:1350*1073741824}],history:Array.from({length:30},(_,i)=>({time:Date.now()/1000-(29-i)*5,memory:(48+Math.sin(i/4)*4)*1073741824})),operation:{busy:false,job:null,message:'Ready',error:null},models:[{key:'sglang',name:'Qwen3-Coder-Next',runtime:'SGLang',memory:'Not available',loaded:true},{key:'qwen3:8b',name:'qwen3:8b',runtime:'Ollama',memory:'—',loaded:false},{key:'nomic-embed-text',name:'nomic-embed-text',runtime:'Ollama',memory:'0.3 GiB',loaded:true,embedding:true},{key:'example-unavailable',name:'Example unavailable model',runtime:'SGLang',memory:'Not available',loaded:false,uncertain:true}]};
const demoEvents=[];
async function demoRequest(path,opts={}){
  if(path==='/api/status'){demoState.time=Date.now()/1000;return structuredClone(demoState);}
  if(path==='/api/activity')return structuredClone(demoEvents);
  if(path==='/api/library')return {status:'Representative inventory · No NAS access',groups:[{name:'Research collection',category:'Language',files:2,bytes:32*1073741824,formats:['safetensors']}],files:[{path:'Example / research / model-00001.safetensors',format:'safetensors',size:16*1073741824},{path:'Example / research / model-00002.safetensors',format:'safetensors',size:16*1073741824}]};
  if(path!=='/api/action')throw Error('Unknown prototype request');
  if(demoState.operation.busy)throw Error('An operation is already running');
  const {action,target,stops=[]}=JSON.parse(opts.body),m=demoState.models.find(x=>x.key===target);
  if(!m||m.uncertain)throw Error('Model state is unavailable');
  const fail=failNextDemo&&action!=='unload';failNextDemo=false;$('#demo-failure').setAttribute('aria-pressed','false');
  demoState.operation={busy:true,job:action+': '+m.name,message:'Waiting for simulated runtime',error:null};
  setTimeout(()=>{
    if(!fail){if(action==='switch')demoState.models.forEach(x=>{if(stops.includes(x.key))x.loaded=false;});m.loaded=action!=='unload';}
    const message=fail?'Simulated load failed. Previous models remain unchanged.':'Simulated operation complete';
    demoState.operation={busy:false,job:null,message,error:fail?message:null};demoEvents.unshift({operation:action,stage:fail?'Failed':'Complete',model:m.name,time:new Date().toLocaleTimeString(),detail:message});update();
  },2400);
  return {message:'Simulation accepted'};
}
const navigationIcons=['M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z', 'M4 5h16v14H4z M8 9h8 M8 13h5', 'M4 4h16v16H4z M8 4v16 M12 8h4 M12 12h4', 'M3 19h18 M6 15V9 M12 15V4 M18 15v-7', 'M3 7h18v13H3z M3 7V4h7l3 3', 'M12 3a9 9 0 1 0 9 9 M12 7v5l4 2', 'M4 6h16 M4 12h16 M4 18h16 M8 3v6 M16 9v6 M10 15v6'];
$$('.nav-item').forEach((b,i)=>{b.querySelector('span').innerHTML=`<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${navigationIcons[i]}"/></svg>`;});
function uiIcon(path){return `<svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg>`;}
$('.brand-mark').innerHTML=uiIcon('M4 18 10 5h4l6 13 M7 13h10');
$('#theme-btn').innerHTML=uiIcon('M12 3a9 9 0 1 0 9 9 7 7 0 0 1-9-9');
$('#refresh-btn').innerHTML=uiIcon('M20 9a8 8 0 1 0 0 6 M20 3v6h-6');
$$('.quick-grid b').forEach((b,i)=>b.innerHTML=uiIcon(navigationIcons[[1,2,3,5][i]]));
$('.metric-heading span').innerHTML=uiIcon(navigationIcons[1]);
$('#settings-theme').onclick=()=>$('#theme-btn').click();
const prototypeURL=new URL(location.href);prototypeURL.searchParams.set('demo','1');$('#prototype-link').href=prototypeURL.href;
setPage(DEMO?'models':'dashboard');
if(DEMO){$('#demo-banner').hidden=false;}
$('#demo-failure').onclick=()=>{failNextDemo=!failNextDemo;$('#demo-failure').setAttribute('aria-pressed',String(failNextDemo));};
update();setInterval(update,5000);
