"use client";

import { useEffect, useState } from "react";

const FULL_TEXT = "RealDoor";

export function PageHeader() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (count >= FULL_TEXT.length) return;
    const id = setTimeout(() => setCount((c) => c + 1), 110);
    return () => clearTimeout(id);
  }, [count]);

  const done = count >= FULL_TEXT.length;

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
        <span
          aria-hidden="true"
          className={`ml-0.5 inline-block w-[2px] -translate-y-[1px] align-middle bg-ink ${done ? "animate-caret-blink" : ""}`}
          style={{ height: "1em" }}
        />
      </div>
    </div>
  );
}
