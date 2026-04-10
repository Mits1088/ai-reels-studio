import React from "react";
import { AbsoluteFill, useCurrentFrame, random } from "remotion";
import { hardOpacity } from "../../utils";

const techIcons = ["⚡", "🤖", "🧠", "💡", "🔮", "✨", "🎯", "🔥"];

export const FloatingIcons: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const opacity = hardOpacity(frame, durationInFrames, 8, 8);

  const icons = React.useMemo(() => {
    return Array.from({ length: 6 }, (_, i) => ({
      icon: techIcons[Math.floor(random(`icon-${i}`) * techIcons.length)],
      x: 80 + random(`ix-${i}`) * 920,
      startY: 1920 + random(`iy-${i}`) * 200,
      speed: 1.5 + random(`is-${i}`) * 2,
      size: 28 + random(`isz-${i}`) * 20,
      wobble: (random(`iw-${i}`) - 0.5) * 40,
      rotation: random(`ir-${i}`) * 360,
    }));
  }, []);

  return (
    <AbsoluteFill style={{ zIndex: 45, opacity, pointerEvents: "none" }}>
      {icons.map((ic, i) => {
        const y = ic.startY - frame * ic.speed;
        if (y < -60 || y > 2000) return null;
        const x = ic.x + Math.sin(frame * 0.03 + i) * ic.wobble;
        const rot = ic.rotation + frame * 0.5;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x, top: y,
              fontSize: ic.size,
              transform: `rotate(${rot}deg)`,
              opacity: 0.3 + Math.sin(frame * 0.06 + i) * 0.2,
            }}
          >
            {ic.icon}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
