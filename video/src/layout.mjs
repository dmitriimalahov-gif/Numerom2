import schematics from '../../packages/full-report/schematics.js';

/** Crop only the SVG viewport; all canonical paths, numbers and lines survive. */
export function svgViewport(svg, bounds) {
  if (!bounds || !['x', 'y', 'width', 'height'].every((key) => Number.isFinite(bounds[key]))
    || bounds.width <= 0 || bounds.height <= 0) throw new Error('Invalid diagram viewport');
  return svg.replace(/viewBox="[^"]*"/, `viewBox="${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}"`);
}

export function canonicalViews(diagram, focusIndex) {
  const svg = schematics.diagramSvg(diagram, {activeIndex: focusIndex ?? undefined});
  const focused = schematics.diagramFocusBounds(diagram, focusIndex);
  // A personal plate is tall even before narration reaches its first number.
  // Show the full upper calculation plate in that introduction, retaining the
  // complete scheme in the thumbnail. No geometry is redrawn here.
  const initial = overviewBounds(diagram);
  const bounds = focused ?? initial;
  return {full: svg, focus: bounds ? svgViewport(svg, bounds) : null, bounds};
}

export function overviewBounds(diagram) {
  return diagram.kind === 'personal' ? {x: 0, y: 86, width: 640, height: 425}
    : ['lines', 'square'].includes(diagram.kind) ? {x: 0, y: 86, width: 640, height: 484} : null;
}

export const svgSource = (svg) => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
