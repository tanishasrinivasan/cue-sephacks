"use client";

import { useId, useState, type KeyboardEvent, type PointerEvent } from "react";
import { limitAt, type Trace } from "@/lib/learning/demo";
import { useWidth } from "./hooks";

const H = 160;
const PAD = { left: 34, right: 8, top: 22, bottom: 22 };
/** A change of slow-down point mid-session worth pointing out, words a minute. */
const NOTABLE_SHIFT = 5;
/** Pace is read every 2 s; each reading is drawn as a column that wide. */
const STEP = 2;

const mmss = (t: number) => `${Math.floor(t / 60)}:${String(Math.round(t % 60)).padStart(2, "0")}`;

/**
 * A session's pace like a sleep-stage chart: a column in the pace color for every reading above
 * the slow-down point in force (rushing), the pace line over it, the slow-down point dashed in
 * Cue's color, and each tap on a strip along the top. Drawn up to `progress` of the session so it
 * can play out; with `rings`, each tap spreads a ring as playback reaches it, like the ring from
 * the motor. Drag across it, or use the arrow keys, to read any moment.
 */
export default function PaceChart({
  trace,
  domain,
  progress = 1,
  rings = false,
}: {
  trace: Trace;
  domain: [number, number];
  progress?: number;
  rings?: boolean;
}) {
  const [ref, width] = useWidth();
  const clip = useId();
  const [at, setAt] = useState<number | null>(null);
  const [lo, hi] = domain;
  const now = progress * trace.duration;
  const x = (t: number) => PAD.left + (t / trace.duration) * (width - PAD.left - PAD.right);
  const y = (wpm: number) => PAD.top + ((hi - wpm) / (hi - lo)) * (H - PAD.top - PAD.bottom);
  const line = (pts: { t: number; wpm: number }[]) => pts.map((p) => `${x(p.t)},${y(p.wpm)}`).join(" ");
  const ticks = [lo, (lo + hi) / 2, hi];
  const minutes = Array.from({ length: Math.floor(trace.duration / 60) + 1 }, (_, k) => k * 60);
  const total = trace.taps.filter((t) => t.behavior === "rushing").length;
  const taps = trace.taps.filter((t) => t.behavior === "rushing" && t.t <= now);
  const drawn = trace.pace.filter((p) => p.t <= now);
  // Without a learned pace, a session learns one after a minute of speech: the step in the line.
  const [, before, after] = trace.limit;
  const learned = after && Math.abs(after.wpm - before.wpm) >= NOTABLE_SHIFT && now >= after.t ? after : null;
  const head = progress > 0 && progress < 1 ? drawn.at(-1) : undefined;
  const runs: [number, number][] = [];
  for (const p of drawn) {
    if (p.wpm <= limitAt(trace, p.t)) continue;
    const last = runs.at(-1);
    if (last && p.t - last[1] <= STEP) last[1] = p.t;
    else runs.push([p.t, p.t]);
  }

  // The reading nearest the pointer or the keyboard's position.
  const read =
    at === null || !drawn.length ? null : drawn.reduce((a, b) => (Math.abs(b.t - at) < Math.abs(a.t - at) ? b : a));
  const rushingAt = read !== null && read.wpm > limitAt(trace, read.t);
  const pointTo = (e: PointerEvent<HTMLDivElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const t = ((e.clientX - box.left - PAD.left) / (width - PAD.left - PAD.right)) * trace.duration;
    setAt(Math.min(now, Math.max(0, t)));
  };
  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? 10 : STEP;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
      e.preventDefault();
      const from = at ?? (e.key === "ArrowRight" ? 0 : now);
      setAt(Math.min(now, Math.max(0, from + (e.key === "ArrowRight" ? step : -step))));
    } else if (e.key === "Escape") setAt(null);
  };
  const readout = read ? `${read.wpm} words a minute at ${mmss(read.t)}${rushingAt ? ", rushing" : ""}` : "";

  return (
    <div ref={ref} className="w-full">
      {width > 0 && (
        <div
          role="slider"
          tabIndex={0}
          aria-label={`Pace over ${mmss(trace.duration)}, with ${total} slow-down taps. Use the arrow keys to read a moment.`}
          aria-valuemin={0}
          aria-valuemax={Math.round(trace.duration)}
          aria-valuenow={Math.round(read?.t ?? 0)}
          aria-valuetext={readout || "No moment selected"}
          onPointerDown={pointTo}
          onPointerMove={(e) => (e.pointerType === "mouse" || e.buttons ? pointTo(e) : undefined)}
          onPointerLeave={(e) => e.pointerType === "mouse" && setAt(null)}
          onKeyDown={onKey}
          onBlur={() => setAt(null)}
          className="relative touch-pan-y select-none pt-9 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-cue"
        >
          {read && (
            <p
              aria-hidden
              className="pointer-events-none absolute top-0 -translate-x-1/2 whitespace-nowrap text-center leading-tight"
              style={{ left: Math.min(width - 44, Math.max(44, x(read.t))) }}
            >
              <span className="text-body-sm font-semibold tabular-nums">{read.wpm} wpm</span>
              <span className="block text-caption text-muted">
                {mmss(read.t)}
                {rushingAt ? " · rushing" : ""}
              </span>
            </p>
          )}
          <svg width={width} height={H} aria-hidden className="block overflow-visible text-caption">
            <defs>
              <clipPath id={clip}>
                <rect x={0} y={0} width={x(now)} height={H} />
              </clipPath>
            </defs>
            {ticks.map((v) => (
              <g key={v}>
                <line x1={PAD.left} x2={width - PAD.right} y1={y(v)} y2={y(v)} stroke="var(--line)" strokeWidth={1} />
                <text x={PAD.left - 6} y={y(v)} dy="0.32em" textAnchor="end" fill="var(--muted)">
                  {Math.round(v)}
                </text>
              </g>
            ))}
            {minutes.map((t) => (
              <text key={t} x={x(t)} y={H - 4} textAnchor={t === 0 ? "start" : "middle"} fill="var(--muted)">
                {mmss(t)}
              </text>
            ))}
            {/* Rushing: one block for each run of readings above the slow-down point in force. */}
            {runs.map(([from, to]) => (
              <rect
                key={from}
                x={x(from - STEP / 2)}
                y={PAD.top}
                width={x(to + STEP / 2) - x(from - STEP / 2)}
                height={H - PAD.top - PAD.bottom}
                rx={3}
                fill="var(--area-pace)"
                fillOpacity={0.45}
              />
            ))}
            {/* Taps sit on a strip along the top, at the moment they were felt. */}
            {taps.map((tap) => (
              <g key={tap.t}>
                <line
                  x1={x(tap.t)}
                  x2={x(tap.t)}
                  y1={8}
                  y2={H - PAD.bottom}
                  stroke="var(--cue)"
                  strokeOpacity={0.5}
                  strokeWidth={1}
                />
                <circle cx={x(tap.t)} cy={8} r={5} fill="var(--cue)" />
                {rings && (
                  <circle
                    className="tap-ring"
                    cx={x(tap.t)}
                    cy={8}
                    r={5}
                    fill="none"
                    stroke="var(--cue)"
                    strokeWidth={1.5}
                  />
                )}
              </g>
            ))}
            <g clipPath={`url(#${clip})`}>
              <polyline
                points={line(trace.limit)}
                fill="none"
                stroke="var(--cue)"
                strokeWidth={1.5}
                strokeDasharray="5 4"
              />
              <polyline
                points={line(trace.pace)}
                fill="none"
                stroke="var(--text)"
                strokeWidth={2}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </g>
            {learned && (
              <text
                x={x(learned.t) + 6}
                y={y(Math.max(learned.wpm, before.wpm)) - 6}
                fill="var(--cue-ink)"
                fontWeight={600}
              >
                Cue learns their pace
              </text>
            )}
            {head && (
              <circle
                cx={x(head.t)}
                cy={y(head.wpm)}
                r={4.5}
                fill="var(--text)"
                stroke="var(--surface)"
                strokeWidth={2}
              />
            )}
            {read && (
              <g>
                <line
                  x1={x(read.t)}
                  x2={x(read.t)}
                  y1={PAD.top - 6}
                  y2={H - PAD.bottom}
                  stroke="var(--text)"
                  strokeWidth={1.5}
                />
                <path d={`M ${x(read.t) - 6} 0 h 12 l -6 7 z`} fill="var(--text)" />
                <circle
                  cx={x(read.t)}
                  cy={y(read.wpm)}
                  r={4}
                  fill="var(--text)"
                  stroke="var(--surface)"
                  strokeWidth={2}
                />
              </g>
            )}
          </svg>
        </div>
      )}
    </div>
  );
}

export function PaceLegend() {
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1 text-caption text-muted">
      <li className="flex items-center gap-1.5">
        <span className="h-0.5 w-4 rounded-full bg-text" /> Pace, words a minute
      </li>
      <li className="flex items-center gap-1.5">
        <span className="h-3 w-2.5 rounded-sm bg-[var(--area-pace)]/45" /> Rushing
      </li>
      <li className="flex items-center gap-1.5">
        <span className="w-4 border-t-[1.5px] border-dashed border-cue" /> Slow-down point
      </li>
      <li className="flex items-center gap-1.5">
        <span className="size-2.5 rounded-full bg-cue" /> Tap
      </li>
      <li>Drag across a chart to read any moment</li>
    </ul>
  );
}
