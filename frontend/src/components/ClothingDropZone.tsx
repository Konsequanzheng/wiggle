"use client";

import { motion } from "motion/react";
import { Shirt } from "lucide-react";
import { SweatshirtIcon } from "./icons/SweatshirtIcon";
import { SockIcon } from "./icons/SockIcon";

interface ClothingDropZoneProps {
  type: "tshirt" | "sweater" | "socks";
  label: string;
  index: number;
  onClick?: () => void;
}

export function ClothingDropZone({
  type,
  label,
  index,
  onClick,
}: ClothingDropZoneProps) {
  const renderIcon = () => {
    const className =
      "fill-gray-800/30 stroke-none transition-all duration-500 ease-out group-hover:scale-[1.2]";

    switch (type) {
      case "tshirt":
        return <Shirt size={160} strokeWidth={0} className={className} />;
      case "sweater":
        return <SweatshirtIcon size={160} className={className} />;
      case "socks":
        return <SockIcon size={160} className={className} />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{
        duration: 0.6,
        delay: index * 0.15,
        ease: [0.6, 0.05, 0.01, 0.9],
      }}
      className="flex flex-col items-center"
    >
      <div
        className="w-64 h-80 rounded-[2rem] border-2 border-gray-300/60 flex flex-col items-center justify-center gap-6 hover:border-gray-400/80 transition-colors duration-300 cursor-pointer group overflow-hidden"
        onClick={onClick}
      >
        <div>{renderIcon()}</div>
        <div className="text-center px-6">
          <h3 className="text-gray-800">{label}</h3>
        </div>
      </div>
    </motion.div>
  );
}
