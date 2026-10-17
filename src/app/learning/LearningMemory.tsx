"use client";

import Link from "next/link";
import { activeAdaptations, STAGE_LABEL, stageOf } from "@/lib/learning/coaching";
import type { Profile } from "@/lib/learning/types";
import type { Learning } from "./useLearning";

/*
 * "Cue learns you": the learning loop on the main screen, so it's visible from the first visit.
 * Each step is lit from the profile, never for effect. The "after N sessions" timings come from
 * docs/continuous-learning.md (pace from one session, a focus from two, patterns from three,
 * held-back taps from four).
 */

const STEPS: { title: string; when: string; done: (p: Profile) => boolean }[] = [
  {
    title: "Learns your pace",
    when: "after your first session",
    done: (p) => Object.values(p.plan.modes).some((m) => m.paceBaselineSps !== null),
  },
  { title: "Picks your focus", when: "after 2 sessions", done: (p) => p.focus.current !== null },
  {
    title: "Finds your patterns",
    when: "after 3 sessions",
    done: (p) => p.insights.some((i) => i.status !== "rejected" && !i.kind.startsWith("coaching:")),
  },
  {
    title: "Tests its own taps",
    when: "from session 4",
    done: (p) => p.interventions.some((r) => r.holdout) || p.experimentsLog.length > 0,
  },
];

const plural = (n: number, one: string) => `${n} ${one}${n === 1 ? "" : "s"}`;

const LINK =
  "rounded-full px-4 py-2 text-label font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cue";

export function LearningMemory({ learning }: { learning: Learning }) {
  const p = learning.profile;
  const sandbox = learning.view === "sandbox";
  const sessions = p.sessions.length;
  const changes = activeAdaptations(p).length;
  // A new update has its own card above; this repeats the last one already read.
  const latest = p.updates.findLast((u) => u.status === "seen");
  const next = STEPS.findIndex((s) => !s.done(p));

  return (
    <section
      aria-labelledby="cue-learns-you"
      className="mt-8 w-full rounded-[28px] border border-cue/30 bg-surface p-6 text-left sm:p-7"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2
          id="cue-learns-you"
          className="flex items-center gap-2 text-caption font-medium uppercase tracking-[0.08em] text-cue-ink"
        >
          <span aria-hidden className="size-2 rounded-full bg-cue" />
          Cue learns you
          {sandbox && <span className="font-normal normal-case tracking-normal text-muted">· practice sandbox</span>}
        </h2>
        <Link href="/learning" className="text-label text-muted underline-offset-4 hover:text-text hover:underline">
          How it works →
        </Link>
      </div>

      <p className="mt-3 font-display text-heading-3-m font-semibold tracking-[-0.015em] sm:text-heading-3">
        {sessions ? STAGE_LABEL[stageOf(p)] : "Cue hasn’t heard you yet"}
      </p>
      <p className="mt-1 text-body text-muted">
        {sessions
          ? `Learned from ${plural(sessions, sandbox ? "simulated session" : "session")} · ${plural(changes, "change")} to how it coaches you`
          : "Every session teaches it something, and the next one is coached differently because of it."}
      </p>

      <ol className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {STEPS.map((s, k) => {
          const done = s.done(p);
          return (
            <li
              key={s.title}
              className={`rounded-2xl border p-3 ${done ? "border-cue bg-cue-soft" : k === next ? "border-line" : "border-line opacity-60"}`}
            >
              <span
                aria-hidden
                className={`flex size-6 items-center justify-center rounded-full text-caption font-semibold ${done ? "bg-cue text-on-cue" : "bg-surface-2 text-muted"}`}
              >
                {done ? "✓" : k + 1}
              </span>
              <p className="mt-2 text-body-sm font-semibold">{s.title}</p>
              <p className="text-caption text-muted">
                <span className="sr-only">{done ? "Done. " : "Not yet. "}</span>
                {s.when}
              </p>
            </li>
          );
        })}
      </ol>

      {latest && (
        <p className="mt-4 line-clamp-2 text-body-sm">
          <span className="font-medium text-cue-ink">{latest.label}: </span>
          {latest.text}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {sandbox ? (
          <>
            <button
              type="button"
              onClick={() => learning.simulate(learning.speakers.burstyRusher, 5)}
              className={`${LINK} bg-text text-bg`}
            >
              5 more simulated sessions
            </button>
            <button
              type="button"
              onClick={() => learning.setView("real")}
              className={`${LINK} border border-line hover:border-text`}
            >
              Back to your memory
            </button>
          </>
        ) : (
          sessions < 4 && (
            <button
              type="button"
              onClick={() => learning.simulate(learning.speakers.burstyRusher, 5)}
              className={`${LINK} bg-text text-bg`}
            >
              Watch Cue learn: 5 simulated sessions
            </button>
          )
        )}
        <Link href="/learning" className={`${LINK} border border-line hover:border-text`}>
          See the three stories
        </Link>
      </div>
      {!sandbox && sessions < 4 && (
        <p className="mt-2 text-caption text-muted">
          Simulated sessions go to a separate practice memory, so they never teach Cue about you.
        </p>
      )}
    </section>
  );
}
