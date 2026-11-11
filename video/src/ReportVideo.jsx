import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import brandLogo from '../../packages/brand/numerom-logo.svg';
import schematics from '../../packages/full-report/schematics.js';
import {buildTimeline, sceneModel, focusAt} from './timeline.mjs';
import {svgSource} from './layout.mjs';
import {appearances, formulaFor, extraNumbers, highlightCues, sharedSteps, spokenExtra, spokenWords} from './motion.mjs';

// Colours of the app and of the author schemes; the same language as «Слово автора».
const C = {background: '#F4F7FB', navy: '#183B62', ink: '#20364E', muted: '#61758B', blue: '#356FA5', line: '#D3DFEA',
  pale: '#EDF6F2', green: '#D0E9DF', accent: '#267568', white: '#FFFFFF', soft: '#EAF1F9', amber: '#B7791F', amberPale: '#FBF1DF'};
const FONT = '-apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif';
const STAGE = {top: 158, height: 414, left: 56, width: 1168};
const clamp = (v) => Math.max(0, Math.min(1, v));
const ease = (v) => {const t = clamp(v); return t * t * (3 - 2 * t);};

// A saved number never counts up: it drops in whole, with a little weight, when the voice names it.
function useMotion(reduced) {
  const frame = useCurrentFrame(), {fps} = useVideoConfig();
  const pop = (at, config) => reduced ? (frame >= at ? 1 : 0)
    : spring({frame: frame - at, fps, config: {damping: 12, stiffness: 150, mass: .7, ...config}});
  const grow = (at, length = 16) => reduced ? (frame >= at ? 1 : 0) : ease((frame - at) / length);
  return {frame, fps, pop, grow};
}
const drop = (p) => ({opacity: clamp(p * 1.6), transform: `translateY(${(1 - p) * -150}px) rotate(${(1 - p) * -6}deg) scale(${.86 + .14 * p})`});

function Drift({frame}) {
  return <AbsoluteFill>{Array.from({length: 16}, (_, i) => {
    const x = (i * 89 + frame * (.12 + (i % 4) * .05)) % 1360 - 40, y = 70 + (i * 47) % 600 + 10 * Math.sin(frame / 55 + i);
    return <div key={i} style={{position: 'absolute', left: x, top: y, fontSize: 24 + (i % 3) * 16, fontWeight: 700, color: C.blue, opacity: .045}}>{(i * 7) % 9 + 1}</div>;
  })}</AbsoluteFill>;
}

function Header({report, index, count, frame}) {
  return <div style={{position: 'absolute', left: 40, right: 40, top: 20, height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
      <Img src={brandLogo} style={{width: 58, height: 46, objectFit: 'contain', transform: `rotate(${Math.sin(frame / 160) * 2}deg)`}}/>
      <span style={{fontSize: 15, letterSpacing: 3, fontWeight: 700, color: C.accent}}>ПОЛНЫЙ РАЗБОР · {report.birthDate}</span>
    </div>
    <span style={{fontSize: 17, color: C.muted, fontVariantNumeric: 'tabular-nums'}}>Глава {index + 1} из {count}</span>
  </div>;
}

function Title({title, frame, reduced}) {
  const m = reduced ? 1 : ease(frame / 14);
  return <div style={{position: 'absolute', left: 56, right: 56, top: 88, height: 60}}>
    <h1 style={{margin: 0, fontSize: title.length > 60 ? 30 : 38, lineHeight: 1.1, fontWeight: 700, letterSpacing: '-0.02em', color: C.navy,
      opacity: m, transform: `translateX(${(1 - m) * -40}px)`}}>{title}</h1>
    <div style={{height: 4, width: 140 * (reduced ? 1 : ease((frame - 6) / 16)), background: C.accent, borderRadius: 2, marginTop: 8}}/>
  </div>;
}

// The current sentence, with the words already spoken in ink and the rest still muted.
function Caption({chapter, frame}) {
  const caption = sceneModel(chapter, frame).caption;
  const words = String(caption.text || '').split(/\s+/).filter(Boolean);
  if (!words.length) return null;
  const said = spokenWords(caption, frame);
  return <div style={{position: 'absolute', left: 56, right: 56, top: 590, height: 96, background: C.white, borderRadius: 18,
    border: `1px solid ${C.line}`, display: 'flex', alignItems: 'center', padding: '0 28px', boxSizing: 'border-box'}}>
    <p style={{margin: 0, fontSize: caption.text.length > 120 ? 23 : 26, lineHeight: 1.35}}>
      {words.map((word, i) => <span key={i} style={{color: i < said ? C.ink : '#9AABBC'}}>{word} </span>)}
    </p>
  </div>;
}

function FormulaPill({label, formula, at, motion, top = 330}) {
  if (!formula) return null;
  const p = motion.pop(at), reveal = motion.grow(at + 4, 14);
  return <div style={{position: 'absolute', left: 0, right: 0, top, display: 'flex', justifyContent: 'center', ...drop(Math.min(1, p))}}>
    <div style={{background: C.navy, color: C.white, borderRadius: 40, padding: '14px 30px', fontSize: 26, display: 'flex', gap: 16, alignItems: 'center',
      maxWidth: 1100, overflow: 'hidden', whiteSpace: 'nowrap', boxShadow: '0 12px 30px rgba(24,59,98,.22)'}}>
      <span style={{opacity: .7, fontSize: 21}}>{label}</span>
      <span style={{fontWeight: 600, clipPath: `inset(0 ${(1 - reveal) * 100}% 0 0)`}}>{formula}</span>
    </div>
  </div>;
}

// At the start of a chapter, the calculation shared by all its values: «Как получено: 1001 × 1982 = 1983982».
function SharedStep({section, motion, top}) {
  const step = sharedSteps(section)[0];
  if (!step || motion.frame > 30 + 24 * 9) return null;
  const fade = 1 - motion.grow(30 + 24 * 8, 20);
  const [label, formula] = step.includes(': ') ? [step.slice(0, step.indexOf(': ')), step.slice(step.indexOf(': ') + 2)] : ['Как получено', step];
  return <div style={{opacity: fade}}><FormulaPill label={label} formula={formula} at={30} motion={motion} top={top}/></div>;
}

function DateDigits({date, motion, y = 0, from = 4}) {
  const chars = [...date];
  return <div style={{position: 'absolute', left: 0, right: 0, top: y, display: 'flex', justifyContent: 'center', gap: 8}}>
    {chars.map((ch, i) => ch === '.' ? <span key={i} style={{fontSize: 34, color: C.muted, alignSelf: 'flex-end'}}>.</span>
      : <div key={i} style={{width: 44, height: 54, borderRadius: 12, background: C.white, border: `2px solid ${C.line}`, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: 30, fontWeight: 700, color: C.navy, ...drop(Math.min(1, motion.pop(from + i * 3)))}}>{ch}</div>)}
  </div>;
}

// Personal numbers, fractal, tasks, periods, profile tools: one tile per saved value.
function Tiles({chapter, report, motion}) {
  const section = chapter.section, values = section.values.slice(0, 12), n = values.length;
  const enter = appearances(chapter, n), {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const kind = section.diagram?.kind;
  const withDate = ['personal', 'fractal', 'vedic-numbers'].includes(section.id);
  const years = kind === 'period' ? section.diagram.years ?? [] : [];
  const cols = n <= 4 ? n : n <= 6 ? 3 : n <= 8 ? 4 : 5, rows = Math.ceil(n / cols);
  const gap = 22, width = Math.min(250, (STAGE.width - 120 - (cols - 1) * gap) / cols);
  const height = rows === 1 ? (years.length ? 150 : 180) : rows === 2 ? (withDate ? 112 : 128) : 92;
  const top = withDate ? 78 : years.length ? 6 : 20;
  const pillTop = years.length ? 330 : Math.min(352, top + rows * (height + 16) + 10);
  const left = (STAGE.width - (cols * width + (cols - 1) * gap)) / 2;
  const chain = kind === 'period' || kind === 'individual' || kind === 'sequence';
  const active = Number.isInteger(focusIndex) && focusIndex < n ? focusIndex : null;
  return <>
    {withDate && <DateDigits date={report.birthDate} motion={motion}/>}
    {values.map((value, i) => {
      const x = left + (i % cols) * (width + gap), y = top + Math.floor(i / cols) * (height + 16);
      const shown = motion.frame >= enter[i].frame, p = Math.min(1.08, motion.pop(enter[i].frame));
      const on = i === active, emphasis = on ? motion.pop(focusFromFrame, {damping: 14}) : 0;
      return <div key={i} style={{position: 'absolute', left: x, top: y, width, height}}>
        {chain && i % cols > 0 && <div style={{position: 'absolute', left: -gap + 2, top: height / 2 - 2, width: (gap - 4) * motion.grow(enter[i].frame, 10), height: 4, background: C.accent, borderRadius: 2}}/>}
        <div style={{position: 'absolute', inset: 0, borderRadius: 18, border: `2px ${shown ? 'solid' : 'dashed'} ${on ? C.accent : C.line}`,
          background: on ? C.green : shown ? C.white : 'transparent', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 4,
          boxShadow: on ? `0 ${10 + 8 * emphasis}px ${24 + 16 * emphasis}px rgba(38,117,104,${.18 + .12 * emphasis})` : 'none',
          transform: `scale(${1 + .07 * emphasis + (on ? .012 * Math.sin(motion.frame / 9) : 0)})`, boxSizing: 'border-box', padding: '6px 10px'}}>
          <div style={{fontSize: rows > 2 ? 15 : 18, color: on ? C.accent : C.muted, textAlign: 'center', lineHeight: 1.15, fontWeight: on ? 700 : 500}}>{value.label}</div>
          <div style={{fontSize: rows > 2 ? 40 : rows === 2 ? 52 : 68, fontWeight: 700, color: C.navy, lineHeight: 1, ...(shown ? drop(p) : {opacity: .14 + .1 * (1 + Math.sin(motion.frame / 11 + i * 1.7)) / 2})}}>{shown ? value.value : '?'}</div>
        </div>
      </div>;
    })}
    {years.length > 0 && <div style={{position: 'absolute', left: 60, right: 60, top: 196, display: 'flex', justifyContent: 'space-between'}}>
      {years.map((year, i) => {const p = Math.min(1, motion.pop(30 + i * 5)); return <div key={i} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, ...drop(p)}}>
        <div style={{width: 58, height: 58, borderRadius: 29, background: C.soft, border: `2px solid ${C.line}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 700, color: C.blue}}>{year.value}</div>
        <div style={{fontSize: 15, color: C.muted}}>{year.age} лет</div><div style={{fontSize: 13, color: C.muted}}>{year.year}</div>
      </div>;})}
    </div>}
    {active !== null ? <FormulaPill key={focusFromFrame} label={values[active].label.split(' · ')[0]} formula={formulaFor(section, active)} at={focusFromFrame} motion={motion} top={pillTop}/>
      : <SharedStep section={section} motion={motion} top={pillTop}/>}
  </>;
}

// Pythagorean square and yantra: the date (and А1–А4) digits fly into their cells, then each named cell lights up.
const CELL = {w: 150, h: 84, gap: 12, x: 300};
const cellCenter = (i, y = 118) => [CELL.x + (i % 3) * (CELL.w + CELL.gap) + CELL.w / 2, y + Math.floor(i / 3) * (CELL.h + CELL.gap) + CELL.h / 2];

function Grid({cells, landed, active, motion, emphasis, y}) {
  return cells.map((cell, i) => {
    const [cx, cy] = cellCenter(i, y), on = i === active, count = landed ? landed[i] : cell.digits.length;
    return <div key={i} style={{position: 'absolute', left: cx - CELL.w / 2, top: cy - CELL.h / 2, width: CELL.w, height: CELL.h, borderRadius: 14,
      background: on ? C.green : C.white, border: `2px solid ${on ? C.accent : C.line}`, boxSizing: 'border-box',
      transform: `scale(${1 + (on ? .08 * emphasis : 0)})`, boxShadow: on ? '0 14px 30px rgba(38,117,104,.25)' : 'none'}}>
      <span style={{position: 'absolute', left: 10, top: 6, fontSize: 15, color: C.muted}}>{cell.digit}</span>
      <div style={{position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: cell.digits.length > 4 ? 28 : 36,
        fontWeight: 700, color: C.navy}}>{count ? cell.digits.slice(0, count) : '—'}</div>
    </div>;
  });
}

function Square({chapter, report, motion}) {
  const section = chapter.section, cells = section.diagram.cells;
  const extras = section.id === 'square' ? extraNumbers(section) : [];
  const dateDigits = [...report.birthDate].filter((c) => /\d/.test(c));
  // Every non-zero digit of the date and of А1–А4, in order; skip the flight if it would not rebuild the saved cells.
  const sources = [...dateDigits.map((d, i) => ({digit: +d, from: [STAGE.width / 2 - 260 + i * 52 + (i > 1 ? 14 : 0) + (i > 3 ? 14 : 0), 27]})),
    ...extras.flatMap((extra, e) => [...extra.value].map((d) => ({digit: +d, from: [STAGE.width / 2 - 250 + e * 150 + 80, 82]})))].filter((s) => s.digit > 0);
  const exact = cells.every((cell) => sources.filter((s) => s.digit === cell.digit).length === cell.digits.length);
  const flights = exact ? sources.map((s, k) => ({...s, at: 34 + k * 4, cell: cells.findIndex((c) => c.digit === s.digit)})) : [];
  const landed = exact ? cells.map((_, i) => flights.filter((f) => f.cell === i && motion.frame >= f.at + 14).length) : null;
  const {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const active = Number.isInteger(focusIndex) && focusIndex < cells.length ? focusIndex : null;
  const value = active !== null ? section.values[active] : null;
  const caption = sceneModel(chapter, motion.frame).caption, named = extras.length ? spokenExtra(caption, motion.frame) : null;
  const namedStep = named && section.steps.find((step) => step.startsWith(named + ':'));
  return <>
    <DateDigits date={report.birthDate} motion={motion}/>
    {extras.length > 0 && <div style={{position: 'absolute', left: 0, right: 0, top: 64, display: 'flex', justifyContent: 'center', gap: 20}}>
      {extras.map((extra, e) => {const on = extra.label === named;
        return <div key={e} style={{padding: '6px 14px', borderRadius: 12, background: on ? C.accent : C.soft, fontSize: 20, color: on ? C.white : C.navy,
          transform: `scale(${on ? 1.12 : 1})`, boxShadow: on ? '0 8px 20px rgba(38,117,104,.35)' : 'none', ...(on ? {} : drop(Math.min(1, motion.pop(16 + e * 4))))}}>
          <span style={{opacity: .75, marginRight: 8}}>{extra.label}</span><b>{extra.value}</b></div>;})}
    </div>}
    {namedStep && <div key={named + caption.fromFrame} style={{position: 'absolute', left: 840, top: value ? 300 : 150, width: 320, background: C.navy, color: C.white, borderRadius: 18,
      padding: '14px 20px', boxSizing: 'border-box', fontSize: 21, lineHeight: 1.35, boxShadow: '0 12px 30px rgba(24,59,98,.22)', ...drop(Math.min(1, motion.pop(caption.fromFrame)))}}>
      <div style={{opacity: .7, fontSize: 17, marginBottom: 4}}>{named}</div><b>{namedStep.slice(named.length + 1).trim()}</b></div>}
    <Grid cells={cells} landed={landed} active={active} motion={motion} emphasis={active !== null ? motion.pop(focusFromFrame) : 0}/>
    {flights.map((f, k) => {
      const t = motion.grow(f.at, 14);
      if (t <= 0 || t >= 1) return null;
      const [tx, ty] = cellCenter(f.cell), x = f.from[0] + (tx - f.from[0]) * t, y = f.from[1] + (ty - f.from[1]) * t - 60 * Math.sin(Math.PI * t);
      return <div key={k} style={{position: 'absolute', left: x - 18, top: y - 22, width: 36, height: 44, borderRadius: 10, background: C.accent, color: C.white,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, fontWeight: 700, boxShadow: '0 8px 18px rgba(38,117,104,.35)'}}>{f.digit}</div>;
    })}
    {value && <div key={focusFromFrame} style={{position: 'absolute', left: 840, top: 150, width: 300, background: C.white, borderRadius: 20, border: `2px solid ${C.accent}`,
      padding: '18px 22px', boxSizing: 'border-box', ...drop(Math.min(1, motion.pop(focusFromFrame)))}}>
      <div style={{fontSize: 20, color: C.accent, fontWeight: 700}}>{value.label}</div>
      <div style={{fontSize: 64, fontWeight: 700, color: C.navy, lineHeight: 1.1}}>{value.value}</div>
      <div style={{fontSize: 16, color: C.muted}}>{section.id === 'square' ? 'сколько раз цифра в расчёте' : 'значение ячейки'}</div>
    </div>}
  </>;
}

// Lines: each named row, column or diagonal is traced across its three cells and its sum pops at the end.
function Lines({chapter, motion}) {
  const section = chapter.section, cells = section.diagram.cells, directions = section.diagram.directions ?? [];
  const enter = appearances(chapter, directions.length), {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const position = (digit) => cellCenter(cells.findIndex((c) => c.digit === digit), 28);
  return <>
    <Grid cells={cells} landed={null} active={null} motion={motion} emphasis={0} y={28}/>
    <svg width={STAGE.width} height={STAGE.height} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
      {directions.map((direction, i) => {
        const [a, b] = [position(direction.digits[0]), position(direction.digits[2])], on = i === focusIndex;
        const dx = b[0] - a[0], dy = b[1] - a[1], length = Math.hypot(dx, dy), ux = dx / length, uy = dy / length;
        const start = [a[0] - ux * 70, a[1] - uy * 34], end = [b[0] + ux * 70, b[1] + uy * 34];
        const t = motion.grow(enter[i].frame, on ? 16 : 10);
        if (t <= 0) return null;
        const tip = [start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t];
        const sum = Math.min(1, motion.pop(enter[i].frame + 12));
        return <g key={direction.id} opacity={on ? 1 : .28}>
          <line x1={start[0]} y1={start[1]} x2={tip[0]} y2={tip[1]} stroke={on ? C.accent : C.blue} strokeWidth={on ? 9 : 4} strokeLinecap="round"/>
          {t >= 1 && <g transform={`translate(${end[0] + ux * 26} ${end[1] + uy * 20}) scale(${sum})`}>
            <circle r="24" fill={on ? C.accent : C.white} stroke={on ? C.accent : C.line} strokeWidth="2"/>
            <text y="8" textAnchor="middle" fontSize="22" fontWeight="700" fill={on ? C.white : C.navy}>{direction.value}</text></g>}
        </g>;
      })}
    </svg>
    <div style={{position: 'absolute', left: 870, top: 4, width: 290, display: 'flex', flexDirection: 'column', gap: 6}}>
      {section.values.slice(0, 8).map((value, i) => {const on = i === focusIndex, shown = motion.frame >= (enter[i]?.frame ?? 0);
        return <div key={i} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: 34, padding: '0 14px', borderRadius: 10, boxSizing: 'border-box',
          background: on ? C.green : C.white, border: `1px solid ${on ? C.accent : C.line}`, fontSize: 17, color: on ? C.accent : C.ink, opacity: shown ? 1 : .35}}>
          <span>{value.label}</span><b style={{fontSize: 22, color: C.navy}}>{shown ? value.value : '·'}</b></div>;})}
    </div>
    {Number.isInteger(focusIndex) && <FormulaPill key={focusFromFrame} label={section.values[focusIndex]?.label ?? ''} formula={formulaFor(section, focusIndex)} at={focusFromFrame} motion={motion} top={352}/>}
  </>;
}

// Planets, energies and other measures: bars grow as their names are said.
function Bars({chapter, motion}) {
  const values = chapter.section.values.filter((v) => typeof v.value === 'number').slice(0, 12), n = values.length;
  const enter = appearances(chapter, n), {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const max = Math.max(1, ...values.map((v) => Math.abs(v.value))), row = Math.min(44, 320 / n);
  return <>{values.map((value, i) => {
    const on = i === focusIndex, t = motion.grow(enter[i].frame, 18), pop = Math.min(1.1, motion.pop(enter[i].frame + 10));
    return <div key={i} style={{position: 'absolute', left: 60, right: 60, top: 18 + i * row, height: row - 8, display: 'flex', alignItems: 'center', gap: 18,
      transform: `scale(${on ? 1 + .03 * motion.pop(focusFromFrame) : 1})`}}>
      <div style={{width: 280, fontSize: row > 36 ? 22 : 18, color: on ? C.accent : C.ink, fontWeight: on ? 700 : 500, textAlign: 'right'}}>{value.label}</div>
      <div style={{flex: 1, height: row * .55, background: C.soft, borderRadius: 12, overflow: 'hidden'}}>
        <div style={{width: `${Math.abs(value.value) / max * 100 * t}%`, height: '100%', borderRadius: 12, background: on ? C.accent : C.blue,
          boxShadow: on ? '0 0 18px rgba(38,117,104,.45)' : 'none'}}/>
      </div>
      <div style={{width: 90, fontSize: row > 36 ? 30 : 24, fontWeight: 700, color: C.navy, transform: `scale(${t > 0 ? pop : 1})`, opacity: t > 0 ? clamp(pop) : .2}}>{t > 0 ? value.value : '?'}</div>
    </div>;
  })}
  {!Number.isInteger(focusIndex) && <SharedStep section={chapter.section} motion={motion} top={340}/>}</>;
}

// A hundred personal years, thirty route days, twenty-four hours: the line draws itself and the named point lights up.
const ageLabel = (age) => {
  const tail = age % 10, teen = age % 100 >= 11 && age % 100 <= 14;
  return `${age} ${!teen && tail === 1 ? 'год' : !teen && tail >= 2 && tail <= 4 ? 'года' : 'лет'}`;
};

function Series({chapter, motion}) {
  const section = chapter.section;
  const points = section.diagram?.years?.map((y) => ({label: ageLabel(y.age), value: y.value}))
    ?? (section.chart?.items ?? section.values).filter((v) => typeof v.value === 'number').map((v) => ({label: v.label, value: v.value}));
  if (!points.length) return null;
  // Personal years and planet codes are digits: a fixed 0–9 scale. Measures (route days) get their own range.
  const digits = !!section.diagram?.years || points.every((p) => Number.isInteger(p.value) && p.value >= 0 && p.value <= 9);
  const low = digits ? 0 : Math.floor(Math.min(...points.map((p) => p.value)) - 3), high = digits ? 9 : Math.ceil(Math.max(...points.map((p) => p.value)) + 3);
  const W = 1060, H = 270, X = 70, Y = 20;
  const px = (i) => X + i / Math.max(1, points.length - 1) * W, py = (v) => Y + H - (v - low) / Math.max(1, high - low) * H;
  const draw = motion.grow(20, 70);
  const {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const active = Number.isInteger(focusIndex) && focusIndex < points.length ? focusIndex : null;
  const path = points.map((p, i) => `${px(i)},${py(p.value)}`).join(' ');
  return <><svg width={STAGE.width} height={STAGE.height} style={{position: 'absolute', left: 0, top: 0}}>
    {(section.diagram?.periods ?? []).map((period, i) => {
      const a = px(Math.max(0, period.start - 1)), b = px(Math.min(points.length - 1, period.end - 1)), p = motion.grow(90 + i * 8, 14);
      return <g key={i} opacity={p}><rect x={a} y={Y} width={Math.max(0, b - a)} height={H} fill={i % 2 ? C.pale : C.soft}/>
        <text x={(a + b) / 2} y={Y + 22} textAnchor="middle" fontSize="18" fill={C.accent} fontWeight="700">{period.start}–{period.end}</text></g>;
    })}
    {[low, (low + high) / 2, high].map((v) => <g key={v}><line x1={X} x2={X + W} y1={py(v)} y2={py(v)} stroke={C.line}/>
      <text x={X - 12} y={py(v) + 6} textAnchor="end" fontSize="16" fill={C.muted}>{Math.round(v)}</text></g>)}
    <polyline points={path} fill="none" stroke={C.blue} strokeWidth="3.5" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - draw}/>
    {points.length <= 40 && points.map((p, i) => i / points.length <= draw && <circle key={i} cx={px(i)} cy={py(p.value)} r="5" fill={C.white} stroke={C.blue} strokeWidth="2.5"/>)}
    {[0, Math.floor((points.length - 1) / 2), points.length - 1].map((i) => <text key={i} x={px(i)} y={Y + H + 28} textAnchor="middle" fontSize="16" fill={C.muted}>{points[i].label.split(' · ')[0]}</text>)}
    {active !== null && (() => {const e = Math.min(1, motion.pop(focusFromFrame)), x = px(active), y = py(points[active].value);
      return <g key={focusFromFrame}><line x1={x} x2={x} y1={Y} y2={Y + H} stroke={C.accent} strokeDasharray="6 6" opacity={e}/>
        <circle cx={x} cy={y} r={10 * e} fill={C.accent} stroke={C.white} strokeWidth="3"/>
        <g transform={`translate(${Math.min(W - 60, Math.max(X + 90, x))} ${Math.max(Y + 40, y - 44)}) scale(${e})`}>
          <rect x="-110" y="-30" width="220" height="44" rx="14" fill={C.navy}/>
          <text y="0" textAnchor="middle" fontSize="19" fill={C.white} fontWeight="700">{points[active].label.split(' · ')[0]} · {points[active].value}</text></g></g>;})()}
  </svg>
  {active === null && <SharedStep section={section} motion={motion} top={344}/>}</>;
}

// Interpretation without a number (practices, solar intervals): one card per theme, flying in as it is read.
function Cards({chapter, motion}) {
  const values = chapter.section.values, n = values.length;
  const {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const index = Number.isInteger(focusIndex) && focusIndex < n ? focusIndex : Math.min(n - 1, Math.floor(motion.frame / chapter.durationInFrames * n));
  const since = Number.isInteger(focusIndex) ? focusFromFrame : Math.floor(index * chapter.durationInFrames / n);
  const item = values[index], p = Math.min(1, motion.pop(since));
  const reading = chapter.section.position_readings?.find(entry => entry.value_index === index);
  return <>
    <div style={{position: 'absolute', left: 60, top: 20, display: 'flex', flexDirection: 'column', gap: 6, width: 300}}>
      {values.slice(0, 9).map((v, i) => <div key={i} style={{height: 34, lineHeight: '34px', padding: '0 14px', borderRadius: 10, fontSize: 16, whiteSpace: 'nowrap', overflow: 'hidden',
        textOverflow: 'ellipsis', background: i === index ? C.green : C.white,
        border: `1px solid ${i === index ? C.accent : C.line}`, color: i === index ? C.accent : i < index ? C.ink : C.muted, fontWeight: i === index ? 700 : 500}}>{v.label}</div>)}
    </div>
    <div key={since} style={{position: 'absolute', left: 400, top: 20, width: 760, minHeight: 300, background: C.white, borderRadius: 24, border: `2px solid ${C.accent}`,
      padding: '26px 32px', boxSizing: 'border-box', opacity: clamp(p * 1.4), transform: `translateX(${(1 - p) * 160}px) rotate(${(1 - p) * 3}deg)`,
      boxShadow: '0 16px 40px rgba(24,59,98,.12)'}}>
      <div style={{fontSize: 22, color: C.accent, fontWeight: 700, marginBottom: 12}}>{item.label}</div>
      <div style={{fontSize: 25, lineHeight: 1.35, color: C.ink}}>{reading?.insight || item.meaning.split('\nОснование в расчёте:')[0]}</div>
    </div>
  </>;
}

// «Главное в вашем разборе»: potentials on the left, points of attention on the right, each appearing as it is read.
function Summary({chapter, report, motion}) {
  const groups = highlightCues(chapter, report.highlights);
  const first = groups[0]?.fromFrame ?? chapter.durationInFrames;
  if (motion.frame < first) {
    const fade = 1 - motion.grow(first - 12, 12);
    // The opening (title, dates, notice) is the first sentence; the overview follows, one sentence per card.
    const said = chapter.segments.slice(1).filter((segment) => segment.fromFrame < first && segment.fromFrame <= motion.frame).slice(-3);
    if (said.length) return <div style={{position: 'absolute', inset: 0, opacity: fade}}>
      <div style={{fontSize: 18, letterSpacing: 2, fontWeight: 700, color: C.accent, marginLeft: 60, marginBottom: 14}}>ОБЗОР ВАШЕГО РАЗБОРА</div>
      {said.map((segment, i) => {const current = i === said.length - 1, p = Math.min(1, motion.pop(segment.fromFrame));
        return <div key={segment.fromFrame} style={{margin: '0 60px 12px', padding: current ? '18px 26px' : '10px 22px', borderRadius: 18, background: current ? C.white : 'transparent',
          border: `2px solid ${current ? C.accent : C.line}`, fontSize: current ? 28 : 19, lineHeight: 1.3, color: current ? C.navy : C.muted,
          opacity: clamp(p * 1.4), transform: `translateX(${(1 - p) * 120}px)`}}>{segment.text}</div>;})}
    </div>;
    return <div style={{position: 'absolute', inset: 0, opacity: fade}}>
      <DateDigits date={report.birthDate} motion={motion} y={40}/>
      <div style={{position: 'absolute', left: 0, right: 0, top: 150, display: 'flex', justifyContent: 'center', gap: 28}}>
        {report.highlights.map((group, g) => <div key={g} style={{padding: '18px 30px', borderRadius: 20, fontSize: 26, fontWeight: 700,
          background: g === 0 ? C.pale : C.amberPale, color: g === 0 ? C.accent : C.amber, border: `2px solid ${g === 0 ? C.accent : C.amber}`,
          ...drop(Math.min(1, motion.pop(40 + g * 10)))}}>{g === 0 ? '✦ ' : '◎ '}{group.title}</div>)}
      </div>
    </div>;
  }
  return groups.map((group, g) => {
    if (motion.frame < group.fromFrame) return null;
    const left = g === 0 ? 0 : 590, colour = g === 0 ? C.accent : C.amber, pale = g === 0 ? C.pale : C.amberPale;
    const current = group.items.reduce((at, item, i) => motion.frame >= item.fromFrame ? i : at, -1);
    const live = current >= 0 && (groups[g + 1] ? motion.frame < groups[g + 1].fromFrame : true);
    return <div key={g} style={{position: 'absolute', left, top: 0, width: 578, height: STAGE.height}}>
      <div style={{fontSize: 24, fontWeight: 700, color: colour, marginBottom: 10, ...drop(Math.min(1, motion.pop(group.fromFrame)))}}>{g === 0 ? '✦ ' : '◎ '}{group.title}</div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 8}}>
        {group.items.map((item, i) => {
          if (motion.frame < item.fromFrame) return null;
          const open = live && i === current, p = Math.min(1, motion.pop(item.fromFrame));
          return <div key={i} style={{background: open ? pale : C.white, border: `2px solid ${open ? colour : C.line}`, borderRadius: 16, padding: open ? '14px 18px' : '8px 16px',
            fontSize: open ? 21 : 16, lineHeight: 1.3, color: C.ink, overflow: 'hidden', maxHeight: open ? 170 : 36, whiteSpace: open ? 'normal' : 'nowrap', textOverflow: 'ellipsis', ...drop(p)}}>
            {item.text}</div>;
        })}
      </div>
    </div>;
  });
}

function Schematic({chapter, motion}) {
  const {focusIndex, focusFromFrame} = focusAt(chapter, motion.frame);
  const diagram = chapter.section.diagram, svg = schematics.diagramSvg(diagram, {activeIndex: focusIndex ?? undefined});
  const p = Math.min(1, motion.pop(8)), pulse = Number.isInteger(focusIndex) ? motion.pop(focusFromFrame) : 1;
  return <div style={{position: 'absolute', inset: 0, display: 'flex', justifyContent: 'center', ...drop(p)}}>
    <Img src={svgSource(svg)} style={{height: STAGE.height, width: 760, objectFit: 'contain', transform: `scale(${.97 + .03 * pulse})`}}/>
  </div>;
}

function TextOnly({chapter, motion}) {
  const text = chapter.section?.paragraphs?.[0] || chapter.title;
  return <div style={{position: 'absolute', left: 120, right: 120, top: 60, fontSize: 32, lineHeight: 1.4, color: C.navy, textAlign: 'center', ...drop(Math.min(1, motion.pop(10)))}}>{text}</div>;
}

export function sceneKind(chapter, highlights) {
  const section = chapter.section, kind = section?.diagram?.kind;
  if (chapter.id === 'full-report-summary' && highlights?.length) return 'summary';
  if (!section || !section.values.length) return 'text';
  if (kind === 'square' && section.diagram.cells?.length === 9) return 'square';
  if (kind === 'lines' && section.diagram.cells?.length === 9) return 'lines';
  if (kind === 'triangle' || kind === 'human') return 'schematic';
  if (['personal', 'sequence', 'tasks', 'individual', 'period'].includes(kind)) return 'tiles';
  if (kind === 'series' || section.chart?.type === 'series' || section.values.length > 12) return 'series';
  if (section.values.every((v) => v.value === null)) return 'cards';
  if (kind === 'bars' || (section.values.length > 6 && section.values.every((v) => typeof v.value === 'number'))) return 'bars';
  return 'tiles';
}
const SCENES = {summary: Summary, square: Square, lines: Lines, schematic: Schematic, series: Series, cards: Cards, bars: Bars, tiles: Tiles, text: TextOnly};

function Chapter({chapter, index, count, report, startFrame, totalFrames}) {
  const reduced = report.motion === 'reduced';
  const motion = useMotion(reduced), {frame} = motion;
  const kind = sceneKind(chapter, report.highlights), Scene = SCENES[kind];
  const stage = reduced ? 1 : ease((frame - 6) / 14);
  return <AbsoluteFill style={{fontFamily: FONT, color: C.ink, background: C.background}}>
    <Audio src={chapter.audioSrc} volume={1}/>
    {!reduced && <Drift frame={startFrame + frame}/>}
    <Header report={report} index={index} count={count} frame={startFrame + frame}/>
    <Title title={kind === 'summary' ? 'Главное в вашем разборе' : chapter.section?.title || chapter.title} frame={frame} reduced={reduced}/>
    <div style={{position: 'absolute', left: STAGE.left, top: STAGE.top, width: STAGE.width, height: STAGE.height, opacity: stage}}>
      <Scene chapter={chapter} report={report} motion={motion}/>
    </div>
    <Caption chapter={chapter} frame={frame}/>
    <div style={{position: 'absolute', left: 0, bottom: 0, height: 5, width: `${Math.min(100, (startFrame + frame + 1) / totalFrames * 100)}%`, background: C.accent}}/>
  </AbsoluteFill>;
}

export function ReportVideo({report}) {
  const timeline = buildTimeline(report.chapters);
  return <AbsoluteFill>{timeline.chapters.map(({chapter, index, fromFrame, durationInFrames}) =>
    <Sequence key={chapter.id} from={fromFrame} durationInFrames={durationInFrames} premountFor={0}>
      <Chapter chapter={chapter} index={index} count={timeline.chapters.length} report={{...report, highlights: report.highlights ?? []}}
        startFrame={fromFrame} totalFrames={timeline.durationInFrames}/>
    </Sequence>)}</AbsoluteFill>;
}
