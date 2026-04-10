import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate, random } from "remotion";

/**
 * EmojiReactions — Floating emoji burst like IG Live reactions.
 * Emojis rise from the bottom with varying speeds and paths.
 * Great for engagement moments, proof scenes, celebration.
 */
export const EmojiReactions: React.FC<{
  emojis?: string[];
  count?: number;
  durationInFrames: number;
  originX?: number;
}> = ({
  emojis = ["🔥", "😮", "💯", "🙌", "❤️", "👏", "⚡", "🤯"],
  count = 12,
  durationInFrames,
  originX = 85,
}) => {
  const frame = useCurrentFrame();

  const reactions = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      emoji: emojis[Math.floor(random(`re-${i}`) * emojis.length)],
      x: originX + (random(`rx-${i}`) - 0.5) * 20,
      speed: 2 + random(`rs-${i}`) * 3,
      wobble: (random(`rw-${i}`) - 0.5) * 50,
      delay: Math.floor(random(`rd-${i}`) * durationInFrames * 0.6),
      size: 24 + random(`rsz-${i}`) * 16,
      startY: 100,
    }));
  }, [count, emojis, originX, durationInFrames]);

  return (
    <AbsoluteFill style={{ zIndex: 46, pointerEvents: "none", overflow: "hidden" }}>
      {reactions.map((r, i) => {
        const localFrame = frame - r.delay;
        if (localFrame < 0) return null;

        const yPercent = r.startY - localFrame * r.speed * 0.5;
        if (yPercent < -5) return null;

        const xWobble = r.x + Math.sin(localFrame * 0.08) * r.wobble * 0.3;
        const opacity = interpolate(yPercent, [r.startY, r.startY - 10, 20, -5], [0, 1, 0.8, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        const scale = interpolate(localFrame, [0, 4], [0.3, 1], { extrapolateRight: "clamp" });

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${xWobble}%`,
              top: `${yPercent}%`,
              fontSize: r.size,
              opacity,
              transform: `scale(${scale})`,
            }}
          >
            {r.emoji}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
