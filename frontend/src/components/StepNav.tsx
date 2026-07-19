import Link from "next/link";

const STEPS = [
  { href: "/profile", num: 1, label: "PROFILE" },
  { href: "/understand", num: 2, label: "UNDERSTAND" },
  { href: "/prepare", num: 3, label: "PREPARE" },
  { href: "/discover", num: 4, label: "DISCOVER" },
] as const;

export function StepNav({ current }: { current: (typeof STEPS)[number]["href"] }) {
  const currentIndex = STEPS.findIndex((s) => s.href === current);

  return (
    <nav aria-label="Application progress" className="flex items-center mb-2">
      {STEPS.map((step, i) => {
        const isCurrent = i === currentIndex;
        return (
          <div key={step.href} className={i === STEPS.length - 1 ? "flex items-center" : "flex flex-1 items-center"}>
            <Link
              href={step.href}
              aria-current={isCurrent ? "step" : undefined}
              className="flex items-center gap-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring rounded-sm"
            >
              <span
                className={`flex size-6 shrink-0 items-center justify-center rounded-full font-heading text-[11px] font-bold ${
                  isCurrent ? "bg-ink text-paper border-2 border-ink" : "bg-transparent text-ink/40 border-2 border-ink/30"
                }`}
              >
                {step.num}
              </span>
              <span
                className={`sr-only font-heading text-xs font-semibold tracking-wide sm:not-sr-only ${isCurrent ? "text-ink" : "text-ink/40"}`}
              >
                {step.label}
              </span>
            </Link>
            {i < STEPS.length - 1 && <div className="mx-1.5 h-px flex-1 bg-ink/[0.18] sm:mx-3.5" aria-hidden="true" />}
          </div>
        );
      })}
    </nav>
  );
}
