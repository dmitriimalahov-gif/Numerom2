import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import Diagram from '../FullReportDiagram';
const report = require('../../../../../docs/artifacts/full-report-fixture.json').report;
const { sectionDiagram, diagramSvg } = require('../../../../../packages/full-report/schematics');
let host, root;
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
test('eight lines render the canonical grid and allow selecting a direction', async () => {
  const section = report.sections.find(item => sectionDiagram(report, item)?.kind === 'lines');
  await act(async () => root.render(<Diagram report={report} section={section} />));
  const canonical = document.createElement('div'); canonical.innerHTML = diagramSvg(sectionDiagram(report, section));
  expect(host.querySelector('.fr-diagram-svg').innerHTML).toBe(canonical.innerHTML);
  expect(host.querySelectorAll('.fr-directions button')).toHaveLength(9);
  await act(async () => host.querySelectorAll('.fr-directions button')[1].click());
  expect(host.querySelectorAll('.fr-directions button')[1].getAttribute('aria-pressed')).toBe('true'); expect(host.querySelector('.fr-bars')).toBeNull();
});
test('legacy unknown sections keep their stored chart', async () => {
  const section = { id: 'legacy-unknown', title: 'Старый раздел', chart: { type: 'matrix', items: [{ label: 'Ячейка', value: 2 }] } };
  await act(async () => root.render(<Diagram report={{}} section={section} />)); expect(host.querySelector('.fr-matrix')).not.toBeNull();
});
