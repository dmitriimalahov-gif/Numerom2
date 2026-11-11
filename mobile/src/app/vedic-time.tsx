import {router} from 'expo-router';
import {Button,Heading,Loading,Screen} from '../components/ui';
import {NarrationProvider} from '../components/audio/Narration';
import {useSession} from '../lib/session';
import VedicTime from '../features/VedicTime';
export default function VedicRoute(){const {user,status}=useSession();if(status==='loading')return <Screen><Loading/></Screen>;if(status!=='signedIn')return <Screen><Heading title="Планетарный маршрут" subtitle="Войдите, чтобы рассчитать время и сохранить личный маршрут."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;return <NarrationProvider key={user!.id} path="/narration/project"><VedicTime/></NarrationProvider>;}
