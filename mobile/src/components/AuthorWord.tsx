import {useState} from 'react';
import {Image,Text,View,useWindowDimensions} from 'react-native';
import {Button,Card,s} from './ui';
import {AudioTrack} from './audio/AudioTrack';
import {AuthorVideo} from './AuthorVideo';

// scripts/render-author-conversation.py: selected voice and measured sentence timings.
const word=require('../../assets/author/author-word.json') as {title:string;author:string;paragraphs:string[];seconds:number};
const VIDEO=require('../../assets/author/author-word.mp4');
// The same video laid out for 9:16 phone screens (render-author.mjs --vertical).
const VIDEO_TALL=require('../../assets/author/author-word-vertical.mp4');
const AUDIO=require('../../assets/author/author-word.m4a');
// The video adds a 4 s end card (video/src/author/AuthorWord.jsx TAIL_SECONDS) after the voice.
const VIDEO_SECONDS=Math.round(word.seconds+4);
const length=`${Math.floor(VIDEO_SECONDS/60)}:${String(VIDEO_SECONDS%60).padStart(2,'0')}`;

export function AuthorWord(){
 const [video,setVideo]=useState(false),[audio,setAudio]=useState(false),[text,setText]=useState(false);
 const {width,height}=useWindowDimensions(),tall=height>width;
 return <Card tinted>
  <Text style={s.eyebrow}>{word.title}</Text>
  <Text style={s.title}>{word.author}</Text>
  {video?<AuthorVideo key={tall?'tall':'wide'} source={tall?VIDEO_TALL:VIDEO} tall={tall}/>:<View style={[s.row,{gap:14}]}>
   <Image accessibilityIgnoresInvertColors source={require('../../assets/illustrations/KVADRATW.png')} style={{width:84,height:84}} resizeMode="contain"/>
   <Text style={[s.small,{flex:1}]}>Короткое обращение о том, зачем создан NumerOM и с чего начать. {length} мин.</Text>
  </View>}
  {!video&&<Button title={`Смотреть обращение · ${length}`} onPress={()=>{setVideo(true);setAudio(false);}}/>}
  {!video&&<Button secondary title={audio?'Скрыть аудио':'Слушать без видео'} onPress={()=>setAudio(!audio)}/>}
  {!video&&audio&&<AudioTrack source={AUDIO} seconds={word.seconds} label={word.title}/>}
  <Button secondary title={text?'Скрыть текст':'Текст обращения'} onPress={()=>setText(!text)}/>
  {text&&<View style={{gap:10}}>{word.paragraphs.map((p,i)=><Text key={i} selectable style={s.body}>{p}</Text>)}</View>}
 </Card>;
}
