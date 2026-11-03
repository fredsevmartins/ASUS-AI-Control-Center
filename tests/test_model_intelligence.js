'use strict';
// Behavioral DOM harness: no sockets, runtime requests, packages or live inference.
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('web/app.js','utf8');
const elements=new Map();
function element(id){if(!elements.has(id))elements.set(id,{innerHTML:'',textContent:'',disabled:false,checked:false,value:'',dataset:{},classList:{add(){},remove(){},toggle(){}},focus(){context.document.activeElement=this;},addEventListener(type,fn){this['on'+type]=fn;}});return elements.get(id);}
const stops=[{dataset:{id:'old'},checked:false}];
let requests=[],pending=[],focusables=[];
const context={console,Date,Map,Set,Number,JSON,Error,encodeURIComponent,URLSearchParams,
  connectionHealthy:true,submitting:false,actionError:'',DEMO:false,modelFilter:'all',modelDetails:new Map(),
  state:{operation:{busy:false},models:[]},modalData:null,modalTrigger:null,
  document:{activeElement:{},},
  $:element,$$:selector=>selector==='.stop-checkbox:checked'?stops.filter(s=>s.checked):selector==='.stop-checkbox'?stops:selector.includes('#modal button')?focusables:[],
  toast:()=>{},update:async()=>{},memoryGaugeReading:()=>null,
  request:async(path,options)=>{requests.push({path,options});return new Promise((resolve,reject)=>pending.push({resolve,reject}));}};
context.document= {activeElement:{},querySelector(){},};element('#app').inert=false;
vm.createContext(context);
const helper=source.slice(source.indexOf('function escapeHTML('),source.indexOf('function pct('));
const models=source.slice(source.indexOf('function modelBlocked('),source.indexOf('let updating=false;'));
vm.runInContext(helper+models,context);
const fixture={key:'target',name:'<script>alert(1)</script>',runtime:'Ollama',loaded:false,state:'unloaded',metadata:{parameters:{value:'8B',confidence:'Verified from runtime',source:'Ollama /api/show'},quantization:{value:'Q4_K_M',confidence:'Verified from runtime',source:'Ollama /api/tags'}},health:{checked_at:'2026-11-03T12:00:00Z',readiness:'Not ready',failure_reason:'<network failure>'}};
const plan={id:'plan',expires_at:Date.now()/1000+120,stops:[],loaded_models:[{key:'old',name:'Previous model'}],available_bytes:40*1073741824,reserve_bytes:6*1073741824,estimated_release_bytes:0,projected_available_bytes:40*1073741824,requirement:{bytes:null,kind:'Unknown requirement',method:'Weight size unavailable'},blocked:false,reasons:[],warnings:['Unknown allocation','Clients may be interrupted'],expected_outcome:'Target resident'};
context.state.models=[fixture,{key:'old',name:'Previous model',loaded:true,runtime:'SGLang',state:'ready'}];
let html=context.modelCardHTML(fixture,true);
assert(html.includes('&lt;script&gt;')&&!html.includes('<script>'),'runtime names are escaped');
assert(html.includes('8B')&&html.includes('Q4_K_M')&&html.includes('Verified from runtime'));
assert(html.includes('Unknown requirement')&&html.includes('Last health check')&&html.includes('&lt;network failure&gt;'));
assert(html.includes('data-action="load"')&&html.includes('data-action="switch"'));
html=context.modelCardHTML({...fixture,state:'unknown',uncertain:true});assert(!html.includes('data-action='));
html=context.modelCardHTML({...fixture,runtime:'SGLang',state:'unknown',uncertain:true,health:{service_status:'active',container_status:'running',readiness:'Unverified',failure_reason:'Authentication required at /get_model_info (HTTP 401); inference readiness is unverified'}});
assert(html.includes('Service process')&&html.includes('>active<')&&html.includes('Container process')&&html.includes('>running<'));
assert(html.includes('Unverified')&&html.includes('HTTP 401')&&!html.includes('Not ready')&&!html.includes('data-action='));
html=context.modelCardHTML({...fixture,state:'error',loaded:true});assert(html.includes('data-action="unload"')&&!html.includes('data-action="load"'));
assert.strictEqual(context.matchingModels(context.state.models,'ollama','all').length,1);
assert.strictEqual(context.matchingModels(context.state.models,'','loaded').length,1);
assert.strictEqual(context.matchingModels([{...fixture,state:'error'}],'','attention').length,1);
assert.strictEqual(context.matchingModels(context.state.models,'does not exist','all').length,0);
assert(context.planHTML({...plan,blocked:true,reasons:['Insufficient memory']}).includes('Insufficient memory'));
assert(context.planHTML(plan).includes('Unknown requirement'));
assert(!context.planHTML(plan).includes('value="'),'no fabricated operation percentages');
const settle=()=>new Promise(setImmediate);
(async()=>{
  context.showModal('switch','target');
  assert(element('#app').inert,'confirmation protects focus');
  assert(element('#modal-accept').disabled,'cannot confirm before preflight');
  assert(element('#modal-options').innerHTML.includes('id="risk-ack"'));
  assert(!stops[0].checked,'no implicit unload selection');
  const initial=pending.shift();
  stops[0].checked=true;
  const refresh=context.refreshPlan();
  const revised=pending.shift();
  initial.resolve({...plan,id:'stale'});await Promise.resolve();
  assert.strictEqual(context.modalData.plan,null,'stale response cannot authorize confirmation');
  revised.resolve({...plan,id:'revised',stops:['old']});await refresh;
  assert.strictEqual(context.modalData.plan.id,'revised');
  assert(element('#modal-accept').disabled,'risk acknowledgement is separate');
  element('#risk-ack').checked=true;element('#risk-ack').onchange();
  assert(!element('#modal-accept').disabled);
  context.closeModal();assert(!element('#app').inert);
  context.showModal('load','target');
  pending.shift().reject(Error('runtime timeout'));
  await settle();
  assert(element('#modal-plan').textContent.includes('runtime timeout'));
  assert(element('#modal-accept').disabled);
  context.closeModal();
  context.showModal('load','target');pending.shift().resolve({...plan,blocked:true,reasons:['Insufficient memory']});
  await settle();
  element('#risk-ack').checked=true;element('#risk-ack').onchange();assert(element('#modal-accept').disabled);
  context.closeModal();
  // Server rejection remains visible after the finally render, rather than reverting to Ready.
  context.showModal('load','target');pending.shift().resolve(plan);await settle();
  element('#risk-ack').checked=true;
  vm.runInContext('renderModels=()=>{}',context);
  const submit=element('#modal-accept').onclick();
  assert.strictEqual(requests.at(-1).path,'/api/action');
  const body=JSON.parse(requests.at(-1).options.body);
  assert(body.confirmed&&body.acknowledge_risks&&body.plan_id==='plan');
  pending.shift().reject(Error('State changed'));await submit;
  assert(context.actionError.includes('State changed'));
  // Accessible focus trap follows DOM order including expandable advanced details.
  focusables=[element('summary'),element('#risk-ack'),element('#modal-cancel'),element('#modal-accept')];
  element('#modal-accept').disabled=false;context.document.activeElement=focusables.at(-1);
  element('#modal').onkeydown({key:'Tab',shiftKey:false,preventDefault(){}});assert.strictEqual(context.document.activeElement,focusables[0]);
  element('#modal').onkeydown({key:'Tab',shiftKey:true,preventDefault(){}});assert.strictEqual(context.document.activeElement,focusables.at(-1));
  const css=fs.readFileSync('web/style.css','utf8');
  assert(css.includes('body.dark')&&css.includes('.metadata-source')&&css.includes('.plan-facts'));
  assert(source.includes('#modal summary')&&source.includes("e.key==='Escape'"));
  console.log('Model evidence, states, filtering, details, preflight races, explicit risk confirmation and error feedback passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
