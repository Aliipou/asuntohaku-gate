import type { OutcomeValue } from "@/lib/api";

/**
 * The three outcome states, distinguishable in greyscale and by shape, not
 * colour alone (spec section 7, design direction). Colour is reinforcement:
 * a screen reader or a printed page still gets a different shape and label
 * for each state.
 */
const SHAPES: Record<OutcomeValue, { path: string; className: string }> = {
  kelpoinen: {
    // A check inside a circle.
    path: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm-1.2 14.4-4-4 1.4-1.4 2.6 2.6 6-6 1.4 1.4-7.4 7.4Z",
    className: "text-emerald-700",
  },
  puuttuvat_tiedot: {
    // A question mark inside a triangle.
    path: "M12 3 2 20h20L12 3Zm0 5.5c1 0 1.75.7 1.75 1.65 0 .7-.35 1.1-.95 1.6-.55.45-.8.75-.8 1.35v.3h-1.3v-.4c0-.95.4-1.45 1.05-1.95.5-.4.7-.6.7-.95 0-.4-.35-.7-.85-.7-.55 0-.9.35-.95.85l-1.35-.15c.1-1.15 1-1.9 2.4-1.9Zm-.75 6.7h1.4v1.4h-1.4v-1.4Z",
    className: "text-amber-700",
  },
  ei_kelpoinen: {
    // An X inside a rounded square.
    path: "M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm2.1 3.5-1.6 1.6L10.4 12l-4.9 3.9 1.6 1.6L12 13.6l4.9 3.9 1.6-1.6L13.6 12l4.9-3.9-1.6-1.6L12 10.4 7.1 6.5Z",
    className: "text-rose-700",
  },
};

export function OutcomeBadge({ outcome, label }: { outcome: OutcomeValue; label: string }) {
  const shape = SHAPES[outcome];
  return (
    <span className={`inline-flex items-center gap-1.5 font-medium ${shape.className}`}>
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
        <path d={shape.path} />
      </svg>
      {label}
    </span>
  );
}
