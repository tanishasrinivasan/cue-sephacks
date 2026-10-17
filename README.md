# Cue

**A speech coach that sits behind your ear, taps you when a speaking habit gets in your way, and learns how you speak.**

SEPHacks 2026 · Tracks: Continual Learning (Grand Tech), Design, Scale, Agents

- **Live app:** [add link] (the learning views are at `/learning`)
- **Demo video:** [add link]
- **Team:** Tanisha Srinivasan, Sam Williamson, [add teammates]

## What we built at SEPHacks

Cue existed before this hackathon. The live coaching (speech recognition, detectors, the decision engine and the three cues) was already working. **At SEPHacks we built continuous learning:** everything in `src/lib/learning/` and `src/app/learning/`, the coaching plan the live engine now reads (`src/lib/cue/plan.ts`), and the changes to `engine.ts` and `session.ts` that use it. That's about 5,600 lines and 32 new tests.

## The problem

Most people get almost no help with how they speak, and the help that exists doesn't fit how speaking is changing. Speaking coaches are expensive and only see you once a week. Apps record you and hand you a report afterwards, when the moment is gone. Tools that do coach live use the same fixed rules for everyone. A naturally fast talker gets told to slow down all the time, so they stop listening, or take the device off.

How someone speaks also keeps changing: new roles, new audiences, a new habit you pick up, an old one you've fixed. A coach that never updates falls behind its own user within a few weeks.

## The solution

Cue is a small device that sits behind your ear. While you talk, it listens for habits like a run of filler words, rushing, going too long without a pause, a turn that runs too long, or speaking too quietly. When one is getting in your way, it gives you a private tap. Nobody else notices.

Live, Cue only ever asks for three things, and each has its own feel:

| Cue       | Tap              | When                                       |
| --------- | ---------------- | ------------------------------------------ |
| Pause     | One short tap    | No pause for a while, a long turn, fillers |
| Slow down | Three slow steps | Rushing                                    |
| Speak up  | One long push    | Too quiet                                  |

What makes Cue different is that it **learns each wearer across sessions**. It works out your normal pace, which habits are real problems for you, and whether its own taps are actually helping. Then it changes how it coaches you next time.

The hardware is in progress: the dev board is being made now. Until it arrives, the web app shows each tap on a 3D model of the device, and can play the cues as quiet sounds in AirPods so people can try Cue for real.

## How it works

```
 Mic ──▶ Deepgram Flux (live speech to text, keeps "um" and "uh")
     ──▶ Silero voice detection (real pauses, in the browser)
     ──▶ Detectors: fillers, "like" classifier, pace, pauses, turn length, volume
     ──▶ Decision engine: "would a tap help right now?" ──▶ tap
     ──▶ Session ends ──▶ numbers-only summary ──▶ learning loop ──▶ next session's coaching plan
```

**AI component.**

- Live speech recognition with Deepgram Flux.
- Voice activity detection with Silero, run in the browser with ONNX Runtime.
- Part-of-speech tagging with compromise. It tells a filler "like" ("I like went") from a real one ("I like tofu").
- A statistical learning loop that adapts to each person: sign tests, binomial tests and Bayesian (Beta) estimates. It doesn't use an LLM, and that's on purpose. A few sessions per person isn't enough data to train a model, and every change Cue makes has to be explainable in one sentence.

**Stack.**

- App: Next.js 16, React 19 and TypeScript, deployed on Vercel.
- 3D device model: three.js.
- Cue sounds: Web Audio.
- Tests: Vitest, with 309 tests.
- Hardware: a KiCad dev board with a Bluetooth module and a DRV2605L haptic driver.

## Continual Learning track (Grand Tech)

**What it is.** Continuous learning means Cue gets to know each wearer across sessions and changes how it coaches them. Without it, Cue is a fixed set of rules: speak faster than a standard pace and you get a slow-down tap, the same for everyone. With it, every session ends with Cue recording a summary in numbers only: pace, fillers, pauses and turns, with no audio and no transcript. It looks for patterns that hold across sessions, and only trusts one after a statistical check over several sessions, not a hunch from one.

What it learns goes into a personal profile stored in your browser. The next session's coaching plan is rebuilt from that profile, and the live engine reads it. For example, a naturally fast talker stops getting slow-down taps once Cue has learned their own pace. Someone who says the taps are "too many" gets fewer, starting with the very next session.

```
OBSERVE ─▶ DISCOVER ─▶ REMEMBER ─▶ ADAPT ─▶ EVALUATE ─▶ IMPROVE ─┐
   ▲                                                             │
   └──────────── next session is coached with the new plan ◀─────┘
```

**How it checks itself.** Cue doesn't assume its taps work. It holds back about one tap in five at random, then compares what happens after a tap with what happens after a held-back one. People often slow down on their own anyway, so "they slowed down after the tap" proves nothing.

If taps aren't beating the held-back ones, Cue alternates between its current way of tapping and an alternative for a few sessions. It keeps whichever does as well with less interruption. It also steps back where you've improved, and picks a new focus once you've made progress on the current one.

Every change comes with a plain-language "Cue updated" note saying what it changed and why, and you can correct or undo any of it.

**Does it get better the more people use it?** Yes. For each person, every session adds to their profile, so Cue coaches you better in week three than in week one. A fast talker stops getting taps for their normal pace. Someone who pauses on purpose stops being flagged for it. If filler words are your real problem, Cue focuses there.

Across people, the next step is opt-in sharing of session numbers (never audio). That would let new wearers start from better thresholds instead of fixed rules.

**Is learning core, or an add-on?** It's core. Without learning, Cue is an alarm with a fixed setting, and people tune it out. Learning decides when Cue taps, how often, and what it coaches on next, and it checks whether the taps work at all.

**Could a product that never learns solve this?** No, for three reasons:

- **People speak too differently.** A pace that's rushed for one person is normal for another, and someone with an accent or a stutter would get constant false taps from a fixed rule.
- **A fixed product can't tell whether its taps help.** Cue can, because it compares taps against held-back ones.
- **A fixed product doesn't notice progress.** It keeps tapping you for things you've already fixed. Cue steps back and moves to a new focus.

**Does it grow more valuable as it scales?** For each person, every session makes the profile sharper, and the coaching gets quieter and more precise. Across users, shared numbers would give new wearers better starting points. They would also show which ways of tapping work for which kinds of speakers, so the alternatives Cue tests get better over time.

A coach with many clients could see each client's progress without hearing a single recording.

**Why it matters.** A coach that taps you for things that aren't problems for you gets ignored, or taken off. Coaching only works if you trust it. You trust it when it fits how you actually speak and visibly responds to what you tell it. Continuous learning is what turns Cue from a generic alarm into a personal coach. It also keeps Cue honest: Cue measures whether its own taps help instead of assuming they do, and it does all of this privately in the browser.

**What we've shown.** Simulated speakers run through the real live engine show three results:

- **A quick talker** (about 215 words a minute) gets "slow down" taps in session 1. In session 2, with the same speech, they get none.
- **A wearer who rates the taps "too many"** gets taps only for longer bursts of rushing in session 2.
- **Over 20 sessions,** held-back taps showed that prompt slow-down taps weren't helping one speaker. Cue tested an alternative and adopted the sparser one.

We also ran this through Deepgram Flux using synthetic speech at about 228 words a minute. The same recognized words got 2 slow-down taps in session 1 and none in session 2.

One caveat: so far this has only been tested on simulated speakers, not real wearers, so the thresholds are starting points.

## Agents track: how Cue monitors itself

Cue's learning loop is an agent that changes its own behavior over time, so it needs to know when it's getting things wrong.

**What counts as failure.** We count four things as failure:

- **A tap that doesn't help.** The tap does no better than a randomly held-back one.
- **A tap the wearer rates "too many" or "distracting".**
- **A change the wearer corrects.** They reject a pattern or say "That's not right" on a "Cue updated" note.
- **A pattern that stops holding.** It's marked stale.

**How it notices on its own.** The held-back taps make the check automatic. Cue keeps a running estimate of how likely it is that tapping beats not tapping, for each habit. When that drops below 75% after at least 8 taps and 4 holdouts, Cue knows its current approach isn't working and starts testing an alternative. It also tracks each habit against your first sessions. If you slip back after Cue stepped away, support comes back.

**Guardrails.**

- **One session isn't enough.** A pattern needs at least 3 sessions with 75% of them agreeing, plus a significance test, before it changes anything.
- **Pace limits are fixed.** The learned pace stays between 3.6 and 6 syllables a second, so a session that opens with very fast talking can't teach Cue that rushing is normal.
- **Tap limits are fixed.** Cooldowns between taps always apply. When you're presenting, Cue taps at most 2 times a minute.
- **The wearer always wins.** What you tell Cue applies right away. What Cue infers needs several sessions, and stays marked as inferred until you confirm it.
- **Every change can be undone.** Each change is logged with its reason, and undoing it is logged too.
- **There's always a fallback.** With no profile, the engine runs the original rules exactly. All 277 tests from before learning existed still pass unchanged.
- **Practice is kept apart.** Simulated and practice sessions use a separate memory, so they can't train your real profile.

**Reliability as it runs longer.** The two risks we care about over many sessions are drift and runaway changes. Against drift, patterns that stop holding go stale, and the learned pace only moves when your baseline shifts by 4% or more. Against runaway changes, a new way of tapping must match the old one over 3+ sessions before it's adopted, otherwise Cue goes back. The wearer can also pause learning, turn off held-back taps, forget a session or reset everything.

## Design track

**Purpose at a glance.** Cue has three cues, and each one has its own color, its own tap shape and its own sound:

- **Pause** is red: one tick.
- **Slow down** is orange: three steps going down.
- **Speak up** is green: a sweep going up.

When a cue fires, a large card says what to do and why, big enough to read with a quick glance down.

**Making something complex feel simple.** Behind the scenes there are sign tests, held-back taps and strategy experiments. The wearer sees one sentence: "Cue updated: you naturally speak about 215 words a minute, so I stopped tapping you for that." Every pattern Cue learns is shown in plain language, with a button to say it's wrong.

**Wanting to come back.** "Your focus" shows the one habit you're working on, and the learning timeline shows two tracks side by side: how you improved and how Cue improved. Seeing the coach adapt to you is the reason to do the next session.

## Scale track

**A real problem in a large market.** Public speaking is one of the most common fears, and almost everyone has to do it at work. The groups we're testing now:

- About 123,000 professional coaches worldwide, who could give Cue to their clients.
- About 265,000 Toastmasters members.
- About 140,000 high school speech and debate students.
- Sales teams.
- People preparing for job interviews.

We're running a paid ad test with a landing page for each group, to see which one signs up fastest.

**Path to $1B.** We plan to grow in three steps:

1. **Sell to individuals preparing for high-stakes moments:** interviews, talks, pitches.
2. **Sell through coaches,** who hand Cue to clients between sessions. One coach brings many wearers.
3. **Sell to companies for people stepping into leadership.** A speech coach we interviewed told us these people get almost no speaking training once they're promoted, especially in tech.

Learning is what makes each step stronger. The longer someone uses Cue, the better it fits them, and the harder it is to switch away.

**Would someone pay today?** We're running paid ads to a sign-up page for each market and measuring sign-ups per dollar right now. An executive coach told us coaches would pay $300–500 per user.

**Why now.** Live speech recognition is finally fast and cheap enough to catch an "um" within a fraction of a second, and small Bluetooth haptic chips make a discreet device possible. Meanwhile, more conversations happen on video and in front of AI note-takers. Speaking well, and sounding like yourself, matters more, not less.

## Privacy

- The learning profile stays in your browser. Nothing is sent to a server.
- Cue keeps numbers from each session, the filler words themselves, and at most five short phrases you repeat. It never keeps audio or transcripts.
- You can pause learning, delete anything Cue learned, or reset everything.

## Files to look at

| File                                                   | What it is                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------- |
| `docs/continuous-learning.md`                          | How the learning works, every rule and threshold              |
| `src/lib/learning/learn.ts`                            | The learning loop: observe, discover, adapt, evaluate         |
| `src/lib/learning/patterns.ts`                         | Finding patterns across sessions, with the statistical checks |
| `src/lib/learning/evaluation.ts`                       | Taps vs. held-back taps, strategy experiments                 |
| `src/lib/learning/coaching.ts` → `src/lib/cue/plan.ts` | Turning the profile into the next session's coaching plan     |
| `src/lib/cue/engine.ts`                                | The live decision engine: "would a tap help right now?"       |
| `src/lib/learning/__tests__/scenarios.test.ts`         | The two-session and 20-session demos                          |
| `src/app/learning/`                                    | What the wearer sees: Your focus, Cue updated, timeline       |

## Run it

```bash
npm install
npm run dev     # http://localhost:3000
npm test        # 309 tests
```

You'll need a Deepgram API key for live listening. The app asks for one the first time you start.

## What's next

- Test with real wearers and tune the starting thresholds.
- Finish the dev board and connect it over Web Bluetooth.
- Opt-in shared numbers so new wearers start from better defaults.
