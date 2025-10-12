"use client";

import { motion } from "motion/react";
import { Button } from "./ui/button";
import { WormLogo } from "./WormLogo";
import ModelViewer from "./ModelViewer";

export function ResultsPage() {
  return (
    <div className="min-h-screen bg-[#f5f5f5] px-8 py-20 relative">
      {/* Logo */}
      <motion.div
        className="absolute top-8 right-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.6 }}
      >
        <p className="text-[15px] flex items-center">
          <WormLogo />
          wiggly.
        </p>
      </motion.div>

      {/* Credits */}
      <motion.div
        className="absolute bottom-10 right-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
      >
        <p className="text-[10px] text-gray-800 flex items-center gap-1.5">
          <svg
            width="10"
            height="10"
            viewBox="0 0 16 16"
            fill="currentColor"
            className="inline-block"
            style={{ minWidth: "10px" }}
          >
            <path d="M8 2.748l-.717-.737C5.6.281 2.514.878 1.4 3.053c-.523 1.023-.641 2.5.314 4.385.92 1.815 2.834 3.989 6.286 6.357 3.452-2.368 5.365-4.542 6.286-6.357.955-1.885.838-3.362.314-4.385C13.486.878 10.4.28 8.717 2.01L8 2.748z" />
          </svg>
          Created by Yongkang, Fritz & Quan
        </p>
      </motion.div>

      <div className="max-w-7xl mx-auto">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl mb-3">Your model is ready.</h2>
          <p className="text-gray-500">
            Download your files or explore the documentation
          </p>
        </motion.div>

        {/* Centered 3D Preview */}
        <div className="flex justify-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="w-full max-w-2xl"
          >
            <div className="w-full rounded-[2rem] border-2 border-gray-300/60 bg-white/50 overflow-hidden">
              {/* 3D Model Viewer */}
              <div className="h-96 w-full">
                <ModelViewer />
              </div>
            </div>

            {/* Buttons below the box */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-6"
            >
              <div className="flex gap-4">
                <Button
                  variant="default"
                  className="flex-1 rounded-xl bg-black hover:bg-gray-800 text-white"
                >
                  Download Files
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 rounded-xl border-gray-300 hover:bg-gray-100"
                >
                  View Docs
                </Button>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
