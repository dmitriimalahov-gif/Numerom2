// One-time asset rendering; app builds use the committed PNGs and need no Sharp.
const fs=require('node:fs/promises');
const path=require('node:path');
const crypto=require('node:crypto');
const sharp=require('sharp');
async function main(){
 const root=path.resolve(__dirname,'..');
 const source=await fs.readFile(path.join(root,'packages/brand/numerom-logo.svg'));
 const output=path.join(root,'mobile/assets/brand');await fs.mkdir(output,{recursive:true});
 for(const [name,size,background] of [['icon.png',840,'#F6F7F5'],['adaptive-icon.png',660,{r:0,g:0,b:0,alpha:0}]]){
  const logo=await sharp(source,{density:144}).resize(size,size,{fit:'inside'}).png().toBuffer();
  const rendered=await sharp({create:{width:1024,height:1024,channels:4,background}}).composite([{input:logo,gravity:'centre'}]).png().toBuffer();
  const canvas=name==='icon.png'?sharp(rendered).flatten({background:'#F6F7F5'}).removeAlpha():sharp(rendered);
  await canvas.png().toFile(path.join(output,name));
 }
 await fs.writeFile(path.join(output,'source.json'),JSON.stringify({source:'packages/brand/numerom-logo.svg',sha256:crypto.createHash('sha256').update(source).digest('hex'),background:'#F6F7F5',size:1024},null,2)+'\n');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
