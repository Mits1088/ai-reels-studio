/**
 * GuidedDemo — Browser-framed screenshot with virtual camera pan + clean annotation highlights.
 *
 * Visual style: Based on reference reels (marketing/puru style).
 *  • No dim overlay — the screen is ALWAYS fully visible
 *  • Annotation highlight = clean orange border around the target element only
 *  • Outer device frame = subtle orange border around the entire viewport
 *  • objectFit:cover + animated objectPosition pans the virtual camera
 *
 * Highlight regions are in IMAGE-SPACE % (% of original image dimensions).
 * Screen position is computed dynamically: screen_x = (img_x/100)*dispW - panOffsetX
 * Highlights TRACK the element as the camera pans.
 *
 * Timeline JSON format:
 * {
 *   "display": "guided-demo",
 *   "guided_demo": {
 *     "img_width": 2560,
 *     "img_height": 1354,
 *     "show_frame": false,
 *     "pan_moments": [
 *       { "at": 0, "x": 20, "y": 0 },
 *       { "at": 2, "x": 22, "y": 0 }
 *     ],
 *     "highlight_moments": [
 *       { "at": 0.3, "duration": 1.0, "region": { "x": 5, "y": 37, "w": 13, "h": 5 } }
 *     ]
 *   }
 * }
 *
 * pan_moments.x/.y: objectPosition percentage (0–100).
 *   x=0 = left edge of image visible; x=50 = centered; x=100 = right edge visible.
 *
 * highlight_moments.region: IMAGE-SPACE percentages (% of original image dimensions).
 *   x,y = top-left corner of the box in the image.
 *   w,h = width/height of the box.
 *   Automatically converted to screen coordinates based on current pan position.
 *
 * Coordinate math:
 *   coverScale = max(compWidth/imgW, compHeight/imgH)
 *   dispW = imgW * coverScale,  dispH = imgH * coverScale
 *   panOffsetX = (dispW - compWidth) * (panX / 100)
 *   screen_x = (img_x_pct / 100) * dispW - panOffsetX
 *   screen_y = (img_y_pct / 100) * dispH    (y maps ~1:1 since dispH ≈ compHeight)
 */

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  staticFile,
} from "remotion";
import { Img } from "remotion";

// ── Types ──────────────────────────────────────────────────────────────────

export interface GuidedDemoPanMoment {
  at: number;   // seconds after clip start
  x: number;    // objectPosition X  (0 = left edge, 50 = center, 100 = right edge)
  y: number;    // objectPosition Y  (0 = top edge,  50 = center, 100 = bottom edge)
}

export interface GuidedDemoHighlightRegion {
  x: number;  // % of original IMAGE WIDTH  (top-left corner, 0 = left edge)
  y: number;  // % of original IMAGE HEIGHT (top-left corner, 0 = top edge)
  w: number;  // % of original IMAGE WIDTH
  h: number;  // % of original IMAGE HEIGHT
}

export interface GuidedDemoHighlight {
  at: number;       // seconds after clip start when annotation appears
  duration: number; // seconds the annotation stays
  region: GuidedDemoHighlightRegion;
  /** "border" = clean orange outline (default). "dim" = dark vignette with spotlight hole on the region. */
  highlight_style?: "border" | "dim";
  /** CSS color for the border annotation. Defaults to Claude orange (#D97757). Only applies to "border" highlight_style. */
  highlight_color?: string;
}

export interface GuidedDemoConfig {
  url?: string;
  show_frame?: boolean;           // default: false. true = add Mac chrome bar at top.
  img_width?: number;             // original image width in px (needed for correct scale)
  img_height?: number;            // original image height in px
  pan_moments?: GuidedDemoPanMoment[];
  highlight_moments?: GuidedDemoHighlight[];
}

interface GuidedDemoProps {
  asset: string;
  durationInFrames: number;
  guidedDemo?: GuidedDemoConfig;
}

// ── Layout constants ───────────────────────────────────────────────────────
const CHROME_HEIGHT        = 64;             // Mac chrome bar height in px (when show_frame: true)
const CARD_MARGIN_V        = 96;             // px of warm beige visible above and below the card
const WARM_BEIGE           = "#F5F0E8";      // background matching reference reel style
const ANNOTATION_COLOR     = "#D97757";      // Claude orange — matches device frame
const DEVICE_FRAME_COLOR   = "rgba(217, 119, 87, 0.55)";  // same orange, slightly translucent
const ANNOTATION_BORDER_PX = 4;             // clean border, no shadow spread
const ANNOTATION_RADIUS    = 10;            // corner radius on annotation box
const DEVICE_FRAME_RADIUS  = 14;            // corner radius on card frame
const DEVICE_FRAME_PX      = 3;             // device frame border width

// ── Component ──────────────────────────────────────────────────────────────

export const GuidedDemo: React.FC<GuidedDemoProps> = ({
  asset,
  durationInFrames,
  guidedDemo = {},
}) => {
  const frame = useCurrentFrame();
  const { fps, width: compWidth, height: compHeight } = useVideoConfig();

  // Config
  const showChrome  = guidedDemo.show_frame === true;   // default false
  const urlText     = guidedDemo.url ?? "";
  const panMoments  = guidedDemo.pan_moments ?? [];
  const hlMoments   = guidedDemo.highlight_moments ?? [];

  // Image dimensions — REQUIRED for correct scale math.
  // Default to 2560×1340 (typical GitHub/Claude screenshot at 2560 wide display).
  const imgW = guidedDemo.img_width  ?? 2560;
  const imgH = guidedDemo.img_height ?? 1340;

  // Content area — warm beige margins above and below the screenshot card
  const contentTop    = showChrome ? CHROME_HEIGHT : CARD_MARGIN_V;
  const contentBottom = showChrome ? 0 : CARD_MARGIN_V;
  const contentH      = compHeight - contentTop - contentBottom;

  // objectFit:cover scale factor
  const coverScale = Math.max(compWidth / imgW, contentH / imgH);
  const dispW      = imgW * coverScale;
  const dispH      = imgH * coverScale;

  // ── Virtual camera pan ──────────────────────────────────────────────────
  let panX = 50;
  let panY = 0;

  if (panMoments.length >= 2) {
    const framePts = panMoments.map(m => Math.round(m.at * fps));
    panX = interpolate(frame, framePts, panMoments.map(m => m.x), {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });
    panY = interpolate(frame, framePts, panMoments.map(m => m.y), {
      extrapolateLeft: "clamp", extrapolateRight: "clamp",
    });
  } else if (panMoments.length === 1) {
    panX = panMoments[0].x;
    panY = panMoments[0].y;
  }

  // Pan offsets in displayed pixels.
  const panOffsetX = Math.max(0, dispW - compWidth) * (panX / 100);
  const panOffsetY = Math.max(0, dispH - contentH)  * (panY / 100);

  // ── Active highlight ────────────────────────────────────────────────────
  const currentSec = frame / fps;
  const activeHL   = hlMoments.find(
    h => currentSec >= h.at && currentSec < h.at + h.duration,
  );

  let hlOpacity = 0;
  if (activeHL) {
    const localFrame  = Math.round((currentSec - activeHL.at) * fps);
    const totalFrames = Math.max(1, Math.round(activeHL.duration * fps));
    const fadeDur     = Math.min(6, Math.floor(totalFrames * 0.2));
    hlOpacity = interpolate(
      localFrame,
      [0, fadeDur, totalFrames - fadeDur, totalFrames],
      [0, 1, 1, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
    );
  }

  // ── Highlight geometry — image-space % → screen px ────────────────────
  const hlLeft   = activeHL ? (activeHL.region.x / 100) * dispW - panOffsetX : 0;
  const hlTop    = activeHL ? contentTop + (activeHL.region.y / 100) * dispH - panOffsetY : 0;
  const hlWidth  = activeHL ? (activeHL.region.w / 100) * dispW : 0;
  const hlHeight = activeHL ? (activeHL.region.h / 100) * dispH : 0;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: WARM_BEIGE,
        overflow: "hidden",
        zIndex: 12,
      }}
    >
      {/* ── Optional Mac chrome bar ──────────────────────────────────── */}
      {showChrome && (
        <div
          style={{
            position: "absolute",
            top: 0, left: 0, right: 0,
            height: CHROME_HEIGHT,
            background: "#2A2A2C",
            display: "flex",
            alignItems: "center",
            padding: "0 20px",
            zIndex: 30,
            borderBottom: "1px solid rgba(255,255,255,0.07)",
            flexShrink: 0,
          }}
        >
          {/* MacOS traffic lights */}
          <div style={{ display: "flex", gap: 7, flexShrink: 0 }}>
            {(["#FF5F57", "#FEBC2E", "#28C840"] as const).map((c, i) => (
              <div
                key={i}
                style={{
                  width: 13, height: 13,
                  borderRadius: "50%",
                  background: c,
                  flexShrink: 0,
                }}
              />
            ))}
          </div>
          {/* URL address bar */}
          <div
            style={{
              flex: 1,
              background: "#3A3A3C",
              borderRadius: 8,
              padding: "7px 14px",
              marginLeft: 16,
              fontSize: 22,
              color: "rgba(255,255,255,0.58)",
              fontFamily: "'Inter', 'Segoe UI', sans-serif",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              letterSpacing: 0,
              lineHeight: 1,
            }}
          >
            🔒 {urlText}
          </div>
        </div>
      )}

      {/* ── Screenshot card — sits on warm beige with orange device border ── */}
      <div
        style={{
          position: "absolute",
          top: contentTop,
          left: 0, right: 0,
          bottom: contentBottom,
          overflow: "hidden",
          border: `${DEVICE_FRAME_PX}px solid ${DEVICE_FRAME_COLOR}`,
          borderRadius: DEVICE_FRAME_RADIUS,
        }}
      >
        <Img
          src={staticFile(asset)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: `${panX}% ${panY}%`,
            display: "block",
          }}
        />
      </div>

      {/* ── Annotation highlight ─────────────────────────────────────── */}
      {/* "border" mode: clean orange outline, screen fully visible.      */}
      {/* "dim"    mode: dark vignette covers everything OUTSIDE the box, */}
      {/*   creating a spotlight on the target element. box-shadow spread  */}
      {/*   of 2000px dims the whole GuidedDemo area (clipped by overflow) */}
      {activeHL && hlOpacity > 0.01 && (
        <div
          style={{
            position: "absolute",
            top: hlTop,
            left: hlLeft,
            width: hlWidth,
            height: hlHeight,
            ...(activeHL.highlight_style === "dim"
              ? {
                  // Spotlight: massive shadow dims everything outside this box
                  boxShadow: `0 0 0 2000px rgba(0,0,0,0.72)`,
                  border: `1px solid rgba(255,255,255,0.22)`,
                  borderRadius: 6,
                }
              : {
                  // Default: clean orange border outline
                  border: `${ANNOTATION_BORDER_PX}px solid ${activeHL.highlight_color ?? ANNOTATION_COLOR}`,
                  borderRadius: ANNOTATION_RADIUS,
                  outline: `2px solid rgba(255, 255, 255, 0.25)`,
                  outlineOffset: 3,
                }),
            zIndex: 23,
            opacity: hlOpacity,
            pointerEvents: "none",
          }}
        />
      )}
    </div>
  );
};
