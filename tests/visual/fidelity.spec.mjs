import {test,expect} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const url=p=>pathToFileURL(path.resolve(p)).href;
for(const theme of ['light','dark']) for(const [width,height] of [[1440,960],[1024,768],[390,844]]) test(`${theme} ${width} prototype material contract`,async({browser})=>{
 const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1,reducedMotion:'reduce'});
 await context.route('**/*',r=>new URL(r.request().url()).protocol==='file:'?r.continue():r.abort());
 const proto=await context.newPage(), prod=await context.newPage();
 await proto.goto(url('prototypes/liquid-glass/hybrid/index.html')+`?theme=${theme}`);
 await prod.goto(url('web/index.html')+'?demo=1');
 if((await prod.locator('body').getAttribute('class')||'').includes('dark')!==(theme==='dark')) await prod.locator('#theme-btn').click();
 const read=async(page,selector)=>page.locator(selector).evaluate(el=>{const s=getComputedStyle(el), p=getComputedStyle(el,'::before'),b=getComputedStyle(document.body);return {color:s.backgroundColor,image:s.backgroundImage,blur:s.backdropFilter,border:s.borderTopColor,shadow:s.boxShadow,radius:parseFloat(s.borderRadius),pseudo:p.backgroundImage,mask:p.maskImage,body:b.backgroundImage,bg:b.backgroundColor,support:CSS.supports('backdrop-filter','blur(1px)')};});
 const a=await read(proto,'.instrument'),b=await read(prod,'.overview-instruments');
 expect(b.bg).toBe(a.bg);expect(b.body).toBe(a.body);expect(b.color).toBe(a.color);
 if(a.support){expect(b.blur).toBe(a.blur);expect(b.image).toBe(a.image);}
 expect(b.border).toBe(a.border);expect(b.shadow).toBe(a.shadow);expect(b.pseudo).toBe(a.pseudo);expect(b.mask).toBe(a.mask);
 // Production's 24px enclosing radius preserves its existing geometry; prototype is 22px.
 expect(Math.abs(b.radius-a.radius)).toBeLessThanOrEqual(2);
 expect(await prod.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
 await context.close();
});
