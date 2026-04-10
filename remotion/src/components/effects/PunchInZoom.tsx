import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import type { ZoomMoment } from "../../types";

/**
 * PunchInZoom — wraps content and zooms into a specific point at specified moments.
 * Used on demo clips and screenshots to highlight button clicks, outputs, or key UI.
 *
 * How it works:
 * - At `moment.at` seconds, springs in to `moment.scale` centered on (x%, y%)
 * - After `holdFor` seconds, springs back out to 1.0
 * - Only the LATEST triggered moment is ever active — earlier moments hold at peak
 *   zoom rather than zooming out, so there is no double-zoom when moments are
 *   close together or overlapping
 * - Uses CSS transform-origin to zoom toward the correct spot — no layout shift
 * - GPU-only (transform only, zero filters)
 */
export const PunchInZoom: React.FC<{
  children: React.ReactNode;
  moments: ZoomMoment[];
  clipStartSec?: number; // offset if this clip doesn't start at t=0
}> = ({ children, moments, clipStartSec = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let scale = 1;
  let originX = 50;
  let originY = 50;

  // Find the latest moment that has been triggered (iterate all, keep last match).
  // This ensures only one zoom sequence is ever active at a time — earlier moments
  // hold at their peak until the next moment takes over, with no zoom-out between them.
  let activeMoment: ZoomMoment | null = null;
  for (const moment of moments) {
    const zoomInFrame = Math.round((moment.at - clipStartSec) * fps);
    if (frame >= zoomInFrame) {
      activeMoment = moment;
    }
  }

  if (activeMoment) {
    const zoomInFrame = Math.round((activeMoment.at - clipStartSec) * fps);
    const holdFrames =
      activeMoment.holdFor != null
        ? Math.round(activeMoment.holdFor * fps)
        : Infinity;
    const localZoomFrame = frame - zoomInFrame;

    if (localZoomFrame <= holdFrames) {
      // Zooming in or holding
      const zoomSpring = spring({
        frame: localZoomFrame,
        fps,
        config: { damping: 20, stiffness: 120, mass: 0.8 },
      });
      scale = interpolate(zoomSpring, [0, 1], [1, activeMoment.scale]);
      originX = activeMoment.x;
      originY = activeMoment.y;
    } else {
      // Zooming back out — only happens after the LAST moment's holdFor expires
      const outFrame = localZoomFrame - holdFrames;
      const outSpring = spring({
        frame: outFrame,
        fps,
        config: { damping: 18, stiffness: 100, mass: 0.9 },
      });
      scale = interpolate(outSpring, [0, 1], [activeMoment.scale, 1]);
      originX = activeMoment.x;
      originY = activeMoment.y;
    }
  }

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale})`,
          transformOrigin: `${originX}% ${originY}%`,
        }}
      >
        {children}
      </div>
    </div>
  );
};
