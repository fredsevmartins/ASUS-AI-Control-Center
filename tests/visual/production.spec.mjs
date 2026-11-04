import {test,expect} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const url=pathToFileURL(path.resolve('web/index.html')).href+'?demo=1';
test.beforeEach(async({page})=>{
 await page.clock.setFixedTime(new Date('2026-01-15T12:00:00Z'));
 await page.route('**/*',r=>new URL(r.request().url()).protocol==='file:'?r.continue():r.abort());
 await page.goto(url); await page.locator('#model-cards .model-card').first().waitFor();
});
for(const theme of ['light','dark']) for(const [width,height] of [[1440,960],[1024,768],[390,844],[320,720]]) test(`${theme} ${width} production materials and interaction`,async({page})=>{
 await page.setViewportSize({width,height});
 await page.locator('.nav-item[data-page="dashboard"]').click();
 if((await page.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark')) await page.locator('#theme-btn').click();
 const material=await page.locator('.overview-instruments').evaluate(el=>{const s=getComputedStyle(el),b=getComputedStyle(document.body);return {bg:b.getPropertyValue('--bg').trim(),base:b.getPropertyValue('--surface').trim(),alpha:s.backgroundColor,radius:parseFloat(s.borderRadius),shadow:s.boxShadow,border:s.borderTopStyle,blur:s.backdropFilter,support:CSS.supports('backdrop-filter','blur(1px)')};});
 expect(material.bg).toBe(theme==='dark'?'#090e17':'#edf0f3'); expect(material.base).toBe(theme==='dark'?'#19273a':'#ffffff');
 expect(material.radius).toBeGreaterThanOrEqual(20);expect(material.shadow).not.toBe('none');expect(material.border).toBe('solid');
 if(material.support){expect(material.alpha).toContain('0.7');expect(material.blur).toContain('blur');}else expect(material.alpha).not.toContain('0.7');
 expect(await page.locator('.overview-records').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(width>1250?4:width>600?2:1);
 await page.locator('.nav-item[data-page="models"]').click();expect(await page.locator('#model-cards').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(width>1100?3:width>720?2:1);
 const trigger=page.locator('[data-details-key="qwen3:8b"]');await trigger.click();const dialog=page.locator('.details-dialog');await expect(dialog).toBeVisible();
 const bounds=await dialog.evaluate(el=>{const r=el.getBoundingClientRect();return [r.left,r.top,innerWidth-r.right,innerHeight-r.bottom]});for(const edge of bounds) expect(edge).toBeGreaterThanOrEqual(-1);
 await page.locator('#details-close').press('Tab');await expect(page.locator('#details-content')).toBeFocused();await page.locator('#details-content').press('Shift+Tab');await expect(page.locator('#details-close')).toBeFocused();await page.keyboard.press('Escape');await expect(trigger).toBeFocused();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
});
// Approved production views: fixed fixture clock, local assets and reduced motion.
for(const theme of ['light','dark']) for(const [width,height,views] of [
 [1440,960,['dashboard','models','details','library','workspaces','activity','settings']],
 [390,844,['dashboard','models','details']]
]) for(const view of views) test(`approved production ${theme} ${width} ${view}`,async({page})=>{
 await page.setViewportSize({width,height});
 if((await page.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark')) await page.locator('#theme-btn').click();
 await page.locator(`.nav-item[data-page="${view==='details'?'models':view}"]`).click();
 if(view==='details') { await page.locator('[data-details-key="qwen3:8b"]').click(); await expect(page.locator('.details-dialog')).toBeVisible(); }
 await page.evaluate(async()=>{await document.fonts.ready;window.scrollTo(0,0)});
 expect(await page.screenshot({animations:'disabled'})).toMatchSnapshot(`production-${theme}-${width}-${view}.png`);
});
