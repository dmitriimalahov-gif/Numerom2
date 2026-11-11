import {router} from 'expo-router';
import {Button,Heading,Loading,Screen} from '../components/ui';
import {useSession} from '../lib/session';
import NumberTools from '../features/NumberTools';
import {NarrationProvider} from '../components/audio/Narration';
export default function NumberToolsRoute(){
 const {user,status}=useSession();
 if(status==='loading')return <Screen><Loading/></Screen>;
 if(status!=='signedIn')return <Screen><Heading title="Новые расчёты" subtitle="Войдите, чтобы рассчитать числа имени, адреса и автомобиля."/><Button title="Войти" onPress={()=>router.replace('/')}/></Screen>;
 return <NarrationProvider key={user!.id} path="/narration/project"><NumberTools/></NarrationProvider>;
}
