import {Card,Heading,Screen,Loading} from '../components/ui';
import {NarrationProvider,NarrationLibrary,GUEST_GUIDE_PATH} from '../components/audio/Narration';
import {useSession} from '../lib/session';
export default function AudioGuide(){
 const {status,user}=useSession();
 if(status==='loading')return <Screen><Loading/></Screen>;
 // Guests hear the same shared guide; personal calculations stay in the account.
 const provider=status==='signedIn'?{key:user?.id,path:'/narration/project',guest:false}:{key:'guest',path:GUEST_GUIDE_PATH,guest:true};
 return <Screen><Heading title="Аудиогид NumerOM" subtitle="Личные числа, линии квадрата и помощь по разделам."/><NarrationProvider key={provider.key} path={provider.path} guest={provider.guest}><Card><NarrationLibrary/></Card></NarrationProvider></Screen>;
}
