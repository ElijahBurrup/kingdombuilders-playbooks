# Playbook 10x Protocol

This file is the source of truth for what happens when the user says
**"10x [playbook name]"** or **"go into a deep plan session and 10x this"**.

Read this file first. Follow the process. After shipping, update the
"New Patterns Discovered" section at the bottom with anything that
worked or did not work this round, so future 10x sessions inherit
the learnings.

---

## The meta-principle

> **The experience of reading must embody the content the playbook teaches.**

This is the single most important rule. Every 10x decision flows from
asking "what does this playbook teach, and does the form of the
playbook reinforce or contradict the teaching?"

Examples:
- A playbook about **action** (Love the Practice) should make the
  reader act inside the playbook. Drills, commands, dashboards.
  Reading without doing should feel wrong.
- A playbook about **reception** (Manna: Given) should NOT demand
  effort. Drills would betray the content. Use pauses, noticing
  exercises, slow pacing, white space.
- A playbook about **synthesis** should make the reader combine
  things inside the playbook.
- A playbook about **patience** should resist letting the reader
  scroll too fast.
- A playbook about **decomposition** should never present a wall
  of text. The visual structure should be decomposed itself.

When in doubt: ask "if a stranger read this playbook with the sound
off, would the form of the page tell them what this playbook is
about?" The answer should be yes.

---

## Process (run this every time)

### 0. Snapshot the current version BEFORE editing
Before touching the file, copy the existing
`assets/{Playbook}.html` to
`assets/archive/{Playbook}-v{N}-{YYYY-MM-DD}.html` where N is the
version being preserved (i.e., the version that exists right now,
the one your 10x is about to replace).

Naming examples:
- About to ship v2? Snapshot the current file as `...-v1-2026-05-16.html`
- About to ship v3? Snapshot the current file as `...-v2-2026-05-16.html`

This guarantees we can always diff against, recover from, or
reference the prior version of a playbook even after the 10x
overwrites it. Git history also preserves it, but the explicit
archive file is faster to open and compare side-by-side.

The archive folder is not served as a public asset (the router
only resolves `assets/*.html` not `assets/archive/*.html`), so
snapshots do not appear in the catalog or pollute routes.

### 1. Read the existing playbook end to end
Read the actual asset HTML. Count prose words, SVG count, chapter
count. Note current widget count and type.

### 2. Audit honestly
What does it do well? Where does the experience drift away from
the content? Where is the prose carrying weight that should be
visual? Where are the inert passages?

### 3. Identify the playbook's core teaching
One sentence. What is this playbook trying to install in the
reader? Write that sentence down before doing anything else.

### 4. Decide the methodology archetype
Use this table to pick the right family of moves. Most playbooks
land cleanly in one category; some blend two.

| Archetype | Examples | Interactive form | Visual form | Voice |
|---|---|---|---|---|
| **Action** | Love the Practice, Attend, Conductor's Playbook | Inline drills the reader runs. Command blocks ("Now Do It"). Dashboards that track reps. Resistance section disarming excuses. | Stat blocks (sports-line readouts). Bold gold drill cards. Quality-over-turn curves. | Athletic. Coach. Short sentences. Direct second person. |
| **Reception** | Manna: Given, The Bear's Winter, Done Before You Started | Noticing exercises (look around, find one thing). Gift inventories. Pause prompts. Frames that the reader OPENS rather than answers. | Soft borders. Generous white space. Slower fades. Particle drifts. Minimal stat density. | Meditative. Pastoral. Long-breath sentences. Direct address as invitation, not command. |
| **Diagnosis** | The Body Lie, The Cost Ledger, The Ghost Frame | Diagnostic widgets. Audits. Personalization that surfaces the reader's specific bug. | Before/after columns. Anatomical-style illustrations. Heat-map findings. | Clinical-warm. Doctor's voice. Question stacks. |
| **Synthesis** | The Bee's Dance, The Conductor's Playbook (taste lens) | Source combiners. Three-source pickers. Editable highlights. | Venn diagrams. Layered compositions. Crossroads imagery. | Curatorial. The "and also" voice. |
| **Architecture** | The Eden Pattern series, The Mastery Series | Pillar diagrams. Layer cards. Sequence pipelines. | Structural illustrations. Stack-and-stack visuals. Series progress dots. | Engineering. Systems voice. Frame-naming heavy. |
| **Parable** | Most animal-named playbooks | Scene-driven interactives that put the reader inside the parable's world. | Continuous illustration that returns chapter to chapter (the colony, the canyon, the dance floor). | Storyteller's voice. Slower pacing. Naming the world precisely. |

### 5. Plan moves from the move-library below
Not every move applies to every playbook. Pick the ones that
strengthen the methodology archetype. If you find yourself doing
an Action move for a Reception playbook, ask: would this betray
the content?

### 6. Make it interactive in a way the reader cannot skip
The single biggest lever in any 10x is "the playbook is not
consumed; it is operated." Find at least one place per chapter
where the reader DOES something. Form matches content (drill for
action; pause for reception; toggle for diagnosis).

### 7. Cut prose by 30 to 50 percent
Most playbooks are 30 percent padding. Cut the explanation that
the new visual now carries. Cut the second-paragraph restatement.
Cut the throat-clearing sentences before the punch.

### 8. Add the frame-break sentence at every chapter close
One contrarian one-liner that makes the reader say "I will never
see this the same way." Treat it as the pull-quote it is, with a
distinct visual block.

### 9. Build a dashboard or persistent state widget
Use the existing `kbWidget` persistence system. Choose the form
that matches the archetype:
- Action: streak grid, rep counter, daily checkboxes
- Reception: cumulative inventory of what they noticed
- Diagnosis: scored profile that updates over time
- Synthesis: a personal lexicon or library
- Architecture: filled-in pillars over time
- Parable: a journal of moments inside the parable's world

### 10. Run the contrast audit and fix issues
`npx playwright test tests/contrast-audit.spec.js --project=chrome-desktop`
Then `node tests/contrast-audit-summarize.js`. Resolve any SEVERE
findings before shipping.

### 11. Update the catalog
`python scripts/update_archive_columns.py` auto-syncs the archive
grid, row counter, and homepage "library has N playbooks" copy.
If this is a NEW playbook, add a card to
`static/archive-original.html.bak` BEFORE running.

### 12. Commit, push, verify
Commit message follows the convention used in prior 10x commits:
plain-English, structural, no marketing fluff. Push and verify
the URL renders.

### 13. Append learnings to this file
Section at the bottom: "New Patterns Discovered." Add anything
that worked unexpectedly well, or any new move that should be
in the library for future sessions.

### 14. Record stats in the 10x Stats doc on S:
Open `S:\My Drive\1. Projects\KingdomBuilders.AI\Playbook 10x Stats.md`
and add a `## vN (YYYY-MM-DD)` block at the TOP of that playbook's
section. Versions accumulate (v2, then v3, then v4) — never rewrite
prior version blocks. If the playbook has no section yet, add a new
top-level `# Playbook Name` section and insert it alphabetically in
the index.

Every version block records:
- Commit hash and one-line message
- Archetype
- Prose words before → after (delta %)
- Asset lines before → after
- Interactive widgets count + short list
- Custom SVG / visual count
- Frame-break panel count
- Cold-open: yes/no (kind)
- Persistent dashboard: yes/no (kind)
- Contrast audit: SEVERE before → SEVERE after
- What was added (bullet list)
- What was cut (bullet list)
- Patterns this version contributed back to the protocol library
- Self-assessed score before → after with notes on the jump
- Open questions / things to push further next time

The stats doc lives on Drive (not in the repo) so it survives across
machines and can be opened as a Google Doc. Treat it as the canonical
trail of how each playbook evolved.

**Important — Drive Stream new-file workaround.** When creating the
stats file for the first time, or any brand-new file on S:, clone
an existing file to the target path first (`cp existing.md target.md`),
wait ~10 seconds, then overwrite with real content. Drive Stream
deletes brand-new files within ~60 seconds; cloning baits Drive Stream
into treating it as an edit, not a create.

---

## The move library

These are the moves available. Combine them based on the
methodology archetype.

### Cold-open challenge
Before the pregame, a full-bleed colored panel that hands the
reader a specific task (run a rep, notice three things, pick one
of two postures) before they read a single chapter. Persists per
user. Sets the frame: this is operated, not read.

**Used in:** Love the Practice (challenge), should be used in
most Action playbooks.
**Avoid in:** Reception playbooks (would feel demanding).
**Reception equivalent:** "Stop Before Reading" with a single
invitation to notice one thing in the room, then click to
continue. Same architecture; opposite verb.

### Stat block at chapter open
4-cell sports-stat-line display. JetBrains Mono numbers, tiny
labels. Communicates scale of the master's achievement before
any prose. Format: bold number, two-word label, repeat.

**Used in:** Love the Practice (Curry 500/day, Jiro 70 yrs, etc.)
**Best for:** Action and Architecture archetypes.
**Less ideal for:** Reception (numbers feel transactional).

### Inline interactive drill (one per chapter)
The chapter contains the rep, not instructions for the rep.
Examples from Love the Practice:
- Taste Ranker: three sample outputs, click to rank, name why.
- 25/15/5 Compressor: live word-count enforcement.
- Pipeline Builder: goal + 5 atomic step inputs.
- Turn Slider: drag through 10 versions of an output.
- Three-Source Combiner: highlight strongest, synthesize.
- Anchor Hunt: tap suspicious phrases, reveal hallucinations.

Each persists per user via kbWidget. Each takes ~60 seconds.

**Used in:** Love the Practice.
**Reception equivalent:** "Inline Contemplation." A pause prompt
+ text input that does not score, does not rank, just records
what the reader noticed. The form is invitation, not test.

### Frame-break pull-quote panel
End every chapter with a navy/dark panel, gold left border,
oversized open-quote mark, one italic contrarian sentence. This
is the "I will never see this the same way" moment.

**Used in:** Love the Practice (every chapter ends with one).
**Universal.** Works for every archetype. Always do this.

### Resistance section
Before the finale, name 4-5 excuses the reader is about to use
to skip the work. Each gets a hard one-line answer.

**Used in:** Love the Practice ("Why You Won't").
**Reception equivalent:** "Why You Will Not See." Names the
specific resistances to noticing (familiarity, busyness,
optimization reflex). Same architecture; gentler verbs.

### Persistent dashboard widget
30-day calendar grid with shaded cells per day. Adapts per
archetype:
- Action: cells shade by daily reps logged.
- Reception: cells shade by daily noticings or gifts named.
- Diagnosis: cells shade by re-runs of the diagnostic.
- Synthesis: cells shade by sources combined.

Backed by kbWidget so it persists per signed-in user.

**Used in:** Love the Practice (six-reps grid).
**Universal.** Always include some form of this.

### Custom story-specific SVG per chapter
One bespoke illustration per chapter that visualizes the master's
specific achievement. Not stock imagery. Examples:
- Bannister's four splits as colored bars summing to 3:59.4
- Hubble before/after pair of images
- Hamilton's three-circle Venn (Hip-Hop / Broadway / Founding-Father bio)

**Used in:** Love the Practice (6 per chapter).
**Universal.** Always include.

### "Now Do It" command block at chapter end
Crimson gradient panel. Two sentences. Direct order to stop
reading and run the rep.

**Used in:** Love the Practice.
**Avoid in:** Reception (would feel demanding).
**Reception equivalent:** "Now Sit With This." Soft gold panel.
Same architecture; opposite verb. Invitation to pause, not push.

### Embodied opening
Cold-open or pregame that PERFORMS the playbook's teaching as
the reader arrives. Examples:
- Reception: words fade in slowly like manna falling. Reader
  notices the words arriving without trying.
- Action: clock starts. "You have 60 seconds. Go."
- Patience: deliberate scroll delay. The page resists rapid
  scrolling on the first screen.

### Audio cue (optional)
For reception/parable playbooks, an audio companion at the
chapter open. A single spoken sentence. Currently not implemented
library-wide; flag for future addition.

---

## Move recipes by archetype

### Action playbook recipe (Love the Practice template)
- Cold-open challenge (run a rep before reading)
- Stat block at every chapter open
- Inline drill in every chapter (the rep itself)
- Frame-break sentence at every chapter close
- "Now Do It" command block
- Resistance section before finale
- 30-day dashboard with daily checkboxes
- Custom SVG per chapter
- Voice: short sentences, coach, direct second-person

### Reception playbook recipe (Manna: Given template)
- Embodied opening (words fade in like manna)
- Soft invitation at chapter open (no stats, no metrics)
- Inline contemplation in every chapter (notice, not do)
- Frame-break sentence at every chapter close
- "Now Sit With This" gentle pause block
- "Why You Will Not See" resistance section (named softly)
- Gift Inventory dashboard (cumulative noticing, no streak shaming)
- Custom SVG per chapter (slow imagery, not stat charts)
- Voice: long-breath sentences, pastoral, invitations not commands
- Generous white space, slower fade-in reveals

### Diagnosis playbook recipe
- Cold-open: a single question that surfaces which version of the
  bug applies to the reader
- Symptom-stat block at chapter open
- Inline diagnostic widget in every chapter (audit, rate, identify)
- Frame-break sentence at chapter close
- "Look Again" callback that surfaces the personalized diagnosis
- Dashboard: scored profile that updates over time
- Custom anatomical-style SVG per chapter

### Architecture playbook recipe
- Cold-open: a structural question (which pillar is yours weakest?)
- Pillar stat block (load-bearing strength readouts)
- Inline pillar-builder in every chapter
- Frame-break sentence at chapter close
- Resistance section: "Why Your Structure Is Currently Failing"
- Dashboard: filled-in pillars over time
- Structural blueprints per chapter

### Synthesis playbook recipe
- Cold-open: pick three things from different domains
- Frame stat block (the count of known sources combined)
- Inline three-source combiner per chapter
- Frame-break sentence at chapter close
- Personal lexicon dashboard
- Venn / overlap visuals per chapter

### Parable playbook recipe
- Cold-open: drop the reader into the parable's world
- Scene-stat block (what's happening in this parable moment)
- Inline scene-interactive per chapter (the reader is INSIDE
  the parable, not analyzing it)
- Frame-break sentence at chapter close
- Returning illustration that develops chapter to chapter
- Journal-of-moments dashboard

---

## New Patterns Discovered

This section grows after every 10x. Append, do not rewrite.

### From Love the Practice v3 (2026-05-15)
- **The dual-archetype risk.** Love the Practice is an Action
  playbook but uses Synthesis moves (Chapter 5: Three-Source
  Combiner). Mixing archetypes is fine when the chapter content
  warrants it. Do not force one archetype on a chapter that
  obviously calls for a different one.
- **The "you already started" finale.** Closing the finale with
  a direct callback to the cold-open rep ("you did the cold-open.
  Tomorrow is just the second one") creates loop-closure that
  makes the reader feel they have already entered the practice.
  Powerful for Action archetype. Should be tried for Reception
  too ("you already noticed when you opened this. Tomorrow you
  notice again").
- **Frame-break placement.** Putting the frame-break sentence
  AFTER the inline drill (not before) lets the reader's body
  hold the sentence with the rep still in their fingers. Bigger
  emotional impact than placing it at chapter top.
- **The 30-day grid is more valuable than a streak counter.**
  Streaks induce shame on miss-days. The grid visualizes
  compounding without punishing gaps.

### From Manna: Given v2 (2026-05-16)

- **The Reception archetype confirms the meta-principle hard.**
  Forcing Action-archetype moves (drills, "Now Do It" commands,
  stat blocks of career achievement) onto a Reception playbook
  would have actively betrayed the content. The 41% prose cut
  was achievable not by being terser but by letting interactive
  pauses carry weight prose had been doing. **Pauses can carry
  weight that prose cannot.** Note this for future Reception work.
- **The Manna Rain cold-open animation.** 28 particles fall from
  the top of the cover with random durations and delays. No
  interaction required. Reader watches reception happen. Cheaper
  to implement than expected (~15 lines of CSS + JS). Carries the
  central image of the playbook (manna falling daily). For any
  playbook with a defining natural phenomenon (water, snow, light,
  growth), build an ambient animation that performs that
  phenomenon in the cover. New universal pattern.
- **The Decay Slider visualization.** Dragging a slider to age a
  gift through five stages (Gift → Wonder → Routine → Burden →
  Demand) with the circle changing color, the stage name shifting,
  and the descriptive sentence morphing — this was the most
  powerful interactive in the playbook. Visceral. The reader
  experiences the central thesis (perception decays the same
  object) in their own hand. **Pattern: when a playbook's central
  thesis is a transformation over time, build a slider that
  performs the transformation.** Could apply to The Bear's Winter
  (cycle slider), Body Lie (compass declination slider), etc.
- **The Restore button on the Decay Slider.** Below the slider,
  an "← Drag back" button automatically animates the slider
  back to zero, demonstrating that decay is reversible. This is
  the playbook's second-half claim made tactile. **Pattern: when
  the playbook makes a reversibility claim, give the reader a
  button that performs the reversal.** Don't just say it can be
  undone. Show them the slider sliding back.
- **The Trajectory Walker (clickable stages).** Five clickable
  stages of resentment, each revealing the internal state at
  that point. Plus "Walk Forward" and "Walk Back" buttons.
  Combined with the playbook's claim that forgiveness IS walking
  the trajectory backwards, this turns the abstract claim into a
  body movement. Reader literally walks the path in reverse.
  **Pattern: when a playbook claims a process can run both
  directions, build a stepper that lets the reader run it both
  directions.**
- **The Posture Toggle.** A two-state toggle (Owed / Receiving)
  where flipping the toggle subtly changes the page (background
  shifts from cool gray to warm gold; the list of behaviors
  changes; the heading changes). The reader feels the shift in
  their body. **Pattern: when a playbook teaches a binary
  posture, build a literal toggle and have flipping it change
  the visual atmosphere of the surrounding section.**
- **The Gift Inventory glow.** A persistent journal where the
  reader names one gift a day. The widget has a hidden glow
  effect that grows as entries accumulate (0 entries = no glow,
  5 = small, 15 = medium, 30 = full radiance). **Pattern: when
  a playbook teaches that something accumulates invisibly, make
  the widget visibly accumulate as the practice continues.**
  Compounding visualized as ambient warmth, not a streak count.
- **Reception voice + typography.** Switched to Cormorant
  Garamond serif italic for headings and pull quotes. The
  italic, almost-handwritten quality immediately signals "this
  is not a productivity book." Voice shifted to longer-breath
  sentences, lowercase invitations ("a moment"), pastoral
  cadence. **Pattern: voice and typography must match archetype.
  Reception → italic serif. Action → bold sans. Diagnosis →
  clean clinical. Don't use the same type stack for every
  playbook.**
- **Soft "invite" block replaces hard "Now Do It" command block.**
  Where Action playbooks command, Reception playbooks invite.
  Same architectural slot, opposite verb. Pale gold background
  vs Action's crimson. Single italic sentence vs Action's two
  short imperative sentences. **Pattern is now documented: every
  archetype has a chapter-end engagement block; the form varies
  by archetype.**
- **"A moment" eyebrow over invitations.** Instead of "Stop and
  reflect" or "Pause," the eyebrow text is just "A moment." Two
  words. Casual. Non-prescriptive. The reader does not feel
  homework being assigned. **Pattern: in Reception playbooks,
  eyebrow text on engagement blocks should be as small as
  possible.** Less is more.
- **The "Stop Before Reading" cold-open works for Reception.**
  Same architecture as Love the Practice's challenge cold-open,
  but the verb is "look up from this screen and notice one
  thing" instead of "open ChatGPT and generate three outputs."
  Persists per user via kbWidget. The cold-open as a universal
  pattern across archetypes is confirmed; only the verb changes.

### From Manna: Returning v2 (2026-05-16)

- **The Trace-Back stack.** Three click-to-reveal questions
  ("Who hired me? Who taught me? Who built the industry?") that
  each unfold a sentence beneath the question. After all three
  are clicked, a final summary fades in: "Your work is a thousand
  gifts compounded. None of them paid for." The reader physically
  walks back through the layers of stewardship. Lower-effort than
  a slider; higher-impact than a static list. **Pattern: when a
  playbook's claim is layered (this depends on this depends on
  this), build a click-to-reveal stack that physically unfolds
  the layers.** Use for any "you did not author X" argument.
- **The Stranger Lens slider with progressive SVG detail.**
  Sliding from "Certain" to "Strange" makes hidden lines, eye
  details, and wrinkles fade in on a simple face SVG, while the
  overlay text changes ("You have not really looked at this face
  in a long time" → "You are looking at a stranger"). The reader
  sees the same face transform as their attention transforms.
  **Pattern: when a playbook claims the same object becomes
  different under different attention, build a slider that reveals
  hidden detail as the slider moves.** Decay Slider's cousin —
  decay reveals loss; this slider reveals presence.
- **The clickable Installment Calendar.** Seven day-circles in a
  row; six lit, one dashed-empty (tomorrow). Click any to reveal
  a sentence about what that day's arrival actually is. The
  static install-viz from v1 became operated, not consumed.
  **Pattern: any "this happens daily/repeatedly" claim deserves
  a clickable representation of the repetition where each element
  reveals its specific specifically.** Reception especially.
- **The 60-Second Stop timer.** A literal countdown ring that
  asks the reader to sit still and look at one ordinary thing
  for sixty seconds, then capture what they saw. This is the
  most embodied move in the playbook — the playbook stops, the
  page stops, the reader stops, all simultaneously. **Pattern:
  when the playbook teaches stillness, build a widget that
  enforces stillness in the page.** When teaching speed, build
  one that enforces speed. Form must do, not just describe.
- **The Inversion Flip cards (3D).** Three flip-cards with
  CSS 3D rotation; each click rotates the card 180° to reveal
  the inverted statement. Front: "I am raising my child." Back:
  "I was given to this child." The literal physical inversion
  of the card embodies the conceptual inversion. **Pattern: when
  a playbook teaches a Gestalt flip (figure-ground reversal,
  inversion of belonging, reframing), build a flip widget where
  the visual rotation matches the conceptual rotation.**
- **The Place Witness text input.** Reader types their town or
  address and a sentence appears below: "You were placed in
  [town] for the holding of a specific life." Trivial mechanic;
  surprisingly powerful in the body. Personalizes the claim
  without scoring or quantifying it. **Pattern: when a playbook
  makes a "you specifically" claim, take a single text input,
  echo it back inside the claim sentence. Receive what they
  typed; do not analyze it.** Reception specifically: no scoring.
- **The two-pane persistent dashboard (States + Journal).**
  Domain Walker has two tabs — one for state-per-domain
  (demand/opening/received), one for gift-per-domain (free text
  input). Both persist via kbWidget. Widget glows brighter as
  more gifts accumulate. **Pattern: when a playbook has both
  diagnostic AND practice surfaces, separate them into tabs of
  the same dashboard rather than two separate widgets.** Keeps
  the cognitive load down; the reader navigates one persistent
  thing, not two.
- **The "next door" recommendation engine.** The Domain Walker
  reads the state-per-domain map and surfaces a specific
  recommendation: "Begin with X — the chapter that resists you
  the most is the door that will open the most." Makes the
  widget feel like it is reading the user back to themselves.
  **Pattern: any state-collection widget should compute a single
  next-action recommendation, not just display the state.**
- **Soft Resistance section ("Why You Will Not Return") works
  the same architecture as Action's "Why You Won't" but with
  Reception's gentler verbs.** Same 4-5 disarmed excuses pattern.
  Confirmed: resistance is universal; voice is archetype-specific.
- **The series-callback closing.** Closing the playbook by
  explicitly tying it back to its sibling ("Given named the
  condition. Returning walked you through the rooms") gives the
  reader a sense of having completed a journey, not consumed
  two playbooks. **Pattern: for any multi-part series, the
  finale of part N should explicitly name what each prior part
  contributed. Treat the series as a single arc.**
### From The Fox's Trail v2 (2026-05-16) — Application Brief

The user said: "I love the ideas but not sure how to apply it.
See if we can prime the pump more how to apply these concepts."
This unlocked an explicit **Application Brief** — a 10x variant
where the focus is not embodiment (Reception) or operation
(Action) but **specificity-to-the-reader's-situation**.

- **The cold-open anchor pattern.** The cold-open input is not
  just a frame; it is text that gets ECHOED BACK in every chapter's
  Apply box header. Reader sees their own trail-text inside each
  chapter's application widget. The chapter feels like it was
  written for their specific situation because, in a sense, it now
  was. **Use this any time a playbook's applicability varies by
  reader situation.**
- **The universal Apply box.** Rust/teal-bordered card with top
  accent bar, eyebrow + title + sub, anchor chip echoing the cold-
  open input, labeled input fields with example callouts in green,
  save button, "✓ Saved" affordance. **Consistent visual language
  across all chapters** means readers learn the interaction once
  and trust it for the rest of the playbook. Avoid bespoke widget
  designs per chapter for Application-Brief playbooks.
- **The "Example" green callout pattern.** Italic green chip with
  `<b>Example:</b>` headers showing a concrete worked instance
  using a fictional but specific persona. Reduces blank-page
  paralysis. Without examples, application widgets get half-filled
  or skipped.
- **Compounding dashboard that exports.** Persistent dashboard
  whose cells auto-populate from each chapter's Apply box.
  Includes a copy-to-clipboard button that exports the full state
  as Markdown the reader can paste into Notion/Slack/doc. **The
  playbook's output is no longer notes; it is a personal
  strategy.** Pattern is now mandatory for Application Brief.
- **Multi-input Apply box structured to mirror the concept.** When
  the chapter's concept has internal structure (three trails /
  three threats / four IPB steps), the Apply box has multiple
  labeled inputs arranged to match. Form mirrors content; the
  filled widget IS the concept made personal.
- **Pre-filled placeholder text matching the chapter's grammar.**
  Every input's placeholder starts with the natural-language stem
  ("they would predict that I...", "my third trail is..."). Lowers
  the cost of writing the first word.
- **"What is your X?" framing for case studies.** Don't just tell
  Stewart Butterfield's Slack story. Ask the reader "which of
  these three abandoned items is YOUR Slack?" Turn the famous case
  study into a self-identifying prompt. Works for any anecdote
  where a transferable pattern is being illustrated.

When the user says "10x [playbook]" AND mentions application,
context, or "how do I use this" — switch into **Application
Brief mode**:
- Cold-open MUST capture one specific reader situation
- EVERY chapter MUST end with an Apply box, not a Reflect block
- Apply boxes MUST be consistent in visual structure
- EVERY Apply box MUST include a concrete worked example
- Dashboard MUST be present, MUST compound from Apply boxes,
  MUST export to clipboard

### Contrast pitfalls (running list)
- **Italic small-caps eyebrows on cream.**
  Reception's signature look — small italic letter-spaced
  eyebrow text in gold-deep or rose-dawn on cream backgrounds —
  was the single biggest contrast risk. Required darkening
  `--gold-deep` from `#A6822B` to `#6F551A` and introducing
  `--rose-deep` `#8E4554` for label uses. **Pattern: every new
  Reception playbook should pre-emptively use the deeper variants
  for labels/eyebrows; reserve the lighter rose/gold tones for
  body text on dark backgrounds only.**
