import {test,expect} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {existsSync} from 'node:fs';
const url=pathToFileURL(path.resolve('prototypes/liquid-glass/index.html')).href;
for(const theme of ['light','dark']) for(const concept of ['a','b']) test(`${concept} ${theme} material`,async({page},testInfo)=>{
 await page.route('**/*',route=>new URL(route.request().url()).protocol==='file:'?route.continue():route.abort());
 await page.goto(`${url}?concept=${concept}&theme=${theme}`); await page.evaluate(()=>document.fonts.ready);
 const style=await page.locator('.instrument').evaluate(el=>{const s=getComputedStyle(el),b=getComputedStyle(document.body);return {bg:s.backgroundColor,blur:s.backdropFilter,radius:s.borderRadius,shadow:s.boxShadow,theme:b.getPropertyValue('--bg').trim(),supported:CSS.supports('backdrop-filter','blur(1px)')};});
 expect(style.bg).toMatch(/rgba?\(/); expect(style.theme.toLowerCase()).toBe(theme==='dark'?'#090e17':'#edf0f3'); expect(parseFloat(style.radius)).toBeGreaterThanOrEqual(20);expect(style.shadow).not.toBe('none');if(style.supported)expect(style.blur).toContain('blur');
 await page.screenshot({path:testInfo.outputPath(`${concept}-${theme}.png`),animations:'disabled'});
 // No approved reference exists yet. These snapshots intentionally fail until reviewed and explicitly created.
 expect(existsSync(testInfo.snapshotPath(`${concept}-${theme}.png`)) || process.env.APPROVE_PROTOTYPE_SNAPSHOTS === '1', 'Reference requires explicit visual approval').toBe(true);
 expect(await page.screenshot({animations:'disabled'})).toMatchSnapshot(`${concept}-${theme}.png`);
});
