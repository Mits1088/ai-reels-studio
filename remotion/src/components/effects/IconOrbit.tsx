import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  staticFile,
} from "remotion";

interface IconItem {
  src: string;
  label?: string;
}

interface IconOrbitProps {
  icons: IconItem[];
  durationInFrames: number;
  staggerDelay?: number;
  orbitRadius?: number;
  iconSize?: number;
  withCircleBg?: boolean;
  ambientFloat?: boolean;
  exitStyle?: "scatter" | "fade" | "shrink";
  children?: React.ReactNode;
}

export const IconOrbit: React.FC<IconOrbitProps> = ({
  icons,
  durationInFrames,
  staggerDelay = 3,
  orbitRadius = 280,
  iconSize = 56,
  withCircleBg = true,
  ambientFloat = true,
  exitStyle = "fade",
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const exitStart = durationInFrames - 10;
  const angleStep = (2 * Math.PI) / icons.length;

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Central element */}
      {children && (
        <div style={{ position: "relative", zIndex: 2 }}>{children}</div>
      )}

      {/* Orbiting icons */}
      {icons.map((icon, i) => {
        const enterDelay = i * staggerDelay;

        // Spring entrance scale
        const entranceScale = spring({
          frame: frame - enterDelay,
          fps,
          config: {
            damping: 12,
            stiffness: 180,
            mass: 0.8,
          },
        });

        // Base position on the circle
        const angle = angleStep * i - Math.PI / 2; // start from top
        const baseX = Math.cos(angle) * orbitRadius;
        const baseY = Math.sin(angle) * orbitRadius;

        // Ambient floating motion (sinusoidal with per-icon phase offset)
        let floatX = 0;
        let floatY = 0;
        if (ambientFloat) {
          const phaseX = i * 1.7;
          const phaseY = i * 2.3;
          floatX = Math.sin(frame * 0.06 + phaseX) * 4;
          floatY = Math.cos(frame * 0.05 + phaseY) * 3.5;
        }

        // Exit animation
        let exitOpacity = 1;
        let exitScale = 1;
        let exitTranslateX = 0;
        let exitTranslateY = 0;

        if (frame >= exitStart) {
          const exitProgress = interpolate(
            frame,
            [exitStart, durationInFrames],
            [0, 1],
            { extrapolateRight: "clamp" }
          );

          if (exitStyle === "fade") {
            exitOpacity = 1 - exitProgress;
          } else if (exitStyle === "shrink") {
            exitScale = 1 - exitProgress;
            exitOpacity = 1 - exitProgress;
          } else if (exitStyle === "scatter") {
            const scatterDir = angle;
            exitTranslateX = Math.cos(scatterDir) * exitProgress * 200;
            exitTranslateY = Math.sin(scatterDir) * exitProgress * 200;
            exitOpacity = 1 - exitProgress;
          }
        }

        const finalScale = entranceScale * exitScale;
        const finalX = baseX + floatX + exitTranslateX;
        const finalY = baseY + floatY + exitTranslateY;

        // Don't render before entrance starts
        if (frame < enterDelay) return null;

        const circlePadding = withCircleBg ? 12 : 0;
        const circleSize = iconSize + circlePadding * 2;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              zIndex: 1,
              transform: `translate(${finalX}px, ${finalY}px) scale(${finalScale})`,
              opacity: exitOpacity,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 6,
            }}
          >
            <div
              style={{
                width: circleSize,
                height: circleSize,
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: withCircleBg ? "#FFFFFF" : "transparent",
                boxShadow: withCircleBg
                  ? "0 4px 16px rgba(0, 0, 0, 0.12), 0 1px 4px rgba(0, 0, 0, 0.08)"
                  : "0 2px 8px rgba(0, 0, 0, 0.1)",
              }}
            >
              <Img
                src={staticFile(icon.src)}
                style={{
                  width: iconSize,
                  height: iconSize,
                  objectFit: "contain",
                }}
              />
            </div>
            {icon.label && (
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: "#333",
                  textAlign: "center",
                  whiteSpace: "nowrap",
                }}
              >
                {icon.label}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};
