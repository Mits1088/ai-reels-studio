import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

/**
 * CircuitTrace — Animated circuit board lines with traveling light pulses.
 * Tech-feel background pattern. Lines glow as energy pulses travel through.
 */
export const CircuitTrace: React.FC<{
  color?: string;
  lineCount?: number;
  speed?: number;
}> = ({
  color = "rgba(0, 229, 255, 0.2)",
  lineCount = 8,
  speed = 1,
}) => {
  const frame = useCurrentFrame();

  const lines = React.useMemo(() => {
    return Array.from({ length: lineCount }, (_, i) => {
      const isHorizontal = random(`cd-${i}`) > 0.5;
      const pos = 5 + random(`cp-${i}`) * 90; // percent
      const length = 20 + random(`cl-${i}`) * 40; // percent
      const start = random(`cs-${i}`) * (100 - length);
      const pulseDelay = random(`cpd-${i}`) * 60;

      return { isHorizontal, pos, length, start, pulseDelay };
    });
  }, [lineCount]);

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none", opacity: 0.6 }}>
      {lines.map((line, i) => {
        // Pulse position travels along the line
        const pulseFrame = (frame + line.pulseDelay) * speed;
        const pulsePos = (pulseFrame * 1.5) % (line.length + 20) - 10;

        const style: React.CSSProperties = line.isHorizontal
          ? {
              position: "absolute",
              top: `${line.pos}%`,
              left: `${line.start}%`,
              width: `${line.length}%`,
              height: 1,
            }
          : {
              position: "absolute",
              left: `${line.pos}%`,
              top: `${line.start}%`,
              height: `${line.length}%`,
              width: 1,
            };

        const pulseStyle: React.CSSProperties = line.isHorizontal
          ? {
              position: "absolute",
              top: -2,
              left: `${(pulsePos / line.length) * 100}%`,
              width: 20,
              height: 5,
              borderRadius: 3,
            }
          : {
              position: "absolute",
              left: -2,
              top: `${(pulsePos / line.length) * 100}%`,
              height: 20,
              width: 5,
              borderRadius: 3,
            };

        // Node dots at endpoints
        const nodeSize = 4;

        return (
          <React.Fragment key={i}>
            {/* Line */}
            <div style={{ ...style, background: color, overflow: "visible" }}>
              {/* Traveling pulse */}
              <div style={{
                ...pulseStyle,
                background: color.replace(/[\d.]+\)$/, "0.8)"),
                boxShadow: `0 0 8px ${color.replace(/[\d.]+\)$/, "0.4)")}`,
              }} />
            </div>
            {/* Start node */}
            <div style={{
              position: "absolute",
              ...(line.isHorizontal
                ? { top: `${line.pos}%`, left: `${line.start}%`, marginTop: -nodeSize / 2, marginLeft: -nodeSize / 2 }
                : { left: `${line.pos}%`, top: `${line.start}%`, marginLeft: -nodeSize / 2, marginTop: -nodeSize / 2 }),
              width: nodeSize,
              height: nodeSize,
              borderRadius: "50%",
              background: color,
            }} />
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
