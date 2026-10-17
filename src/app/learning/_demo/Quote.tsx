"use client";

import { useState } from "react";

/** Cue's own words, two lines at first so the act stays easy to follow; the rest on request. */
export default function Quote({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2 border-l-2 border-cue pl-3">
      <p className={`text-body-sm ${open ? "" : "line-clamp-2"}`}>&ldquo;{text}&rdquo;</p>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="mt-1 text-caption text-muted underline underline-offset-4 hover:text-text focus-visible:outline-2 focus-visible:outline-cue"
      >
        {open ? "Show less" : "Read all of what Cue said"}
      </button>
    </div>
  );
}
