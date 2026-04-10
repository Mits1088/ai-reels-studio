import React from "react";
import { Img, staticFile } from "remotion";
import type { ZoomMoment } from "../../types";
import { PunchInZoom } from "../effects/PunchInZoom";

export const FramedImage: React.FC<{
  src: string;
  splitScreen?: boolean;
  zoomMoments?: ZoomMoment[];
}> = ({ src, splitScreen, zoomMoments }) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: splitScreen ? "32px 24px" : "20px 16px",
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
        }}
      >
        {zoomMoments && zoomMoments.length > 0 ? (
          <PunchInZoom moments={zoomMoments}>
            <Img
              src={staticFile(src)}
              style={{
                width: "100%",
                display: "block",
                background: "#FFFFFF",
              }}
            />
          </PunchInZoom>
        ) : (
          <Img
            src={staticFile(src)}
            style={{
              width: "100%",
              display: "block",
              background: "#FFFFFF",
            }}
          />
        )}
      </div>
    </div>
  </div>
);
