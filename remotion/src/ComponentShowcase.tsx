import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { TypingInput } from "./components/effects/TypingInput";
import { IconOrbit } from "./components/effects/IconOrbit";
import { SourceProofCard } from "./components/effects/SourceProofCard";
import { StrikethroughSwap } from "./components/effects/StrikethroughSwap";
import { AuroraBackground } from "./components/effects/AuroraBackground";
import { GradientMesh } from "./components/effects/GradientMesh";

// ════════════════════════════════════════════════════════════════════
// COMPONENT SHOWCASE — Preview all 4 new animated mock components
//
// Scene 1 (0–4s):   TypingInput — Google style email input
// Scene 2 (4–8s):   TypingInput — Claude style prompt input
// Scene 3 (8–14s):  IconOrbit — Product icons orbiting a central element
// Scene 4 (14–20s): SourceProofCard — Designed tweet/announcement card
// Scene 5 (20–26s): StrikethroughSwap — Before/after transformation
// Scene 6 (26–30s): All together — quick montage
// ════════════════════════════════════════════════════════════════════

export const ComponentShowcase: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: "#FFFFFF" }}>

      {/* ════ Scene 1: TypingInput — Google style ════ */}
      <Sequence from={0} durationInFrames={120}>
        <AbsoluteFill>
          <AuroraBackground
            speed={0.3}
            intensity={0.6}
            colors={[
              "rgba(66, 133, 244, 0.06)",
              "rgba(52, 168, 83, 0.04)",
              "rgba(251, 188, 4, 0.05)",
              "rgba(234, 67, 53, 0.03)",
              "rgba(255, 255, 255, 0.08)",
            ]}
          />
          <AbsoluteFill style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <div style={{ width: "100%", padding: "0 40px" }}>
              <div style={{
                textAlign: "center",
                marginBottom: 40,
                fontSize: 22,
                fontWeight: 600,
                color: "#333",
                fontFamily: "system-ui, sans-serif",
              }}>
                TypingInput — Google Style
              </div>
              <TypingInput
                text="elisa.beckett"
                suffix="@gmail.com"
                durationInFrames={120}
                style="google"
                accentColor="#4285F4"
                typingSpeed={4}
              />
            </div>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* ════ Scene 2: TypingInput — Claude style ════ */}
      <Sequence from={120} durationInFrames={120}>
        <AbsoluteFill>
          <AuroraBackground
            speed={0.3}
            intensity={0.6}
            colors={[
              "rgba(204, 120, 92, 0.08)",
              "rgba(232, 184, 138, 0.06)",
              "rgba(245, 230, 216, 0.09)",
              "rgba(250, 249, 247, 0.10)",
              "rgba(255, 255, 255, 0.06)",
            ]}
          />
          <AbsoluteFill style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <div style={{ width: "100%", padding: "0 40px" }}>
              <div style={{
                textAlign: "center",
                marginBottom: 40,
                fontSize: 22,
                fontWeight: 600,
                color: "#333",
                fontFamily: "system-ui, sans-serif",
              }}>
                TypingInput — Claude Style
              </div>
              <TypingInput
                text="What skills would enhance my work?"
                durationInFrames={120}
                style="claude"
                typingSpeed={3}
                placeholder="Message Claude..."
              />
            </div>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* ════ Scene 3: IconOrbit ════ */}
      <Sequence from={240} durationInFrames={180}>
        <AbsoluteFill>
          <AuroraBackground
            speed={0.3}
            intensity={0.5}
            colors={[
              "rgba(66, 133, 244, 0.06)",
              "rgba(52, 168, 83, 0.04)",
              "rgba(255, 255, 255, 0.08)",
            ]}
          />
          <AbsoluteFill style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <div style={{
              textAlign: "center",
              position: "absolute",
              top: 80,
              left: 0,
              right: 0,
              fontSize: 22,
              fontWeight: 600,
              color: "#333",
              fontFamily: "system-ui, sans-serif",
            }}>
              IconOrbit — Staggered Spring Entrance
            </div>
            <IconOrbit
              icons={[
                { src: "claude-logo.png", label: "Claude" },
                { src: "claude-logo.png", label: "Gmail" },
                { src: "claude-logo.png", label: "Drive" },
                { src: "claude-logo.png", label: "Sheets" },
                { src: "claude-logo.png", label: "Docs" },
                { src: "claude-logo.png", label: "Photos" },
              ]}
              durationInFrames={180}
              staggerDelay={4}
              orbitRadius={240}
              iconSize={52}
              exitStyle="scatter"
            >
              <div style={{
                width: 120,
                height: 120,
                borderRadius: "50%",
                background: "linear-gradient(135deg, #D97757, #E8B88A)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 48,
                color: "#FFF",
                fontWeight: 700,
                boxShadow: "0 8px 32px rgba(217, 119, 87, 0.3)",
              }}>
                AI
              </div>
            </IconOrbit>
          </AbsoluteFill>
        </AbsoluteFill>
      </Sequence>

      {/* ════ Scene 4: SourceProofCard ════ */}
      <Sequence from={420} durationInFrames={180}>
        <AbsoluteFill style={{ background: "#0A0A0A" }}>
          <div style={{
            textAlign: "center",
            position: "absolute",
            top: 60,
            left: 0,
            right: 0,
            fontSize: 22,
            fontWeight: 600,
            color: "#999",
            fontFamily: "system-ui, sans-serif",
            zIndex: 50,
          }}>
            SourceProofCard — Designed Trust Card
          </div>
          <SourceProofCard
            authorName="Anthropic"
            authorHandle="@AnthropicAI"
            verified
            platform="twitter"
            bodyText="Claude can now remember your preferences, learn your style, and build skills that match how you work. Here's what to know:"
            highlightPhrases={["remember your preferences", "build skills"]}
            highlightColor="rgba(217, 119, 87, 0.3)"
            numberedPoints={[
              { number: 1, text: "Enable memory in Settings → Capabilities" },
              { number: 2, text: "Import your ChatGPT history for instant context" },
              { number: 3, text: "Ask Claude to create skills tailored to your workflow" },
            ]}
            durationInFrames={180}
          />
        </AbsoluteFill>
      </Sequence>

      {/* ════ Scene 5: StrikethroughSwap ════ */}
      <Sequence from={600} durationInFrames={150}>
        <AbsoluteFill>
          <AuroraBackground
            speed={0.3}
            intensity={0.5}
            colors={[
              "rgba(204, 120, 92, 0.06)",
              "rgba(232, 184, 138, 0.04)",
              "rgba(255, 255, 255, 0.08)",
            ]}
          />
          <div style={{
            textAlign: "center",
            position: "absolute",
            top: 100,
            left: 0,
            right: 0,
            fontSize: 22,
            fontWeight: 600,
            color: "#333",
            fontFamily: "system-ui, sans-serif",
            zIndex: 50,
          }}>
            StrikethroughSwap — Before / After
          </div>
          <StrikethroughSwap
            oldValue="Generic ChatGPT responses"
            newValue="Personalized Claude with your context"
            durationInFrames={150}
            strikethroughDelay={15}
            newValueDelay={40}
            fontSize={24}
          />
        </AbsoluteFill>
      </Sequence>

    </AbsoluteFill>
  );
};
