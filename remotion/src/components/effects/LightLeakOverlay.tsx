import React from "react";
import { LightLeak } from "@remotion/light-leaks";

/**
 * LightLeakOverlay — Cinematic WebGL light flare for section transitions.
 *
 * Powered by @remotion/light-leaks. Reveals during the first half of its
 * duration and retracts during the second half — designed to play over
 * a cut point between two scenes.
 *
 * Use inside a TransitionSeries.Overlay for clean scene transitions:
 *   <TransitionSeries.Overlay durationInFrames={20}>
 *     <LightLeakOverlay seed={2} hueShift={30} />
 *   </TransitionSeries.Overlay>
 *
 * Or as a standalone overlay on any composition.
 *
 * Softer alternative to FlashReset — organic flare vs hard white flash.
 * Maximum 1 flash accent per reel (same budget as FlashReset).
 * Use FlashReset for editorial-authority section dividers.
 * Use LightLeakOverlay for cinematic-presenter scene transitions.
 *
 * @remotion/light-leaks requires Remotion ≥ 4.0.415.
 */
export const LightLeakOverlay: React.FC<{
  /** Total duration of the reveal+retract arc. Default 20 frames. */
  durationInFrames?: number;
  /**
   * Shape seed — different values produce different flare patterns.
   * Default: 0 (yellow-orange).
   */
  seed?: number;
  /**
   * Hue rotation in degrees (0–360).
   * 0   = yellow-orange (warm, cinematic default)
   * 120 = green
   * 240 = blue (tech/AI products)
   * 300 = pink/purple (editorial accent)
   * Match to brand: e.g. Google blue ≈ 200, Anthropic orange ≈ 20.
   */
  hueShift?: number;
}> = ({ durationInFrames = 20, seed = 0, hueShift = 0 }) => {
  return <LightLeak durationInFrames={durationInFrames} seed={seed} hueShift={hueShift} />;
};
