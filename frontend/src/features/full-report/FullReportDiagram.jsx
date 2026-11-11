import React, { useMemo, useState } from 'react';
import { sectionDiagram, diagramSvg } from '../../../../packages/full-report/schematics';
import FullReportCharts from './FullReportCharts';

export default function FullReportDiagram({ report, section }) {
  const [activeIndex, setActiveIndex] = useState(undefined);
  const diagram = useMemo(() => sectionDiagram(report, section), [report, section]);
  // Only the application's escaped renderer produces this SVG; API HTML is never inserted.
  const svg = useMemo(() => diagram ? diagramSvg(diagram, { activeIndex }) : '', [diagram, activeIndex]);
  if (!diagram) return <FullReportCharts chart={section.chart} title={`Схема: ${section.title}`} />;
  return <figure className="fr-chart fr-canonical-diagram"><figcaption>{diagram.title}</figcaption><div className="fr-diagram-svg" dangerouslySetInnerHTML={{ __html: svg }} />
    {diagram.kind === 'lines' && diagram.directions?.length > 0 && <div className="fr-directions" aria-label="Линии квадрата"><button type="button" aria-pressed={activeIndex === undefined} onClick={() => setActiveIndex(undefined)}>Все восемь линий</button>{diagram.directions.map((line, index) => <button key={line.id} type="button" aria-pressed={activeIndex === index} onClick={() => setActiveIndex(index)}>{line.label} · {line.value}</button>)}</div>}
  </figure>;
}
