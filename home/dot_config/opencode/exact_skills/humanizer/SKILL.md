---
name: humanizer
description: >-
  Use when writing prose intended for people: documentation, changelogs, pull request or issue
  text, email drafts, READMEs, release notes, announcements, blog posts, or gist content. Do NOT
  use for machine-to-machine text, including subagent prompts, delegation briefs, coding
  instructions, implementation handoffs, or other agent communication. Also exclude in-session
  chat, code, commit messages, and structured data (JSON, YAML, tables).
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

Look for clusters, not isolated words. Rewrite only patterns that are actually present.

### 1. Undue emphasis on significance, legacy, and broader trends

**Watch for:** `stands as`, `serves as`, `testament`, `pivotal`, `crucial`, `underscores`, `reflects
broader`, `symbolizing`, `setting the stage`, `evolving landscape`, `indelible mark`.

**Problem:** The text inflates an ordinary fact into evidence of importance or a wider trend.

> Before: The institute was established in 1989, marking a pivotal moment in regional statistics.
>
> After: The institute was established in 1989 as part of Spain's administrative decentralization.

### 2. Undue emphasis on notability and media coverage

**Watch for:** `independent coverage`, lists of media outlets, `leading expert`, and follower
counts.

**Problem:** The text asserts notability by listing coverage instead of explaining relevant context.

> Before: Her views have been cited in The New York Times, BBC, and several other outlets.
>
> After: Her views have been cited in The New York Times and the BBC.

Keep real context supplied by the source. Never invent what someone said to improve a citation.

### 3. Superficial analysis with `-ing` endings

**Watch for:** `highlighting`, `underscoring`, `ensuring`, `reflecting`, `symbolizing`,
`contributing`, `cultivating`, `fostering`, `encompassing`, and `showcasing`.

**Problem:** A participial phrase adds unsupported interpretation after an otherwise complete fact.

> Before: The palette uses blue and gold, symbolizing the region and reflecting its connection to
> the land.
>
> After: The palette uses blue and gold to evoke the region.

### 4. Promotional language

**Watch for:** `boasts`, `vibrant`, `rich`, `profound`, `showcasing`, `exemplifies`, `renowned`,
`breathtaking`, `must-visit`, `stunning`, `nestled`, and figurative `groundbreaking`.

**Problem:** The prose sounds like an advertisement instead of describing concrete qualities.

> Before: Nestled in a breathtaking region, the vibrant town has a rich cultural heritage.
>
> After: The town is in the Gonder region of Ethiopia.

### 5. Vague attributions and weasel words

**Watch for:** `industry reports`, `observers have cited`, `experts argue`, `some critics argue`,
and `several sources` when no specific source is named.

**Problem:** The text lends authority to a claim without identifying who made it.

> Before: Experts believe the river plays a crucial role in the regional ecosystem.
>
> After: Researchers and conservationists study the river for its unusual characteristics.

Name a real source when the input provides one. Otherwise cut or generalize the unsupported claim.

### 6. Formulaic challenge and future-prospect sections

**Watch for:** `Despite its... faces several challenges`, `Despite these challenges`, `Challenges
and Legacy`, and `Future Outlook`.

**Problem:** A stock challenges paragraph ends with vague optimism instead of concrete information.

> Before: Despite its prosperity, the city faces challenges but continues to thrive.
>
> After: The city has recurring traffic congestion and water shortages.

### 7. Overused AI vocabulary

**Watch for:** `additionally`, `align with`, `crucial`, `delve`, `enduring`, `enhance`, `fostering`,
`garner`, `interplay`, `intricate`, `pivotal`, `showcase`, `tapestry`, `testament`, `underscore`,
`valuable`, `vibrant`, and abstract uses of `landscape`.

**Problem:** These words often cluster in generic post-2023 prose and replace simpler language.

> Before: Additionally, pasta is an enduring testament to influence on the culinary landscape.
>
> After: Pasta, introduced during Italian colonization, remains common in southern Somalia.

### 8. Avoidance of `is` and `are`

**Watch for:** `serves as`, `stands as`, `marks`, `represents`, `boasts`, `features`, and `offers`.

**Problem:** The text replaces simple copulas with elaborate constructions.

> Before: Gallery 825 serves as the exhibition space and boasts four separate rooms.
>
> After: Gallery 825 is the exhibition space. It has four rooms.

### 9. Negative parallelisms and tailing negations

**Watch for:** `not only...but`, `not just X, but Y`, `not merely`, and clipped endings such as `no
guessing` or `no wasted motion`.

**Problem:** The sentence manufactures contrast or appends a slogan-like negation.

> Before: It's not just a beat; it's part of the aggression. No wasted motion.
>
> After: The heavy beat adds to the aggressive tone without wasting time.

### 10. Rule-of-three overuse

**Problem:** The text repeatedly forces ideas into groups of three to sound comprehensive.

> Before: The event offers innovation, inspiration, and insight through talks, panels, and
> networking.
>
> After: The event includes talks and panels, with time for informal networking.

### 11. Elegant variation

**Problem:** The prose cycles through synonyms to avoid repeating the clearest noun.

> Before: The protagonist faces challenges. The main character overcomes obstacles. The hero wins.
>
> After: The protagonist faces several challenges but eventually wins.

### 12. False ranges

**Problem:** A `from X to Y` construction joins items that are not endpoints on a meaningful scale.

> Before: The book explores everything from the Big Bang to the cosmic web, from stars to dark
> matter.
>
> After: The book covers the Big Bang, star formation, and theories about dark matter.

### 13. Passive voice and subjectless fragments

**Problem:** The text hides the actor or drops the subject when naming it would be clearer.

> Before: No configuration file needed. Results are preserved automatically.
>
> After: You do not need a configuration file. The system preserves the results automatically.

Passive voice is fine when the actor is unknown or irrelevant.

### 14. Em dashes and en dashes

**Rule:** The final text contains no em or en dashes unless an authentic user sample establishes
that they belong to the author's voice. Replace them with a period, comma, colon, parentheses, or a
restructured sentence. Treat double hyphens used as em dashes the same way.

> Before: The policy — announced without warning — affects thousands of workers.
>
> After: The policy, announced without warning, affects thousands of workers.

### 15. Overuse of boldface

**Problem:** The text mechanically emphasizes terms that do not need visual prominence.

> Before: It blends **OKRs**, **KPIs**, and the **Business Model Canvas**.
>
> After: It blends OKRs, KPIs, and the Business Model Canvas.

### 16. Inline-header vertical lists

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

### 18. Decorative emoji

**Problem:** Emoji decorate headings or bullets without carrying meaning.

> Before: Launch phase 🚀 Key insight 💡 Next steps ✅
>
> After: Launch phase. Users prefer simplicity. Next step: schedule a follow-up.

### 19. Curly quotation marks

**Problem:** Generated prose uses curly quotes where the target format expects straight quotes.

> Before: She said “the project is on track.”
>
> After: She said "the project is on track."

### 20. Collaborative communication artifacts

**Watch for:** `I hope this helps`, `Of course`, `Certainly`, `You're absolutely right`, `Would you
like`, `Want me to`, `Should I continue`, and generic `let me know`.

**Problem:** Chatbot conversation management leaks into the artifact.

> Before: Here is an overview. I hope this helps! Let me know if you'd like more.
>
> After: The French Revolution began in 1789 amid financial crisis and food shortages.

### 21. Knowledge-cutoff disclaimers and speculative gap-filling

**Watch for:** `as of`, `up to my last training update`, `specific details are limited`, `based on
available information`, `maintains a low profile`, `likely`, `it is believed`, and similar guesses.

**Problem:** The text discusses missing knowledge, then fills the gap with plausible invention.

> Before: Her early life is not public, suggesting she maintains a low profile and likely grew up in
> a middle-class household.
>
> After: Her early life is not documented in the available sources.

State what is unknown or omit it. Never decorate a gap with an invented fact.

### 22. Sycophantic or servile tone

**Problem:** The text praises or agrees with the reader before addressing the substance.

> Before: Great question! You're absolutely right that this is a complex topic.
>
> After: The economic factors you mentioned are relevant here.

### 23. Filler phrases

**Watch for:** `in order to`, `due to the fact that`, `at this point in time`, `in the event that`,
`has the ability to`, and `it is important to note`.

> Before: In order to process the request, the system has the ability to validate the input.
>
> After: To process the request, the system validates the input.

### 24. Excessive hedging

**Problem:** Several qualifiers weaken one uncertain claim.

> Before: It could potentially possibly be argued that the policy might affect outcomes.
>
> After: The policy may affect outcomes.

### 25. Generic positive conclusions

**Problem:** The text ends with vague optimism instead of the final concrete fact.

> Before: The future looks bright as the company continues its journey toward excellence.
>
> After: Cut the paragraph, or end with a real plan stated in the source.

### 26. Hyphenated word-pair overuse

**Watch for:** `third-party`, `cross-functional`, `client-facing`, `data-driven`, `decision-making`,
`high-quality`, `real-time`, `long-term`, and `end-to-end`.

**Problem:** Compounds are hyphenated mechanically, including after the noun.

> Before: The report is high-quality and the methodology is data-driven.
>
> After: The report is high quality and the methodology is data driven.

Keep conventional attributive hyphens, as in `a high-quality report`.

### 27. Persuasive-authority tropes

**Watch for:** `the real question`, `at its core`, `in reality`, `what really matters`,
`fundamentally`, `the deeper issue`, and `the heart of the matter`.

**Problem:** The prose claims special insight before stating an ordinary point.

> Before: The real question is whether teams can adapt. At its core, readiness is what matters.
>
> After: Whether teams adapt depends on whether the organization is ready to change its habits.

### 28. Signposting and announcements

**Watch for:** `let's dive in`, `let's explore`, `let's break this down`, `here's what you need to
know`, `now let's look at`, and `without further ado`.

**Problem:** The text announces what it will explain instead of explaining it.

> Before: Let's dive into caching. Here's what you need to know.
>
> After: Next.js caches data at several layers.

### 29. Fragmented headers

**Problem:** A heading is followed by a warm-up sentence that merely repeats it.

> Before: Performance. Speed matters. Slow pages make users leave.
>
> After: Performance. Slow pages make users leave.

### 30. Diff-anchored writing

**Problem:** Documentation narrates a change instead of describing the current behavior.

> Before: This function was added to replace iteration, which caused O(n²) performance.
>
> After: This function uses a hash map for O(1) lookups instead of O(n²) iteration.

Change narration is appropriate in changelogs, release notes, and migration guides.

### 31. Manufactured punchlines and staccato drama

**Problem:** Several short declarations are stacked to make an ordinary point sound dramatic.

> Before: Then AlphaEvolve arrived. No symmetry. No nostalgia. The old rules were gone.
>
> After: AlphaEvolve changed the search because it did not favor symmetry or human-looking designs.

### 32. Aphorism formulas

**Watch for:** `X is the Y of Z`, `X becomes a trap`, `not a tool but a mirror`, `the language of`,
`the currency of`, and `the architecture of`.

**Problem:** The text turns an ordinary claim into a reusable saying without adding precision.

> Before: Symmetry is the language of trust. Efficiency becomes a trap.
>
> After: Symmetric layouts can feel predictable. Teams can over-optimize workflows.

### 33. Conversational rhetorical openers

**Watch for:** standalone `Honestly?`, `Look`, `Here's the thing`, `The thing is`, `Let's be
honest`, and `Real talk`.

**Problem:** A fake-candid pause manufactures intimacy before an ordinary statement.

> Before: Is it worth the price? Honestly? It depends on how often you'll use it.
>
> After: Whether it is worth the price depends on how often you will use it.

## Detection guidance

Do not flag a phrase merely because it appears on a watch list. Look for clusters and consider the
author's context. These are not reliable indicators on their own:

- Correct grammar, consistent style, formal vocabulary, or complex formatting
- Mixed casual and formal registers
- Bland or dry prose without specific AI patterns
- One transition word, short emphatic sentence, curly quote, or em dash
- A greeting or sign-off in correspondence
- Unsourced claims, unless the rewrite would invent support for them
- Watched phrases inside quotations, titles, proper names, or examples

Preserve specific details, mixed feelings, uncertainty, era-bound references, varied sentence
length, genuine asides, self-corrections, and first-person choices the author can defend. These are
evidence of a person behind the writing. Over-editing them creates the same blandness this skill is
meant to prevent.

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
