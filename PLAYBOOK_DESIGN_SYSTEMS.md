# KingdomBuilders.AI — Playbook Design Systems Vocabulary

A complete taxonomy of every structural element, pedagogical system, and visual component
used across the 36-playbook catalog. Each element has a formal name, description, and
usage pattern.

---

## I. STRUCTURAL ARCHITECTURE

### 1. The Threshold
**What it is:** The full-viewport cover section that greets the reader.
**How it works:** Dark gradient background, animated particles unique to each playbook's theme, a category badge, title with subtitle, and brand attribution. Sets the emotional tone before a single word of content is read.
**Elements:** `cover`, `cover-badge`, `cover-content`, `cover-art` (SVG), `ghost-noise` (texture overlay)
**Used in:** Every playbook

### 2. The Atmosphere
**What it is:** Animated background particles that float across the cover and sometimes the entire page.
**How it works:** Each playbook has a unique particle type tied to its metaphor — feathers for crows, ink dots for octopus, snowflakes for bears, flame rings for spiritual content, sound waves for mockingbird, diamond scales for pangolin. Creates an immersive, living document feel.
**Variants by playbook:**
| Playbook | Particle | Animation |
|----------|----------|-----------|
| Conductor | leaves/acorns | `leaf-drift` |
| Squirrel Economy | leaves + fireflies | `leaf-drift` |
| Ant Network | particles | `drift` |
| Wolf's Table | stars + moon | `star-drift` |
| Salmon Journey | waves + bubbles | `wave-drift` |
| Narrator | typewriter lines | `type-scroll` |
| Crow's Gambit | feathers | `feather-drift` |
| Eagle's Lens | thermals | `thermal-rise` |
| Lighthouse Keeper | light pulses | `pulse` |
| Octopus Protocol | ink dots | `ink-float` |
| Starling's Murmuration | murmuration dots | `murmur` |
| Chameleon's Code | color-shifting dots | `color-shift` |
| Spider's Loom | web strands + dew | `strand-drift` |
| Gecko's Grip | wall cracks + dust | `dust-float` |
| Firefly's Signal | firefly dots + grass | `glow-pulse` |
| Fox's Trail | paw prints | `drift` |
| Moth's Flame | flame particles | `flame-rise` |
| Bear's Winter | snowflakes | `snowfall` |
| Coyote's Laugh | dust | `dust-rise` |
| Pangolin's Armor | diamond scales | `scale-float` |
| Horse's Gait | grass blades | `grass-sway` |
| Compass Rose | stars | `twinkle` |
| Mockingbird's Song | musical notes + waves | `wave-drift` |
| Lay It Down series | flame rings | `flame-ring` |
| Process Model series | (minimal/none) | — |

**Used in:** Every playbook (33/36 have animated particles)

### 3. The Chapter Gate
**What it is:** Chapter header system that marks transitions between major sections.
**How it works:** Displays chapter number (text or numeral), title, and optional subtitle. Acts as a visual "gate" the reader passes through.
**Elements:** `ch-head`, `ch-num`, `ch-badge`, `ch-title`, `ch-sub`
**Variants:**
- Text numbering: "Chapter One" (Conductor, standard playbooks)
- Numeric badge: "01" with `ch-badge` (Squirrel, Ant, later playbooks)
- Icon-embedded: `h2` with `.h2-icon` (Lay It Down series)
**Used in:** Every playbook

### 4. The Scripture Ribbon
**What it is:** A full-width banner displaying a Bible verse between chapters.
**How it works:** Appears after chapter headers, grounding each chapter in scripture. Creates a rhythmic spiritual cadence throughout the reading experience.
**Elements:** `ribbon`
**Used in:** Conductor, Lighthouse Keeper, Starling's Murmuration, Firefly's Signal, Lay It Down series, and others (~20 playbooks)

### 5. The Finale
**What it is:** The closing statement of the playbook — a two-line poetic declaration.
**How it works:** Dark section with a large heading split into two lines (regular weight + bold). The first line states the metaphor's truth; the second line commands action. Example: "The blade is forged. / Now go cut."
**Elements:** `section.finale` or `div.finale`, `finale-icon`/`finale-emoji`, `h2` with `span`
**Used in:** Every playbook

### 6. The Brand Footer
**What it is:** Closing footer with scripture, brand name, and PDF save instructions.
**Elements:** `footer`, `div.brand`, `div.no-print`
**Used in:** Every playbook

---

## II. PEDAGOGICAL SYSTEMS

### 7. The Bold Claim
**What it is:** A paragraph in the Chapter 00 / Pregame section (before Chapter 1) that makes a direct, concrete promise to the reader about what they will gain.
**How it works:** Uses second-person address: "If you finish this story/playbook, you will..." followed by 2-4 specific, tangible outcomes. Must be seamlessly integrated into the pregame flow. Sets stakes and creates commitment before the reader invests time.
**Format:** Prose `<p>` with `<strong>` for emphasis on key outcomes
**Gold Standard (Squirrel Economy):** "If you finish this story, you will understand more about how money works than most adults ever learn. You will see **why banks exist, what interest rates actually do, how crashes happen, and why your grandmother was right about saving.**"
**Used in:** Every playbook (MANDATORY)

### 7b. The Stage Setter
**What it is:** A poetic, provocative cover subtitle (`class="cover-tagline"`) that frames the entire journey in one breath.
**How it works:** Appears on the cover page below the title. Uses contrast pairs, rhythmic structure, and `<em>` for emphasis. Tells the reader what kind of journey they're about to take without spoiling the content.
**Format:** `<p class="cover-tagline">` with `<em>` tags for emphasis words
**Gold Standard (Squirrel Economy):** "An economics parable where *every squirrel decision* ripples through the whole economy — from the savers to the spenders, the careful to the reckless, the boom to the crash, and back again."
**Used in:** Every playbook (MANDATORY)

### 7c. The Knowledge Layer
**What it is:** Hover-to-define tooltips on ~20% of domain-specific terms throughout the playbook.
**How it works:** Key terms are wrapped in `<dfn class="def" data-def="Plain-language definition here">term</dfn>`. On hover (desktop) or tap (mobile), a tooltip appears above the word with a brief, accessible definition. Pure CSS — no JavaScript required.
**CSS spec:**
- `.def`: `cursor: help; border-bottom: 1px dotted rgba(255,255,255,0.3); position: relative`
- `.def::after`: `content: attr(data-def); position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%); background: #1a1a2e; color: #e8c96a; padding: 8px 14px; border-radius: 6px; font-size: 0.78rem; white-space: normal; width: max-content; max-width: 260px; opacity: 0; pointer-events: none; transition: opacity 0.2s; box-shadow: 0 4px 16px rgba(0,0,0,0.5); z-index: 50; line-height: 1.4`
- `.def:hover::after, .def:focus::after`: `opacity: 1`
- Mobile breakpoint (max-width 600px): `left: 0; transform: none`
**Term selection guidelines:**
- Target ~20% of words that carry domain-specific weight
- Include: technical terms, framework names, coined phrases, metaphor-specific vocabulary
- Exclude: common words, terms already explained in adjacent text, proper nouns
- Definitions should be 8-20 words, plain language, no jargon in the definition itself
**Gold Standard (Bonsai Method):** 22 terms defined — "trunk line", "crossing branch", "30/70 Rule", "Happiness Audit", "Three Account Architecture", "shadow spending", "convenience purchases", "lifestyle inflation", etc.
**Used in:** Every playbook (MANDATORY for new playbooks, retrofit existing)

### 8. The Root System
**What it is:** Cumulative memory anchors placed between chapters that review everything learned so far.
**How it works:** After each chapter, ALL previous lessons are listed plus the new one. By the final chapter, the reader has reviewed the core concepts 5-7 times. This is spaced repetition built into the document structure.
**Variants:**
- **Root Check** (`root-ck`): Bullet-style with icons. Label: "Root Check No. 1/2/3" + "Water What Was Planted". Each item has `r-icon` + `r-text`. (Conductor, Lighthouse Keeper, Process Model series)
- **Root Review** (`root-review`): Visual pill-and-arrow flow. Each chapter becomes a `root-layer` with `root-pill` items, `root-arr` arrows between layers, and `.current` highlighting. (Squirrel Economy, Narrator, Lay It Down series)
- **Root System** (`root-system`): Row-based with `root-row`, `root-ch`, `root-pill`. (Gravity Well)
- **Root Map** (`rm-item`): Quick-reference format with visualization text. (Conductor)
**Used in:** ~25 playbooks

### 9. The Final Test
**What it is:** An end-of-playbook comprehension quiz that tests whether the reader absorbed the material.
**How it works:** 5-10 questions that can only be answered if the reader internalized the content (not just read it). Presented with blank lines for writing answers. Often prefaced with "Can You Answer Without Looking Back?"
**Variants:**
- `div.think` with label "The Final Test" + `p.q-start` questions (standard)
- `div.final-test` with `ft-label`, `ft-question`, `ft-num` (numbered format — Spider, Compass Rose)
- `div.dd` blocks as numbered questions (Lay It Down series)
**Used in:** ~30 playbooks

### 10. The Installation Prompt
**What it is:** A copy-paste AI prompt at the end of the playbook for continued learning.
**How it works:** Gives the reader a structured prompt they can use with ChatGPT/Claude to apply the playbook's framework to their specific situation. Turns a static document into an interactive coaching session.
**Elements:** `div.prompt` with `prompt-head` + `prompt-body`, or `div.prompt-card` with `pc-label` + `code` block
**Used in:** Every playbook

### 11. The Cast
**What it is:** Character introduction cards that present the playbook's metaphorical actors.
**How it works:** Each playbook features 2-4 characters (usually animals or archetypes) with name, title/role, and description. Characters embody different approaches to the topic — one represents the wrong way, one represents the lesson.
**Variants:**
- **Grid cards** (`char-grid`, `char-card`): Compact 2-column grid with emoji/SVG + name + title + body
- **Avatar cards** (`character-card`): Larger format with full SVG illustration + name + role
- **Concept cards**: Characters replaced with concepts (Eagle's Lens: "Dual Foveae", "UV Vision")
- **Anti-pattern cards**: Characters represent failure modes (Octopus: "The Simultaneous Builder")
- **No cast**: Lay It Down series uses second-person address instead of characters
**Used in:** ~32 playbooks

### 12. The Visualization Box
**What it is:** A dark-gradient panel that presents a mental image for the reader to internalize.
**How it works:** Contains an icon, label ("Visualization"), title, body text describing the mental image, and a `viz-trigger` — a one-line sequence the reader can replay in their mind. Designed to create lasting neural associations.
**Elements:** `viz`, `viz-glow`, `viz-inner`, `viz-top`, `viz-icon-wrap`, `viz-label`, `viz-body`, `viz-trigger`, `viz-lesson`
**Lighter variant:** `viz-box` with `viz-label` + `h3` (used for frameworks, not mental images)
**Used in:** ~28 playbooks

### 13. The Reflection Well
**What it is:** Journaling/thinking prompts with blank lines for the reader to write.
**How it works:** Poses a direct question that requires self-examination, then provides writing space. Label varies by context: "Think About This", "Your Turn", "Right Now", "Don't Skip This".
**Elements:** `think`, `think-label`, `think-line` or `fill-line` or `<input class="q-line">`
**Used in:** Every playbook

### 14. The Breathe Gate
**What it is:** An animated pause section with concentric rings that expand and contract.
**How it works:** Three animated rings pulse around centered text that says "Pause Here" or "You Made It". Forces the reader to slow down before heavy emotional content. Used before vulnerability-heavy chapters.
**Elements:** `breathe`, `breathe-ring` (x3, animated), `breathe-content`, `breathe-label`
**Used in:** Narrator, Cost Ledger, Ghost Frame, Gravity Well, Lay It Down series (~8 playbooks)

### 15. The Descent Ramp
**What it is:** A series of contrasting echo statements that build emotional momentum.
**How it works:** Short, punchy paragraphs alternate between what was believed and what is true, creating a staircase effect that leads the reader down into a deeper emotional register. Ends with a `ramp-close` transition.
**Elements:** `descent-ramp`, `ramp-echo`, `ramp-close`, `ramp-close-label`
**Used in:** Narrator, Cost Ledger, Ghost Frame, Lay It Down series (~6 playbooks)

### 16. The Mission Stake
**What it is:** A highlighted box that declares the chapter's or playbook's central thesis.
**How it works:** Labeled "The Mission", "The Thesis", "Who This Is For", or "The Uncomfortable Truth". States in one paragraph what the reader must understand or accept.
**Elements:** `mission`, `mission-label`
**Used in:** Conductor, Lighthouse Keeper, Starling's Murmuration, Lay It Down series (~10 playbooks)

### 17. The Identity Card
**What it is:** A before/after identity reframe presented as a formal card.
**How it works:** Header reads "YOUR NEW IDENTITY" or "YOUR ACCOUNTING UPGRADE". Body shows the old identity (crossed out or dimmed) and the new identity (bold, bright). Physically rewrites the reader's self-concept.
**Elements:** `id-card`, `id-card-head`, `id-card-body`, `p.id-old`, `p.id-new`
**Used in:** Conductor, Cost Ledger, Gravity Well, Narrator (~6 playbooks)

### 18. The Recognition Box
**What it is:** A moment where the playbook says "You already know this."
**How it works:** Connects the abstract concept to something the reader has already experienced in their body or life. Bridges theory to felt experience. Labeled "You Already Know This" or "Right Now, In Your Body".
**Elements:** `recognition`, `rec-tag`
**Used in:** Process Model series (all 6 playbooks)

### 19. The Term Card
**What it is:** A vocabulary definition that teaches a formal concept through everyday language.
**How it works:** Three layers — everyday description, formal/academic name, one-line definition. Makes dense philosophy accessible without dumbing it down.
**Elements:** `term-card`, `p.everyday`, `div.gendlin-name`, `p.one-liner`
**Used in:** Process Model series (all 6 playbooks)

---

## III. NARRATIVE SYSTEMS

### 20. The Bit (replaces Scene Block)
**What it is:** A short comedy break that locks in a teaching point through laughter. Named after the comedy term for a short routine.
**How it works:** A rounded, playful box with a distinct visual identity — uses the **Baloo 2** font for the header, a tilted comedy icon (rotating theater mask, rubber duck, megaphone, etc.), and a punchy title. The humor is modern, absurdist, and succinct (3-8 lines max). The comedy format varies per Bit — fake reviews, fake texts, overheard conversations, fake headlines, one-liners, internal monologues. Every Bit ends with a single-line teaching anchor (`bit-anchor`) that connects the joke to the lesson. The goal: make the reader laugh so hard the concept becomes emotionally unforgettable.
**Elements:** `bit`, `bit-head`, `bit-icon`, `bit-tag`, `bit-title`, `bit-body`, `bit-anchor`
**Sub-formats (mix and match per playbook):**
- **The Overheard** — fake conversation someone overhears (2-4 rapid lines)
- **The Review** — fake 1-star or 5-star product/service review
- **The Headline** — fake breaking news banner
- **The Text Thread** — fake text message exchange (2-4 bubbles)
- **The Monologue** — internal thoughts vs. what was actually said
- **The Warning Label** — fake product warning or disclaimer
- **Classic Setup/Punchline** — traditional joke structure
**Design rules:**
- Max 8 lines of comedy content (brevity is the soul of wit)
- One Bit per chapter (same frequency as old scene blocks)
- The `bit-anchor` line must connect humor to the chapter's core teaching
- Humor should be clean, modern, slightly absurdist — think McSweeney's, @dadsaysjokes, modern standup
- Never explain the joke. If it needs explaining, rewrite it.
- The Bit should make sense even if the reader skips it, but reward those who read it
**CSS class:** `.bit` — visually distinct from all other boxes: rounded corners (20px), light warm background with subtle polka-dot or confetti texture, dashed playful border, Baloo 2 header font
**Font:** Google Fonts `Baloo 2` for `.bit-tag` and `.bit-title` (bubbly, round, reads as playful). Body stays in the playbook's standard font for readability.
**Used in:** All new playbooks going forward (MANDATORY, replaces `.scene`)

### 21. The Adventure Sequence
**What it is:** A multi-step real-world application scenario.
**How it works:** Presents a situation, then walks through it step-by-step with tagged responses: `tag-you` (what you do), `tag-ai` (what the system responds), `tag-result` (outcome). Some include `tag-them` for other people's responses, and `adv-result-good`/`adv-result-bad` for branching outcomes.
**Elements:** `adventure`, `adv-head`, `adv-step`, `step-n`, `step-c`, `tag-you`, `tag-result`
**Used in:** Conductor, Wolf's Table, Narrator, Ghost Frame, Lay It Down series (~12 playbooks)

### 22. The Wild Application
**What it is:** A "See It In The Wild" real-world scenario specific to the Process Model series.
**How it works:** Similar to Adventure but framed as observation rather than action. Uses `tag-scene` and `tag-shift` labels to show how the concept manifests in daily life.
**Elements:** `wild`, `wild-head`, `wild-tag`, `wild-title`, `wild-body`, `wild-step`, `tag-scene`, `tag-shift`
**Used in:** Process Model series (all 6 playbooks)

### 23. The Script Box
**What it is:** A formatted dialogue showing old narratives crossed out and new narratives authored.
**How it works:** Looks like a screenplay. Old lines have `script-text.crossed` (struck through), new lines have `script-text.authored` (bold/bright). Visual proof that narratives can be rewritten.
**Elements:** `script-box`, `script-line`, `script-cue`, `script-text`, `script-author`
**Used in:** Narrator

### 24. The Prayer Section
**What it is:** A formatted prayer with labeled attribution.
**How it works:** Presented as a styled block with `prayer-label`. Used in faith-centered playbooks as a spiritual action step.
**Elements:** `prayer`, `prayer-label`
**Used in:** Lay It Down series

---

## IV. VISUAL DATA SYSTEMS

### 25. The Before/After Split
**What it is:** Side-by-side comparison of the old way vs. the new way.
**How it works:** Two columns — left (dimmed, red-tinted) shows the problem; right (bright, green/gold-tinted) shows the solution. Multiple CSS variants exist.
**Variants:**
- `ba-pair` > `ba-card.ba-before` + `ba-card.ba-after` (Conductor, Lay It Down)
- `ba` > `ba-box.ba-before` + `ba-box.ba-after` (Squirrel, Crow)
- `ba-grid` > `ba-before` + `ba-after` (Gravity Well, standard playbooks)
- `split` > `split-before` + `split-after` with `split-tag` (Process Model)
- `compare` > `compare-box.compare-old` + `compare-box.compare-new` (Ant, Squirrel)
**Used in:** ~30 playbooks

### 26. The Flow Diagram
**What it is:** A horizontal or vertical step sequence showing a process.
**How it works:** Circular numbered markers connected by arrows, each with a label. Shows progression, causation, or sequence.
**Variants:**
- Horizontal: `flow` > `fl-step` > `fl-circ` + `fl-lbl` + `fl-arr` (Conductor)
- Vertical: `flow` > `flow-step` > `flow-marker` + `flow-content` + `flow-arrow` (Chameleon, Gecko)
- Stack: `stack` > `stack-flow` > `stack-node` + `stack-arr` (Cost Ledger, Lay It Down)
**Used in:** ~20 playbooks

### 27. The Payoff Matrix
**What it is:** A color-coded 2x2 decision grid showing outcomes of strategic choices.
**How it works:** Row and column headers represent two players' choices. Cells show outcomes color-coded as optimal, tempting, or Nash equilibrium. Legend explains the colors.
**Elements:** `payoff-matrix`, `pm-grid`, `pm-cell`, `pm-optimal`, `pm-tempt`, `pm-nash`, `pm-legend`
**Used in:** Crow's Gambit

### 28. The Decision Tree
**What it is:** A branching visual showing decision paths and their outcomes.
**How it works:** Root question branches into yes/no paths, each leading to further decisions or color-coded results (good/bad/neutral).
**Elements:** `decision-tree`, `dt-node`, `dt-question`, `dt-branches`, `dt-branch-label`, `dt-result`
**Used in:** Crow's Gambit, Spider's Loom

### 29. The Spectrum Bar
**What it is:** A horizontal gradient bar with labeled positions showing a range.
**How it works:** Endpoints represent extremes; markers or items are positioned along the bar. Used for strategy positioning, identity mapping, or intensity rating.
**Variants:**
- **Strategy Spectrum** (`spectrum`, `spectrum-bar`, `spectrum-items`) — Crow's Gambit
- **Identity Spectrum** (`spectrum-wrap`, `spectrum-bar`, `spectrum-marker`) — Narrator
- **Gravity Spectrum** (`gravity-spectrum`, `gs-bar`, `gs-item`, `gs-dot`) — Gravity Well
- **Temperature Spectrum** (`temp-spectrum`) — Mockingbird's Song
**Used in:** ~5 playbooks

### 30. The Orbit Map
**What it is:** Concentric rings with items positioned as "pulling toward" or "pulling away" from center purpose.
**How it works:** Center reads "YOUR PURPOSE". Items on the rings are color-coded as aligned (toward) or misaligned (away). Legend explains the coding.
**Elements:** `orbit-map`, `om-rings`, `om-ring`, `om-core-text`, `om-item`, `om-legend`
**Used in:** Gravity Well

### 31. The Concept Map
**What it is:** A node-and-connection diagram showing how ideas relate.
**How it works:** Labeled nodes with application annotations, connected by lines, with a center label showing the emergent principle.
**Variants:**
- `concept-map` with `cm-nodes`, `cm-app`, `cm-connections`, `cm-center-label` (Starling)
- `constellation` with `const-node`, `const-line` (Mockingbird)
- `cycle-map` with `c-node`, `c-arrow` (Process Model series)
**Used in:** ~8 playbooks

### 32. The Data Hero
**What it is:** A large, dramatic statistic displayed as a visual anchor.
**How it works:** Single number (like "80%", "250K", "200ms", "Figure-8") displayed huge with a note explaining its significance. Stops the reader with data before teaching the concept.
**Elements:** `data-box` with `stat`/`number` + `stat-note`, or `stat-hero` with `number` + `stat-note`
**Used in:** Wolf's Table, Starling's Murmuration, Process Model series (~10 playbooks)

### 33. The Growth Chart
**What it is:** Horizontal bar chart showing comparative growth or metrics.
**How it works:** Labeled bars with percentage fill widths and value displays. Used for financial comparisons, skill assessments, or progress tracking.
**Variants:**
- `growth-chart` with `growth-bar-fill` (Salmon Journey)
- `comp-meter` with `comp-bar-fill` (Lay It Down: Envy)
- `meter-row` with `meter-fill` (Chameleon's Code)
- `storm-meter` with `meter-track` (Lighthouse Keeper)
**Used in:** ~6 playbooks

### 34. The Timeline
**What it is:** A chronological progression showing phases, weeks, or milestones.
**How it works:** Vertical or horizontal sequence with time markers and descriptions.
**Variants:**
- **Vertical timeline** (`timeline`, `timeline-item`, `timeline-dot`, `timeline-year`) — Salmon Journey
- **Dual timeline** (`tl-left`/`tl-right` with `tl-side-label`) — Lighthouse Keeper
- **Weekly protocol** (`tl`, `tl-item`, `tl-wk`) — Starling, Conductor
- **Trigger timeline** (`trigger-timeline`, `tl-track`, `tl-node`) — Lay It Down: Wrath
- **Vertical phase track** (`vt-track`, `vt-phase`, `vt-dot`, `vt-num`) — Starling
**Used in:** ~10 playbooks

### 35. The Diagram System
**What it is:** A collection of inline SVG and CSS-based diagrams unique to the Process Model series.
**How it works:** Each diagram type visualizes a different philosophical concept.
**Variants:**
- **Merge Visualization** — Venn-like overlapping circles (`merge-viz`, `merge-circle`, `merge-overlap`)
- **Wave Visualization** — SVG path with positioned dots (`wave-viz`, `wave-line`, `w-dot`)
- **Cross Visualization** — Two streams converging (`cross-viz`, `stream`, `stream-result`)
- **Rings Visualization** — Concentric rings (`rings-viz`, `ring`)
**Used in:** Process Model series (all 6)

### 36. The Attention Heat Grid
**What it is:** A color-coded grid showing attention weights between tokens.
**How it works:** Table where cells are colored from cool to hot (`.heat-1` through `.heat-5`) showing which words "attend to" which other words. Teaches transformer attention visually.
**Elements:** `attn-grid`, `attn-table`, `heat-1` through `heat-5`
**Used in:** Mockingbird's Song

### 37. The Token Flow
**What it is:** A visual display showing how text gets broken into tokens.
**How it works:** Styled spans showing individual tokens with borders, demonstrating tokenization.
**Elements:** `token-flow`, `token`
**Used in:** Mockingbird's Song

### 38. The Pyramid
**What it is:** A tiered pyramid diagram showing hierarchy or layers.
**How it works:** Five tiers from base to apex, each with different width and color.
**Elements:** `pyramid`, `pyr-1` through `pyr-5`
**Used in:** Mockingbird's Song

---

## V. INTERACTIVE & KINESTHETIC SYSTEMS

### 39. The Taste Signal
**What it is:** A three-color signal system (green/yellow/red) for real-time self-assessment.
**How it works:** Reader learns to detect quality signals in their work — green (good), yellow (uncertain), red (wrong direction). Creates an embodied feedback loop.
**Elements:** `taste-recipe`, `taste-signal`, `taste-sig.sig-green`/`.sig-yellow`/`.sig-red`
**Used in:** Conductor's Playbook

### 40. The Five Gears
**What it is:** A tiered engagement system with specific prompts for each level.
**How it works:** Five levels of AI interaction depth, each with a name, time estimate, suggested prompt, and "when to use" guidance.
**Elements:** `gears`, `gear`, `gear-badge`, `gear-prompt`, `gear-when`
**Used in:** Conductor's Playbook

### 41. The Arm Grid
**What it is:** A sequential revenue stream builder with build order and revenue targets.
**How it works:** Five numbered "arms" (income streams) with specific sequence, target revenue, and transition thresholds.
**Elements:** `arm-grid`, `arm-card`, `arm-num`, `arm-rev`
**Used in:** Octopus Protocol

### 42. The Step Grid
**What it is:** A color-coded decision framework with timed steps.
**How it works:** 4 steps (STRIP, TEST, COMMIT, CORRECT) each with a unique color, step number, and target time.
**Elements:** `step-grid`, `step-card`, `step-num`, `step-time`
**Used in:** Eagle's Lens

### 43. The Walk-Through
**What it is:** A detailed scenario replay with color-coded action tags.
**How it works:** Walks through a real decision step-by-step, tagging each action with the framework step it belongs to (STRIP, TEST, COMMIT, CORRECT, RESULT).
**Elements:** `walk`, `walk-step`, `walk-step-tag`
**Used in:** Eagle's Lens

### 44. The Seven Grid
**What it is:** A seven-item input framework for mapping relationships.
**How it works:** Seven numbered cards where the reader fills in their seven closest "neighbors" (influences). Final card is full-width for synthesis.
**Elements:** `seven-grid`, `seven-card`, `seven-num`, `seven-full`
**Used in:** Starling's Murmuration

### 45. The Ledger Bill
**What it is:** A financial ledger showing the true cost of decisions.
**How it works:** Styled like an actual bill/invoice with line items, costs, and a total. Red items for losses, green for gains.
**Elements:** `ledger-bill`, `ledger-row`, `ledger-item`, `ledger-cost`, `ledger-total`
**Used in:** Cost Ledger

### 46. The Donut Chart
**What it is:** Dual-ring donut chart comparing perceived vs actual costs.
**How it works:** Outer ring shows actual distribution, inner ring shows perceived distribution. Legend explains each segment.
**Elements:** `donut-section`, `donut-ring.donut-outer`/`.donut-inner`, `donut-legend`
**Used in:** Cost Ledger

### 47. The Audit Block
**What it is:** A structured self-assessment grid with verdict.
**How it works:** Grid of labeled cells the reader fills in, followed by a verdict/conclusion based on the data.
**Elements:** `audit`, `audit-grid`, `audit-cell`, `audit-verdict`
**Used in:** Cost Ledger

---

## VI. SERIES-SPECIFIC SYSTEMS

### 48. The Series Progress Tracker
**What it is:** A row of dots showing position within a multi-part series.
**How it works:** Dots represent each installment. `done` dots are filled, `active` dot is highlighted, future dots are dimmed.
**Elements:** `series-progress`, `series-dots`, `series-dot` (`.active`/`.done`), `series-dot-label`
**Used in:** Lay It Down series (7 dots), Process Model series (6 dots via `div.progress`)

### 49. The Read Progress Bar
**What it is:** A fixed-position scroll progress indicator at the top of the viewport.
**How it works:** JavaScript tracks scroll position and fills a thin bar across the top of the screen.
**Elements:** `#read-progress`
**Used in:** Lay It Down series

### 50. The Chapter Pill
**What it is:** A floating label that shows the current chapter name during scrolling.
**How it works:** JavaScript + IntersectionObserver detects which chapter is in view and displays it in a fixed-position pill.
**Elements:** `#chapter-pill`
**Used in:** Lay It Down series

---

## VII. EMOTIONAL ARCHITECTURE SYSTEMS

### 51. The Dark Panel
**What it is:** A dark-background content box for warnings, deeper concepts, or uncomfortable truths.
**How it works:** Contrasts with the lighter content around it. Used for content that requires extra weight — "The Anatomy of a Stopped Process", "When Brightness Attracts the Wrong Eyes", predatory mimicry warnings.
**Elements:** `dark-panel`, `dp-label`
**Used in:** Firefly's Signal, Fox's Trail, Moth's Flame, Bear's Winter, Coyote's Laugh, Pangolin's Armor, Horse's Gait, Process Model series (~15 playbooks)

### 52. The Grand Quote
**What it is:** A large pull-quote that stops the reader with a core truth.
**How it works:** Dark or highlighted box with large text. Sometimes attributed to a character, sometimes to scripture, sometimes anonymous. Two class variants: `gq` (abbreviated) and `grand-quote` (full name).
**Elements:** `gq` or `grand-quote`, optional `div.attr` or `cite` for attribution
**Used in:** ~30 playbooks

### 53. The Insight Box
**What it is:** An italic narrative reflection that bridges story to principle.
**How it works:** Set apart from regular prose with distinct styling. Not a quote, not instruction — it's the narrator stepping in to explain what just happened in the story.
**Elements:** `insight`
**Used in:** Conductor, Lighthouse Keeper, Lay It Down series (~8 playbooks)

### 54. The Instruction Block
**What it is:** A "how to read this" guide that appears before Chapter 1.
**How it works:** Explains the playbook's unique pedagogy — visualization technique, Root System, etc. Gives the reader permission to read slowly and take it seriously.
**Elements:** `inst`
**Used in:** Conductor, Ghost Frame, Gravity Well, Lighthouse Keeper, Compass Rose (~8 playbooks)

---

## VIII. UNIQUE ONE-OFF SYSTEMS

| # | Name | Playbook | Description |
|---|------|----------|-------------|
| 55 | The Venn Diagram | Narrator | Overlapping circles showing identity intersections |
| 56 | The Audience Seats | Narrator | Visual of whose approval you're performing for |
| 57 | The Author's Chair | Narrator | Rewriting your narrative from the author's position |
| 58 | The Frame Stack | Ghost Frame | Five layers of frame formation stacked vertically |
| 59 | The Comparison Matrix | Ghost Frame | 4-column matrix (victim/neutral/situation/growth) |
| 60 | The Rage Cycle | Lay It Down: Wrath | Circular flow diagram of anger escalation with break point |
| 61 | The Resentment Ledger | Lay It Down: Wrath | Table tracking grudges and their real cost |
| 62 | The Response Detector | Lay It Down: Envy | Side-by-side genuine vs. performed celebration |
| 63 | The Lane Grid | Lay It Down: Envy | "Their Lane" vs "Your Lane" comparison |
| 64 | The Control Grid | Lay It Down: Pride | "Grip" vs "Release" two-column layout |
| 65 | The Correction Filter | Lay It Down: Pride | Flow diagram for intercepting pride responses |
| 66 | The Convergence Meter | Conductor | Horizontal bar chart measuring skill convergence |
| 67 | The 80/20 Inversion | Conductor | Side-by-side cards showing ratio flip |
| 68 | The Three Cuts | Conductor | Negative space protocol — what to remove |
| 69 | The Math Box | Salmon Journey | Formatted mathematical formulas with breakdown |
| 70 | The Code Block | Ant Network | Technical code display |
| 71 | The Threshold Table | Octopus Protocol | Color-coded transition criteria between phases |
| 72 | The Compass Diagram | Compass Rose | CSS-positioned N/E/S/W navigation visual |
| 73 | The Wave Visualizer | Mockingbird's Song | Animated sound wave bars |
| 74 | The Frequency Grid | Chameleon's Code | 4 communication frequency cards (warm/cool/bright/deep) |
| 75 | The Web Strength Matrix | Spider's Loom | Color-coded web assessment grid |
| 76 | The Grip Grid | Gecko's Grip | 4 recovery grip type cards |
| 77 | The Signal Grid | Firefly's Signal | Multi-purpose colored signal cards |

---

## VIII-b. WRITING RULES (apply to ALL playbook text)

**NO HYPHENS OR DASHES.** Never use em dashes (—), en dashes (–), or hyphens (-) as punctuation in prose text. Use commas, periods, or restructure sentences instead. This is a hard rule for all new SetHut playbooks and has been retroactively applied to all 44 existing playbooks.

---

## IX. THE MANDATORY NINE (required in every new playbook)

| # | Element | Why It's Mandatory |
|---|---------|-------------------|
| 1 | **Bold Claim** | Stakes — "If you finish this, you will..." gives the reader a reason to commit |
| 1b | **Stage Setter** | Cover tagline — contrast pairs that frame the journey in one breath |
| 2 | **Root System** | Spaced repetition — this is what makes playbooks teach, not just inform |
| 3 | **Final Test** | Accountability — proves whether the reader absorbed it or just read it |
| 4 | **Scripture Ribbon** | Faith thread — this is KingdomBuilders, the spiritual cadence must be consistent |
| 5 | **The Cast** | Characters — the reader needs someone to follow through the story |
| 6 | **Visualization Box** | Mental image — what sticks months later. The neural anchor |
| 7 | **Installation Prompt** | Continuation — turns a static document into an interactive coaching session |
| 8 | **Knowledge Layer** | Hover definitions on ~20% of domain terms — instant comprehension without leaving the flow |

### Optional (used intentionally, not everywhere):
- Breathe Gate — only before emotionally heavy content
- Descent Ramp — selective emotional tool
- Identity Card — only fits identity-reframe playbooks
- Dark Panel — warning/depth tool, not every topic needs it
- Mission Stake, Instruction Block, Data Hero, Timeline — topic-dependent

---

## X. ELEMENT FREQUENCY ACROSS ALL 36 PLAYBOOKS

| Element | Count | Status |
|---------|-------|--------|
| Threshold (cover) | 36/36 | Universal |
| Chapter Gate | 36/36 | Universal |
| Finale | 36/36 | Universal |
| Brand Footer | 36/36 | Universal |
| Installation Prompt | 36/36 | **MANDATORY** |
| Reflection Well (think) | 36/36 | Universal |
| The Cast (characters) | ~32/36 | **MANDATORY** |
| The Bit (was Scene Block) | ~30/36 | **MANDATORY** |
| Grand Quote | ~30/36 | Near-universal |
| Before/After Split | ~30/36 | Near-universal |
| Final Test | ~30/36 | **MANDATORY** |
| Atmosphere (particles) | ~33/36 | Near-universal |
| Visualization Box | ~28/36 | **MANDATORY** |
| Root System | ~25/36 | **MANDATORY** |
| Scripture Ribbon | ~20/36 | **MANDATORY** |
| Bold Claim | 44/44 | **MANDATORY** |
| Stage Setter | 44/44 | **MANDATORY** |
| Knowledge Layer | 1/44 | **MANDATORY** (retrofit in progress) |
| Dark Panel | ~15/36 | Frequent |
| Flow Diagram | ~20/36 | Frequent |
| Data Hero | ~10/36 | Occasional |
| Breathe Gate | ~8/36 | Selective |
| Descent Ramp | ~6/36 | Selective |
| Identity Card | ~6/36 | Selective |
| Mission Stake | ~10/36 | Selective |
| Instruction Block | ~8/36 | Selective |
| Timeline | ~10/36 | Occasional |

---

## XI. FONT SIZE STANDARD (Conductor Baseline)

Font **families** can vary between playbooks to match each theme (Poppins, Nunito, Lora, etc.). But font **sizes** and readability must be consistent. All playbooks must match these canonical sizes from The Conductor's Playbook:

| Element | Size | Font |
|---------|------|------|
| Base (html) | 18px | — |
| Body text (p) | 1rem | Lora |
| h2 headings | 1.35rem | Poppins |
| Chapter title | clamp(1.9rem, 5vw, 3rem) | Poppins 700 |
| Chapter number label | 0.65rem, ls 6px | Poppins 600 |
| **Scripture ribbon** | **0.95rem** | **Lora italic** |
| Scene/insight text | 1.02rem | Lora italic |
| Viz body | 0.95rem | — |
| Viz label | 0.5rem, ls 5px | Poppins 700 |
| Think label | 0.55rem, ls 5px | Poppins 700 |
| Think body | 0.88rem | — |
| Before/After body | 0.88rem | — |
| Grand quote | 1.05rem | Lora italic |
| Root check text | 0.85rem | — |
| Prompt body | 0.88rem | Lora |
| Footer text | 0.78rem | Lora italic |
| Finale heading | clamp(1.5rem, 4vw, 2.2rem) | Poppins 700 |

**Note:** Scripture ribbon was increased from 0.82rem to 0.95rem (two points larger) for better readability and spiritual emphasis.

---

## X. DESIGN SYSTEM FAMILIES

The 36 playbooks fall into **4 distinct design families**:

### Family 1: The Original System (Conductor's Playbook)
The most elaborate single playbook. Contains nearly every element. Serves as the design template that others inherited from.

### Family 2: The Standard Animal Playbook (~20 playbooks)
Shared component library: cover + particles, ch-head, character-card, scene, signal-grid, ba-grid, data-row, think, grand-quote, viz-box, adventure, flow, dark-panel, prompt-card, root-check, finale, footer. Each varies by theme colors, particle types, and topic-specific custom elements.

### Family 3: The Lay It Down Series (3 published, 7 planned)
Spiritual/devotional design system. Adds: read progress bar, chapter pill, prayer sections, breathe gates, descent ramps, series progress tracker, correction filters, mission-as-altar framing. Heavier emotional architecture. No animal characters — direct second-person address.

### Family 4: The Process Model Series (6 playbooks)
Philosophy/Gendlin design system. Adds: term cards, recognition boxes, wild applications, split comparisons, diagram system (merge/wave/cross/rings), cycle maps, stat heroes, chapter dividers. No Final Test or Installation Prompt in the traditional sense. Academic but experiential.
