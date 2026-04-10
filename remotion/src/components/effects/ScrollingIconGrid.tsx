import React from "react";
import { AbsoluteFill, useCurrentFrame, Img, staticFile, interpolate } from "remotion";

/**
 * ScrollingIconGrid — Rotated multi-row grid of app logo cards that scrolls
 * diagonally, creating the animated "AI tools" background seen in editorial
 * authority reels (Lindsay.ai reference).
 *
 * The grid is rotated ~15-20 degrees and translates upward continuously.
 * Each cell is a dark rounded rectangle with a logo centered inside.
 * A colored gradient overlay sits on top for atmosphere.
 *
 * Frame-driven animation — no CSS keyframes, no framer-motion.
 */
export const ScrollingIconGrid: React.FC<{
  /** Array of image filenames in remotion/public/ for the logo icons */
  icons: string[];
  /** Scroll speed in pixels per frame (default 1.5) */
  speed?: number;
  /** Grid cell size in px (default 160) */
  cellSize?: number;
  /** Gap between cells in px (default 16) */
  gap?: number;
  /** Grid rotation in degrees (default -18) */
  rotation?: number;
  /** Number of columns (default 4) */
  columns?: number;
  /** Number of rows to render — should exceed screen height after rotation (default 14) */
  rows?: number;
  /** Cell background color (default "rgba(30,30,40,0.85)") */
  cellBg?: string;
  /** Cell border radius (default 24) */
  cellRadius?: number;
  /** Icon size as fraction of cell (default 0.5) */
  iconScale?: number;
  /** Overlay gradient — array of CSS color stops (default purple gradient) */
  overlayGradient?: string;
  /** Overall opacity (default 1) */
  opacity?: number;
  durationInFrames?: number;
}> = ({
  icons,
  speed = 1.5,
  cellSize = 160,
  gap = 16,
  rotation = -18,
  columns = 4,
  rows = 14,
  cellBg = "rgba(30, 30, 40, 0.85)",
  cellRadius = 24,
  iconScale = 0.5,
  overlayGradient,
  opacity = 1,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  if (!icons.length) return null;

  const rowHeight = cellSize + gap;
  const totalGridHeight = rows * rowHeight;

  // Scroll offset — loops seamlessly
  const scrollOffset = (frame * speed) % rowHeight;

  // Fade in/out
  const fadeIn = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = durationInFrames
    ? interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;

  // Generate grid cells
  const cells: React.ReactNode[] = [];
  for (let row = -2; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const iconIndex = ((row + 2) * columns + col) % icons.length;
      const x = col * (cellSize + gap);
      const y = row * rowHeight - scrollOffset;

      // Alternate row offset for brick pattern
      const rowOffset = row % 2 === 0 ? 0 : (cellSize + gap) * 0.5;

      cells.push(
        <div
          key={`${row}-${col}`}
          style={{
            position: "absolute",
            left: x + rowOffset,
            top: y,
            width: cellSize,
            height: cellSize,
            borderRadius: cellRadius,
            backgroundColor: cellBg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 16px rgba(0,0,0,0.3)",
          }}
        >
          <Img
            src={staticFile(icons[iconIndex])}
            style={{
              width: cellSize * iconScale,
              height: cellSize * iconScale,
              objectFit: "contain",
              opacity: 0.7,
            }}
          />
        </div>,
      );
    }
  }

  const gridWidth = columns * (cellSize + gap) + (cellSize + gap) * 0.5;
  const gridHeight = totalGridHeight + rowHeight * 2;

  const defaultGradient =
    "linear-gradient(180deg, rgba(45, 27, 105, 0.6) 0%, rgba(45, 27, 105, 0.3) 40%, rgba(45, 27, 105, 0.7) 100%)";

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        opacity: opacity * fadeIn * fadeOut,
      }}
    >
      {/* Rotated scrolling grid */}
      <div
        style={{
          position: "absolute",
          // Center the grid and offset so rotation doesn't leave gaps
          left: "50%",
          top: "50%",
          width: gridWidth,
          height: gridHeight,
          transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
          // Scale up to cover corners after rotation
          scale: "1.6",
        }}
      >
        {cells}
      </div>

      {/* Color overlay gradient */}
      <AbsoluteFill
        style={{
          background: overlayGradient ?? defaultGradient,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
