import {Text,View} from 'react-native';
import {Button,Card,s} from '../../components/ui';
import {ResourceState,useAdminData} from './common';
export default function Overview(){
 const data=useAdminData<Record<string,number>>('/admin/manage/overview'),mail=useAdminData<{configured:boolean}>('/admin/manage/recovery-status');
 const labels:Record<string,string>={users_total:'Пользователей',users_disabled:'Закрыт доступ',admins_total:'Администраторов',lessons_total:'Уроков',consultations_total:'Консультаций'};
 return <View style={{gap:16}}><ResourceState {...data}/><View style={{flexDirection:'row',flexWrap:'wrap',gap:12}}>{data.data&&Object.entries(labels).map(([key,title])=><View key={key} style={{flexGrow:1,flexBasis:140}}><Card><Text style={s.body}>{title}</Text><Text style={s.heading}>{Number.isFinite(data.data?.[key])?data.data?.[key]:'—'}</Text></Card></View>)}</View><Card><Text style={s.title}>Восстановление пароля</Text><ResourceState {...mail}/>{mail.data&&<><Text style={s.body}>{mail.data.configured?'Отправка писем настроена.':'Отправка писем пока не настроена.'}</Text><Text style={s.small}>Проверка настроек не отправляет письмо. Доставку конкретного письма проверяют отдельно.</Text></>}</Card><Button secondary title="Обновить обзор" disabled={data.loading||mail.loading} onPress={()=>{void data.reload();void mail.reload();}}/></View>;
}
