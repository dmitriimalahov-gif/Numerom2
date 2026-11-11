// The saved file takes the document's own title: «10.01.1982 Иван Петров — полный разбор».
const ENTITIES:Record<string,string>={amp:'&',lt:'<',gt:'>',quot:'"','#39':"'"};
export function reportName(html:string){
 // Only the page title: diagrams carry their own <title> elements inside SVG.
 const head=/<head[^>]*>([\s\S]*?)<\/head>/i.exec(html)?.[1]??'';
 const title=(/<title>([^<]*)<\/title>/i.exec(head)?.[1]??'').replace(/&(amp|lt|gt|quot|#39);/g,(_,name:string)=>ENTITIES[name]);
 const name=title.replace(/[\u0000-\u001f\u007f/\\:*?"<>|]+/g,' ').replace(/\s+/g,' ').replace(/^[\s.]+|[\s.]+$/g,'').slice(0,100).trim();
 return name||'NumerOM-report';
}
