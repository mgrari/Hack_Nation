"use client";

import { useEffect, useState } from "react";

const FULL_TEXT = "RealDoor";
const TYPE_MS = 110; // per character
const HOLD_MS = 6000; // pause after fully typed before re-animating

export function PageHeader() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count < FULL_TEXT.length) {
      const id = setTimeout(() => setCount((c) => c + 1), TYPE_MS);
      return () => clearTimeout(id);
    }
    // fully typed: hold, then restart the typing animation
    const id = setTimeout(() => setCount(0), HOLD_MS);
    return () => clearTimeout(id);
  }, [count]);

  return (
    <div className="flex items-center gap-2.5 mb-9">
      <div aria-hidden="true" className="relative size-[26px] shrink-0 rounded-[3px] border-2 border-ink">
        <div className="absolute left-1.5 top-1.5 h-3 w-2.5 border-r-2 border-ink" />
      </div>
      <div
        className="font-heading text-[17px] font-bold tracking-wide"
        aria-label={FULL_TEXT}
      >
        <span aria-hidden="true">{FULL_TEXT.slice(0, count)}</span>
      </div>
    </div>
  );
}
