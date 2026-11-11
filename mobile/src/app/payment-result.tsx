import {router,useLocalSearchParams} from 'expo-router';
import {useSession} from '../lib/session';
import {Button,Heading,Loading,Screen} from '../components/ui';
import {TopUp} from '../components/TopUp';
import FullReport from '../features/FullReport';
export default function PaymentResult(){
 const {status,user}=useSession();const {session_id,cancelled,service,order_id}=useLocalSearchParams<{session_id?:string;cancelled?:string;service?:string;order_id?:string}>();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Screen><Heading title="Вернитесь в NumerOM" subtitle="Платёж подтверждается сервером автоматически. Откройте приложение или войдите в свой аккаунт и проверьте баланс и историю оплат."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;
 const sid=typeof session_id==='string'&&/^cs_(?:test_|live_)?[A-Za-z0-9]+$/.test(session_id)?session_id:undefined;
 if(service==='full-report')return <FullReport key={user?.id} orderId={typeof order_id==='string'&&/^[a-f0-9]{64}$/.test(order_id)?order_id:undefined} cancelled={cancelled==='1'}/>;
 return <TopUp key={user?.id} sessionId={sid} cancelled={cancelled==='1'}/>;
}
