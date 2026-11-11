import {router,useLocalSearchParams} from 'expo-router';
import {useSession} from '../lib/session';
import {Button,Heading,Loading,Screen} from '../components/ui';
import FullReport from '../features/FullReport';
export default function FullReportRoute(){
 const {status,user}=useSession();const {order_id,cancelled}=useLocalSearchParams<{order_id?:string;cancelled?:string}>();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Screen><Heading title="Полный разбор за 6,66 €" subtitle="Войдите, чтобы купить разбор или открыть сохранённый отчёт. Оплаченные заказы остаются в вашем аккаунте."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;
 return <FullReport key={user!.id} orderId={typeof order_id==='string'&&/^[a-f0-9]{64}$/.test(order_id)?order_id:undefined} cancelled={cancelled==='1'}/>;
}
