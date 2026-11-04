import {chromium,firefox} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {mkdir} from 'node:fs/promises';
const out='prototypes/liquid-glass/hybrid/evidence/final';await mkdir(out,{recursive:true});
for(const [name,engine] of Object.entries({chromium,firefox})){
 const browser=await engine.launch();
 for(const theme of ['light','dark'])for(const [width,height] of [[1440,960],[1024,768],[768,1024],[390,844],[320,720]])for(const view of ['overview','models','details']){
  const page=await browser.newPage({viewport:{width,height},reducedMotion:'reduce',deviceScaleFactor:1});
  await page.route('**/*',r=>new URL(r.request().url()).protocol==='file:'?r.continue():r.abort());
  await page.goto(pathToFileURL(path.resolve('prototypes/liquid-glass/hybrid/index.html')).href+`?theme=${theme}&view=${view}`);await page.evaluate(()=>document.fonts.ready);
  await page.screenshot({path:`${out}/${name}-${theme}-${width}-${view}.png`,animations:'disabled',fullPage:view!=='details'});await page.close();
 }
 await browser.close();
}
