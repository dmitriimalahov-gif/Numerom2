// Loads a self-contained TypeScript module of the app (no runtime imports) for a test.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
module.exports=function tsModule(file){
 const mod={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.resolve(__dirname,'..',file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,
  {exports:mod.exports,require:name=>{throw new Error(`Unexpected dependency: ${name}`);},Date});
 return mod.exports;
};
