// Reproducible rasterization of the original code-native SVG; no image service.
import {chromium} from 'playwright-core';
import {readFile,writeFile,rm,readdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('.',import.meta.url));
const svg=await readFile(path.join(root,'assets/icon.svg'),'utf8');
const browser=await chromium.launch({headless:true,...(process.env.RUNAWAY_CHROME?{executablePath:process.env.RUNAWAY_CHROME}:{})});
try{
  const page=await browser.newPage({deviceScaleFactor:1});
  async function render(file,size,content=svg){
    await page.setViewportSize({width:size,height:size});
    await page.setContent('<style>body{margin:0;background:#f6f5ed}svg{width:100vw;height:100vh;display:block}</style>'+content);
    await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
    await page.screenshot({path:path.join(root,file)});
  }
  await render('ios/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png',1024);
  const splash=svg.replace('viewBox="0 0 1024 1024"','viewBox="-1800 -1800 4624 4624"');
  await render('ios/App/App/Assets.xcassets/Splash.imageset/splash-2732x2732.png',2732,splash);
  for(const suffix of ['-1','-2'])await writeFile(path.join(root,'ios/App/App/Assets.xcassets/Splash.imageset/splash-2732x2732'+suffix+'.png'),await readFile(path.join(root,'ios/App/App/Assets.xcassets/Splash.imageset/splash-2732x2732.png')));
  for(const [density,size]of Object.entries({mdpi:48,hdpi:72,xhdpi:96,xxhdpi:144,xxxhdpi:192})){
    for(const name of ['ic_launcher','ic_launcher_round'])await render('android/app/src/main/res/mipmap-'+density+'/'+name+'.png',size);
    await render('android/app/src/main/res/mipmap-'+density+'/ic_launcher_foreground.png',size*2.25);
  }
  for(const dir of await readdir(path.join(root,'android/app/src/main/res')))if(/^drawable-(land|port)-/.test(dir))await rm(path.join(root,'android/app/src/main/res',dir),{recursive:true});
  await rm(path.join(root,'android/app/src/main/res/drawable/splash.png'));
}finally{await browser.close();}
