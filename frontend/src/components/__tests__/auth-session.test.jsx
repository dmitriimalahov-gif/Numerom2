import React, {act} from 'react';
import {createRoot} from 'react-dom/client';
import axios from 'axios';
import {AuthProvider,useAuth} from '../AuthContext';
import {api} from '../../services/api';
jest.mock('../../services/api',()=>({api:{profile:jest.fn()}}));
jest.mock('axios',()=>({defaults:{headers:{common:{}}},post:jest.fn()}));
let root,container,auth;
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
function Probe(){auth=useAuth();return <span>{auth.user?.id || 'signed-out'}</span>;}
beforeEach(()=>{
 global.IS_REACT_ACT_ENVIRONMENT=true;localStorage.clear();localStorage.setItem('token','token-a');localStorage.setItem('login_timestamp',Date.now().toString());
 api.profile.mockReset();api.profile.mockResolvedValue({id:'a'});axios.post.mockResolvedValue({status:200,data:{access_token:'token-b',user:{id:'b',email:'b@example.invalid'}}});
 container=document.createElement('div');document.body.appendChild(container);root=createRoot(container);
 jest.spyOn(console,'log').mockImplementation(()=>{});jest.spyOn(console,'error').mockImplementation(()=>{});jest.spyOn(console,'warn').mockImplementation(()=>{});
});
afterEach(async()=>{await act(async()=>root.unmount());container.remove();jest.restoreAllMocks();});
async function switchUserWithPendingProfile(){
 await act(async()=>{root.render(<AuthProvider><Probe/></AuthProvider>);});
 const pending=deferred();api.profile.mockImplementationOnce(()=>pending.promise);let request;
 await act(async()=>{request=auth.refreshProfile();});
 await act(async()=>{auth.logout();});
 api.profile.mockResolvedValue({id:'b',email:'b@example.invalid'});
 await act(async()=>{await auth.login('b@example.invalid','test-only');});
 return {pending,request};
}
test('a previous account profile cannot overwrite the newly signed in account',async()=>{
 const {pending,request}=await switchUserWithPendingProfile();
 await act(async()=>{pending.resolve({id:'a'});await request;});
 expect(auth.user.id).toBe('b');expect(auth.token).toBe('token-b');
});
test('a previous account 401 cannot sign out the newly signed in account',async()=>{
 const {pending,request}=await switchUserWithPendingProfile();
 await act(async()=>{pending.reject(Object.assign(new Error('expired'),{status:401}));await request;});
 expect(auth.user.id).toBe('b');expect(localStorage.getItem('token')).toBe('token-b');
});
