import React, { useEffect, useState } from 'react';
import { loadingFrame } from '../../../../packages/full-report/loading-motion';

// «Отчёт готовится»: the birth date's digits fly into the Pythagorean square, then its lines are traced.
export default function ReportPreparing({ birthDate, message }) {
  const [seconds, setSeconds] = useState(0);
  const [reduced, setReduced] = useState(() => typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    if (!query) return undefined;
    const change = (event) => setReduced(event.matches);
    query.addEventListener?.('change', change);
    return () => query.removeEventListener?.('change', change);
  }, []);
  useEffect(() => {
    if (reduced || typeof requestAnimationFrame !== 'function') return undefined;
    let frame = 0, last = 0;
    const start = performance.now();
    const tick = (now) => { if (now - last >= 33) { last = now; setSeconds((now - start) / 1000); } frame = requestAnimationFrame(tick); };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [reduced]);
  const view = loadingFrame(seconds, birthDate, reduced);
  return <div className="fr-preparing" role="progressbar" aria-label={`Отчёт готовится. ${view.caption}`}>
    <svg viewBox={`0 0 ${view.width} ${view.height}`} aria-hidden="true">
      {view.shapes.map((shape, i) => shape.kind === 'rect'
        ? <rect key={i} x={shape.x} y={shape.y} width={shape.w} height={shape.h} rx={shape.r} fill={shape.fill} stroke={shape.stroke} strokeWidth="1.2" opacity={shape.opacity} />
        : shape.kind === 'line'
          ? <line key={i} x1={shape.x1} y1={shape.y1} x2={shape.x2} y2={shape.y2} stroke={shape.color} strokeWidth={shape.width} strokeLinecap="round" opacity={shape.opacity} />
          : <text key={i} x={shape.x} y={shape.y} fontSize={shape.size} fontWeight={shape.weight} fill={shape.color} textAnchor={shape.anchor || 'middle'} opacity={shape.opacity}>{shape.text}</text>)}
    </svg>
    <strong aria-live="polite">{view.caption}…</strong>
    {message && <p>{message}</p>}
  </div>;
}
