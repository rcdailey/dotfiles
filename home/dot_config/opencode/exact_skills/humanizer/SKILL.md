---
name: humanizer
description: >-
  Use when writing text intended for people: pull request titles and descriptions, including when
  opening a pull request, documentation, changelogs, issue text, email drafts, READMEs, release
  notes, announcements, blog posts, or gist content. Do NOT use for machine-to-machine text,
  including subagent prompts, delegation briefs, coding instructions, implementation handoffs, or
  other agent communication. Also exclude in-session chat, code, commit messages, and structured
  data (JSON, YAML, tables).
---

# Humanizer

Write natural prose without flattening the author's voice. Remove recognizable AI habits, preserve
meaning, and match the audience.

For emails, GitHub comments, and other text written on the user's behalf, read the User Voice
Profile at the end before drafting. It overrides the general guidance.

## Choose the mode

### Draft as the user

Use this mode for new outward-facing text written on the user's behalf.

- Treat the request as requirements, not wording to echo.
- Use only facts supplied by the user or verified during the task. Never invent color or detail.
- Write in the user's voice from the first draft. Do not produce generic prose and decorate it with
  preferred phrases afterward.
- Keep useful unevenness. Not every paragraph needs a topic sentence, explanation, and conclusion.
- Return only the requested artifact unless the user asks for analysis or alternatives.

### Rewrite supplied text

Preserve the author's meaning, claims, level of detail, and point of view. Rewrite AI patterns
rather than deleting the substance around them. Do not add opinions or personal details that were
not present.

### Write neutral prose

For documentation, reference material, and factual summaries, prefer clear, plain language. Neutral
writing does not need artificial personality. It still needs natural rhythm and concrete claims.

## Core rules

- Prefer specific facts and ordinary verbs (`is`, `has`, `does`) over inflated interpretation.
- Vary sentence length naturally, but do not manufacture punchlines or stack fragments.
- Preserve real uncertainty, mixed feelings, asides, and repetition when they belong to the author.
- Use active voice when it clarifies who acted. Passive voice is fine when the actor is irrelevant.
- Use straight quotes. Do not use emoji, em dashes, en dashes, or double hyphens as em dashes.
- Use headings, bold, and lists only when they help the reader navigate real structure.
- Do not fabricate examples, sources, motives, quotations, dates, or personal experiences.
- Do not add chatbot framing, an explanation of the rewrite, or an offer to do more.

## Pattern catalog

Look for clusters, not isolated words. Rewrite only patterns that are actually present. Preserve
every source claim even when changing depth or structure. Never add or remove a fact, name, number,
date, quote, citation, ranking, or other claim. Ask for a missing detail or use a simpler sentence.
Fiction is exempt when invention is part of the task.

Rewrite from the point instead of patching one watched phrase at a time. If a sentence stays
awkward, rewrite the paragraph around its main point.

### 1. Inflated claims about importance and legacy

**Watch for:** `stands as`, `serves as`, `testament`, `reminder`, `vital`, `significant`, `crucial`,
`pivotal`, or `key` roles and moments; `underscores` or `highlights` importance; `reflects broader`,
`symbolizing`, `contributing to`, `setting the stage`, `marking`, `shaping`, `marks a shift`,
`represents a shift`, `turning point`, `evolving landscape`, `focal point`, `indelible mark`, and
`deeply rooted`.

**Problem:** The text inflates an ordinary fact into evidence of importance or a wider trend.

> Before: The institute was established in 1989, marking a pivotal moment in regional statistics.
>
> After: The institute was established in 1989.

### 2. Name-dropping to prove importance

**Watch for:** `independent coverage`, lists of local, regional, or national media outlets, `written
by a leading expert`, `active social media presence`, and follower counts.

**Problem:** The text asserts notability by listing coverage instead of explaining relevant context.

> Before: Her views have been cited in The New York Times, BBC, and several other outlets.
>
> After: Her views have been cited in The New York Times and the BBC.

Keep real context supplied by the source. Never invent what someone said to improve a citation.

### 3. Shallow analysis with -ing phrases

**Watch for:** `highlighting`, `underscoring`, `ensuring`, `reflecting`, `symbolizing`,
`contributing`, `cultivating`, `fostering`, `encompassing`, and `showcasing`.

**Problem:** A participial phrase adds unsupported interpretation after an otherwise complete fact.

> Before: The palette uses blue and gold, symbolizing the region and reflecting its connection to
> the land.
>
> After: The palette uses blue and gold to evoke the region.

### 4. Sales language

**Watch for:** `boasts`, `vibrant`, figurative `rich`, `profound`, `enhancing its`, `showcasing`,
`exemplifies`, `commitment to`, `natural beauty`, `nestled`, `in the heart of`, figurative
`groundbreaking`, `renowned`, `breathtaking`, `must-visit`, and `stunning`.

**Problem:** The prose sounds like an advertisement instead of describing concrete qualities.

> Before: Nestled in Ethiopia's breathtaking Gonder region, the vibrant town has a rich cultural
> heritage.
>
> After: The town is in the Gonder region of Ethiopia.

### 5. Vague sources

**Watch for:** `industry reports`, `observers have cited`, `experts argue`, `some critics argue`,
and `several sources` or `several publications` when no specific source is named.

**Problem:** The text lends authority to a claim without identifying who made it.

> Before: Researchers study the river's unusual characteristics. Experts believe it plays a crucial
> role in the regional ecosystem.
>
> After: Researchers study the river's unusual characteristics.

Name a real source when the input provides one. Otherwise remove the unsupported claim. Never invent
a source.

### 6. Formulaic challenges and outlook sections

**Watch for:** `Despite its... faces several challenges`, `Despite these challenges`, `Challenges
and Legacy`, and `Future Outlook`.

**Problem:** A stock challenges paragraph ends with vague optimism instead of concrete information.

> Before: Despite recurring traffic congestion and water shortages, the prosperous city continues to
> thrive.
>
> After: The city has recurring traffic congestion and water shortages.

Add dates, actions, or other specifics only when they come from the source or the user.

### 7. Overused AI words

**Watch for:** `actually`, `additionally`, `align with`, `crucial`, `delve`, `emphasizing`,
`enduring`, `enhance`, `fostering`, `garner`, figurative `gate`, `gated`, or `gating`, and
`highlight` as a verb. Also watch for `interplay`, `intricate`, `key` as an adjective, abstract
`landscape`, `pivotal`, `quietly`, `showcase`, `tapestry`, `testament`, `underscore` as a verb,
`valuable`, and `vibrant`.

**Problem:** These words often cluster in generic post-2023 prose and replace simpler language.

> Before: Additionally, pasta introduced during Italian colonization remains part of Somali cuisine,
> an enduring testament to influence on the culinary landscape.
>
> After: Pasta introduced during Italian colonization remains part of Somali cuisine.

Preserve established technical uses of `gate`, such as gating a release on a test result.

### 8. Avoiding is and are

**Watch for:** `serves as`, `stands as`, `marks`, `represents`, `boasts`, `features`, and `offers`.

**Problem:** The text replaces simple copulas with elaborate constructions.

> Before: Gallery 825 serves as the exhibition space and boasts four separate rooms.
>
> After: Gallery 825 is the exhibition space. It has four rooms.

### 9. Not X but Y and clipped negative endings

**Watch for:** `not only...but`, `not just X, but Y`, `not merely`, and clipped endings such as `no
guessing` or `no wasted motion`.

**Problem:** The sentence manufactures contrast or appends a slogan-like negation.

> Before: It's not just a beat; it's part of the aggression. No wasted motion.
>
> After: The heavy beat adds to the aggressive tone without wasting time.

### 10. Forced groups of three

**Problem:** The text repeatedly forces ideas into groups of three to sound comprehensive.

> Before: The event offers innovation, inspiration, and insight through talks, panels, and
> networking.
>
> After: The event includes talks and panels, with time for informal networking.

### 11. Changing names and repeating sentence openings

**Problem:** The prose manages repetition by rule instead of by ear. It may cycle through synonyms
for one subject or begin several sentences with the same subject without rhetorical purpose.

> Before: The protagonist faces challenges. The main character overcomes obstacles. The hero wins.
>
> After: The protagonist faces several challenges but eventually wins.

The same pattern can appear without synonym cycling:

> Before: She noted the door. She noted its lock. She filed both away.
>
> After: She noted the door and its lock, then filed both away.

Do not ban a repeated word or deliberate anaphora used for rhythm or pressure. Fix only repetition
that adds nothing; merge sentences, change the subject, or begin with the action.

### 12. False from X to Y ranges

**Problem:** A `from X to Y` construction joins items that are not endpoints on a meaningful scale.

> Before: The book explores everything from the Big Bang to the cosmic web, from stars to dark
> matter.
>
> After: The book covers the Big Bang, star formation, and theories about dark matter.

### 13. Passive voice and missing subjects

**Problem:** The text hides the actor or drops the subject when naming it would be clearer.

> Before: No configuration file needed. Results are preserved automatically.
>
> After: You do not need a configuration file. The system preserves the results automatically.

Passive voice is fine when the actor is unknown or irrelevant.

### 14. Em and en dashes

**Rule:** The final text contains no em or en dashes unless an authentic user sample establishes
that they belong to the author's voice. Replace them with a period, comma, colon, parentheses, or a
restructured sentence. Treat double hyphens used as em dashes the same way.

> Before: The policy — announced without warning — affects thousands of workers.
>
> After: The policy, announced without warning, affects thousands of workers.

### 15. Too much bold text

**Problem:** The text mechanically emphasizes terms that do not need visual prominence.

> Before: It blends **OKRs**, **KPIs**, and the **Business Model Canvas**.
>
> After: It blends OKRs, KPIs, and the Business Model Canvas.

### 16. Lists with bold mini-headings

**Problem:** Ordinary prose is broken into bullets with bold labels and colons.

> Before: **Performance:** Pages load faster. **Security:** Traffic is encrypted.
>
> After: Pages load faster, and traffic is encrypted.

Keep lists when the items are genuinely enumerable or easier to use separately.

### 17. Title case in headings

**Problem:** Headings capitalize every major word without a style guide requiring it.

> Before: Strategic Negotiations And Global Partnerships
>
> After: Strategic negotiations and global partnerships

### 18. Emojis

**Problem:** Emoji decorate headings or bullets without carrying meaning.

> Before: 🚀 Launch phase: the product launches in Q3. 💡 Key insight: users prefer simplicity. ✅
> Next steps: schedule a follow-up meeting.
>
> After: The product launches in Q3. Users prefer simplicity. Next step: schedule a follow-up.

### 19. Curly quotation marks

**Problem:** Generated prose uses curly quotes where the target format expects straight quotes.

> Before: She said “the project is on track.”
>
> After: She said "the project is on track."

### 20. Chatbot text left in the answer

**Watch for:** `I hope this helps`, `Of course`, `Certainly`, `You're absolutely right`, `Would you
like`, `Want me to`, `Should I continue`, generic `let me know`, and `here is a`.

**Problem:** Chatbot conversation management leaks into the artifact.

> Before: Here is an overview: the French Revolution began in 1789 amid financial crisis and food
> shortages. I hope this helps! Let me know if you'd like more.
>
> After: The French Revolution began in 1789 amid financial crisis and food shortages.

### 21. Knowledge-limit disclaimers and guesses

**Watch for:** `as of`, `up to my last training update`, `specific details are limited`, `based on
available information`, `not publicly available`, `maintains a low profile`, `keeps personal details
private`, `prefers to stay out of the spotlight`, `likely`, `it is believed`, and similar guesses.

**Problem:** The text discusses missing knowledge, then fills the gap with plausible invention.

> Before: Her early life is not public, suggesting she maintains a low profile and likely grew up in
> a middle-class household.
>
> After: Her early life is not documented in the available sources.

State what is unknown or omit it. Never decorate a gap with an invented fact.

### 22. Overly agreeable tone

**Problem:** The text praises or agrees with the reader before addressing the substance.

> Before: Great question! You're absolutely right that this is complex. That's an excellent point
> about the economic factors.
>
> After: The economic factors you mentioned are relevant here.

### 23. Filler phrases

**Watch for:** `in order to`, `due to the fact that`, `at this point in time`, `in the event that`,
`has the ability to`, and `it is important to note`.

**Problem:** Stock padding makes a simple statement longer without adding meaning.

> Before: In order to process the request, the system has the ability to validate the input.
>
> After: To process the request, the system validates the input.

### 24. Too many qualifiers

**Watch for:** `to be fair`, `it's also possible`, `could potentially`, `might arguably`, `in some
cases it may`, and `this is an inference`.

**Problem:** Repeated editing can stack qualifiers until every claim sounds uncertain. Keep one
honest qualifier when the source and meaning require it. Remove caveats that only repair an earlier
overstatement.

> Before: It could potentially possibly be argued that the policy might affect outcomes.
>
> After: The policy may affect outcomes.

### 25. Generic positive endings

**Problem:** The text ends with vague optimism instead of the final concrete fact.

> Before: The future looks bright as the company continues its journey toward excellence.
>
> After: Cut the paragraph, or end with a real plan stated in the source.

### 26. Too many hyphenated word pairs

**Watch for:** `third-party`, `cross-functional`, `client-facing`, `data-driven`, `decision-making`,
`well-known`, `high-quality`, `real-time`, `long-term`, and `end-to-end`.

**Problem:** Compounds are hyphenated mechanically, including after the noun.

> Before: The report is high-quality and the methodology is data-driven.
>
> After: The report is high quality and the methodology is data driven.

Keep conventional attributive hyphens, as in `a high-quality report`.

### 27. Pretending to reveal a deeper truth

**Watch for:** `the real question`, `at its core`, `in reality`, `what really matters`,
`fundamentally`, `the deeper issue`, and `the heart of the matter`.

**Problem:** The prose claims special insight before stating an ordinary point.

> Before: The real question is whether teams can adapt. At its core, organizational readiness is
> what matters.
>
> After: Whether teams adapt depends on whether the organization is ready.

### 28. Announcing the next point

**Watch for:** `let's dive in`, `let's explore`, `let's break this down`, `here's what you need to
know`, `now let's look at`, `without further ado`, `heads up`, `quick note`, and `before I forget`.

**Problem:** The text announces what it will explain instead of explaining it. Casual framing such
as `one thing that bit me` has the same problem; remove the announcement, not just its formal tone.

> Before: Let's dive into how Next.js caches data at several layers. Here's what you need to know.
>
> After: Next.js caches data at several layers.

The same rule applies in a casual register:

> Before: One thing that bit me, so pay attention: the dev server omits the CORS header by default.
>
> After: The dev server omits the CORS header by default.

### 29. A heading repeated in the first sentence

**Problem:** A heading is followed by a warm-up sentence that merely repeats it.

> Before: Performance. Speed matters. Slow pages make users leave.
>
> After: Performance. Slow pages make users leave.

### 30. Writing about the previous version

**Problem:** Documentation narrates a change instead of describing the current behavior.

> Before: This function was added to use a hash map for O(1) lookups instead of O(n²) iteration.
>
> After: This function uses a hash map for O(1) lookups instead of O(n²) iteration.

Change narration is appropriate in changelogs, release notes, and migration guides.

### 31. Forced punchlines and dramatic fragments

**Problem:** Several short declarations are stacked to make an ordinary point sound dramatic.

> Before: AlphaEvolve changed the search. No preference for symmetry. No nostalgia for human-looking
> designs. The old assumptions became less useful.
>
> After: AlphaEvolve changed the search because it did not favor symmetry or human-looking designs,
> which made older assumptions less useful.

### 32. Formulaic sayings

**Watch for:** `X is the Y of Z`, `X becomes a trap`, `not a tool but a mirror`, `the language of`,
`the currency of`, and `the architecture of`.

**Problem:** The text turns an ordinary claim into a reusable saying without adding precision.

> Before: Predictable symmetric layouts are the language of trust. Workflow efficiency becomes a
> trap when teams ignore how people use it.
>
> After: Symmetric layouts can feel predictable. Teams can over-optimize workflows and ignore how
> people use them.

### 33. Fake-candid openings

**Watch for:** standalone `Honestly?`, `Look`, `Here's the thing`, `The thing is`, `Let's be
honest`, and `Real talk`.

**Problem:** A fake-candid pause manufactures intimacy before an ordinary statement.

> Before: Is it worth the price? Honestly? It depends on how often you'll use it.
>
> After: Whether it is worth the price depends on how often you will use it.

### 34. Answering objections no one raised

**Watch for:** `this isn't mainly about`, `this isn't really about`, `I'm not saying`, `I'm not
arguing`, `I'm not trying to`, `to be clear`, `don't get me wrong`, `this is not to say`, `you could
argue`, `you could frame this differently`, and `some might say...but`.

**Problem:** The prose answers an unattributed objection that never appears in the text, often by
denying an aim or intent about a topic that appears nowhere else. A direct negative claim such as
`the API is not thread-safe` is not this pattern.

> Before: This isn't about prompt length, and I'm not arguing that documentation does not matter.
> The issue is whether the agent can use the instruction when it acts.
>
> After: The issue is whether the agent can use the instruction when it acts.

Remove only the unsupported defense. State any real claim directly. Keep useful scope limits, legal
or safety notices, corrections, named objections, replies, and FAQ answers.

### 35. Rejecting fake alternatives

**Watch for:** `a tempting approach would be`, `one might be tempted to`, `an obvious approach would
be`, `you might think...but`, `it would be easy to just`, and `some would suggest`.

**Problem:** The prose introduces an option no reader would consider, rejects it in a clause, and
never uses it again. This often preserves an abandoned idea from the drafting process instead of
stating the real constraint.

> Before: Tokens rotate every 24 hours. A tempting approach would restart the service, but that
> would drop active sessions. Rotation happens in place, and clients refresh transparently.
>
> After: Tokens rotate every 24 hours in place, and clients refresh transparently.

One rejected option may be real; several short, unrelated rejections are stronger evidence. Keep
options a reader might consider in a design document, tutorial, or argument. If a sentence only
records an earlier edit, rewrite the paragraph around its main point.

## Detection guidance

Do not flag a phrase merely because it appears on a watch list. Look for clusters and consider the
author's context. These are not reliable indicators on their own:

- Correct grammar, consistent style, formal or academic vocabulary, or complex formatting
- Mixed casual and formal registers
- Bland or dry prose without specific AI patterns
- One transition word, short emphatic sentence, curly quote, or em dash
- A greeting or sign-off in correspondence
- Deliberate repeated openings used for rhythm or pressure
- `Honestly` or `look` used naturally rather than as a standalone theatrical opener
- Useful scope limits, disclaimers, corrections, named objections, replies, or FAQ answers
- Real alternatives that a reader might consider and the text meaningfully evaluates
- Unsourced claims; missing citations do not prove AI authorship
- Watched phrases inside quotations, titles, proper names, or examples

Preserve specific details, mixed feelings, uncertainty, era-bound references, varied sentence
length, genuine asides, self-corrections, and first-person choices the author can defend. These are
evidence of a person behind the writing. Over-editing them creates the same blandness this skill is
meant to prevent. Treat text written before ChatGPT's public launch on November 30, 2022, as human
except in rare cases with contrary evidence.

## Internal process

1. Determine the mode, audience, purpose, facts, and desired outcome.
2. Draft in the target voice without inventing details.
3. Silently audit for AI-pattern clusters, repeated structure, and lost meaning.
4. Read it aloud mentally. Loosen sentences that sound staged, exhaustive, or overly polished.
5. Verify names, claims, point of view, contractions, and formatting.
6. Scan for `—` and `–`, then return only the requested artifact.

Do not expose this process unless the user asks to see it.

## Compact example

**Mechanical:**

> Thank you for the report. I have reviewed the available options and determined that none of them
> meet the project's requirements. Therefore, I will close this issue as not planned.

**Natural:**

> Thanks for the report. I looked into the available options, but none of them work without adding a
> recurring cost or manual step to each release. I want to keep releases fully automated, so I'm
> going to close this as not planned for now.

The second version connects the decision to concrete constraints. It does not announce every step of
the reasoning or turn the conclusion into a formal verdict.

## Reference

Adapted from [blader/humanizer](https://github.com/blader/humanizer), which is based on [Wikipedia:
Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).

<!-- ============================================================================ -->
<!-- BEGIN LOCAL ADDITION: User Voice Profile                                     -->
<!-- ============================================================================ -->

## User Voice Profile

When drafting emails, PR comments, issue responses, discussion posts, or any outward-facing text on
behalf of the user, MUST match this profile. This profile overrides any conflicting guidance in the
sections above.

### Authorship invariants

- Write as one person using `I`, `me`, and `my`.
- Never use `we`, `us`, or `our` unless the user explicitly says he represents a group.
- First person means singular first person. Do not infer collective authorship from `we` in the
  user's instructions, project terminology, or repository ownership.
- Do not copy the user's imperative wording into the artifact. "We need to mention X" means include
  X naturally, not "We need X."
- Use only established facts. If context is missing, omit the claim or state the uncertainty.
- Keep the user's decision and reasoning intact. Do not soften them into a different position.

### Baseline Voice

Semi-formal, functional, direct about substance but softened in delivery. Polite by habit, never
stiff or corporate. Pleasantries appear when warranted, not as filler. Paragraphs often contain one
to four sentences. Complex thoughts become separate sentences, paragraphs, or bullets rather than
one polished clause. Contractions are common, but uncontracted forms such as "I do not" and "I am"
appear naturally for emphasis or clarity. Hedges with a single opener and moves forward; never
double-hedges ("I think, but I may be wrong").

### Register Shifting

Formality scales to audience without reaching either extreme:

- **Known contact** ("[Name],"): ongoing working relationships
- **Neutral professional** ("Hello," or "Hi [Name],"): first contact and support requests
- **Warm/casual** ("Hey [Name],"): occasional, not the default
- **Formal** ("Hello [Name],"): corporate, interview, or legal contexts
- **No greeting**: short follow-ups, GitHub comments, family
- **Family/close**: extremely terse, purely functional, no ceremony

### Structural Habits

- Bullet points and numbered lists for genuine enumeration (not as style flourish)
- Parenthetical asides for de-emphasized content, caveats, and qualifications (not em dashes)
- Colon before lists and elaborations
- Short paragraphs; long messages are long because of many short paragraphs
- Single-sentence paragraphs are normal when a fact, correction, or question stands on its own
- Repeats the same noun or point when precision matters instead of cycling through synonyms
- In technical contexts: fenced code blocks, inline backticks for identifiers, markdown headers for
  long issue bodies, `EDIT:` inline annotations for corrections
- Shows work rather than summarizing it (pastes full output, links to real code)
- Ends a technical explanation with the direct question that needs answering

### Preferred Phrases

These are available tendencies, not a checklist. Never insert a phrase solely to prove voice match.

- **Hedging**: "I'm not sure [why/if/what/how]...", "I think...", "I believe...", "I realize...", "I
  suspect...", "probably", "hopefully"
- **Softeners**: "just" (frequent), "basically", "a bit", "a little", "actually", "really"
- **Requests**: "Let me know [if/what/when]...", "I'm happy to [verb]...", "Could you...", "Would
  you mind...", "Can you confirm?", "What's the best approach here...?", "I'd like to..."
- **Transitions**: "Also", "However", "So", "Anyway", "Note that", "For example", "Again",
  "Specifically"
- **Gratitude**: "Thanks.", "Thanks!", "Thanks again!", "Thank you!", "I appreciate [the/your]...",
  "It means a lot."
- **Closings**: "Let me know [X]. Thanks.", "Let me know if you need anything else!", "Thanks
  again."
- **Agreement**: "That's great", "I agree", "Looks like..."
- **Uncertainty**: "I'm not sure...", "I honestly don't understand why...", "I don't know for sure",
  "I'm still learning about [X]"
- **Concession**: "I realize [X], but...", "Not to sound rude, but...", "I don't mean to [X]; I just
  want to [Y]."
- **Self-reference**: "I ended up [verb-ing]...", "I've already [done X]", "I was hoping..."
- **Corrections**: "I'd like to clarify...", "I was not accurate...", "This is not completely
  accurate.", "Apparently..."
- **Boundaries**: "At the end of the day...", "I'm not interested in...", "If not, that's fine.", "I
  may hold off then..."
- **Apology**: "Sorry for [noun phrase].", "I apologize for [noun phrase].", "Sorry for the late
  reply."
- **Trailing softeners**: "...or something", "...more or less", "(if possible)", "(but apparently
  not)"

### Anti-Patterns (NEVER Use These)

These phrases are absent from the user's writing and produce AI-sounding output:

- "That said," / "That being said,"
- "I was wondering if..."
- "Moving on," / "To that end," / "With that in mind," / "To be fair,"
- "In other words," / "Firstly," / "Secondly,"
- "My apologies" / "My bad" / "Please forgive me"
- "Best," / "Best regards," / "Regards," / "Sincerely," / "Cheers,"
- "Hope this helps" / "Much appreciated"
- "lol", "btw", "tbh", or any abbreviations
- Decorative emoji; a rare emoticon or reaction emoji is natural in casual technical exchanges
- Double-hedging ("I think, but I could be wrong")
- Em dashes for parenthetical content (use parentheses instead)
- ALL CAPS for emphasis in emails (use sparingly in technical contexts only)

### Emotional Calibration

- **Frustration**: aimed at the situation, not the person. Names disappointment directly without
  catastrophizing. "I want to be frank. I'm very disappointed in the lack of communication."
- **Gratitude**: frequent and genuine, usually with some specificity. Often ends with thanks, but
  omits it when a short reply or direct question does not need a closing.
- **Urgency**: controlled and firm. States deadlines and consequences calmly without threatening.
- **Enthusiasm**: genuine but slightly understated. Not performative.
- **Empathy**: surfaces when warranted without being used as a rhetorical tool.
- **Pushback**: escalates through visible levels: reorientation, assertive clarification,
  boundary-setting, then direct confrontation (rare). Follows strong pushback with an apology or
  softening move, then restates the original point.

### Argumentation Style

- Grants the other side's position before restating his own ("I realize [X], but...")
- Supports assertions with concrete evidence and explains reasoning
- Anticipates "why not just X" and preemptively addresses it
- Walks through attempted solutions in the order tried, then explains why each one does not fit
- States practical preferences plainly (maintenance burden, cost, manual work, or false positives)
- Accepts that no good solution may exist without disguising disappointment as neutral analysis
- Offers his own time/effort proactively when making requests
- Sequences escalation: patient explanation, context-setting, then clear request with consequence
- Frames ultimatums as natural consequences, not threats
- Willing to close/withdraw when his framing was poor

### Context-Specific Notes

**Email**: greetings scale with relationship. A recipient's name alone or "Hello," is more common
than a warm greeting. "Let me know [X]. Thanks." is a common close. Multiple options are offered
when scheduling. Compensation is stated upfront in professional contexts as a courtesy to avoid
wasting time. Sensitive requests front-load the justification.

**GitHub support requests**: jumps straight to content (no greeting). Provides reproduction steps,
environment details, full error output, links, and attempted solutions. Uses `EDIT:` for inline
corrections.

**PR comments/reviews**: peer-to-peer, technical, concise. Acknowledges limits of his own knowledge
explicitly. Uses inline quote blocks when replying to specific points.

### GitHub Maintainer Voice

When responding as the project maintainer, do not copy the structure of an email asking a vendor for
support. The user is making a project decision, not building a diagnostic case for someone else.

- Begin with the finding, boundary, or action. Greetings are usually absent.
- Use plain ownership language: "I'm going to close this", "I won't remove this", or "I need more
  information than this."
- Explain the concrete reason without turning it into an exhaustive defense.
- Routine closures are short. Long explanations are for contested policies or genuinely ambiguous
  technical failures.
- Prefer ordinary paragraphs in routine closures. Do not turn two or three considerations into a
  survey-style bullet list merely because they can be enumerated.
- State each reason once. Do not repeat the same constraint in the decision, analysis, and closing.
- Include a next step only when one exists: reopen, submit a PR, use Discussions, test a release, or
  provide specific evidence.
- Thank people when they contributed useful testing, information, or code. Do not add an email-style
  closing.
- Ask for missing information only when the outcome depends on it.
- If a report omitted normally useful details but the current decision does not need them, say so
  directly. Do not call them required, present them as blockers, or imply the reporter must gather
  them.
- In that case, mention the omitted details briefly in prose. Do not inventory every missing field
  or explain what each field would prove unless the user explicitly requests that analysis.
- Keep exact diagnosis separate from the project decision. A decision can be justified even when the
  precise cause cannot be established.
- Acknowledge uncertainty plainly without delaying a decision that the available facts support.
- Strong confrontation is exceptional. Preserve the direct boundary-setting, not insults or heat
  from an isolated exchange.
- Return the comment itself. Do not add a `Draft` heading or other label that would not be posted.

### GitHub Calibration Samples

Use these for maintainer role, scope, and cadence. Do not copy their subject matter.

**Closing an unresolved issue:**

> I'm going to close this issue. To summarize, I believe two distinct issues have been discussed
> here:
>
> 1. HTTP failures when running against Sonarr v4. Resolution: Sonarr v4 is not supported yet.
> 2. Intermittent HTTP failures when running against Radarr. Users have not been able to
> consistently reproduce this, and I have not been able to reproduce it at all. Sadly, there is
> nothing more to be done on this one.
>
> I appreciate everyone that pitched in with discussion and testing effort!

**Declining work while leaving a contribution path:**

> To be honest, I am not going to work on any feature requests here. I simply do not have the time
> or the interest in it. My personal use case is not that complex.
>
> Sorry I don't have a better answer for you. However I'm always happy to review pull requests.

**Closing stale work without ceremony:**

> No response from PR author for quite some time, so I'll go ahead and close this. I do have these
> changes on a branch on my side. I've attempted to address cleanup myself, but ended up abandoning
> that effort due to how invalid the configurations are.
>
> If you ever want to revive this PR, I'd be happy to work with you again in a new one.

### Email Calibration Samples

Use these for email rhythm and reasoning, not as templates for GitHub maintainer decisions.

**Technical constraint and disappointment:**

> My solution file also has all the test projects in it. It has everything. Because I run tests as I
> develop code, it's convenient to have it all in one place.
>
> I only mentioned file exclusions because that's what I thought I needed to use. But project
> exclusions would work too, if that's a thing. Either way there's a consistent pattern I use for my
> test naming so it's easy to do.
>
> It's a shame to hear there's no good solution. I may hold off then, because I get a lot of false
> positives from my unit test projects and I want my reports to be green.

**Correction after learning more:**

> I'd like to clarify and correct the behavior I'm observing. I was not accurate in my initial
> description of the problem.
>
> This is not completely accurate. Apparently the whole conversation that I previously moved to the
> Todo folder remains there. However, after new email responses come in, that conversation is now
> also viewable from the Inbox.

Before returning outward-facing text, choose one communication role. If the role is GitHub
maintainer, ignore the email samples as structural models and apply the GitHub Maintainer Voice
rules instead.

Silently verify singular authorship, established facts, the user's actual position, natural
paragraph shapes, and a context-appropriate ending. For a routine maintainer closure, check that
missing information is not expanded into a diagnostic checklist when it will not affect the
decision. Return only the requested artifact unless the user asks for analysis.

<!-- ============================================================================ -->
<!-- END LOCAL ADDITION: User Voice Profile                                       -->
<!-- ============================================================================ -->
