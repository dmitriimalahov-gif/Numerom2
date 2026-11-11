/** Deterministic, frame-based direction. Saved numbers never tween or shuffle. */
import schematics from '../../packages/full-report/schematics.js';
import {overviewBounds, svgViewport} from './layout.mjs';

export const clamp = (value) => Math.max(0, Math.min(1, value));
export const ease = (value) => {const t = clamp(value); return t * t * (3 - 2 * t);};
const mix = (a, b, t) => a + (b - a) * t;
const fixed = (value) => Number(value.toFixed(4));
const same = (a, b) => ['x', 'y', 'width', 'height'].every((k) => Math.abs(a[k] - b[k]) < .001);

export function entrance(frame, delay = 0, duration = 18, reduced = false) {
  const amount = reduced ? 1 : ease((frame - delay) / duration);
  return {opacity: amount, y: 18 * (amount - 1), scale: .96 + .04 * amount};
}

function targetBounds(diagram, index) {
  const base = overviewBounds(diagram) ?? {x: 0, y: 0, width: diagram.width, height: diagram.height};
  if (index === null) return base;
  const known = schematics.diagramFocusBounds(diagram, index);
  if (known) return known;
  const svg = schematics.diagramSvg(diagram, {activeIndex: index});
  // Read the canonical geometry; no second layout/formula implementation.
  let point, width, height;
  if (diagram.kind === 'series') {
    const circle = svg.match(/<circle data-active-year="[^"]*" cx="([\d.]+)" cy="([\d.]+)"/);
    if (circle) {point = [+circle[1], +circle[2]]; width = 320; height = 300;}
  } else if (['sequence', 'individual', 'period'].includes(diagram.kind)) {
    const nodes = [...svg.matchAll(/<g data-node="[^"]*"><rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"/g)];
    const node = nodes[index];
    if (node) {width = Math.min(diagram.width, +node[3] + 100); height = Math.min(diagram.height, +node[4] + 100); point = [+node[1] + +node[3] / 2, +node[2] + +node[4] / 2];}
  }
  return point ? {x: Math.max(0, Math.min(diagram.width - width, point[0] - width / 2)),
    y: Math.max(0, Math.min(diagram.height - height, point[1] - height / 2)), width, height} : base;
}

/** Reconstruct interrupted camera moves too, so fast cue changes cannot jump. */
export function cameraAt(diagram, events, frame, reduced = false) {
  const targets = new Map();
  const bounds = (index) => {if (!targets.has(index)) targets.set(index, targetBounds(diagram, index)); return targets.get(index);};
  let from = bounds(null), target = from, since = 0;
  const interpolate = (at) => Object.fromEntries(['x', 'y', 'width', 'height'].map((key) =>
    [key, fixed(mix(from[key], target[key], reduced ? 1 : ease((at - since) / 18)))]));
  for (const [index, event] of events.entries()) {
    if (event.fromFrame > frame) break;
    // A rapid enumeration stays on the overview; the correct field still lights
    // up. Reserve camera travel for explanations long enough to read the inset.
    const brief = events[index + 1] && events[index + 1].fromFrame - event.fromFrame < 24;
    from = interpolate(event.fromFrame); target = bounds(brief ? null : event.focusIndex); since = event.fromFrame;
  }
  return interpolate(frame);
}

export function animateCanonicalSvg(svg, diagram, model, frame, reduced = false) {
  if (reduced) return svg;
  let order = 0;
  let result = svg.replace(/<g ([^>]*data-(cell|node|direction|legend)="([^"]+)"[^>]*)>([\s\S]*?)<\/g>/g,
    (_, attrs, kind, id, body) => {
      const index = kind === 'cell' ? diagram.cells?.findIndex((c) => String(c.digit) === id)
        : ['direction', 'legend'].includes(kind) ? diagram.directions?.findIndex((d) => d.id === id)
        : diagram.entries.findIndex((entry) => entry.id === id);
      const active = model.focusIndex !== null && (kind !== 'cell' || diagram.kind === 'square') && index === model.focusIndex;
      const entering = entrance(frame, active ? 0 : Math.min(12, order++) * 2, 16);
      const revealFrames = Math.min(14, Math.max(4, (model.focusDuration ?? 50) * .3));
      const reveal = active ? entrance(model.focusAge, 0, revealFrames) : {opacity: 1, y: 0};
      const pulse = active ? Math.sin(Math.PI * clamp(model.focusAge / 24)) : 0;
      const numeric = body.replace(/<text\b([^>]*font-size="(\d+(?:\.\d+)?)"[^>]*)>([^<]*)<\/text>/g,
        (original, properties, size, text) => +size >= 28
          ? `<text ${properties} opacity="${fixed(reveal.opacity)}" transform="translate(0 ${fixed(reveal.y)})">${text}</text>` : original);
      let content = numeric;
      if (kind === 'direction' && active) content = content.replace('<line ', `<line pathLength="1" stroke-dasharray="1" stroke-dashoffset="${fixed(1 - ease(model.focusAge / 20))}" `);
      return `<g ${attrs} opacity="${fixed(entering.opacity)}" transform="translate(0 ${fixed(entering.y)})" style="filter:drop-shadow(0 0 ${fixed(pulse * 5)}px rgba(53,111,165,${fixed(pulse * .22)}))">${content}</g>`;
    });
  result = result.replace('<polyline data-series=', `<polyline pathLength="1" stroke-dasharray="1" stroke-dashoffset="${fixed(1 - ease(frame / 36))}" data-series=`);
  result = result.replace(/<line ([^>]*data-link-target="[^"]*" data-active="true"[^>]*)\/>/g,
    (_, attributes) => `<line ${attributes} pathLength="1" stroke-dasharray="1" stroke-dashoffset="${fixed(1 - ease(model.focusAge / 16))}"/>`);
  return result;
}

export function directedViews(diagram, model, frame, reduced = false) {
  const original = schematics.diagramSvg(diagram, {activeIndex: model.focusIndex ?? undefined});
  const bounds = cameraAt(diagram, model.focusEvents, frame, reduced);
  const complete = {x: 0, y: 0, width: diagram.width, height: diagram.height};
  const inset = !same(bounds, complete) || overviewBounds(diagram) !== null;
  const animated = animateCanonicalSvg(original, diagram, model, frame, reduced);
  const full = inset ? original.replace('</svg>', `<rect x="${bounds.x}" y="${bounds.y}" width="${bounds.width}" height="${bounds.height}" rx="8" fill="none" stroke="#356FA5" stroke-width="2" opacity="0.7"/></svg>`) : original;
  return {full, focus: svgViewport(animated, bounds), animated, bounds};
}
