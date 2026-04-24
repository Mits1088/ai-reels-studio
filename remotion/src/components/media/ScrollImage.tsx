import React from "react";
import {
  AbsoluteFill, Img, staticFile,
  useCurrentFrame, interpolate,
} from "remotion";

/**
 * ScrollImage — renders a tall portrait image and scrolls it vertically over the beat duration.
 *
 * Natural height at 1080px wide = 1080 / imageAspectRatio.
 * If naturalH > 1920 (frame height), the image scrolls from top to bottom.
 * If naturalH ≤ 1920, no scroll (image fully visible — renders as objectFit:cover).
 */
export const ScrollImage: React.FC<{
  src: string;
  durationInFrames: number;
  imageAspectRatio: number;
}> = ({ src, durationInFrames, imageAspectRatio }) => {
  const frame = useCurrentFrame();

  const naturalH = Math.round(1080 / imageAspectRatio);
  const maxScroll = Math.max(0, naturalH - 1920);

  const translateY = maxScroll > 0
    ? interpolate(frame, [0, Math.max(1, durationInFrames)], [0, -maxScroll], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 0;

  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#F8F8F8" }}>
      {maxScroll > 0 ? (
        <Img
          src={staticFile(src)}
          style={{
            width: "100%",
            height: "auto",
            display: "block",
            transform: `translateY(${translateY}px)`,
          }}
        />
      ) : (
        <Img
          src={staticFile(src)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center",
            display: "block",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
