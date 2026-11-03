'use strict';
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const setPage = source.match(/function setPage\(p\)\{[^\n]+\}/)[0];
let visible = false, drawn = false;
const page = {id: 'performance', classList: {toggle: (name, value) => { visible = value; }}};
const element = {textContent: ''};
const context = {activePage: '', pages: {performance: ['Performance', 'Performance', 'Details']},
  $$: selector => selector === '.page' ? [page] : [],
  $: () => element, renderPerformance: () => {},
  drawCharts: () => { assert(visible, 'chart must be visible before drawing'); drawn = true; }};
vm.runInNewContext(setPage + "\nsetPage('performance');", context);
assert(drawn, 'opening Performance should draw its chart');
console.log('Frontend navigation regression passed');

// Canvas backing-store scaling must not compound across redraws on high-DPI screens.
const drawChart = source.match(/function drawChart\(canvas,history\)\{[^\n]+\}/)[0];
const noop = () => {};
const ctx = {scale: noop, clearRect: noop, beginPath: noop, moveTo: noop, lineTo: noop,
  stroke: noop, closePath: noop, fill: noop,
  createLinearGradient: () => ({addColorStop: noop})};
const canvas = {dataset: {}, width: 0, height: 250, getClientRects: () => [1],
  getBoundingClientRect: () => ({width: 400}),
  getAttribute: function (name) { return name === 'height' ? String(this.height) : null; },
  getContext: () => ctx};
const chartContext = {window: {getComputedStyle: () => ({}), devicePixelRatio: 2},
  document: {body: {classList: {contains: () => false}}}, state: {memory: {total: 100}}};
vm.runInNewContext(drawChart, chartContext);
chartContext.drawChart(canvas, [{memory: 30}]);
assert.strictEqual(canvas.height, 500);
chartContext.drawChart(canvas, [{memory: 30}, {memory: 40}]);
assert.strictEqual(canvas.height, 500, 'redraw must not rescale the previous backing height');
console.log('High-DPI chart redraw regression passed');
