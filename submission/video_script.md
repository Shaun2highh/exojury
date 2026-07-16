# Demo video script (~2.5 minutes)

Record screen + voice (⌘⇧5 → Options → pick your microphone). Use the
deployed app or localhost:8501. Do one silent click-through first so
every page is cached. Speak naturally — this is a guide, not a
teleprompter.

---

**[0:00–0:20] Hook — Home page (let the 3D planet rotate)**

> "This is ExoJury — every candidate world gets a fair trial. It's built
> on NASA's Kepler archive, and it found real errors in NASA's own
> catalog. But first: did you know most models on this dataset cheat
> without knowing it?"

*Switch to Methods — point at the answer-key chart.*

> "The dataset quietly contains the answer key. Two lines of code —
> 99.96% accuracy, zero machine learning. Our project starts where that
> trick ends."

**[0:20–0:50] The honest model (stay on Methods — stat row + reliability)**

> "ExoJury assigns every one of the 140 columns to a documented leakage
> tier and throws out everything NASA's vetting wrote. What's left is pure
> physics — transit shapes, centroid offsets, stellar properties. That
> honest model still reaches 98.2% on held-out data — and its
> probabilities are calibrated, with a 95% conformal guarantee that
> actually holds: 95.6% measured."

**[0:50–1:30] The trial — 'The Trial' page**

*Kepler-62e loads by default. Drag the 3D system view; let a transit dip
draw on the live light curve.*

> "Every candidate gets a trial. This is Kepler-62e, a habitable-zone
> super-Earth — the system view is drawn from its real fitted parameters,
> and you can watch the transit dip in the light curve. Calibrated
> probability: over 99.9%. The verdict comes with a 95% statistical
> guarantee from conformal prediction — and when evidence is ambiguous,
> ExoJury doesn't guess. It says NEEDS REVIEW and hands it to a human."

*Scroll to the AI dossier (already visible for cached objects).*

> "Then the sponsor's Featherless API writes the astronomer's report — the
> model decides, the LLM only narrates the evidence."

**[1:30–2:10] The killer result — 'The Audit' page**

> "Here's our favourite part. We used our model to audit NASA's own labels.
> Its number-one disagreement: Kepler-854 b, a 'confirmed planet' our model
> scored at three-in-a-hundred-thousand. We looked it up afterwards — NASA
> demoted it to false positive in 2022. Our dataset snapshot still has the
> old label. Same for Kepler-840 b. It even flagged Kepler-452 b — 'Earth's
> cousin' — whose confirmation is genuinely disputed in the literature.
> One CSV, a laptop, and a pipeline built to distrust labels."

**[2:10–2:30] The frontier + close ('Frontier' page — flip on the
🌍 habitable-zone toggle, then end on 'Sky Map', slowly rotating the 3D view)**

> "Finally, the 1,978 candidates NASA hasn't resolved: ExoJury settles 74%
> of them with statistical guarantees and honestly flags the rest for human
> review — a ready-made telescope-time priority list. ExoJury: every
> candidate gets a fair trial."

---

Tips:
- 1080p screen recording (QuickTime: ⌘⇧5), external mic if possible
- Do one full silent run-through first so tabs are cached and instant
- The dossier button uses cached reports — safe to click live
