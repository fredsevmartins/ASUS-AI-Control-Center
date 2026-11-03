'use strict';
// No HTTP calls or real runtime operations: evaluate the prototype and action guards in isolation.
const assert=require('assert');
const fs=require('fs');
const vm=require('vm');
const source=fs.readFileSync('web/app.js','utf8');
const timers=[];
let networkCalls=0;
const context={URLSearchParams,structuredClone,Date,JSON,Error,setTimeout:fn=>timers.push(fn),update:()=>{},
  $:()=>({setAttribute:()=>{}}),fetch:()=>{networkCalls++;throw Error('Network forbidden');},TOKEN:'test'};
vm.createContext(context);
const fixture=source.slice(source.indexOf('const demoState='),source.indexOf('const navigationIcons='));
const request=source.slice(source.indexOf('async function request('),source.indexOf('function setPage('));
vm.runInContext('const DEMO=true;let failNextDemo=false;'+fixture+request,context);
(async()=>{
  async function action(payload){const plan=await context.request('/api/preflight',{body:JSON.stringify(payload)});return context.request('/api/action',{body:JSON.stringify({...payload,plan_id:plan.id,confirmed:true,acknowledge_risks:true})});}
  const before=await context.request('/api/status');
  assert(before.models[0].loaded);
  before.models[0].loaded=false;
  assert((await context.request('/api/status')).models[0].loaded,'status returns an independent snapshot');
  await action({action:'switch',target:'qwen3:8b',stops:['sglang']});
  assert((await context.request('/api/status')).operation.busy);
  await assert.rejects(context.request('/api/action',{body:'{}'}),/already running/);
  timers.shift()();
  let after=await context.request('/api/status');
  assert(!after.models[0].loaded && after.models[1].loaded);
  assert(after.models[2].loaded,'unselected model must remain loaded');
  vm.runInContext('failNextDemo=true',context);
  await action({action:'switch',target:'sglang',stops:['qwen3:8b']});
  timers.shift()();
  after=await context.request('/api/status');
  assert(after.operation.error && after.models[1].loaded && !after.models[0].loaded);
  assert.strictEqual((await context.request('/api/activity')).length,2);
  assert((await context.request('/api/library')).status.includes('No NAS access'));
  await assert.rejects(context.request('/api/unknown'),/Unknown prototype/);
  const confirmation={action:'load',target:'qwen3:8b',stops:[]};
  const plan=await context.request('/api/preflight',{body:JSON.stringify(confirmation)});
  await assert.rejects(context.request('/api/action',{body:JSON.stringify({...confirmation,plan_id:plan.id})}),/Explicit confirmation/);
  const confirmed={...confirmation,plan_id:plan.id,confirmed:true,acknowledge_risks:true};
  await context.request('/api/action',{body:JSON.stringify(confirmed)});timers.shift()();
  await assert.rejects(context.request('/api/action',{body:JSON.stringify(confirmed)}),/new preflight/);
  assert.strictEqual(networkCalls,0,'demo must never reach fetch');
  const guard=source.slice(source.indexOf('function modelBlocked('),source.indexOf('const phaseLabels='));
  const safety={connectionHealthy:true,submitting:false,state:{operation:{busy:false}}};
  vm.createContext(safety);vm.runInContext(guard,safety);
  assert(!safety.modelBlocked({uncertain:false}));
  for(const flag of ['connectionHealthy','submitting']){const old=safety[flag];safety[flag]=!old;assert(safety.modelBlocked({}));safety[flag]=old;}
  assert(safety.modelBlocked({uncertain:true}));safety.state.operation.busy=true;assert(safety.modelBlocked({}));
  console.log('Prototype isolation, explicit switch selection, failure recovery and action guard tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
