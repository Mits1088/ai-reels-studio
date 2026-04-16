import { Composition, Folder } from "remotion";
import { GenericReelComposition } from "./GenericReelComposition";
import type { Timeline } from "./types";
import timelineData from "../public/timeline.json";
import timelineCinematic from "../public/timeline-cinematic.json";

const FPS = 30;
const reelFrames = Math.ceil(timelineData.total_duration * FPS);
const reelFramesCinematic = Math.ceil(timelineCinematic.total_duration * FPS);

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="Reels">
        {/* Editorial — hard cuts + stat punches */}
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
        {/* Cinematic — slide-up reveals, smooth transitions */}
        <Composition
          id="ReelCompositionCinematic"
          component={GenericReelComposition}
          durationInFrames={reelFramesCinematic}
          fps={FPS}
          width={1080}
          height={1920}
          defaultProps={{
            timeline: timelineCinematic as unknown as Timeline,
          }}
        />
      </Folder>
      {/* YouTube folder hidden — re-enable when working on YouTube pipeline */}
    </>
  );
};
