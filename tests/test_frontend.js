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
