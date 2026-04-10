import { Composition, Folder } from "remotion";
import { ReelComposition } from "./ReelComposition";
import { GenericReelComposition } from "./GenericReelComposition";
import { YouTubeComposition } from "./YouTubeComposition";
import type { Timeline, YouTubeTimeline } from "./types";
import timelineData from "../public/timeline.json";

const FPS = 30;
const reelFrames = Math.ceil(timelineData.total_duration * FPS);

// YouTube timeline — loaded dynamically when youtube-timeline.json exists.
// Falls back to a minimal placeholder so the composition is always registered.
let ytData: YouTubeTimeline;
try {
  ytData = require("../public/youtube-timeline.json") as YouTubeTimeline;
} catch {
  ytData = { total_duration: 10, video: "video.mp4", lanes: { overlays: [] } };
}
const ytFrames = Math.ceil(ytData.total_duration * FPS);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Reels">
        {/* Default for new projects — data-driven from timeline.json */}
        <Composition
          id="ReelComposition"
          component={GenericReelComposition}
          durationInFrames={reelFrames}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            timeline: timelineData as unknown as Timeline,
          }}
        />
        {/* Legacy — hardcoded per-project composition. Use for old projects
            that rely on custom inline components (ScrollingBenchmark, etc.) */}
        <Composition
          id="LegacyReel"
          component={ReelComposition}
          durationInFrames={reelFrames}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            timeline: timelineData as unknown as Timeline,
          }}
        />
      </Folder>
      <Folder name="YouTube">
        <Composition
          id="YouTubeComposition"
          component={YouTubeComposition}
          durationInFrames={ytFrames}
          fps={FPS}
          width={1920}
          height={1080}
          defaultProps={{
            timeline: ytData as unknown as YouTubeTimeline,
          }}
        />
      </Folder>
    </>
  );
};
