export function WormLogo() {
  return (
    <svg width="20" height="8" viewBox="0 0 20 8" className="inline-block mr-2">
      <circle cx="3" cy="4" r="2.5" fill="currentColor" />
      <circle cx="7" cy="4" r="2.5" fill="currentColor" />
      <circle cx="11" cy="4" r="2.5" fill="currentColor" />
      <circle cx="15" cy="4" r="2.5" fill="currentColor" />
      {/* Eyes on the first circle */}
      <circle cx="4.2" cy="3.2" r="0.5" fill="white" />
      <circle cx="4.2" cy="4.8" r="0.5" fill="white" />
    </svg>
  );
}
