import React,{act} from 'react';
import {createRoot} from 'react-dom/client';
import PaymentSuccess from '../PaymentSuccess';
import {useAuth} from '../AuthContext';
import {api} from '../../services/api';
jest.mock('react-router-dom',()=>({useSearchParams:()=>[new URLSearchParams('session_id=cs_test_123&success=true')],useNavigate:()=>jest.fn()}));
jest.mock('../AuthContext',()=>({useAuth:jest.fn()}));
jest.mock('../../services/api',()=>({api:{request:jest.fn()}}));
const paid={order_id:'a'.repeat(64),session_id:'cs_test_123',status:'paid',payment_status:'paid',mode:'test',title:'Стартовый пакет',credits:10,amount_total:99,currency:'eur'};
let root,container,refreshProfile;
beforeEach(()=>{global.IS_REACT_ACT_ENVIRONMENT=true;sessionStorage.clear();api.request.mockReset();refreshProfile=jest.fn().mockResolvedValue({});useAuth.mockReturnValue({user:{id:'student'},refreshProfile});container=document.createElement('div');document.body.appendChild(container);root=createRoot(container);});
afterEach(async()=>{await act(async()=>root.unmount());container.remove();});
const render=async()=>act(async()=>root.render(<PaymentSuccess/>));
test('return URL cannot grant credits before server confirmation',async()=>{
 api.request.mockRejectedValue(new Error('Нет подтверждения'));
 await render();expect(container.textContent).toContain('Нет подтверждения');expect(container.textContent).not.toContain('Оплата подтверждена');expect(refreshProfile).not.toHaveBeenCalled();expect(api.request.mock.calls.every(([url,options])=>!options?.method)).toBe(true);
});
test('confirmed test payment clears its own attempt and keeps working balance unchanged',async()=>{
 sessionStorage.setItem('numerom.web.payment.student',JSON.stringify({session_id:'cs_test_123'}));api.request.mockResolvedValue(paid);
 await render();expect(container.textContent).toContain('Рабочий баланс не изменён');expect(sessionStorage.getItem('numerom.web.payment.student')).toBeNull();expect(refreshProfile).toHaveBeenCalledTimes(1);
});
test('signed out users make no payment lookup or credit request',async()=>{
 useAuth.mockReturnValue({user:null,refreshProfile});await render();expect(api.request).not.toHaveBeenCalled();expect(container.textContent).toContain('Войдите в аккаунт');
});
test('a different signed in account cannot inherit the previous receipt',async()=>{
 api.request.mockResolvedValue(paid);await render();expect(container.textContent).toContain('Тестовая оплата подтверждена');
 useAuth.mockReturnValue({user:{id:'other'},refreshProfile});api.request.mockRejectedValue(new Error('Платёж не найден'));
 await render();expect(container.textContent).not.toContain('Тестовая оплата подтверждена');expect(container.textContent).toContain('Платёж не найден');
});
