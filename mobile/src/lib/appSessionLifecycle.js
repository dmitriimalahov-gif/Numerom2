/** Remove credentials before any asynchronous work when native UI goes away. */
function appSessionLifecycle(session){
 let resume=false;
 return next=>{
  const status=session.getSnapshot().status;
  if(next==='background'&&(status==='signedIn'||status==='loading')){
   resume=true;session.lock();
  }else if(next==='active'&&resume){
   resume=false;
   // restore(false) never opens protected storage. Enabled biometrics remain
   // locked until the user's explicit OS authentication; ordinary sessions resume.
   if(session.getSnapshot().status==='locked')void session.restore(false);
  }
 };
}
module.exports={appSessionLifecycle};
