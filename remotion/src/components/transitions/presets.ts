import type { TransitionPreset, TimelineEntry } from "../../types";

export const DEFAULT_TRANSITION: TransitionPreset = {
  enter: "fade",
  exit: "fade",
  enterDur: 3,
  exitDur: 2,
};

/**
 * Resolve transition preset from timeline entry data.
 * Falls back to DEFAULT_TRANSITION if no preset is defined.
 */
export function getPreset(entry?: TimelineEntry): TransitionPreset {
  if (entry?.transition_preset) {
    return {
      enter: entry.transition_preset.enter as TransitionPreset["enter"],
      exit: entry.transition_preset.exit as TransitionPreset["exit"],
      enterDur: entry.transition_preset.enterDur,
      exitDur: entry.transition_preset.exitDur,
      kenBurns: entry.transition_preset.kenBurns,
    };
  }
  return DEFAULT_TRANSITION;
}
