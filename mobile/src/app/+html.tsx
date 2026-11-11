import type {ReactNode} from 'react';
import {ScrollViewStyleReset,useServerDocumentContext} from 'expo-router/html';

// Static/SSR HTML. The SPA export uses public/index.html with the same language policy.
export default function Root({children}:{children:ReactNode}){
 const {bodyAttributes,bodyNodes,htmlAttributes,headNodes}=useServerDocumentContext();
 return <html {...htmlAttributes} lang="ru" translate="no">
  <head>
   <meta charSet="utf-8"/>
   <meta httpEquiv="X-UA-Compatible" content="IE=edge"/>
   <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no"/>
   <meta name="google" content="notranslate"/>
   <ScrollViewStyleReset/>
   {headNodes}
  </head>
  <body {...bodyAttributes}>{children}{bodyNodes}</body>
 </html>;
}
