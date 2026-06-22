"use client";

import { useEffect, useState } from "react";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";
import { gaugeColorForScore } from "@/lib/severity";

export function RiskGauge({
  score,
  size = 200,
}: {
  score: number;
  size?: number;
}) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const color = gaugeColorForScore(score);

  useEffect(() => {
    const duration = 1200;
    const start = performance.now();
    let frame: number;

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * score));
      if (progress < 1) frame = requestAnimationFrame(tick);
    }
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const data = [{ value: score, fill: color }];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <RadialBarChart
        width={size}
        height={size}
        cx="50%"
        cy="50%"
        innerRadius="78%"
        outerRadius="100%"
        barSize={size * 0.09}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar
          background={{ fill: "#E2E8F0" }}
          dataKey="value"
          cornerRadius={999}
          isAnimationActive={false}
        />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-display text-3xl font-bold tabular-nums"
          style={{ color }}
        >
          {animatedScore}
        </span>
        <span className="text-xs text-text-muted">out of 100</span>
      </div>
    </div>
  );
}
