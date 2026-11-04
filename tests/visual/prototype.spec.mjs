import {test,expect} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const url=pathToFileURL(path.resolve('prototypes/liquid-glass/index.html')).href;
for(const theme of ['light','dark']) for(const concept of ['a','b']) test(`${concept} ${theme} material`,async({page})=>{
 await page.route('**/*',route=>new URL(route.request().url()).protocol==='file:'?route.continue():route.abort());
 await page.goto(`${url}?concept=${concept}&theme=${theme}`); await page.evaluate(()=>document.fonts.ready);
 const style=await page.locator('.instrument').evaluate(el=>{const s=getComputedStyle(el),b=getComputedStyle(document.body);return {bg:s.backgroundColor,blur:s.backdropFilter,radius:s.borderRadius,shadow:s.boxShadow,theme:b.getPropertyValue('--bg').trim(),supported:CSS.supports('backdrop-filter','blur(1px)')};});
 expect(style.bg).toMatch(/rgba?\(/); expect(style.theme.toLowerCase()).toBe(theme==='dark'?'#090e17':'#edf0f3'); expect(parseFloat(style.radius)).toBeGreaterThanOrEqual(20);expect(style.shadow).not.toBe('none');if(style.supported)expect(style.blur).toContain('blur');
 // Historical A/B concepts are retained as material smoke tests, not approved visual baselines.
});
