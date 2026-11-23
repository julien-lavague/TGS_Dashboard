"use client";

import dynamic from "next/dynamic";
import { useIsMobile } from "@/hooks/useIsMobile";
import type { PlotlyFigure } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  figure: string; // JSON-encoded Plotly figure from the API
  className?: string;
  onBarClick?: (xValue: number) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Layout = Record<string, any>;

/** Phone overrides on top of the backend layout: the figures are sized for a
 *  desktop card, so trim side margins, move the legend under the plot and let
 *  axes grow their own margins instead of clipping tick labels. */
function mobileLayout(layout: Layout): Layout {
  const margin = layout.margin ?? {};
  const axes: Layout = {};
  for (const key of Object.keys(layout)) {
    if (/^[xy]axis\d*$/.test(key)) axes[key] = { ...layout[key], automargin: true };
  }
  return {
    ...layout,
    ...axes,
    margin: {
      ...margin,
      l: Math.min(margin.l ?? 40, 40),
      r: Math.min(margin.r ?? 16, 16),
      t: Math.min(margin.t ?? 50, 50),
    },
    legend: {
      ...layout.legend,
      orientation: "h",
      x: 0,
      xanchor: "left",
      y: -0.2,
      yanchor: "top",
      font: { size: 10 },
    },
    title: layout.title
      ? { ...layout.title, font: { ...layout.title?.font, size: 13 } }
      : layout.title,
    // Dragging must scroll the page on touch screens, not zoom the chart — except
    // on maps, where dragging is the only way to pan.
    dragmode: layout.map || layout.mapbox || layout.geo ? layout.dragmode : false,
  };
}

export function PlotlyChart({ figure, className, onBarClick }: PlotlyChartProps) {
  const isMobile = useIsMobile();
  const parsed: PlotlyFigure = JSON.parse(figure);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const layout = parsed.layout as any;

  return (
    <div className={className}>
      <Plot
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data={parsed.data as any[]}
        layout={{
          autosize: true,
          ...(isMobile ? mobileLayout(layout) : layout),
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          font: { family: "inherit" },
        }}
        config={{ responsive: true, displayModeBar: false }}
        useResizeHandler
        style={{ width: "100%", height: "100%", cursor: onBarClick ? "pointer" : "default" }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onClick={onBarClick ? (event: any) => {
          const x = event?.points?.[0]?.x;
          if (typeof x === "number") onBarClick(x);
        } : undefined}
      />
    </div>
  );
}
