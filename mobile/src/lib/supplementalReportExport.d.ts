import {AssessmentReceipt} from './assessment';
import {VedicReceipt} from './vedicCalculations';
import {PersonalResultView} from './personalReport';
export function assessmentDocument(receipt:AssessmentReceipt):string;
export function vedicDocument(receipt:VedicReceipt):string;
export function comprehensiveHtml(result:PersonalResultView):string;
