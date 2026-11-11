// Shared presentation coordinates for native SVG and saved-document SVG.
// No numerology or solar calculation belongs in this module.
const VEDIC_PLANETS = Object.freeze([
  ['surya','Солнце',1,'#f47758','#c9654e'], ['chandra','Луна',2,'#ffffff','#8aafa0'],
  ['guru','Юпитер',3,'#fa9418','#b96b0e'], ['rahu','Раху',4,'#ba9669','#92724d'],
  ['budha','Меркурий',5,'#bedfd0','#719b89'], ['shukra','Венера',6,'#f8cbd3','#ba8390'],
  ['ketu','Кету',7,'#bcbfc0','#777f82'], ['shani','Сатурн',8,'#3867ad','#3867ad'],
  ['mangal','Марс',9,'#f53f58','#b92640'],
].map(([key,title,digit,color,stroke]) => Object.freeze({key,title,digit,color,stroke})));
const periodColors = {rahu_kaal:'#bc8461',gulika_kaal:'#8f91ab',yamaghanta:'#cb7a8d',abhijit_muhurta:'#4e9277'};
const validNumber = value => typeof value === 'number' && Number.isFinite(value);
const dimension = (value, fallback, min) => validNumber(value) && value >= min ? value : fallback;
function dayNumber(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const stamp = Date.parse(value + 'T00:00:00Z');
  return Number.isFinite(stamp) && new Date(stamp).toISOString().slice(0,10) === value ? stamp / 86400000 : null;
}
function parsedLocal(value, baseDate) {
  if (typeof value !== 'string') return null;
  const match = /^(?:(\d{4}-\d{2}-\d{2})T)?(\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?$/.exec(value);
  if (!match || +match[2] > 23 || +match[3] > 59 || +(match[4] || 0) > 59) return null;
  const date = match[1] || baseDate, serial = dayNumber(date);
  if (serial === null) return null;
  // The server has already chosen the city's local clock. Even an explicit
  // suffix must not convert its displayed hours into the device's timezone.
  const explicitOffset = !!match[1] && /(?:Z|[+-]\d{2}:\d{2})$/.test(value);
  const absoluteMinute = explicitOffset ? Date.parse(value) / 60000 : null;
  if (explicitOffset && !Number.isFinite(absoluteMinute)) return null;
  return {date, label: `${match[2]}:${match[3]}`, minute: serial * 1440 + +match[2] * 60 + +match[3] + +(match[4] || 0) / 60,absoluteMinute};
}
function localTimeLabel(value) {
  return parsedLocal(value, '2000-01-01')?.label || '—';
}
function dateLabel(value) { return dayNumber(value) === null ? '—' : value.slice(8,10) + '.' + value.slice(5,7); }

function planetSeriesModel(days, planetKey, options = {}) {
  const planet = VEDIC_PLANETS.find(item => item.key === planetKey);
  if (!planet || !Array.isArray(days) || !days.length) return null;
  const dates = days.map(day => dayNumber(day?.date));
  if (dates.some((date,index) => date === null || (index > 0 && date !== dates[index - 1] + 1))) return null;
  const width = dimension(options.width,336,160), height = dimension(options.height,184,120);
  const left = 32, right = width - 15, top = 18, bottom = height - 34;
  const x = index => days.length === 1 ? (left + right) / 2 : left + index * (right - left) / (days.length - 1);
  const points = [], segments = [], missingDates = [];
  let run = [];
  const endRun = () => {if (run.length > 1) segments.push({points:run.map(point => `${point.x},${point.y}`).join(' ')}); run = [];};
  days.forEach((day,index) => {
    const entries = Array.isArray(day.energies) ? day.energies.filter(item => item?.key === planetKey) : [];
    const value = entries.length === 1 ? entries[0].value : null;
    if (!validNumber(value) || value < 0 || value > 100) {missingDates.push(day.date); endRun(); return;}
    const point = {index,date:day.date,label:dateLabel(day.date),value,x:x(index),y:bottom - value / 100 * (bottom - top)};
    points.push(point); run.push(point);
  });
  endRun();
  if (!points.length) return null;
  const tickCount = Math.min(width < 300 ? 3 : 5,days.length);
  const indices = [...new Set(Array.from({length:tickCount},(_,i) =>
    Math.round(i * (days.length - 1) / Math.max(1,tickCount - 1))))];
  return {width,height,left,right,top,bottom,planet:{...planet},points,segments,missingDates,
    ticks:[0,25,50,75,100].map(value => ({value,y:bottom - value / 100 * (bottom - top)})),
    dateTicks:indices.map(index => ({index,label:dateLabel(days[index].date),x:x(index)}))};
}

const rounded = value => Number(value.toFixed(4));
function polar(cx,cy,radius,angle) {
  const radians = (angle - 90) * Math.PI / 180;
  return {x:rounded(cx + radius * Math.cos(radians)),y:rounded(cy + radius * Math.sin(radians))};
}
function ringPath(cx,cy,inner,outer,start,end) {
  const a = polar(cx,cy,outer,start), b = polar(cx,cy,outer,end), c = polar(cx,cy,inner,end), d = polar(cx,cy,inner,start);
  const large = end - start > 180 ? 1 : 0;
  return `M ${a.x} ${a.y} A ${outer} ${outer} 0 ${large} 1 ${b.x} ${b.y} L ${c.x} ${c.y} A ${inner} ${inner} 0 ${large} 0 ${d.x} ${d.y} Z`;
}
function solarWheelModel(day, options = {}) {
  if (dayNumber(day?.date) === null || !Array.isArray(day.hours) || day.hours.length !== 24) return null;
  const entries = [];
  for (let index = 0; index < day.hours.length; index++) {
    const hour = day.hours[index], start = parsedLocal(hour?.start), end = parsedLocal(hour?.end);
    const planet = VEDIC_PLANETS.find(item => item.key === hour?.planet);
    if (!start || !end || !planet || typeof hour.title !== 'string' || !hour.title || hour.hour !== index + 1
      || hour.period !== (index < 12 ? 'day' : 'night')) return null;
    entries.push({hour,start,end,planet});
  }
  const offsetCount = entries.reduce((sum,entry) => sum + Number(entry.start.absoluteMinute !== null) + Number(entry.end.absoluteMinute !== null),0);
  if (offsetCount !== 0 && offsetCount !== 48) return null;
  const timeBasis = offsetCount === 48 ? 'elapsed' : 'local-wall-clock';
  const coordinate = point => timeBasis === 'elapsed' ? point.absoluteMinute : point.minute;
  if (entries.some((entry,index) => coordinate(entry.end) <= coordinate(entry.start)
    || (index > 0 && Math.abs(coordinate(entry.start) - coordinate(entries[index - 1].end)) > 1 / 60 + .000001))) return null;
  const first = entries[0].start, last = entries[23].end;
  const sunrise = parsedLocal(day.sunrise,day.date), sunset = parsedLocal(day.sunset,day.date);
  if (!sunrise || !sunset || first.date !== day.date || dayNumber(last.date) !== dayNumber(day.date) + 1
    || Math.abs(first.minute - sunrise.minute) >= 1 || Math.abs(entries[12].start.minute - sunset.minute) >= 1) return null;
  const size = dimension(options.size,288,180), cx = size / 2, cy = size / 2;
  const innerRadius = rounded(size * .265), outerRadius = rounded(size * .425), total = coordinate(last) - coordinate(first);
  const angle = minute => (minute - coordinate(first)) / total * 360;
  const segments = entries.map(({hour,start,end,planet},index) => {
    const startAngle = angle(coordinate(start)), endAngle = angle(coordinate(end)), label = polar(cx,cy,(innerRadius + outerRadius) / 2,(startAngle + endAngle) / 2);
    return {index,hour:hour.hour,planet:hour.planet,title:hour.title,period:hour.period,startLabel:start.label,endLabel:end.label,
      startDate:start.date,endDate:end.date,nextDate:start.date !== day.date || end.date !== day.date,
      startMinute:coordinate(start) - coordinate(first),endMinute:coordinate(end) - coordinate(first),startAngle,endAngle,
      path:ringPath(cx,cy,innerRadius,outerRadius,startAngle,endAngle),labelX:label.x,labelY:label.y,color:planet.color,stroke:planet.stroke};
  });
  const sunsetAngle = angle(coordinate(entries[12].start));
  const markers = [{kind:'sunrise',label:first.label,angle:0},{kind:'sunset',label:entries[12].start.label,angle:sunsetAngle}].map(item => {
    const label = polar(cx,cy,size * .49,item.angle);
    return {...item,...polar(cx,cy,size * .465,item.angle),labelX:Math.max(23,Math.min(size - 23,label.x)),labelY:Math.max(12,Math.min(size - 3,label.y + 4))};
  });
  return {width:size,height:size,cx,cy,innerRadius,outerRadius,startLabel:first.label,endLabel:last.label,sunsetLabel:entries[12].start.label,timeBasis,segments,markers,
    bands:[{period:'day',path:ringPath(cx,cy,size*.443,size*.465,0,sunsetAngle)},
      {period:'night',path:ringPath(cx,cy,size*.443,size*.465,sunsetAngle,360)}]};
}

function periodTimelineModel(day, options = {}) {
  const start = parsedLocal(day?.sunrise,day?.date), end = parsedLocal(day?.sunset,day?.date);
  if (!start || !end || end.minute <= start.minute || !Array.isArray(day?.periods)) return null;
  const width = dimension(options.width,336,160), left = 12, right = width - 12;
  const rows = [], missingIds = [];
  for (const id of Object.keys(periodColors)) {
    const matches = day.periods.filter(period => period?.id === id), period = matches.length === 1 ? matches[0] : null;
    const from = parsedLocal(period?.start,day.date), to = parsedLocal(period?.end,day.date);
    if (!period || typeof period.title !== 'string' || !period.title || typeof period.meaning !== 'string'
      || !from || !to || to.minute <= from.minute || from.minute < start.minute || to.minute > end.minute) {missingIds.push(id); continue;}
    rows.push({id,title:period.title,meaning:period.meaning,startLabel:from.label,endLabel:to.label,
      x:left + (from.minute - start.minute) / (end.minute - start.minute) * (right - left),y:rows.length * 56 + 32,
      width:(to.minute - from.minute) / (end.minute - start.minute) * (right - left),height:12,color:periodColors[id]});
  }
  if (!rows.length) return null;
  return {width,height:rows.length * 56 + 30,left,right,startLabel:start.label,endLabel:end.label,rows,missingIds,
    ticks:[{label:start.label,x:left},{label:end.label,x:right}]};
}
module.exports = {VEDIC_PLANETS,localTimeLabel,planetSeriesModel,solarWheelModel,periodTimelineModel};
