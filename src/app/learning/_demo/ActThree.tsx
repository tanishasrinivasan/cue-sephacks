"use client";

import { useState } from "react";
import { experimentStory, type ManySessions } from "@/lib/learning/demo";
import SessionStrip from "./SessionStrip";
import TapsChart, { TapsLegend } from "./TapsChart";
import { useTimeline } from "./hooks";
import { ARRIVE, BUTTON, CARD } from "./shared";
import Quote from "./Quote";
import { Act, Result } from "./ui";

/** Each session takes this long to appear, in milliseconds. */
const PER_SESSION = 120;
const SESSIONS = 20;

export default function ActThree() {
  const [run, setRun] = useState<ManySessions | null>(null);
  const [busy, setBusy] = useState(false);
  const [elapsed, play] = useTimeline(SESSIONS * PER_SESSION);

  function start() {
    setBusy(true);
    // Let the button show it's working before twenty sessions run on the main thread.
    window.setTimeout(() => {
      setRun(experimentStory());
      setBusy(false);
      play();
    }, 30);
  }

  const shown = Math.floor(elapsed / PER_SESSION) + 1;
  const ex = run?.experiment;
  const marks = run && ex ? [run.sessions[ex.started - 1], run.sessions[ex.settled - 1]] : [];
  const steps = ex
    ? [
        {
          at: ex.started - 1,
          when: `Sessions 1–${ex.started}`,
          title: "Checked whether its taps help",
          quote: marks[0].update?.text,
        },
        { at: ex.started, when: `Sessions ${ex.started + 1}–${ex.settled}`, title: "Tried a sparser way of tapping" },
        { at: ex.settled, when: `From session ${ex.settled + 1}`, title: "Kept it", quote: marks[1].update?.text },
      ]
    : [];

  return (
    <Act
      n={3}
      title="Cue tests itself"
      steps={["Evaluate", "Improve"]}
      lede="Cue holds back some taps at random to check its taps really help. Run 20 sessions and watch it test, try something new, and decide."
    >
      <button type="button" className={BUTTON} onClick={start} disabled={busy}>
        <span aria-hidden>▶</span> {busy ? "Running 20 sessions…" : run ? "Run again" : "Run 20 sessions"}
      </button>
      {run && ex && (
        <div
          className="mt-6 flex max-w-3xl flex-col gap-3 [--old-strategy:var(--neutral)] dark:[--old-strategy:#7d7871]"
          aria-live="polite"
        >
          <div className={CARD}>
            <p className="text-label font-semibold">Slow-down taps, session by session</p>
            <div className="mt-4">
              <TapsChart run={run} started={ex.started} adopted={ex.settled} shown={shown} />
            </div>
          </div>
          <TapsLegend />
          {/* What Cue did, in three steps, each appearing as the run reaches it. */}
          <ol className="grid gap-3 sm:grid-cols-3">
            {steps.map((st, k) =>
              shown > st.at ? (
                <li key={st.title} className={`${CARD} ${ARRIVE}`}>
                  <span className="flex size-7 items-center justify-center rounded-full bg-cue text-label font-semibold text-on-cue">
                    {k + 1}
                  </span>
                  <p className="mt-2 text-body-sm text-muted">{st.when}</p>
                  <p className="text-title-m font-semibold">{st.title}</p>
                  {st.quote && <Quote text={st.quote} />}
                </li>
              ) : (
                <li
                  key={st.title}
                  aria-hidden
                  className="hidden rounded-card border border-dashed border-line sm:block"
                />
              ),
            )}
          </ol>
          {shown >= SESSIONS && run.before && run.after && (
            <div className={ARRIVE}>
              <Result
                title="Cue kept the way of tapping that worked just as well with less."
                rows={[
                  {
                    label: "Taps a session",
                    before: run.before.tapsPerSession.toFixed(1),
                    after: run.after.tapsPerSession.toFixed(1),
                  },
                  {
                    label: "Time rushing",
                    before: `${Math.round(run.before.rushShare * 100)}%`,
                    after: `${Math.round(run.after.rushShare * 100)}%`,
                  },
                ]}
              />
            </div>
          )}
          {shown >= SESSIONS && (
            <details className={`${CARD} group`}>
              <summary className="cursor-pointer list-none text-label font-semibold focus-visible:outline-2 focus-visible:outline-cue">
                <span className="mr-1 inline-block transition-transform group-open:rotate-90" aria-hidden>
                  ›
                </span>
                Look inside each session
              </summary>
              <div className="mt-3">
                <SessionStrip run={run} shown={shown} />
              </div>
            </details>
          )}
        </div>
      )}
    </Act>
  );
}
