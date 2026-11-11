import React from 'react';
import { chartValues } from '@numerom/full-report';

export default function FullReportCharts({ chart, title }) {
  const items = chartValues(chart);
  if (!items.length) return null;
  const maximum = Math.max(1, ...items.map(item => Math.abs(Number(item.value))));
  if (chart.type === 'matrix') return <figure className="fr-chart"><figcaption>{title}</figcaption><div className="fr-matrix">{items.map((item, index) => <div key={index}><span>{item.label}</span><strong>{item.value}</strong></div>)}</div></figure>;
  if (chart.type === 'series') {
    const x = index => 24 + index * 612 / Math.max(1, items.length - 1), y = value => 166 - value / maximum * 140;
    return <figure className="fr-chart"><figcaption>{title}</figcaption><svg className="fr-series" viewBox="0 0 660 205" role="img" aria-label={title}><path d="M24 20V166H636" fill="none" stroke="#c7dfe1" /><polyline points={items.map((item, index) => `${x(index)},${y(item.value)}`).join(' ')} fill="none" stroke="#3a8b83" strokeWidth="2.5" />{items.map((item, index) => (index === 0 || index === items.length - 1 || index % 10 === 0) && <text key={index} x={x(index)} y="192" textAnchor="middle" fontSize="9" fill="#5b707a">{item.label}</text>)}</svg><details><summary>Все значения графика</summary><dl className="fr-series-values">{items.map((item, index) => <div key={index}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}</dl></details></figure>;
  }
  return <figure className="fr-chart"><figcaption>{title}</figcaption><div className="fr-bars">{items.map((item, index) => <div className="fr-bar" key={index}><span>{item.label}</span><div><i style={{ width: `${Math.max(0, Math.abs(Number(item.value)) / maximum * 100)}%` }} /></div><strong>{item.value}</strong></div>)}</div></figure>;
}
