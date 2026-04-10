import React from "react";
import { AbsoluteFill, useCurrentFrame, random } from "remotion";

/**
 * SmokeWisp — Subtle animated smoke/mist wisps.
 * Ethereal premium feel. Semi-transparent blobs that drift slowly.
 * Very subtle — adds atmosphere without distraction.
 */
export const SmokeWisp: React.FC<{
  count?: number;
  color?: string;
  speed?: number;
}> = ({
  count = 5,
  color = "rgba(255, 255, 255, 0.02)",
  speed = 1,
}) => {
  const frame = useCurrentFrame();

  const wisps = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      baseX: random(`sx-${i}`) * 100,
      baseY: 50 + random(`sy-${i}`) * 50,
      width: 200 + random(`sw-${i}`) * 400,
      height: 100 + random(`sh-${i}`) * 200,
      speedX: (random(`svx-${i}`) - 0.5) * 0.3 * speed,
      speedY: (random(`svy-${i}`) - 0.5) * 0.1 * speed,
      phase: random(`sp-${i}`) * Math.PI * 2,
      opacity: 0.3 + random(`so-${i}`) * 0.5,
    }));
  }, [count, speed]);

  return (
    <AbsoluteFill style={{ zIndex: 1, pointerEvents: "none", overflow: "hidden" }}>
      {wisps.map((w, i) => {
        const t = frame * 0.01;
        const x = w.baseX + Math.sin(t * (0.5 + i * 0.1) + w.phase) * 15 + t * w.speedX * 50;
        const y = w.baseY + Math.cos(t * (0.3 + i * 0.1) + w.phase) * 8;
        const scaleBreath = 1 + Math.sin(t * 0.4 + i) * 0.1;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${x}%`,
              top: `${y}%`,
              width: w.width,
              height: w.height,
              borderRadius: "50%",
              background: `radial-gradient(ellipse, ${color}, transparent 70%)`,
              opacity: w.opacity,
              transform: `translate(-50%, -50%) scale(${scaleBreath})`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
