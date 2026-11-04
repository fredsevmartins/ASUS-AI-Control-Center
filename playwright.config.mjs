import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests/visual',outputDir:'test-results',reporter:'list',use:{viewport:{width:1440,height:960},reducedMotion:'reduce',deviceScaleFactor:1,locale:'en-US',timezoneId:'UTC',screenshot:'only-on-failure'},projects:[{name:'chromium',use:{browserName:'chromium'}},{name:'firefox',use:{browserName:'firefox'}}]});
