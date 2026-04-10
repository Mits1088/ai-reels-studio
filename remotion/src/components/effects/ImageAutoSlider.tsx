import React from "react";
import { AbsoluteFill, useCurrentFrame, Img, interpolate } from "remotion";

/**
 * ImageAutoSlider — Infinite horizontal scroll of images.
 * Remotion-compatible: driven by useCurrentFrame(), no CSS keyframes.
 *
 * Props:
 * - images: array of image URLs or staticFile paths
 * - speed: pixels per frame to scroll (default 2)
 * - imageSize: width/height of each image card in px (default 280)
 * - gap: gap between images in px (default 24)
 * - borderRadius: corner radius of image cards (default 16)
 * - direction: "left" | "right" (default "left")
 * - fadeEdges: apply edge fade mask (default true)
 * - backgroundColor: background color (default "transparent")
 * - verticalAlign: position in frame — "center" | "top" | "bottom" (default "center")
 */
export const ImageAutoSlider: React.FC<{
  images: string[];
  speed?: number;
  imageSize?: number;
  gap?: number;
  borderRadius?: number;
  direction?: "left" | "right";
  fadeEdges?: boolean;
  backgroundColor?: string;
  verticalAlign?: "center" | "top" | "bottom";
  durationInFrames?: number;
}> = ({
  images,
  speed = 2,
  imageSize = 280,
  gap = 24,
  borderRadius = 16,
  direction = "left",
  fadeEdges = true,
  backgroundColor = "transparent",
  verticalAlign = "center",
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  if (!images.length) return null;

  // Total width of one full set of images
  const setWidth = images.length * (imageSize + gap);

  // Scroll offset — loops seamlessly by wrapping with modulo
  const rawOffset = frame * speed;
  const offset = rawOffset % setWidth;
  const translateX = direction === "left" ? -offset : offset - setWidth;

  // Fade in
  const fadeIn = interpolate(frame, [0, 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade out (if durationInFrames provided)
  const fadeOut = durationInFrames
    ? interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  // Duplicate images 3x to ensure seamless wrap at any speed
  const tripled = [...images, ...images, ...images];

  const alignItems =
    verticalAlign === "top"
      ? "flex-start"
      : verticalAlign === "bottom"
        ? "flex-end"
        : "center";

  return (
    <AbsoluteFill
      style={{
        backgroundColor,
        display: "flex",
        alignItems,
        justifyContent: "center",
        overflow: "hidden",
        opacity: fadeIn * fadeOut,
      }}
    >
      {/* Edge fade mask */}
      <div
        style={{
          width: "100%",
          overflow: "hidden",
          ...(fadeEdges
            ? {
                maskImage:
                  "linear-gradient(90deg, transparent 0%, black 10%, black 90%, transparent 100%)",
                WebkitMaskImage:
                  "linear-gradient(90deg, transparent 0%, black 10%, black 90%, transparent 100%)",
              }
            : {}),
        }}
      >
        {/* Scrolling track */}
        <div
          style={{
            display: "flex",
            gap,
            transform: `translateX(${translateX}px)`,
            width: "max-content",
          }}
        >
          {tripled.map((src, i) => (
            <div
              key={i}
              style={{
                flexShrink: 0,
                width: imageSize,
                height: imageSize,
                borderRadius,
                overflow: "hidden",
                boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
              }}
            >
              <Img
                src={src}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};
