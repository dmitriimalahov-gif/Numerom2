export interface PlanetChartItem {
  name: string; value: number; meaning: string; weekday: string; weekdayShort: string; color: string; border: string;
}
export interface PlanetChartGeometry {
  width: number; height: number; left: number; right: number; top: number; bottom: number; step: number;
  ticks: {value: number; y: number}[];
  points: (PlanetChartItem & {x: number; y: number; barHeight: number})[];
}
export function orderedPlanetItems(items: unknown): PlanetChartItem[] | null;
export function planetChartGeometry(items: unknown, width: number, height?: number): PlanetChartGeometry | null;
