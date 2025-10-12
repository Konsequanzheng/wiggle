"use client";

import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";
import { X } from "lucide-react";
import confetti from "canvas-confetti";

interface ImageUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  categoryLabel: string;
  onSubmit: () => void;
}

export function ImageUploadModal({
  isOpen,
  onClose,
  categoryLabel,
  onSubmit,
}: ImageUploadModalProps) {
  const [frontImage, setFrontImage] = useState<File | null>(null);
  const [backImage, setBackImage] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [frontImagePreview, setFrontImagePreview] = useState<string | null>(
    null
  );
  const [backImagePreview, setBackImagePreview] = useState<string | null>(null);

  const handleFrontDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find((file) => file.type === "image/png");
    if (imageFile) {
      setFrontImage(imageFile);
      const reader = new FileReader();
      reader.onload = (e) => {
        setFrontImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(imageFile);
    }
  };

  const handleBackDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find((file) => file.type === "image/png");
    if (imageFile) {
      setBackImage(imageFile);
      const reader = new FileReader();
      reader.onload = (e) => {
        setBackImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(imageFile);
    }
  };

  const handleFrontFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "image/png") {
      setFrontImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setFrontImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleBackFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "image/png") {
      setBackImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setBackImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const canSubmit = frontImage && backImage && !isUploading;

  const handleSubmit = async (e: React.MouseEvent<HTMLButtonElement>) => {
    if (canSubmit && frontImage && backImage) {
      setIsUploading(true);

      // Skip API call in development mode
      if (process.env.NODE_ENV === "development") {
        console.log("Dev mode: Skipping API call, files would be sent:", {
          frontImage: frontImage.name,
          backImage: backImage.name,
        });

        // Get button position for localized confetti
        const rect = e.currentTarget.getBoundingClientRect();
        const x = (rect.left + rect.width / 2) / window.innerWidth;
        const y = (rect.top + rect.height / 2) / window.innerHeight;

        // Trigger subtle confetti animation around the button
        confetti({
          particleCount: 20,
          spread: 40,
          origin: { x, y },
          colors: ["#1f2937"], // gray-800 to match logo
          disableForReducedMotion: true,
          ticks: 100,
          gravity: 1,
          scalar: 0.8, // Thinner ribbons
          shapes: ["square"], // Ribbon-like particles
          startVelocity: 15, // Slower upward movement
          drift: 0, // No horizontal drift
        });

        // Small delay before transitioning to next page
        setTimeout(() => {
          onSubmit();
        }, 300);
        return;
      }

      try {
        // Create FormData with the files
        const formData = new FormData();
        formData.append("front.png", frontImage);
        formData.append("back.png", backImage);

        // Send to API endpoint
        const response = await fetch("/api/generate-texture", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to generate texture");
        }

        // Get button position for localized confetti
        const rect = e.currentTarget.getBoundingClientRect();
        const x = (rect.left + rect.width / 2) / window.innerWidth;
        const y = (rect.top + rect.height / 2) / window.innerHeight;

        // Trigger subtle confetti animation around the button
        confetti({
          particleCount: 20,
          spread: 40,
          origin: { x, y },
          colors: ["#1f2937"], // gray-800 to match logo
          disableForReducedMotion: true,
          ticks: 100,
          gravity: 1,
          scalar: 0.8, // Thinner ribbons
          shapes: ["square"], // Ribbon-like particles
          startVelocity: 15, // Slower upward movement
          drift: 0, // No horizontal drift
        });

        // Small delay before transitioning to next page
        setTimeout(() => {
          onSubmit();
        }, 300);
      } catch (error) {
        console.error("Error uploading images:", error);
        setIsUploading(false);
        // You might want to show an error message to the user here
      }
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.3, ease: [0.6, 0.05, 0.01, 0.9] }}
            className="fixed inset-0 z-50 flex items-center justify-center p-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-[#f5f5f5] rounded-[2rem] p-8 max-w-3xl w-full relative max-h-[90vh] overflow-y-auto">
              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={24} />
              </button>

              {/* Title */}
              <div className="text-center mb-8">
                <h2 className="text-3xl mb-2">Upload {categoryLabel} Images</h2>
                <p className="text-gray-500">
                  Please upload both front and back views
                </p>
              </div>

              {/* Two upload boxes */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Front Side */}
                <div className="flex flex-col items-center">
                  <div
                    className={`w-full aspect-[4/5] rounded-[1.5rem] border-2 ${
                      frontImage
                        ? "border-green-400 bg-green-50/50"
                        : "border-gray-300/60 hover:border-gray-400/80"
                    } flex flex-col items-center justify-center cursor-pointer transition-all duration-300`}
                    onDragOver={handleDragOver}
                    onDrop={handleFrontDrop}
                  >
                    <input
                      type="file"
                      accept="image/png"
                      onChange={handleFrontFileChange}
                      className="hidden"
                      id="front-file-input"
                    />
                    <label
                      htmlFor="front-file-input"
                      className="w-full h-full flex flex-col items-center justify-center cursor-pointer"
                    >
                      <div className="text-center px-6">
                        {frontImagePreview ? (
                          <div className="w-full h-full flex flex-col items-center justify-center">
                            <img
                              src={frontImagePreview}
                              alt="Front preview"
                              className="max-w-full max-h-full object-contain rounded-lg"
                            />
                            <p className="text-sm text-green-500 mt-2 font-medium">
                              {frontImage?.name}
                            </p>
                          </div>
                        ) : (
                          <>
                            <svg
                              className="w-12 h-12 mx-auto mb-3 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                              />
                            </svg>
                            <h3 className="text-gray-800 mb-1">Front Side</h3>
                            <p className="text-sm text-gray-400">
                              Drop PNG image or click to upload
                            </p>
                          </>
                        )}
                      </div>
                    </label>
                  </div>
                </div>

                {/* Back Side */}
                <div className="flex flex-col items-center">
                  <div
                    className={`w-full aspect-[4/5] rounded-[1.5rem] border-2 ${
                      backImage
                        ? "border-green-400 bg-green-50/50"
                        : "border-gray-300/60 hover:border-gray-400/80"
                    } flex flex-col items-center justify-center cursor-pointer transition-all duration-300`}
                    onDragOver={handleDragOver}
                    onDrop={handleBackDrop}
                  >
                    <input
                      type="file"
                      accept="image/png"
                      onChange={handleBackFileChange}
                      className="hidden"
                      id="back-file-input"
                    />
                    <label
                      htmlFor="back-file-input"
                      className="w-full h-full flex flex-col items-center justify-center cursor-pointer"
                    >
                      <div className="text-center px-6">
                        {backImagePreview ? (
                          <div className="w-full h-full flex flex-col items-center justify-center">
                            <img
                              src={backImagePreview}
                              alt="Back preview"
                              className="max-w-full max-h-full object-contain rounded-lg"
                            />
                            <p className="text-sm text-green-500 mt-2 font-medium">
                              {backImage?.name}
                            </p>
                          </div>
                        ) : (
                          <>
                            <svg
                              className="w-12 h-12 mx-auto mb-3 text-gray-400"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                              />
                            </svg>
                            <h3 className="text-gray-800 mb-1">Back Side</h3>
                            <p className="text-sm text-gray-400">
                              Drop PNG image or click to upload
                            </p>
                          </>
                        )}
                      </div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Submit button */}
              <div className="flex justify-center">
                <button
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                  className={`px-10 py-3 rounded-xl transition-all duration-300 ${
                    canSubmit
                      ? "bg-black text-white hover:bg-gray-800"
                      : "bg-gray-200 text-gray-400 cursor-not-allowed"
                  }`}
                >
                  {isUploading ? "Generating..." : "Continue"}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
