interface SweatshirtIconProps {
  size?: number;
  className?: string;
}

export function SweatshirtIcon({
  size = 160,
  className = "",
}: SweatshirtIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Body */}
      <path d="M8 9h8v11H8z" />
      {/* Left sleeve */}
      <path d="M4 9l4 1v4l-4 1V9z" />
      {/* Right sleeve */}
      <path d="M20 9l-4 1v4l4 1V9z" />
      {/* Neckline */}
      <path d="M9 6h6v3H9z" />
      {/* Collar/shoulders */}
      <path d="M8 8l-4 1V9l4-1zM16 8l4 1V9l-4-1z" />
    </svg>
  );
}
