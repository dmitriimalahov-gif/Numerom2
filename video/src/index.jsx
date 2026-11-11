import './frame-scheduler.mjs';
import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {ReportVideo} from './ReportVideo.jsx';
import {buildTimeline} from './timeline.mjs';

function Root() {
  return <Composition id="NumeromReport" component={ReportVideo} width={1280} height={720} fps={24}
    durationInFrames={24} calculateMetadata={({props}) => ({durationInFrames: buildTimeline(props.report.chapters).durationInFrames})}/>;
}
registerRoot(Root);
