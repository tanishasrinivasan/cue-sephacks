import { limitAt, rushingShare, typicalPace, type Trace } from "@/lib/learning/demo";
import { rushingTaps } from "./shared";

/** A ring of the share of time spent rushing, in the pace color, filling as a session plays. */
export function RushRing({ share, size = 112, stroke = 11 }: { share: number; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden className="shrink-0 -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={stroke} />
      {share > 0 && (
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--area-pace)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - share)}
        />
      )}
    </svg>
  );
}

function Tile({ label, value, unit, tick }: { label: string; value: number; unit?: string; tick?: boolean }) {
  return (
    <div className="rounded-2xl bg-surface-2 p-3">
      <dt className="text-caption text-muted">{label}</dt>
      <dd className="mt-1 flex items-baseline gap-1">
        {/* Keyed by the value, so each new tap ticks it once. */}
        <span
          key={tick ? value : undefined}
          className={`inline-block text-heading-3-m font-semibold tabular-nums sm:text-heading-3 ${tick ? "tap-tick text-cue-ink" : ""}`}
        >
          {value}
        </span>
        {unit && <span className="text-caption text-muted">{unit}</span>}
      </dd>
    </div>
  );
}

/**
 * A session at a glance, up to `progress` of it: time spent rushing as a ring, then slow-down
 * taps, the slow-down point in force (it steps when Cue learns a pace mid-session) and the
 * session's typical pace.
 */
export default function SessionSummary({ trace, progress = 1 }: { trace: Trace; progress?: number }) {
  const now = progress * trace.duration;
  const share = rushingShare(trace, now) ?? 0;
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="relative self-center">
        <RushRing share={share} />
        <p className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-heading-3-m font-semibold tabular-nums sm:text-heading-3">
            {Math.round(share * 100)}%
          </span>
          <span className="text-caption text-muted">rushing</span>
        </p>
      </div>
      <dl className="grid flex-1 grid-cols-3 gap-2">
        <Tile label="Taps" value={rushingTaps(trace, progress)} tick />
        <Tile label="Slow-down at" value={limitAt(trace, now)} unit="wpm" />
        <Tile label="Typical pace" value={typicalPace(trace)} unit="wpm" />
      </dl>
    </div>
  );
}
