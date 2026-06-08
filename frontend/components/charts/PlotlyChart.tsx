"use client";

import dynamic from "next/dynamic";
import type { PlotlyFigure } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface PlotlyChartProps {
  figure: string; // JSON-encoded Plotly figure from the API
  className?: string;
  onBarClick?: (xValue: number) => void;
}

export function PlotlyChart({ figure, className, onBarClick }: PlotlyChartProps) {
  const parsed: PlotlyFigure = JSON.parse(figure);

  return (
    <div className={className}>
      <Plot
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data={parsed.data as any[]}
        layout={{
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ...(parsed.layout as any),
          autosize: true,
          margin: { l: 60, r: 30, t: 50, b: 60 },
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
