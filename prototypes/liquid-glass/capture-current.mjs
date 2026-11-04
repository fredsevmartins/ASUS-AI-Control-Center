import {chromium,firefox} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
for(const [name,engine] of Object.entries({chromium,firefox})){
 const browser=await engine.launch();const page=await browser.newPage({viewport:{width:1440,height:960},reducedMotion:'reduce'});await page.route('**/*',r=>new URL(r.request().url()).protocol==='file:'?r.continue():r.abort());
 await page.goto(pathToFileURL(path.resolve('web/index.html')).href+'?demo=1');await page.locator('#model-cards .model-card').first().waitFor();
 for(const theme of ['light','dark']){if((await page.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark'))await page.locator('#theme-btn').click();await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`prototypes/liquid-glass/evidence/${name}-${theme}-current.png`,animations:'disabled'});}
 await browser.close();
}
