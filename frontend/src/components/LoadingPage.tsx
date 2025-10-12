"use client";

import { motion } from "motion/react";
import { useEffect, useState } from "react";

interface LoadingPageProps {
  onComplete?: () => void;
}

export function LoadingPage({ onComplete }: LoadingPageProps) {
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    // Skip loading in development mode
    if (process.env.NODE_ENV === "development") {
      console.log("Dev mode: Skipping loading animation");
      onComplete?.();
      return;
    }

    // Simulate loading completion after animation
    const timer = setTimeout(() => {
      setIsComplete(true);
      onComplete?.();
    }, 16500);
    return () => clearTimeout(timer);
  }, [onComplete]);

  // Create caterpillar segments
  const numSegments = 12;
  const segments = Array.from({ length: numSegments }, (_, i) => i);

  return (
    <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center px-8 overflow-hidden">
      <div className="relative w-full h-48">
        {/* Caterpillar made of overlapping circles */}
        <motion.div
          className="absolute left-0 top-1/2 -translate-y-1/2"
          initial={{ x: "-200px" }}
          animate={{ x: "calc(100vw + 100px)" }}
          transition={{
            duration: 16,
            ease: [0.25, 0.1, 0.7, 1],
          }}
        >
          <svg
            width="220"
            height="140"
            viewBox="0 0 220 140"
            className="text-black"
          >
            {/* Caterpillar body segments */}
            {segments.map((segment, index) => {
              const baseX = 30 + index * 14;
              const baseY = 70;
              const radius = index === 0 ? 13 : 11; // Head is slightly bigger

              // Create smooth wave motion that travels through the body
              const wigglePhase = index * 0.4;

              return (
                <motion.circle
                  key={segment}
                  cx={baseX}
                  cy={baseY}
                  r={radius}
                  fill="currentColor"
                  animate={{
                    cy: [
                      baseY,
                      baseY - 18 + index * 0.8,
                      baseY + 5 - index * 0.3,
                      baseY - 22 + index * 0.9,
                      baseY + 8 - index * 0.4,
                      baseY - 15 + index * 0.7,
                      baseY,
                    ],
                  }}
                  transition={{
                    duration: 5,
                    repeat: Infinity,
                    ease: [0.34, 0.06, 0.52, 0.94],
                    delay: wigglePhase,
                  }}
                />
              );
            })}

            {/* Eyes on the head - positioned on right side of first circle (index 0 at cx=30) */}
            <motion.circle
              cx={40}
              cy={66}
              r={2}
              fill="white"
              animate={{
                cy: [66, 66 - 18, 66 + 5, 66 - 22, 66 + 8, 66 - 15, 66],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: [0.34, 0.06, 0.52, 0.94],
              }}
            />
            <motion.circle
              cx={40}
              cy={74}
              r={2}
              fill="white"
              animate={{
                cy: [74, 74 - 18, 74 + 5, 74 - 22, 74 + 8, 74 - 15, 74],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: [0.34, 0.06, 0.52, 0.94],
              }}
            />
          </svg>
        </motion.div>

        {/* Loading text */}
        <motion.div
          className="absolute left-1/2 -translate-x-1/2 -bottom-16"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1, 1, 0] }}
          transition={{
            duration: 16,
            times: [0, 0.08, 0.88, 1],
          }}
        >
          <p className="text-gray-500">Processing your images...</p>
        </motion.div>
      </div>
    </div>
  );
}
