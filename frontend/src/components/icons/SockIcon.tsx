interface SockIconProps {
  size?: number;
  className?: string;
}

export function SockIcon({ size = 160, className = "" }: SockIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Ankle part */}
      <path d="M10 4h4v6h-4z" />
      {/* Foot part */}
      <path d="M8 10h6v4h2v4H8v-6z" />
      {/* Toe curve */}
      <path d="M8 14h8c0 2.2-1.8 4-4 4s-4-1.8-4-4z" />
    </svg>
  );
}
