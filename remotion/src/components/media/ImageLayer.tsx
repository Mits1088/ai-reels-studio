import React from "react";
import type { TimelineEntry } from "../../types";
import { getPreset } from "../transitions/presets";
import { CONTENT_HEIGHT_PCT } from "../../utils";
import { TransitionWrapper } from "../transitions/TransitionWrapper";
import { FramedImage } from "./FramedImage";

export const ImageLayer: React.FC<{
  src: string;
  durationInFrames: number;
  entry?: TimelineEntry;
  splitScreen?: boolean;
}> = ({ src, durationInFrames, entry, splitScreen }) => {
  const preset = getPreset(entry);
  const display = entry?.display;
  const zoomMoments = entry?.zoom_moments;

  // ── center-full: image fills entire screen, white bg ──
  if (display === "center-full") {
    return (
      <div style={{
        position: "absolute", inset: 0,
        background: "#FAFAFA",
        zIndex: 12,
      }}>
        <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
          <FramedImage src={src} splitScreen={false} zoomMoments={zoomMoments} />
        </TransitionWrapper>
      </div>
    );
  }

  const containerStyle: React.CSSProperties = splitScreen
    ? { position: "absolute", top: 0, left: 0, right: 0, height: `${CONTENT_HEIGHT_PCT}%`, overflow: "hidden" }
    : { position: "absolute", top: 0, left: 0, right: 0, bottom: 0 };

  return (
    <div style={containerStyle}>
      <TransitionWrapper durationInFrames={durationInFrames} preset={preset}>
        <FramedImage src={src} splitScreen={splitScreen} zoomMoments={zoomMoments} />
      </TransitionWrapper>
    </div>
  );
};
