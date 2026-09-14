"use client";

/**
 * The application form's one deliberate moment of motion (spec section 7:
 * "Motion: one place only, the moment a section appears or disappears in the
 * application form because the basket changed"). A CSS grid-rows transition
 * rather than mount/unmount, so the section still exists in the DOM while it
 * collapses instead of vanishing instantly. Respects prefers-reduced-motion
 * via the site-wide rule in app/globals.css, which zeroes every transition
 * duration.
 */
export function AnimatedSection({ open, children }: { open: boolean; children: React.ReactNode }) {
  return (
    <div
      className="grid transition-[grid-template-rows] duration-300 ease-out motion-reduce:transition-none"
      style={{ gridTemplateRows: open ? "1fr" : "0fr" }}
      aria-hidden={!open}
      // Collapsed content stays in the DOM so it can animate shut, but must
      // not be reachable by keyboard or a screen reader while it is — plain
      // aria-hidden doesn't remove focusability on its own.
      inert={!open || undefined}
    >
      <div className="overflow-hidden">{children}</div>
    </div>
  );
}
