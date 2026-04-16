/**
 * sfx-map.ts — Resolves SFX asset strings in timeline.json to actual audio URLs.
 *
 * Two sources:
 *
 * 1. @remotion/sfx (CDN-hosted, zero local files required)
 *    Use these keys in timeline.json sfx lane asset field:
 *
 *    "@sfx/whoosh"         — short sharp whoosh
 *    "@sfx/whip"           — fast whip crack
 *    "@sfx/ding"           — notification ding
 *    "@sfx/uiSwitch"       — toggle/switch click
 *    "@sfx/mouseClick"     — mouse click
 *    "@sfx/pageTurn"       — page turn swish
 *    "@sfx/shutterModern"  — camera shutter (modern)
 *    "@sfx/shutterOld"     — camera shutter (classic)
 *
 * 2. Local files in remotion/public/ (legacy) — resolved via staticFile()
 *    All existing sfx-* filenames continue to work unchanged.
 *
 * Usage in ReelComposition:
 *   import { resolveSfxAsset } from "./lib/sfx-map";
 *   <Audio src={resolveSfxAsset(entry.asset)} />
 */

import {
  whoosh,
  whip,
  ding,
  uiSwitch,
  mouseClick,
  pageTurn,
  shutterModern,
  shutterOld,
} from "@remotion/sfx";
import { staticFile } from "remotion";

const SFX_REGISTRY: Record<string, string> = {
  "@sfx/whoosh": whoosh,
  "@sfx/whip": whip,
  "@sfx/ding": ding,
  "@sfx/uiSwitch": uiSwitch,
  "@sfx/mouseClick": mouseClick,
  "@sfx/pageTurn": pageTurn,
  "@sfx/shutterModern": shutterModern,
  "@sfx/shutterOld": shutterOld,
};

/**
 * Resolves an SFX asset string to a URL safe to pass to <Audio src={}>.
 *
 * - "@sfx/whoosh" → @remotion/sfx CDN URL (no local file needed)
 * - "sfx-pop.mp3" → staticFile("sfx-pop.mp3")
 * - "sfx-pop"     → staticFile("sfx-pop.mp3") (extension added automatically)
 */
export function resolveSfxAsset(asset: string | undefined): string {
  if (!asset) return "";

  // CDN shorthand — no local file needed
  if (asset in SFX_REGISTRY) {
    return SFX_REGISTRY[asset];
  }

  // Local file — add .mp3 if no extension present
  const hasExtension = /\.[a-z0-9]+$/i.test(asset);
  return staticFile(hasExtension ? asset : `${asset}.mp3`);
}

/**
 * All available @sfx/ shorthand keys.
 * Use these in timeline.json sfx lane entries to avoid local file dependencies.
 */
export const SFX_KEYS = Object.keys(SFX_REGISTRY) as (keyof typeof SFX_REGISTRY)[];
