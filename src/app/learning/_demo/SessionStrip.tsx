"use client";

import { useState } from "react";
import type { Strategy } from "@/lib/cue/plan";
import { STRATEGY_TEXT } from "@/lib/learning/coaching";
import type { ManySessions } from "@/lib/learning/demo";
import { RushRing } from "./SessionSummary";

const capitalize = (t: string) => t[0].toUpperCase() + t.slice(1);

/**
 * Every session of the run as a small ring of time spent rushing, like a week of sleep scores;
 * a gold center marks the new way of tapping. Choose one to see what happened in it.
 */
export default function SessionStrip({ run, shown }: { run: ManySessions; shown: number }) {
  const [chosen, setChosen] = useState<number | null>(null);
  const visible = run.sessions.filter((s) => s.index <= shown);
  const s = visible.find((x) => x.index === chosen) ?? visible.at(-1);
  if (!s) return null;
  return (
    <div>
      <div className="grid grid-cols-5 gap-1 sm:grid-cols-10" role="group" aria-label="Sessions">
        {visible.map((x) => (
          <button
            key={x.index}
            type="button"
            aria-pressed={x.index === s.index}
            aria-label={`Session ${x.index}`}
            onClick={() => setChosen(x.index)}
            className={`flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-xl py-1 transition-colors focus-visible:outline-2 focus-visible:outline-cue ${x.index === s.index ? "bg-surface-2" : "hover:bg-surface-2/60"}`}
          >
            <span className="relative">
              <RushRing share={x.rushShare ?? 0} size={34} stroke={4} />
              {x.strategy === "sustained" && (
                <span aria-hidden className="absolute inset-0 m-auto size-2.5 rounded-full bg-cue" />
              )}
            </span>
            <span className="text-caption tabular-nums text-muted">{x.index}</span>
          </button>
        ))}
      </div>

      <div className="mt-3 rounded-2xl bg-surface-2 p-4" aria-live="polite">
        <p className="text-body-sm font-semibold">
          Session {s.index}{" "}
          <span className="font-normal text-muted">
            · {capitalize(STRATEGY_TEXT[s.strategy as Strategy] ?? s.strategy)}
          </span>
        </p>
        <dl className="mt-2 grid grid-cols-3 gap-2">
          {[
            ["Taps", s.rushingTaps, ""],
            ["Held back", s.rushingHoldouts, ""],
            ["Rushing", s.rushShare === null ? "–" : Math.round(s.rushShare * 100), s.rushShare === null ? "" : "%"],
          ].map(([label, value, unit]) => (
            <div key={label}>
              <dt className="text-caption text-muted">{label}</dt>
              <dd className="text-title-m font-semibold tabular-nums sm:text-title">
                {value}
                <span className="text-caption font-normal text-muted">{unit}</span>
              </dd>
            </div>
          ))}
        </dl>
        {s.update && (
          <p className="mt-3 text-body-sm">
            <span className="font-medium text-cue-ink">{s.update.label}: </span>
            {s.update.text}
          </p>
        )}
      </div>
    </div>
  );
}
