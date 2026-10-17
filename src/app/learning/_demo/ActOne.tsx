"use client";

import { useState } from "react";
import { quickTalkerStory, type TwoSessions } from "@/lib/learning/demo";
import PaceChart, { PaceLegend } from "./PaceChart";
import SessionSummary from "./SessionSummary";
import { useTimeline } from "./hooks";
import { ARRIVE, BUTTON, CARD, paceDomain, span } from "./shared";
import { Act, CueSays, SlowDownShift } from "./ui";

/** Play, in milliseconds: session 1 plays out, Cue updates, then the same script again. */
const T = { first: [0, 2600], update: 2900, second: [3400, 2600] } as const;
const TOTAL = T.second[0] + T.second[1];

export default function ActOne() {
  const [story, setStory] = useState<TwoSessions | null>(null);
  const [elapsed, play] = useTimeline(TOTAL);

  function start() {
    setStory(quickTalkerStory());
    play();
  }

  return (
    <Act
      n={1}
      title="Same speech, different coaching"
      steps={["Remember", "Adapt"]}
      lede="A naturally quick talker, fast but steady, gives the same speech twice. In session 1 Cue judges them against a standard pace; by session 2 it has learned theirs."
    >
      <button type="button" className={BUTTON} onClick={start}>
        <span aria-hidden>▶</span> {story ? "Play again" : "Play"}
      </button>
      {story && <Story story={story} elapsed={elapsed} />}
    </Act>
  );
}

function Story({ story, elapsed }: { story: TwoSessions; elapsed: number }) {
  const domain = paceDomain(story.first, story.second);
  const p1 = span(elapsed, ...T.first);
  const p2 = span(elapsed, ...T.second);
  return (
    <div className="mt-6 flex max-w-3xl flex-col gap-3" aria-live="polite">
      <div className={CARD}>
        <p className="text-label font-semibold">
          Session 1 <span className="font-normal text-muted">· Cue doesn&rsquo;t know them yet</span>
        </p>
        <div className="mt-4">
          <SessionSummary trace={story.first} progress={p1} />
        </div>
        <div className="mt-4">
          <PaceChart trace={story.first} domain={domain} progress={p1} rings />
        </div>
      </div>
      <PaceLegend />
      {elapsed >= T.update && (
        <div className={ARRIVE}>
          <CueSays label={story.update?.label ?? "Cue updated"}>
            <p>{story.update?.text}</p>
            <div className="mt-2">
              <SlowDownShift first={story.first} second={story.second} />
            </div>
          </CueSays>
        </div>
      )}
      {elapsed >= T.second[0] && (
        <div className={`${CARD} ${ARRIVE}`}>
          <p className="text-label font-semibold">
            Session 2 <span className="font-normal text-muted">· same script, and Cue knows their pace</span>
          </p>
          <div className="mt-4">
            <SessionSummary trace={story.second} progress={p2} />
          </div>
          <div className="mt-4">
            <PaceChart trace={story.second} domain={domain} progress={p2} rings />
          </div>
        </div>
      )}
    </div>
  );
}
