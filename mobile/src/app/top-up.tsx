import {Redirect} from 'expo-router';
import {useSession} from '../lib/session';
import {Loading,Screen} from '../components/ui';
import {TopUp} from '../components/TopUp';
import {TelegramTopUp} from '../components/TelegramTopUp';
import {telegramApp} from '../lib/telegram';
export default function TopUpPage(){const {status,user}=useSession();if(status==='loading')return <Screen><Loading/></Screen>;if(status!=='signedIn')return <Redirect href="/"/>;return telegramApp()?<TelegramTopUp key={user?.id}/>:<TopUp key={user?.id}/>;}
