const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const {execFileSync} = require('node:child_process');

test('Pages serves every static mobile route after a direct visit or reload', async () => {
 const root=path.resolve(__dirname,'../..');
 const output=await fs.mkdtemp(path.join(os.tmpdir(),'numerom-pages-routes-'));
 try {
  await fs.writeFile(path.join(output,'index.html'),'<html lang="en"><head></head><body><script src="/numerom-app/_expo/entry.js"></script></body></html>');
  execFileSync(process.execPath,[path.join(root,'scripts/prepare-mobile-pages.mjs'),output],{env:{...process.env,EXPO_PUBLIC_WEB_BASE_PATH:'/numerom-app'}});
  async function walk(folder,segments=[]){
   for(const item of await fs.readdir(folder,{withFileTypes:true})){
    const name=item.name;
    if(item.isDirectory())await walk(path.join(folder,name),name.startsWith('(')?segments:[...segments,name]);
    else if(name.endsWith('.tsx')&&!name.startsWith('_')&&!name.startsWith('+')){
     const route=[...segments,name.replace(/\.tsx$/,'')].filter(p=>p!=='index');
     if(route.some(p=>p.includes('[')))continue;
     const file=path.join(output,...route,'index.html');
     assert.equal(await fs.readFile(file,'utf8'),await fs.readFile(path.join(output,'index.html'),'utf8'),`Missing static route /${route.join('/')}`);
    }
   }
  }
  await walk(path.join(root,'mobile/src/app'));
 } finally {await fs.rm(output,{recursive:true,force:true});}
});
