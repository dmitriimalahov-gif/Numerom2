import React, {createContext, useContext} from 'react';
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import example from './example.json';

// Colours of the app and of the author schemes (packages/full-report/schematics.js).
const C = {background: '#F4F7FB', navy: '#183B62', ink: '#20364E', muted: '#61758B', blue: '#356FA5', line: '#CEDDD8',
  pale: '#EDF6F2', green: '#D0E9DF', accent: '#267568', white: '#FFFFFF', soft: '#EAF1F9'};
const FONT = '-apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif';
export const TAIL_SECONDS = 4;

const clamp = (v) => Math.max(0, Math.min(1, v));
const ease = (v) => {const t = clamp(v); return t * t * (3 - 2 * t);};
const span = (t, from, length) => ease((t - from) / length);
const mix = (a, b, v) => a + (b - a) * v;

// Scheme geometry: Ч/Д·Ч/У·Ч/С column, the 3×3 square 1–4–7 / 2–5–8 / 3–6–9, row sums, column sums and diagonals.
const CW = 124, CH = 92, GAP = 12;
const LAYOUT = [1, 4, 7, 2, 5, 8, 3, 6, 9];
const dateOffset = (i) => i * 54 + (i > 1 ? 18 : 0) + (i > 3 ? 18 : 0);

// One table of positions per orientation; every scene reads it, so both videos tell the same story.
const LANDSCAPE = {W: 1280, H: 720, portrait: false, X0: 400, Y0: 232, personalLeft: 230, dateLeft: 452, dateY: 130, extraLeft: 452, extraY: 182,
  shift: -110, card: {left: 870, top: 210, width: 360}, sum: {left: 918, top: 342, width: 330, textAlign: 'left'},
  caption: {left: 140, right: 140, bottom: 34, size: 26, small: 23}, header: {left: 40, top: 26, logo: 92, size: 16}};
const PORTRAIT = {W: 720, H: 1280, portrait: true, X0: 191, Y0: 360, personalLeft: 29, dateLeft: 153, dateY: 200, extraLeft: 162, extraY: 262,
  shift: 0, card: {left: 40, top: 770, width: 640}, sum: {left: 40, top: 740, width: 640, textAlign: 'center'},
  caption: {left: 36, right: 36, bottom: 64, size: 33, small: 29}, header: {left: 36, top: 44, logo: 118, size: 18}};
const Geometry = createContext(LANDSCAPE);
const useG = () => useContext(Geometry);

// The approved text has twelve sentences; scenes follow them, so timings come from the voiced audio.
function scenes(sentences, total) {
  const at = (i) => sentences[Math.min(i, sentences.length - 1)].start;
  return {intro: [0, at(2)], sources: [at(2), at(3)], path: [at(3), at(5)], scheme: [at(5), at(7)], listen: [at(7), at(8)],
    report: [at(8), at(9)], begin: [at(9), at(10)], rhythm: [at(10), at(11)], outro: [at(11), total]};
}

function Scene({t, range, children}) {
  const [from, to] = range;
  if (t < from - .2 || t > to + .4) return null;
  const opacity = Math.min(span(t, from - .2, .45), 1 - span(t, to - .05, .4));
  return <AbsoluteFill style={{opacity, transform: `translateY(${(1 - span(t, from - .2, .5)) * 18}px)`}}>{children}</AbsoluteFill>;
}

function Chip({x, y, w = 46, h = 56, text, size = 32, fill = C.white, color = C.navy, border = C.line, opacity = 1, scale = 1, weight = 700}) {
  return <div style={{position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, borderRadius: 12, background: fill,
    border: `2px solid ${border}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: size, fontWeight: weight,
    color, opacity, transform: `scale(${scale})`, boxSizing: 'border-box'}}>{text}</div>;
}

// Faint digits drifting behind every scene keep the frame alive without competing with the content.
function Drift({frame}) {
  const g = useG();
  return <AbsoluteFill>{Array.from({length: 14}, (_, i) => {
    const x = (i * 97 + frame * (0.15 + (i % 4) * .05)) % (g.W + 80) - 40, y = 80 + (i * 53 * g.H / 720) % (g.H - 160) + 12 * Math.sin(frame / 50 + i);
    return <div key={i} style={{position: 'absolute', left: x, top: y, fontSize: 26 + (i % 3) * 14, fontWeight: 700, color: C.blue, opacity: .05}}>{(i * 7) % 9 + 1}</div>;
  })}</AbsoluteFill>;
}

function Intro({t, range, sentences}) {
  const g = useG(), name = span(t, sentences[1].start, .6), orbit = t * 1.6;
  const left = g.portrait ? 210 : mix(490, 230, name), top = g.portrait ? mix(380, 230, name) : 200;
  return <Scene t={t} range={range}>
    <div style={{position: 'absolute', left, top, width: 300, height: 300}}>
      <Img src={staticFile('numerom-logo.svg')} style={{width: 300, transform: `scale(${.85 + .15 * span(t, 0, .8)})`}}/>
      <div style={{position: 'absolute', left: 150 + 150 * Math.cos(orbit) - 9, top: 150 + 150 * Math.sin(orbit) - 9, width: 18, height: 18, borderRadius: 9, background: C.green, border: `2px solid ${C.accent}`}}/>
    </div>
    <div style={{position: 'absolute', ...(g.portrait ? {left: 0, right: 0, top: 600, textAlign: 'center'} : {left: 620, top: 270}), opacity: name,
      transform: g.portrait ? `translateY(${(1 - name) * 40}px)` : `translateX(${(1 - name) * 40}px)`}}>
      <div style={{color: C.accent, fontSize: 20, letterSpacing: 5, fontWeight: 700}}>СЛОВО АВТОРА</div>
      <div style={{color: C.navy, fontSize: g.portrait ? 76 : 68, fontWeight: 800, marginTop: 6}}>Дмитрий</div>
      <div style={{color: C.muted, fontSize: 30, marginTop: 4}}>автор NumerOM</div>
    </div>
  </Scene>;
}

function Sources({t, range}) {
  const g = useG(), [from] = range, u = t - from;
  const cards = [{title: 'Дата рождения', value: example.date, at: 1.2}, {title: 'Имя', value: 'Дмитрий', at: 3.1}, {title: 'Адрес', value: 'дом 25', at: 4.2}];
  const gather = span(u, 5.6, 1.6);
  const box = (i) => g.portrait ? {left: 80, top: mix(200 + i * 165, 180 + i * 140, gather), width: 560, height: 140}
    : {left: 120 + i * 360, top: mix(250, 160, gather), width: 320, height: 150};
  const start = (i) => g.portrait ? [112 + 26 * i + (i > 1 ? 12 : 0) + (i > 3 ? 12 : 0), mix(300, 280, gather)] : [150 + 26 * i + (i > 1 ? 12 : 0) + (i > 3 ? 12 : 0), 328];
  const end = (i) => g.portrait ? [101 + i * 74, 760] : [384 + i * 74, 470];
  return <Scene t={t} range={range}>
    {cards.map((card, i) => {
      const show = span(u, card.at, .6);
      return <div key={i} style={{position: 'absolute', ...box(i), borderRadius: 22, background: C.white, border: `2px solid ${i === 0 ? C.accent : C.line}`,
        opacity: show * (i === 0 ? 1 : 1 - .5 * gather), transform: `translateY(${(1 - show) * 30}px)`, boxSizing: 'border-box', padding: '22px 26px'}}>
        <div style={{color: C.muted, fontSize: 22}}>{card.title}</div>
        <div style={{color: C.navy, fontSize: 44, fontWeight: 800, marginTop: 12}}>{card.value}</div>
      </div>;
    })}
    {example.digits.map((digit, i) => {
      const go = span(u, 5.6 + i * .12, 1.2), [x1, y1] = start(i), [x2, y2] = end(i);
      return <Chip key={i} x={mix(x1, x2, go)} y={mix(y1, y2, go)} text={digit} size={34} opacity={go} fill={digit ? C.green : C.pale} border={digit ? C.accent : C.line}/>;
    })}
    <div style={{position: 'absolute', left: 30, right: 30, top: g.portrait ? 830 : 540, textAlign: 'center', color: C.accent, fontSize: g.portrait ? 30 : 26, opacity: span(u, 7.4, .8)}}>
      цифры даты — начало каждой схемы
    </div>
  </Scene>;
}

function Path({t, range, sentences}) {
  const g = useG(), [from] = range, u = t - from, second = sentences[4].start - from;
  const strike = (at) => span(u, at, .5);
  const words = [['гадание', .6], ['предсказание судьбы', 1.4]];
  const circle = span(u, second, 1), [cx, cy, r] = g.portrait ? [360, 640, 210] : [640, 390, 170];
  return <Scene t={t} range={range}>
    {words.map(([word, at], i) => <div key={word} style={{position: 'absolute', ...(g.portrait ? {left: 0, right: 0, top: 300 + i * 100, textAlign: 'center'} : {left: 300 + i * 330, top: 230}),
      opacity: span(u, at - .4, .4) * (1 - circle)}}>
      <div style={{position: 'relative', display: 'inline-block', fontSize: 46, color: C.muted, fontWeight: 600}}>{word}
        <div style={{position: 'absolute', left: -6, top: 30, height: 4, width: `${strike(at + .4) * 104}%`, background: '#C2584A', borderRadius: 2}}/>
      </div>
    </div>)}
    <div style={{position: 'absolute', left: cx - r * circle, top: cy - r * circle, width: 2 * r * circle, height: 2 * r * circle, borderRadius: '50%',
      border: `3px solid ${C.accent}`, background: 'rgba(208,233,223,.35)', opacity: circle}}/>
    {Array.from({length: 9}, (_, i) => {
      const angle = i / 9 * Math.PI * 2 + t * .35;
      return <Chip key={i} x={cx + r * circle * Math.cos(angle)} y={cy + r * circle * Math.sin(angle)} w={44} h={44} text={i + 1} size={24} opacity={circle} fill={C.white}/>;
    })}
    <div style={{position: 'absolute', left: 0, right: 0, top: cy - 22, textAlign: 'center', fontSize: 40, fontWeight: 800, color: C.navy, opacity: span(u, second + .4, .6)}}>самопознание</div>
  </Scene>;
}

function SchemeScene({t, range}) {
  const g = useG(), [from] = range, u = t - from, {X0, Y0} = g;
  const cellXY = (index) => [X0 + (index % 3) * (CW + GAP) + CW / 2, Y0 + Math.floor(index / 3) * (CH + GAP) + CH / 2];
  const dateX = (i) => g.dateLeft + dateOffset(i), extraX = (i) => g.extraLeft + i * 112;
  const personal = [['Ч/Д', example.personal.soul, '1 + 4', .8], ['Ч/У', example.personal.mind, '07', 1.4], ['Ч/С', example.personal.destiny, '14 + 7 + 1988 → 2', 2.0]];
  // Every working digit (date + А1..А4) flies to its cell; zeros fade, they are not counted.
  const flights = [];
  example.digits.forEach((digit, i) => flights.push({digit, x: dateX(i), y: g.dateY}));
  example.extra.forEach((item, i) => String(item.value).split('').forEach((d, k) => flights.push({digit: +d, x: extraX(i) + 30 + k * 18, y: g.extraY})));
  const counted = {};
  const landed = flights.map((f, i) => {
    const start = 3.6 + i * .09, go = span(u, start, .5);
    if (f.digit && go >= 1) counted[f.digit] = (counted[f.digit] || 0) + 1;
    return {...f, start, go};
  });
  const lineStart = 5.4, lineStep = .42;
  const lines = example.lines;
  const sweep = Math.floor((u - lineStart) / lineStep);
  const explain = span(u, 8.2, .7);
  const focus = explain > 0 ? lines.findIndex((l) => l.title.startsWith('Диагональ 1')) : sweep >= 0 && sweep < lines.length ? sweep : -1;
  const active = focus >= 0 ? lines[focus] : null;
  const planets = span(u, 6.4, .8);
  const lineEnds = (line) => [cellXY(LAYOUT.indexOf(line.digits[0])), cellXY(LAYOUT.indexOf(line.digits[2]))];
  const below = Y0 + 3 * (CH + GAP);
  const formulaAt = personal.findIndex(([, , , at]) => u >= at && u < at + 1.1);
  return <Scene t={t} range={range}>
    <div style={{position: 'absolute', inset: 0, transform: `translateX(${explain * g.shift}px)`}}>
      <div style={{position: 'absolute', ...(g.portrait ? {left: 0, right: 0, top: 148, textAlign: 'center'} : {left: 300, top: 118, width: 110, textAlign: 'right'}),
        fontSize: 20, color: C.muted, opacity: span(u, 0, .4)}}>Пример</div>
      {example.digits.map((digit, i) => <Chip key={'d' + i} x={dateX(i)} y={g.dateY} text={digit} size={30} w={44} h={50}
        opacity={span(u, i * .06, .4)} border={u > .8 && u < 2.6 && (i < 2 || i === 3) ? C.accent : C.line}/>)}
      {[1, 3].map((i) => <div key={'dot' + i} style={{position: 'absolute', left: dateX(i) + 26, top: g.dateY + 4, fontSize: 30, color: C.muted, opacity: span(u, .2, .4)}}>.</div>)}
      {example.extra.map((item, i) => <div key={item.name} style={{position: 'absolute', left: extraX(i) - 22, top: g.extraY - 22, width: 104, height: 44, borderRadius: 12,
        background: C.pale, border: `2px solid ${C.line}`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 24,
        color: C.navy, fontWeight: 700, opacity: span(u, 2.6 + i * .22, .35)}}><span style={{color: C.muted, fontSize: 18}}>{item.name}</span>{item.value}</div>)}
      {personal.map(([name, value, formula, at], i) => {
        const show = span(u, at, .5);
        return <div key={name} style={{position: 'absolute', left: g.personalLeft, top: Y0 + i * (CH + GAP), width: 150, height: CH, borderRadius: 16, background: C.pale,
          border: `2px solid ${show > 0 && u < at + 1 ? C.accent : C.line}`, boxSizing: 'border-box', padding: '10px 14px', opacity: span(u, .3, .5)}}>
          <div style={{fontSize: 22, fontWeight: 700, color: C.navy}}>{name}</div>
          <div style={{fontSize: 40, fontWeight: 700, color: C.navy, textAlign: 'right', marginTop: -6, opacity: show, transform: `scale(${.6 + .4 * show})`}}>{value}</div>
          {!g.portrait && <div style={{position: 'absolute', left: -190, top: 30, width: 176, textAlign: 'right', fontSize: 18, color: C.accent, opacity: show * (1 - span(u, at + 1.1, .4))}}>{formula}</div>}
        </div>;
      })}
      {g.portrait && formulaAt >= 0 && <div style={{position: 'absolute', left: 0, right: 0, top: below + 70, textAlign: 'center', fontSize: 34, fontWeight: 700, color: C.accent}}>
        {personal[formulaAt][0]}: {personal[formulaAt][2]}{personal[formulaAt][2].includes('→') ? '' : ` = ${personal[formulaAt][1]}`}</div>}
      {LAYOUT.map((digit, index) => {
        const cell = example.cells.find((c) => c.digit === digit), count = counted[digit] || 0;
        const [x, y] = cellXY(index), lit = active && active.digits.includes(digit);
        return <div key={digit} style={{position: 'absolute', left: x - CW / 2, top: y - CH / 2, width: CW, height: CH, borderRadius: 16,
          background: lit ? C.green : C.pale, border: `2px solid ${lit ? C.accent : C.line}`, boxSizing: 'border-box', opacity: span(u, 2.4 + index * .05, .4)}}>
          <div style={{position: 'absolute', left: 9, top: 5, fontSize: 15, color: C.muted}}>{digit}</div>
          <div style={{position: 'absolute', left: 0, right: 0, top: 22, textAlign: 'center', fontSize: count > 3 ? 30 : 36, fontWeight: 700, color: C.navy}}>{count ? String(digit).repeat(count) : '—'}</div>
          <div style={{position: 'absolute', left: 0, right: 0, bottom: 5, textAlign: 'center', fontSize: 15, color: C.accent, opacity: planets}}>{cell.planet}</div>
        </div>;
      })}
      {landed.map((f, i) => f.go > 0 && f.go < 1 && (() => {
        const [tx, ty] = f.digit ? cellXY(LAYOUT.indexOf(f.digit)) : [f.x, f.y + 40];
        const x = mix(f.x, tx, f.go), y = mix(f.y, ty, f.go) - Math.sin(f.go * Math.PI) * 60;
        return <Chip key={'f' + i} x={x} y={y} w={34} h={40} size={24} text={f.digit} fill={f.digit ? C.green : C.pale} border={C.accent} opacity={f.digit ? 1 : 1 - f.go}/>;
      })())}
      <svg width={g.W} height={g.H} style={{position: 'absolute', left: 0, top: 0}}>
        {lines.map((line, i) => {
          const [[x1, y1], [x2, y2]] = lineEnds(line), on = i === focus, grow = on ? span(u, explain > 0 ? 8.2 : lineStart + i * lineStep, .3) : 0;
          return on && <line key={line.title} x1={x1} y1={y1} x2={mix(x1, x2, grow)} y2={mix(y1, y2, grow)} stroke={C.accent} strokeWidth="6" strokeLinecap="round" opacity=".35"/>;
        })}
      </svg>
      {lines.slice(0, 3).map((line, i) => <div key={line.title} style={{position: 'absolute', left: X0 + 3 * (CW + GAP), top: Y0 + i * (CH + GAP), width: 92, height: CH,
        borderRadius: 16, background: focus === i ? C.green : C.white, border: `2px solid ${focus === i ? C.accent : C.line}`, boxSizing: 'border-box',
        textAlign: 'center', paddingTop: 12, opacity: span(u, lineStart + i * lineStep, .25)}}>
        <div style={{fontSize: 15, color: C.muted}}>Σ ряда</div><div style={{fontSize: 34, fontWeight: 700, color: C.navy}}>{line.value}</div></div>)}
      {lines.slice(3, 6).map((line, i) => <div key={line.title} style={{position: 'absolute', left: X0 + i * (CW + GAP), top: below, width: CW, textAlign: 'center',
        fontSize: 30, fontWeight: 700, color: focus === i + 3 ? C.accent : C.navy, opacity: span(u, lineStart + (i + 3) * lineStep, .25)}}>Σ {line.value}</div>)}
      {[[7, X0 - 64, '3–5–7'], [6, X0 + 3 * (CW + GAP) + 46, '1–5–9']].map(([index, x, name]) => <div key={name} style={{position: 'absolute', left: x - 50, top: below - 6,
        width: 100, textAlign: 'center', opacity: span(u, lineStart + index * lineStep, .25)}}>
        <div style={{fontSize: 15, color: C.muted}}>{name}</div><div style={{fontSize: 30, fontWeight: 700, color: focus === index ? C.accent : C.navy}}>{lines[index].value}</div></div>)}
      {active && explain === 0 && <div style={{position: 'absolute', ...g.sum, fontSize: g.portrait ? 30 : 26, lineHeight: 1.35, color: C.accent, fontWeight: 700}}>
        <div>{active.title.replaceAll('-', '–')}</div><div style={{fontSize: g.portrait ? 44 : 36, color: C.navy}}>{active.digits.map((d) => counted[d] || 0).join(' + ')} = {active.value}</div></div>}
    </div>
    <div style={{position: 'absolute', ...g.card, borderRadius: 22, background: C.white, border: `2px solid ${C.accent}`, padding: '22px 24px',
      boxSizing: 'border-box', opacity: explain, transform: g.portrait ? `translateY(${(1 - explain) * 40}px)` : `translateX(${(1 - explain) * 60}px)`}}>
      <div style={{fontSize: 18, color: C.muted}}>Понятное объяснение</div>
      <div style={{fontSize: 28, fontWeight: 800, color: C.navy, marginTop: 8}}>Диагональ 1–5–9 = {active?.value}</div>
      <div style={{fontSize: g.portrait ? 24 : 21, lineHeight: 1.4, color: C.ink, marginTop: 12}}>{(active?.meaning || '').split('. ').slice(0, 2).join('. ').replace(/\.*$/, '.')}</div>
    </div>
  </Scene>;
}

function Listen({t, range}) {
  const g = useG(), [from] = range, u = t - from;
  const rates = ['1×', '1,2×', '1,5×', '1,7×', '2×'], rate = Math.min(rates.length - 1, Math.floor(Math.max(0, u - 1.4) / .5));
  const [read, listen] = g.portrait ? [{left: 60, top: 190, width: 600, height: 250}, {left: 60, top: 480, width: 600, height: 300}]
    : [{left: 170, top: 190, width: 400, height: 280}, {left: 630, top: 190, width: 480, height: 280}];
  return <Scene t={t} range={range}>
    <div style={{position: 'absolute', ...read, borderRadius: 24, background: C.white, border: `2px solid ${C.line}`, padding: 28, boxSizing: 'border-box', opacity: span(u, .1, .5)}}>
      <div style={{fontSize: 26, fontWeight: 800, color: C.navy}}>Читать</div>
      {[1, .92, .97, .7, .85].map((w, i) => <div key={i} style={{height: 12, borderRadius: 6, background: C.soft, marginTop: g.portrait ? 16 : 20, width: `${w * 100 * span(u, .3 + i * .12, .4)}%`}}/>)}
    </div>
    <div style={{position: 'absolute', ...listen, borderRadius: 24, background: C.white, border: `2px solid ${C.accent}`, padding: 28, boxSizing: 'border-box', opacity: span(u, .9, .5)}}>
      <div style={{fontSize: 26, fontWeight: 800, color: C.navy}}>Слушать</div>
      <div style={{display: 'flex', alignItems: 'center', gap: 6, height: 110, marginTop: 10}}>
        {Array.from({length: 30}, (_, i) => <div key={i} style={{width: 8, borderRadius: 4, background: i / 30 < span(u, 1, 3) ? C.accent : C.line,
          height: 18 + 70 * Math.abs(Math.sin(i * .7 + t * 5) * Math.cos(i * .23 + t * 2))}}/>)}
      </div>
      <div style={{display: 'flex', gap: 10, marginTop: 14}}>{rates.map((r, i) => <div key={r} style={{padding: '6px 12px', borderRadius: 12, fontSize: 20, fontWeight: 700,
        background: i === rate ? C.navy : C.white, color: i === rate ? C.white : C.navy, border: `2px solid ${C.line}`}}>{r}</div>)}</div>
    </div>
  </Scene>;
}

function Report({t, range}) {
  const g = useG(), [from] = range, u = t - from;
  const pieces = ['квадрат', 'линии', 'планеты', 'периоды', 'озвучка'];
  const pack = span(u, 1.6, 1.4);
  const piece = (i) => g.portrait ? [80 + (i % 2) * 300, 200 + i * 80] : [170 + i * 200, 220 + (i % 2) * 70];
  const [packX, packY, pageX, pageY] = g.portrait ? [260, 330, 245, 200] : [440, 300, 420, 180];
  const video = g.portrait ? {left: 150, top: 600, width: 420, height: 240} : {left: 740, top: 230, width: 360, height: 210};
  return <Scene t={t} range={range}>
    {pieces.map((name, i) => {
      const show = span(u, .1 + i * .22, .4), [x, y] = piece(i);
      return <div key={name} style={{position: 'absolute', left: mix(x, packX, pack), top: mix(y, packY, pack), padding: '12px 20px', borderRadius: 16, background: C.pale,
        border: `2px solid ${C.accent}`, fontSize: 24, fontWeight: 700, color: C.navy, opacity: show * (1 - pack)}}>{name}</div>;
    })}
    {[2, 1, 0].map((k) => <div key={k} style={{position: 'absolute', left: pageX + k * 16, top: pageY + k * 14, width: 230, height: 310, borderRadius: 14, background: C.white,
      border: `2px solid ${C.line}`, boxShadow: '0 10px 30px rgba(24,59,98,.08)', opacity: pack}}>
      {k === 0 && <div style={{padding: 20}}><div style={{fontSize: 20, fontWeight: 800, color: C.navy}}>Полный разбор</div>
        {[.9, .7, .8, .6, .85, .5].map((w, i) => <div key={i} style={{height: 10, borderRadius: 5, background: C.soft, marginTop: 16, width: `${w * 100}%`}}/>)}
        <div style={{marginTop: 22, display: 'inline-block', padding: '6px 14px', borderRadius: 10, background: C.navy, color: C.white, fontSize: 18, fontWeight: 800}}>PDF</div></div>}
    </div>)}
    <div style={{position: 'absolute', ...video, borderRadius: 18, background: C.navy, opacity: span(u, 3, .6),
      display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${.9 + .1 * span(u, 3, .6)})`}}>
      <div style={{width: 0, height: 0, borderLeft: '46px solid white', borderTop: '28px solid transparent', borderBottom: '28px solid transparent', marginLeft: 10}}/>
      <div style={{position: 'absolute', bottom: 14, left: 18, right: 18, height: 6, borderRadius: 3, background: 'rgba(255,255,255,.25)'}}>
        <div style={{height: 6, borderRadius: 3, background: C.green, width: `${span(u, 3.2, 2.5) * 100}%`}}/></div>
    </div>
  </Scene>;
}

function Begin({t, range}) {
  const g = useG(), [from] = range, u = t - from;
  const schemes = ['KVADRATW.png', '123W.png', '159W.png'];
  const typed = example.date.slice(0, Math.floor(span(u, 1.6, 1.4) * example.date.length));
  const card = (i) => g.portrait ? {left: 40 + i * 215, top: 220 + (i % 2) * 40, width: 210, height: 172} : {left: 120 + i * 250, top: 180 + (i % 2) * 30, width: 230, height: 190};
  return <Scene t={t} range={range}>
    {schemes.map((file, i) => {
      const show = span(u, .1 + i * .25, .5);
      return <div key={file} style={{position: 'absolute', ...card(i), borderRadius: 18, background: C.white,
        border: `2px solid ${C.line}`, overflow: 'hidden', opacity: show, transform: `translateY(${(1 - show) * 30}px) rotate(${(i - 1) * 2}deg)`}}>
        <Img src={staticFile(file)} style={{width: '100%', height: '100%', objectFit: 'contain'}}/>
      </div>;
    })}
    <div style={{position: 'absolute', ...(g.portrait ? {left: 110, top: 560, width: 500} : {left: 900, top: 230, width: 300}), opacity: span(u, 1.2, .5)}}>
      <div style={{fontSize: g.portrait ? 26 : 20, color: C.muted}}>Дата рождения</div>
      <div style={{marginTop: 10, height: g.portrait ? 84 : 64, borderRadius: 14, background: C.white, border: `2px solid ${C.accent}`, display: 'flex', alignItems: 'center', padding: '0 18px',
        fontSize: g.portrait ? 44 : 34, fontWeight: 700, color: C.navy}}>{typed || <span style={{color: C.line}}>ДД.ММ.ГГГГ</span>}<span style={{opacity: Math.round(t * 2) % 2, color: C.accent}}>|</span></div>
    </div>
  </Scene>;
}

function Rhythm({t, range}) {
  const g = useG(), [from, to] = range, u = t - from, travel = span(u, .3, Math.max(1, to - from - .8));
  const points = Array.from({length: 5}, (_, i) => g.portrait ? [360 + 130 * Math.sin(i * 1.3), 220 + i * 150] : [220 + i * 210, 360 + 60 * Math.sin(i * 1.3)]);
  const at = travel * (points.length - 1), k = Math.min(points.length - 2, Math.floor(at)), f = at - k;
  const [mx, my] = [mix(points[k][0], points[k + 1][0], f), mix(points[k][1], points[k + 1][1], f)];
  return <Scene t={t} range={range}>
    <svg width={g.W} height={g.H} style={{position: 'absolute', left: 0, top: 0}}>
      <polyline points={points.map((p) => p.join(',')).join(' ')} fill="none" stroke={C.line} strokeWidth="6" strokeLinecap="round" strokeDasharray="2 14"/>
    </svg>
    {points.map(([x, y], i) => <Chip key={i} x={x} y={y} w={58} h={58} size={28} text={i < at + .01 ? '✓' : ''} fill={i < at + .01 ? C.green : C.white} border={i < at + .01 ? C.accent : C.line}/>)}
    <div style={{position: 'absolute', left: mx - 16, top: my - 16, width: 32, height: 32, borderRadius: 16, background: C.accent, boxShadow: '0 0 0 10px rgba(38,117,104,.15)'}}/>
    <div style={{position: 'absolute', left: 30, right: 30, top: g.portrait ? 930 : 480, textAlign: 'center', fontSize: g.portrait ? 32 : 28, color: C.accent, fontWeight: 600, opacity: span(u, 1, .6)}}>в своём ритме · проверяя на опыте</div>
  </Scene>;
}

function Outro({t, range, end}) {
  const g = useG(), [from] = range, u = t - from, card = span(t, end + .2, .7);
  return <Scene t={t} range={[from, from + 99]}>
    <Img src={staticFile('numerom-logo.svg')} style={{position: 'absolute', left: g.portrait ? 210 : mix(490, 150, card), top: g.portrait ? mix(360, 200, card) : mix(170, 210, card), width: 300, opacity: span(u, 0, .5)}}/>
    <div style={{position: 'absolute', ...(g.portrait ? {left: 30, right: 30, top: 560, textAlign: 'center'} : {left: 560, top: 250}), opacity: card,
      transform: g.portrait ? `translateY(${(1 - card) * 40}px)` : `translateX(${(1 - card) * 40}px)`}}>
      <div style={{color: C.navy, fontSize: g.portrait ? 52 : 48, fontWeight: 800, lineHeight: 1.15}}>Начните с авторских схем</div>
      <div style={{color: C.muted, fontSize: 28, marginTop: 14}}>или введите дату рождения</div>
      <div style={{color: C.accent, fontSize: g.portrait ? 24 : 26, marginTop: 30, fontWeight: 700}}>1.numer.om</div>
    </div>
  </Scene>;
}

export function AuthorWord({word, audio, portrait = false}) {
  const frame = useCurrentFrame();
  const {fps, durationInFrames, width} = useVideoConfig();
  const g = portrait ? PORTRAIT : LANDSCAPE;
  const t = frame / fps;
  const parts = scenes(word.sentences, word.seconds);
  let index = 0;
  word.sentences.forEach((s, i) => {if (s.start <= t) index = i;});
  const sentence = word.sentences[index], ending = t > word.seconds + .2;
  const caption = ending ? 0 : Math.min(span(t, sentence.start, .3), 1 - span(t, sentence.end + .25, .3) * (index < word.sentences.length - 1 ? 1 : 0));
  return <AbsoluteFill style={{backgroundColor: C.background, fontFamily: FONT}}>
    <Audio src={staticFile(audio)}/>
    {/* Positions are authored on a 1280×720 or 720×1280 canvas and scaled to the composition size. */}
    <div style={{position: 'absolute', left: 0, top: 0, width: g.W, height: g.H, transform: `scale(${width / g.W})`, transformOrigin: '0 0'}}>
      <Geometry.Provider value={g}>
        <Drift frame={frame}/>
        <div style={{position: 'absolute', left: g.header.left, top: g.header.top, display: 'flex', alignItems: 'center', gap: 14, opacity: span(t, 3, .6)}}>
          <Img src={staticFile('numerom-logo.svg')} style={{width: g.header.logo}}/>
          <div style={{color: C.accent, fontSize: g.header.size, letterSpacing: 4, fontWeight: 700}}>СЛОВО АВТОРА · ДМИТРИЙ</div>
        </div>
        <Intro t={t} range={parts.intro} sentences={word.sentences}/>
        <Sources t={t} range={parts.sources}/>
        <Path t={t} range={parts.path} sentences={word.sentences}/>
        <SchemeScene t={t} range={parts.scheme}/>
        <Listen t={t} range={parts.listen}/>
        <Report t={t} range={parts.report}/>
        <Begin t={t} range={parts.begin}/>
        <Rhythm t={t} range={parts.rhythm}/>
        <Outro t={t} range={parts.outro} end={word.seconds}/>
        <div style={{position: 'absolute', left: g.caption.left, right: g.caption.right, bottom: g.caption.bottom, textAlign: 'center',
          fontSize: sentence.text.length > 110 ? g.caption.small : g.caption.size, lineHeight: 1.3, color: C.ink, opacity: caption,
          background: 'rgba(244,247,251,.85)', borderRadius: 14, padding: '6px 12px'}}>{sentence.text}</div>
        <div style={{position: 'absolute', left: 0, right: 0, bottom: 0, height: 6, backgroundColor: C.soft}}>
          <div style={{height: 6, width: `${Math.min(100, frame / durationInFrames * 100)}%`, backgroundColor: C.accent}}/>
        </div>
      </Geometry.Provider>
    </div>
  </AbsoluteFill>;
}
