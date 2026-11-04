import {chromium,firefox} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {mkdir,writeFile} from 'node:fs/promises';
const out=path.resolve('prototypes/liquid-glass/evidence');await mkdir(out,{recursive:true});
for(const [name,engine] of Object.entries({chromium,firefox})){
 const browser=await engine.launch();const page=await browser.newPage({viewport:{width:1440,height:960},reducedMotion:'reduce'});await page.route('**/*',r=>new URL(r.request().url()).protocol==='file:'?r.continue():r.abort());
 const results=[];
 for(const theme of ['light','dark'])for(const concept of ['a','b']){await page.goto(pathToFileURL(path.resolve('prototypes/liquid-glass/index.html')).href+`?concept=${concept}&theme=${theme}`);await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:`${out}/${name}-${theme}-${concept}.png`,animations:'disabled'});results.push(await page.locator('.instrument').evaluate(el=>{let s=getComputedStyle(el);return {background:s.backgroundColor,blur:s.backdropFilter,shadow:s.boxShadow,radius:s.borderRadius,border:s.borderColor,support:CSS.supports('backdrop-filter','blur(1px)')};}));}
 await writeFile(`${out}/${name}-styles.json`,JSON.stringify(results,null,2));await browser.close();
}
