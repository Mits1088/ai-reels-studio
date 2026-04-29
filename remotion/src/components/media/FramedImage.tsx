import React from "react";
import { Img, staticFile, useCurrentFrame } from "remotion";
import type { ZoomMoment } from "../../types";
import { PunchInZoom } from "../effects/PunchInZoom";

/**
 * FramedImage — static screenshot or image in a rounded card with shadow.
 *
 * splitScreen:  renders in top 40% split zone (padding: 32px 24px)
 * center-full:  renders without split padding (padding: 20px 16px)
 * motionMode:
 *   "still"            — no hold motion (default)
 *   "perspective-tilt" — subtle 3D oscillation on X/Y axes during hold
 */
export const FramedImage: React.FC<{
  src: string;
  splitScreen?: boolean;
  zoomMoments?: ZoomMoment[];
  motionMode?: "still" | "perspective-tilt";
}> = ({ src, splitScreen, zoomMoments, motionMode = "still" }) => {
  const frame = useCurrentFrame();

  // Perspective-tilt: deterministic sin/cos oscillation — no Math.random()
  const tiltX = motionMode === "perspective-tilt" ? Math.sin(frame * 0.022) * 3 : 0;
  const tiltY = motionMode === "perspective-tilt" ? Math.cos(frame * 0.016) * 1.5 : 0;

  const cardTransform =
    motionMode === "perspective-tilt"
      ? `rotateX(${tiltX}deg) rotateY(${tiltY}deg)`
      : undefined;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: splitScreen ? "32px 24px" : "20px 16px",
        perspective: motionMode === "perspective-tilt" ? "1200px" : undefined,
      }}
    >
      <div style={{ width: "100%", maxHeight: "100%" }}>
        <div
          style={{
            width: "100%",
            borderRadius: 16,
            overflow: "hidden",
            background: "#FFFFFF",
            boxShadow: "0 12px 48px rgba(0, 0, 0, 0.5), 0 2px 8px rgba(0, 0, 0, 0.3)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            transform: cardTransform,
            transformStyle: motionMode === "perspective-tilt" ? "preserve-3d" : undefined,
          }}
        >
          {zoomMoments && zoomMoments.length > 0 ? (
            <PunchInZoom moments={zoomMoments}>
              <Img
                src={staticFile(src)}
                style={{ width: "100%", display: "block", background: "#FFFFFF" }}
              />
            </PunchInZoom>
          ) : (
            <Img
              src={staticFile(src)}
              style={{ width: "100%", display: "block", background: "#FFFFFF" }}
            />
          )}
        </div>
      </div>
    </div>
  );
};
