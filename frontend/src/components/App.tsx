"use client";

import { motion } from "motion/react";
import { useState, useEffect } from "react";
import { ClothingDropZone } from "./ClothingDropZone";
import { LoadingPage } from "./LoadingPage";
import { ResultsPage } from "./ResultsPage";
import { ImageUploadModal } from "./ImageUploadModal";
import { WormLogo } from "./WormLogo";

export default function App() {
  const text = "Wiggle, wiggle, wiggle.";
  const [showHero, setShowHero] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  // Skip to results page in development mode
  if (process.env.NODE_ENV === "development") {
    console.log("Dev mode: Skipping to ResultsPage");
    return <ResultsPage />;
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowHero(false);
    }, 4000);
    return () => clearTimeout(timer);
  }, []);

  const handleCategoryClick = (category: string) => {
    setSelectedCategory(category);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
  };

  const handleImagesSubmit = () => {
    setIsModalOpen(false);
    setIsLoading(true);
  };

  const handleLoadingComplete = () => {
    setIsComplete(true);
  };

  if (isLoading && !isComplete) {
    return <LoadingPage onComplete={handleLoadingComplete} />;
  }

  if (isComplete) {
    return <ResultsPage />;
  }

  return (
    <div className="bg-[#f5f5f5]">
      {showHero ? (
        /* First Page - Hero */
        <motion.div
          className="min-h-screen flex flex-col items-center justify-center px-8"
          initial={{ opacity: 1 }}
          animate={{ opacity: showHero ? 1 : 0 }}
          transition={{ duration: 0.6, delay: showHero ? 0 : 0 }}
        >
          <div className="flex-1 flex items-center justify-center">
            <h1 className="text-7xl md:text-8xl lg:text-9xl text-center text-[48px] font-bold">
              {text.split("").map((char, index) => (
                <motion.span
                  key={index}
                  initial={{ opacity: 0, y: 20, rotate: -10 }}
                  animate={{
                    opacity: 1,
                    y: 0,
                    rotate: 0,
                  }}
                  transition={{
                    duration: 0.6,
                    delay: index * 0.08,
                    ease: [0.6, 0.05, 0.01, 0.9],
                  }}
                  style={{ display: "inline-block" }}
                >
                  {char === " " ? "\u00A0" : char}
                </motion.span>
              ))}
            </h1>
          </div>

          <motion.div
            className="pb-12"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 1,
              delay: text.length * 0.08 + 0.5,
              ease: "easeOut",
            }}
          >
            <p className="text-center text-lg">
              Where your product comes to life.
            </p>
          </motion.div>
        </motion.div>
      ) : (
        /* Second Page - Drop Zones */
        <motion.div
          className="min-h-screen flex flex-col items-center justify-center px-8 py-20 relative"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          {/* Logo */}
          <motion.div
            className="absolute top-8 right-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <p className="text-[15px] flex items-center">
              <WormLogo />
              wiggly.
            </p>
          </motion.div>
          <div className="max-w-6xl w-full">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl mb-3 font-bold">
                What do you want to bring to life?
              </h2>
              <p className="text-gray-500">
                Upload your product images to get started
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12 justify-items-center">
              <ClothingDropZone
                type="tshirt"
                label="T-Shirts"
                index={0}
                onClick={() => handleCategoryClick("T-Shirts")}
              />
              <ClothingDropZone
                type="sweater"
                label="Sweaters"
                index={1}
                onClick={() => handleCategoryClick("Sweaters")}
              />
              <ClothingDropZone
                type="socks"
                label="Socks"
                index={2}
                onClick={() => handleCategoryClick("Socks")}
              />
            </div>
          </div>
        </motion.div>
      )}

      {/* Image Upload Modal */}
      <ImageUploadModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        categoryLabel={selectedCategory}
        onSubmit={handleImagesSubmit}
      />
    </div>
  );
}
