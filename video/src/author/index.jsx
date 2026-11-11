import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {AuthorWord, TAIL_SECONDS} from './AuthorWord.jsx';

const FPS = 30;
const duration = ({props}) => ({durationInFrames: Math.ceil((props.word.seconds + TAIL_SECONDS) * FPS)});
function Root() {
  return <>
    <Composition id="AuthorWord" component={AuthorWord} width={1280} height={720} fps={FPS} durationInFrames={FPS} calculateMetadata={duration}/>
    {/* Phone screens: the same story laid out for 9:16. */}
    <Composition id="AuthorWordVertical" component={(props) => <AuthorWord {...props} portrait/>} width={1080} height={1920} fps={FPS} durationInFrames={FPS} calculateMetadata={duration}/>
  </>;
}
registerRoot(Root);
