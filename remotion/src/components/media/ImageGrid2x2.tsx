import React from "react";
import {
  AbsoluteFill, Img, staticFile,
  useCurrentFrame, useVideoConfig,
  spring, interpolate,
} from "remotion";

const DEFAULT_STAGGER = [0, 5, 10, 15];
const DEFAULT_SPRING  = { mass: 1, damping: 12, stiffness: 80 };
const DISSOLVE_FRAMES = 8;

export const ImageGrid2x2: React.FC<{
  images: Array<{ src: string }>;
  durationInFrames: number;
  staggerDelays?: number[];
  springConfig?: { mass: number; damping: number; stiffness: number };
  dissolveFromPrevious?: boolean;
  bookSpreadIndex?: number;
}> = ({
  images,
  durationInFrames,
  staggerDelays = DEFAULT_STAGGER,
  springConfig  = DEFAULT_SPRING,
  dissolveFromPrevious = false,
  bookSpreadIndex = -1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Grid cross-dissolve: entire grid fades in over DISSOLVE_FRAMES if dissolveFromPrevious
  const gridOpacity = dissolveFromPrevious
    ? interpolate(frame, [0, DISSOLVE_FRAMES], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  const cells = images.slice(0, 4);

  return (
    <AbsoluteFill style={{ background: "#000000" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gridTemplateRows: "1fr 1fr",
          gap: 2,
          opacity: gridOpacity,
        }}
      >
        {cells.map((img, idx) => {
          const delay = staggerDelays[idx] ?? idx * 5;
          const localFrame = Math.max(0, frame - delay);

          const progress = spring({
            frame: localFrame,
            fps,
            config: springConfig,
          });

          const cellScale = interpolate(progress, [0, 1], [0.72, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const cellOpacity = interpolate(progress, [0, 0.25, 1], [0, 1, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          // Book-spread pan: linear objectPosition 0%→100% (left→right) for the named cell
          const panPct = bookSpreadIndex === idx
            ? interpolate(frame, [0, durationInFrames], [0, 100], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            : 50;

          return (
            <div
              key={idx}
              style={{
                overflow: "hidden",
                transform: `scale(${cellScale})`,
                opacity: cellOpacity,
              }}
            >
              <Img
                src={staticFile(img.src)}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                  objectPosition: `${panPct}% 50%`,
                  display: "block",
                }}
              />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
