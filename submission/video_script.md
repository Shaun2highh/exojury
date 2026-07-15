# Demo video script (~2.5 minutes)

Record screen + voice. Have the dashboard running (`streamlit run
app/dashboard.py`) and the README open. Speak naturally — this is a guide,
not a teleprompter.

---

**[0:00–0:20] Hook — the leakage chart (README figure 4)**

> "This is a model that gets 99.96% accuracy classifying exoplanets — with
> zero machine learning. Two lines of code. How? The NASA dataset every
> competitor is using quietly contains the answer key. Our project starts
> where that trick ends."

**[0:20–0:50] The honest model (README results table)**

> "ExoJury assigns every one of the 140 columns to a documented leakage
> tier and throws out everything NASA's vetting wrote. What's left is pure
> physics — transit shapes, centroid offsets, stellar properties. That
> honest model still reaches 98.2% on held-out data, and we can measure
> exactly how much the leaky columns would have inflated it."

**[0:50–1:30] The trial — dashboard, '⚖️ The Trial' tab**

*Pick K00701.03 (Kepler-62e), point at the three metrics.*

> "Every candidate gets a trial. Kepler-62e: calibrated probability over
> 99.9% — and calibrated means when we say 90%, we're right 90% of the
> time. The verdict comes with a 95% statistical guarantee from conformal
> prediction. And when evidence is ambiguous, ExoJury doesn't guess — it
> says NEEDS REVIEW and hands it to a human."

*Click "Write AI vetting dossier".*

> "Then the sponsor's Featherless API writes the astronomer's report — the
> model decides, the LLM only narrates the evidence."

**[1:30–2:10] The killer result — '🧾 The Audit' tab**

> "Here's our favourite part. We used our model to audit NASA's own labels.
> Its number-one disagreement: Kepler-854 b, a 'confirmed planet' our model
> scored at three-in-a-hundred-thousand. We looked it up afterwards — NASA
> demoted it to false positive in 2022. Our dataset snapshot still has the
> old label. Same for Kepler-840 b. It even flagged Kepler-452 b — 'Earth's
> cousin' — whose confirmation is genuinely disputed in the literature.
> One CSV, a laptop, and a pipeline built to distrust labels."

**[2:10–2:30] The frontier + close ('🚀 Frontier' tab — flip on the
🌍 habitable-zone toggle, then end on the '🌌 Sky Map' zoomed out)**

> "Finally, the 1,978 candidates NASA hasn't resolved: ExoJury settles 74%
> of them with statistical guarantees and honestly flags the rest for human
> review — a ready-made telescope-time priority list. ExoJury: every
> candidate gets a fair trial."

---

Tips:
- 1080p screen recording (QuickTime: ⌘⇧5), external mic if possible
- Do one full silent run-through first so tabs are cached and instant
- The dossier button uses cached reports — safe to click live
