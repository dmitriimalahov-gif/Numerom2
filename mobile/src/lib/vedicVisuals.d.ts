export interface VedicPlanetVisual {key:string;title:string;digit:number;color:string;stroke:string}
export const VEDIC_PLANETS:readonly VedicPlanetVisual[];
export function localTimeLabel(value:unknown):string;
export interface PlanetSeriesModel {
  width:number;height:number;left:number;right:number;top:number;bottom:number;planet:VedicPlanetVisual;
  ticks:{value:number;y:number}[];points:{index:number;date:string;label:string;value:number;x:number;y:number}[];
  segments:{points:string}[];dateTicks:{index:number;label:string;x:number}[];missingDates:string[];
}
export function planetSeriesModel(days:unknown,planetKey:string,options?:{width?:number;height?:number}):PlanetSeriesModel|null;
export interface SolarWheelSegment {
  index:number;hour:number;planet:string;title:string;period:string;startLabel:string;endLabel:string;
  startDate:string;endDate:string;nextDate:boolean;startMinute:number;endMinute:number;startAngle:number;endAngle:number;
  path:string;labelX:number;labelY:number;color:string;stroke:string;
}
export interface SolarWheelModel {
  width:number;height:number;cx:number;cy:number;innerRadius:number;outerRadius:number;
  startLabel:string;endLabel:string;sunsetLabel:string;timeBasis:'elapsed'|'local-wall-clock';segments:SolarWheelSegment[];
  markers:{kind:string;label:string;angle:number;x:number;y:number;labelX:number;labelY:number}[];
  bands:{period:string;path:string}[];
}
export function solarWheelModel(day:unknown,options?:{size?:number}):SolarWheelModel|null;
export interface PeriodTimelineModel {
  width:number;height:number;left:number;right:number;startLabel:string;endLabel:string;
  ticks:{label:string;x:number}[];missingIds:string[];
  rows:{id:string;title:string;meaning:string;startLabel:string;endLabel:string;x:number;y:number;width:number;height:number;color:string}[];
}
export function periodTimelineModel(day:unknown,options?:{width?:number}):PeriodTimelineModel|null;
