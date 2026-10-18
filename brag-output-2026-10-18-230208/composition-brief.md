# Hyperframes Composition Brief: ReproSafe

## Objective

Create a short, polished judge-facing presentation video for ReproSafe, a local-first developer tool that turns sensitive bug reports into smaller, verified reproductions.

## Output

- Composition directory: `brag-output-2026-10-18-230208/composition/`
- Rendered video: `brag-output-2026-10-18-230208/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material

- Project root: `/Users/krishna/dev/reproSafe`
- Primary files read: `static/index.html`, `static/styles.css`, `README.md`, `SUBMISSION_CHECKLIST.md`, `server.py`, `fixtures/northstar-invoice.json`
- Product name: ReproSafe
- Tagline / strongest claim: “Share the bug without sharing the customer data.”
- Key UI or visual moment to recreate: the real four-step rail and the evidence panels showing target failure, reduction bytes, transformation comparison, and review/export boundary
- Copy that must appear verbatim:
  - `Share the bug without sharing the customer data.`
  - `Target failure reproduced`
  - `REPROSAFE_TARGET_FAILURE`
  - `1,643 bytes`
  - `992 bytes`
  - `Disclosure: Not run`
  - `Original input included: no`
  - `Verified locally`

## Creative Direction

- Tone preset: polished
- Creative direction: a quiet, evidence-led developer-tool launch film for hackathon judges
- Interpretation: restrained confidence, crisp UI choreography, clear proof labels, and one satisfying payoff instead of hype or generic startup language.
- Angle: show that ReproSafe treats privacy and reproducibility as two independently checked properties, then refuses to export until both are satisfied.
- Hook: `The bug is real. The customer data doesn’t have to be.`
- Outro / punchline: `Share the bug. Not the customer data.`
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Unrelated visual redesign
  - Any real customer data, credentials, or external URLs

## Visual Identity

- Background: `#f5f7f9`, with deep navy `#152a46` for the final evidence stage
- Text: `#17222f`
- Accent: teal `#0d7c76`, amber `#e8ba6b`, observed-failure amber `#9b5e17`
- Display font: local system UI / Inter-style sans, bold and oversized for video readability
- Body font: local system UI / Inter-style sans; monospace for JSON and evidence markers
- Visual references from the project: navy top bar, teal workflow rail, amber target-failure state, white evidence cards, dark code blocks, exact status taxonomy

## Storyboard

Use `brag-plan.md` as the creative contract.

Scene summary:
1. The tension — 2.4s — hook promise and failure marker
2. Reproduce — 3.4s — actual working UI and target-failure proof
3. Reduce — 4.2s — checked byte reduction with disclosure not run
4. Transform — 4.2s — redaction fails reproducibility; synthetic values pass both checks
5. Review & export — 3.8s — exact outbound package and clean replay evidence
6. Verified promise — 2.0s — final wordmark, claim, and local verification stamp

## Audio

- Audio role: sparse professional accents over a warm business pulse
- Audio arc: fade in under the hook, rise through the proof sequence, duck under the final boundary check, then fade under the final lockup
- Music: `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`
- Music treatment: volume around 0.30; subtle fade-in at 0.0s, duck to around 0.18 under the final export evidence, fade out by 20s
- Music cue guidance: `assets/music/cues/happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.json`; major optional cue locks around 8.74s, 13.11s, and 17.47s; beat grid is available for small accents but readability wins
- Audio-reactive treatment: subtle; use the navy evidence panel glow and final logo presence, never waveform/equalizer graphics
- Audio-coupled moments:
  - Scene 1 marker snap — dry UI tick
  - Scene 2 target failure — soft impact
  - Scene 3 checked reductions — sparse low-risk ticks
  - Scene 4 synthetic candidate — restrained success bell
  - Scene 5/6 export lock — final warm confirmation
- SFX selection guidance: use low-risk `interface/click_003.ogg`, `interface/bong_001.ogg`, and `impact/impactSoft_medium_001.ogg` or equivalent; exact timestamps should follow implemented motion
- SFX analysis guidance: `/Users/krishna/.agents/skills/brag/assets/sfx/sfx-analysis.md`
- Exact SFX choice: Hyperframes should choose filenames, timestamps, density, and volume based on the implemented animation.
- Audio files: copy music and selected SFX into `composition/assets/`

## Hyperframes Instructions

- Use a single standalone root timeline registered at `window.__timelines["main"]`.
- Use `data-start`, `data-duration`, and `class="clip"` for timed scenes.
- Build motion synchronously with a paused GSAP timeline; no clocks, network, random values, or external content.
- Recreate the real UI surface as a cinematic evidence board, not a literal website screenshot or iframe.
- Keep all proof text readable at 1920x1080.
- Use a full-bleed child background and layered midground evidence panels; keep ambient motion seek-safe.
- Add a motion sidecar for the major scene order and a continuous ambient motion assertion.
- Run `npx hyperframes check` before preview/render and fix all errors.
