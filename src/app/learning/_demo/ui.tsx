import type { ReactNode } from "react";
import type { Trace } from "@/lib/learning/demo";
import { STEPS, type Step } from "./shared";

/** A numbered step from the loop, as a small badge. */
export function StepBadge({ step }: { step: Step }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-cue-soft py-1 pl-1 pr-2.5 text-label font-medium text-cue-ink">
      <span className="flex size-5 items-center justify-center rounded-full bg-surface font-mono text-caption">
        {STEPS.indexOf(step) + 1}
      </span>
      {step}
    </span>
  );
}

export function Act({
  n,
  title,
  lede,
  steps,
  children,
}: {
  n: number;
  title: string;
  lede: string;
  steps: Step[];
  children: ReactNode;
}) {
  return (
    <section className="mt-20 sm:mt-28" aria-labelledby={`act-${n}`}>
      <div className="flex flex-wrap items-center gap-2">
        <p className="mr-1 text-label font-medium uppercase tracking-[0.08em] text-muted">Act {n}</p>
        {steps.map((s) => (
          <StepBadge key={s} step={s} />
        ))}
      </div>
      <h2
        id={`act-${n}`}
        className="mt-3 scroll-mt-8 text-heading-2-m font-semibold tracking-[-0.02em] sm:text-display-lg-m"
      >
        {title}
      </h2>
      <p className="mt-3 max-w-2xl text-body-lg-m text-muted sm:text-body-lg">{lede}</p>
      <div className="mt-6">{children}</div>
    </section>
  );
}

/** What Cue said, set apart in Cue's color. */
export function CueSays({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-card border border-cue/30 bg-cue-soft p-5">
      <p className="text-label font-semibold text-cue-ink">{label}</p>
      <div className="mt-2 text-body">{children}</div>
    </div>
  );
}

/** Where slow-down taps started at the beginning of each session. */
export function SlowDownShift({ first, second }: { first: Trace; second: Trace }) {
  return (
    <p className="text-body-sm text-muted">
      Slow-down point at the start of a session:{" "}
      <span className="whitespace-nowrap font-semibold tabular-nums text-text">
        {first.limit[0].wpm} → {second.limit[0].wpm}
      </span>{" "}
      words a minute
    </p>
  );
}

/**
 * What an act shows, large enough to read from across a room: one line, then each measure
 * before and after.
 */
export function Result({ title, rows }: { title: string; rows: { label: string; before: string; after: string }[] }) {
  return (
    <div className="rounded-card border-2 border-cue bg-surface p-5 sm:p-7">
      <p className="text-label font-semibold text-cue-ink">The result</p>
      <p className="mt-1 text-title-m font-semibold sm:text-heading-3">{title}</p>
      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        {rows.map((r) => (
          <div key={r.label}>
            <dt className="text-body-sm text-muted">{r.label}</dt>
            <dd className="mt-1 flex items-baseline gap-2 tabular-nums">
              <span className="text-heading-3-m text-muted sm:text-heading-3">{r.before}</span>
              <span aria-label="became" className="text-title text-cue-ink">
                →
              </span>
              <span className="text-display-lg-m font-semibold tracking-[-0.02em]">{r.after}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
