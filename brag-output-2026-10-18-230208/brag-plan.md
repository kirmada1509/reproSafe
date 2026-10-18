# Brag Plan: ReproSafe

## What is this app?

ReproSafe turns a sensitive bug report into a smaller, shareable reproduction that still demonstrates the original failure, while keeping the original input local.

## The angle

Treat the product like a calm incident-response instrument: the bug is not hidden or hand-waved; it is reproduced, reduced, transformed, independently replayed, and only then exported. The judge sees a concrete proof chain, not a generic privacy promise.

## Hook (first 2-3 seconds)

Start on an oversized, quiet statement: **“The bug is real.”** A small amber failure marker snaps in beside it, then the second line lands: **“The customer data doesn’t have to be.”** This immediately frames the tension ReproSafe resolves.

## Key moments (the middle)

- The real ReproSafe journey rail assembles: **Reproduce → Reduce → Transform → Review & Export**.
- A fictional Northstar Billing request visibly runs and returns **Target failure reproduced** with `REPROSAFE_TARGET_FAILURE`.
- The reduction panel counts down from **1,643 bytes → 992 bytes**, while checked candidates tick in and the disclosure state stays **Not run**.
- A split transformation proof compares **[REDACTED]** (bug gone) against **synthetic values** (bug preserved + disclosure passed).
- The review panel reveals the exact five-file ZIP, then locks in **Original input included: no**.

## Outro / punchline

Finish on the product promise, with the export manifest shrinking into a clean lockup: **“Share the bug. Not the customer data.”** ReproSafe and **Verified locally** hold long enough for a judge to read.

## User flow worth showing

Load the fictional invoice incident → run and reproduce the target failure → reduce it with repeated checks → transform configured sensitive fields → review and export a clean replay package.

## Tone

- Preset: polished
- Creative direction: a quiet, evidence-led developer-tool launch film for hackathon judges
- Interpretation: restrained confidence, crisp UI choreography, clear proof labels, and one satisfying payoff instead of hype or generic startup language.

## Format: landscape — 1920x1080

## Duration: 20 seconds

## Visual identity (from the project)

- Background: `#f5f7f9` with the product’s deep navy `#152a46` as the proof-stage anchor
- Accent: teal `#0d7c76`, amber `#e8ba6b`, and the observed-failure amber family
- Text: `#17222f`
- Display font: system UI / Inter-style sans, heavy weight for proof statements
- Body font: system UI / Inter-style sans; monospace for JSON and markers
- Strongest visual element: the four-step workflow rail plus the side-by-side evidence panels from the working UI

## Share copy (draft)

ReproSafe turns a sensitive bug into a smaller, verified reproduction. **Share the bug without sharing the customer data.**

## Audio direction

- Role: restrained professional support with crisp evidence accents
- Music: `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`, warm and clean at a low bed level
- Music treatment: fade in under the hook, rise slightly through the workflow, duck briefly for the final promise, then fade cleanly at 20s
- Music cue guidance: bundled preset at `assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`; 109.96 BPM. Major cue targets: 8.74s for the reproduced-failure proof, 13.11s for the transformation comparison, 17.47s for the verified export lockup. Sequential UI accents may use the beat grid around 9.29, 9.83, 10.37s, but readable text should reveal as a set and hold.
- Audio-reactive treatment: subtle; let the navy proof panel’s ambient glow breathe with music energy, never use waveform/equalizer visuals.
- SFX posture: sparse and motion-matched; low-risk interface clicks for actions, soft impact for the target-failure proof, one restrained success bell for the final verified export.
- Audio-coupled moments: hook marker snap, Run example click, byte-count tick, redaction/synthetic comparison reveal, final export lock.
- Restraint rule: audio must support evidence clarity, never turn the privacy claim into a loud security-ad cliché.

## Storyboard

### Scene 1 — The tension — 2.4s

On the light canvas, oversized headline copy enters from opposite sides: “The bug is real.” then “The customer data doesn’t have to be.” A tiny amber failure marker locks beside the first line. The deep-navy brand mark sits at the lower-right edge as an anchor.

Sequential/interaction: yes — the two lines enter in order; the marker snaps after the first line and holds.

Audio intent: a low music bed begins; one dry, soft UI tick lands on the marker.

Audio-coupled idea: marker snap on the first nearby beat; no rapid typing sound on the full sentence.

Music: warm, low-volume business pulse.

Transition mood: clean wipe → Scene 2

### Scene 2 — Reproduce — 3.4s

The actual ReproSafe working UI is recreated as a large evidence window: the four-step rail, Northstar invoice parser, expected HTTP 200 card, observed HTTP 500 card, and the primary **Run example** action. The action indicator moves from ready to a clear amber **Target failure reproduced** state with `REPROSAFE_TARGET_FAILURE`.

Sequential/interaction: yes — rail steps assemble left-to-right, then the simulated Run example action resolves into the target-failure banner.

Audio intent: confident click, then a soft low impact when the failure classification resolves.

Audio-coupled idea: the failure proof is the first major cue lock at 8.74s only if the preceding scene timing is extended by the composition; otherwise land it on the nearest local strong cue without rushing the status text.

Music: warm pulse, slightly brighter at the result.

Transition mood: hard evidence cut → Scene 3

### Scene 3 — Reduce — 4.2s

The UI slides into the reduction panel. A large counter changes from **1,643 bytes** to **992 bytes** while a candidate list shows checked removals. The line **Every accepted change was executed** appears beneath it, and a clearly amber **Disclosure: Not run** badge remains visible. A thin progress rail fills behind the candidate card.

Sequential/interaction: yes — three checked candidate rows arrive with a readable stagger, then the size reduction locks in.

Audio intent: three quiet ticks for checked candidates, then a soft click on the byte-count lock.

Audio-coupled idea: use the beat grid as small accents, but reveal the full text block together and hold it for readability.

Music: steady and precise.

Transition mood: smooth slide → Scene 4

### Scene 4 — Transform — 4.2s

Split the frame into two proof cards labeled **Ordinary redaction** and **Synthetic values**. The redaction card shows `success / target failure absent`; the synthetic card shows `target failure reproduced / disclosure passed`. The acceptable candidate gets a teal outline and a small **Acceptable candidate** seal. Keep the exact-value-only limitation visible as a small footer.

Sequential/interaction: yes — left card lands first, then the right card resolves and becomes the visual focal point.

Audio intent: a restrained negative click on the redaction card, then a clean positive bell when the synthetic candidate passes both checks.

Audio-coupled idea: the right-hand proof should land close to the 13.11s strong cue, but its copy must hold for a full read.

Music: slightly lifted, still professional.

Transition mood: crossfade into dark navy → Scene 5

### Scene 5 — Review & export — 3.8s

On the deep-navy panel, five outbound files reveal as a clean manifest: `request.json`, `replay.py`, `evidence-report.json`, `manifest.json`, and `README.txt`. A green check pair reads **Defect mode: reproduced** and **Fixed mode: HTTP 200**. The bottom line locks: **Original input included: no**.

Sequential/interaction: yes — manifest rows appear as a readable group with one subtle stagger; the two independent replay checks arrive after the file list.

Audio intent: quiet file ticks, then one warm confirmation hit on the no-original-input line.

Audio-coupled idea: export lock near the 17.47s strong cue; keep the exact file names readable, not beat-snapped one per half-beat.

Music: duck slightly under the evidence lock.

Transition mood: decisive zoom-out → Scene 6

### Scene 6 — Verified promise — 2.0s

The manifest collapses into a final clean lockup with the amber R mark, ReproSafe wordmark, and the promise **Share the bug. Not the customer data.** A small `VERIFIED LOCALLY` stamp sits beneath. Hold the final frame as the poster-worthy moment.

Sequential/interaction: none — this is the confident final hold.

Audio intent: one restrained success bell, then a short music fade.

Audio-coupled idea: final lock lands near the 17.47s or nearby strong cue, with a clean 2s hold afterward.

Music: fade out by 20s.

Transition mood: final hold.

**Music mood for this video:** polished upbeat.

**Audio summary:** a warm, low music bed supports a proof-driven UI sequence, with only a few motion-matched clicks and two restrained confirmations.
