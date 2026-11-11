import {useCallback, useState} from 'react';
import {Text, View} from 'react-native';
import {Redirect,router} from 'expo-router';
import {Button, Card, Heading, Loading, Notice, Screen, s} from '../components/ui';
import {useResource} from '../lib/useResource';
import {useSession} from '../lib/session';
import {colors} from '../lib/theme';
import {serverDate} from '../lib/serverDate';
import type {ApiClient} from '@numerom/api-client';

type Transaction = {id:string; amount:number; description:string; created_at:string};
type History = {transactions:Transaction[];total:number};
function HistoryBody({api}: {api:ApiClient}) {
 const [page, setPage] = useState(0);
 const history = useResource(useCallback(() => api.request<History>(`/user/credit-history?limit=20&offset=${page*20}`), [api,page]));
 return <Screen refreshing={history.loading} onRefresh={() => void history.reload()}><Heading title="История баллов" subtitle="Расчёты, начисления за обучение и корректировки администратора."/>
 <Button title="Пополнить баллы" onPress={()=>router.push('/top-up')}/>{history.loading ? <Loading/> : history.error ? <Notice message={history.error} action="Повторить" onAction={() => void history.reload()}/> : <>
 {!history.data?.transactions.length && <Card><Text style={s.body}>Операций пока нет. Здесь появится история ваших баллов.</Text></Card>}
 {history.data?.transactions.map(item => <Card key={item.id}><View style={s.row}><Text style={[s.label,{flex:1}]}>{item.description || 'Операция с баллами'}</Text><Text style={[s.title,{color:item.amount>0 ? colors.green : colors.ink}]}>{item.amount>0?'+':''}{item.amount}</Text></View><Text style={s.small}>{serverDate(item.created_at)?.toLocaleString('ru-RU') || 'Дата не указана'}</Text></Card>)}
 <View style={s.row}>{page>0 && <Button title="Предыдущие" secondary onPress={() => setPage(page-1)}/>} {!!history.data && (page+1)*20<history.data.total && <Button title="Следующие" secondary onPress={() => setPage(page+1)}/>}</View></>}
 </Screen>;
}
export default function Credits() {
 const {api,status,user} = useSession();
 if (status === 'loading') return <Screen><Loading/></Screen>;
 if (status !== 'signedIn') return <Redirect href="/"/>;
 return <HistoryBody key={user?.id} api={api}/>;
}
