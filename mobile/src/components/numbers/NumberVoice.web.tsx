import {Text} from 'react-native';
import {AvailableNarration} from '../audio/Narration';
import {s} from '../ui';
import {numberKnowledge} from '../../lib/numberKnowledge';
export function NumberVoice({digit}:{digit:number}) {
 if(!numberKnowledge(digit))return null;
 // Previous recordings were removed at the owner's request. Use only published current narration.
 return <AvailableNarration id={`number-${digit}`} fallback={<Text style={s.small}>Озвучка готовится. Новая запись появится здесь автоматически.</Text>}/>;
}
