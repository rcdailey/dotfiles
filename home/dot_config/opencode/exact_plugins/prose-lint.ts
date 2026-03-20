import type { Plugin } from "@opencode-ai/plugin";

// gh subcommands that publish user-facing prose. Matches the subcommand
// portion of "gh <noun> <verb>" and requires --body, --title, --notes,
// or a heredoc to be present (so dry-run/list invocations are ignored).
const GH_POSTING_COMMANDS = new RegExp(
  [
    String.raw`gh\s+pr\s+(create|edit|comment|review|merge)`,
    String.raw`gh\s+issue\s+(create|edit|comment)`,
    String.raw`gh\s+release\s+(create|edit)`,
    String.raw`gh-review\s+comment`,
  ].join("|"),
);

const CONTENT_FLAGS = /--(?:body|title|notes)\b|<<[-~]?['"]?\w+/;

function isProseCommand(command: string): boolean {
  return GH_POSTING_COMMANDS.test(command) && CONTENT_FLAGS.test(command);
}

// ---------------------------------------------------------------------------
// Character-level violations
// ---------------------------------------------------------------------------

// Emoji detection covering most common emoji ranges. Excludes basic ASCII
// punctuation emoticons and symbols commonly used in code/shell.
const EMOJI_RE = new RegExp(
  [
    String.raw`[\u{1F600}-\u{1F64F}]`, // emoticons
    String.raw`[\u{1F300}-\u{1F5FF}]`, // misc symbols & pictographs
    String.raw`[\u{1F680}-\u{1F6FF}]`, // transport & map
    String.raw`[\u{1F1E0}-\u{1F1FF}]`, // flags
    String.raw`[\u{2600}-\u{26FF}]`, // misc symbols
    String.raw`[\u{2700}-\u{27BF}]`, // dingbats
    String.raw`[\u{FE00}-\u{FE0F}]`, // variation selectors
    String.raw`[\u{1F900}-\u{1F9FF}]`, // supplemental symbols
    String.raw`[\u{1FA00}-\u{1FA6F}]`, // chess symbols
    String.raw`[\u{1FA70}-\u{1FAFF}]`, // symbols extended-A
    String.raw`[\u{200D}]`, // ZWJ
    String.raw`[\u{20E3}]`, // combining enclosing keycap
  ].join("|"),
  "gu",
);

const EM_DASH = /\u2014/g;
const EN_DASH = /\u2013/g;
const CURLY_QUOTES = /[\u201C\u201D\u2018\u2019]/g;

interface CharViolation {
  name: string;
  pattern: RegExp;
  examples: string;
}

const CHAR_VIOLATIONS: CharViolation[] = [
  { name: "emoji", pattern: EMOJI_RE, examples: "" },
  { name: "em dash (\u2014)", pattern: EM_DASH, examples: "use comma, semicolon, or parentheses" },
  { name: "en dash (\u2013)", pattern: EN_DASH, examples: "use a hyphen" },
  {
    name: "curly quotes",
    pattern: CURLY_QUOTES,
    examples: "use straight quotes (\"...\" or '...')",
  },
];

// ---------------------------------------------------------------------------
// Phrase-level violations (case-insensitive)
// ---------------------------------------------------------------------------

// Anti-patterns from AGENTS.md and sycophantic/collaborative artifacts from
// the humanizer skill. Each entry is [pattern, suggestion]. Word boundaries
// prevent false positives inside longer words.
const PHRASE_VIOLATIONS: [RegExp, string][] = [
  // AGENTS.md anti-patterns
  [/\bthat said,/i, "remove transitional filler"],
  [/\bthat being said,/i, "remove transitional filler"],
  [/\bwould you mind\b/i, 'use "Could you..." or "Let me know..."'],
  [/\bI was wondering if\b/i, 'be direct: "Could we..." or "I\'d like to..."'],
  [/\bmoving on,/i, "remove transitional filler"],
  [/\bto that end,/i, "remove transitional filler"],
  [/\bwith that in mind,/i, "remove transitional filler"],
  [/\bto be fair,/i, "remove transitional filler"],
  [/\bin other words,/i, "remove transitional filler"],
  [/\bfirstly,/i, 'use "First," or restructure'],
  [/\bsecondly,/i, 'use "Second," or restructure'],
  [/\bmy apologies\b/i, 'use "Sorry for..."'],
  [/\bmy bad\b/i, 'use "Sorry for..."'],
  [/\bplease forgive me\b/i, 'use "Sorry for..."'],
  [/\bhope this helps\b/i, "remove; this is a chatbot artifact"],
  [/\bmuch appreciated\b/i, 'use "Thanks" or "I appreciate..."'],
  [/^Best,?\s*$/im, "remove sign-off"],
  [/^Best regards,?\s*$/im, "remove sign-off"],
  [/^Regards,?\s*$/im, "remove sign-off"],
  [/^Sincerely,?\s*$/im, "remove sign-off"],
  [/^Cheers,?\s*$/im, "remove sign-off"],

  // Sycophantic / collaborative artifacts (humanizer skill #19, #21)
  [/\bgreat question\b/i, "remove sycophantic opener"],
  [/\byou're absolutely right\b/i, "remove sycophantic validation"],
  [/\bcertainly!\s/i, "remove servile opener"],
  [/\bof course!\s/i, "remove servile opener"],
  [/\bI hope this helps\b/i, "remove chatbot artifact"],
  [/\blet me know if you'd like me to expand\b/i, "remove chatbot artifact"],
  [/\bhere is (?:a|an) (?:overview|summary|breakdown)\b/i, "remove chatbot preamble"],

  // Overused AI vocabulary (humanizer skill #7) that are almost never
  // appropriate in concise technical prose
  [/\bdelve\b/i, 'use "explore", "examine", or "look at"'],
  [/\btapestry\b(?!\s*\()/i, "avoid abstract metaphor"],
  [/\bpivotal\b/i, 'use "important" or "key" or be specific'],
  [/\btestament to\b/i, "just state the fact directly"],
  [/\bunderscore(?:s|d)?\b/i, 'use "shows" or "highlights" sparingly'],
  [/\bfostering\b/i, 'use "building", "encouraging", or be specific'],
  [/\bgarner(?:s|ed)?\b/i, 'use "get", "attract", or "earn"'],
  [/\bshowcas(?:e|es|ed|ing)\b/i, 'use "shows" or "demonstrates"'],
  [/\binterplay\b/i, "use a more concrete description"],
  [/\bintricate\b/i, 'use "complex" or "detailed"'],
  [/\blandscape\b(?=\s+of\b)/i, "avoid abstract 'landscape of'; be specific"],
  [/\bvibrant\b/i, "avoid promotional language"],
  [/\bgroundbreaking\b/i, "avoid promotional language; be specific about what changed"],
  [/\bseamless\b/i, "avoid promotional language"],
];

// ---------------------------------------------------------------------------
// Scan and report
// ---------------------------------------------------------------------------

function lintProse(text: string): string[] {
  const violations: string[] = [];

  for (const { name, pattern, examples } of CHAR_VIOLATIONS) {
    const matches = text.match(pattern);
    if (!matches) continue;

    const unique = [...new Set(matches)];
    const found = unique.slice(0, 5).join(" ");
    const hint = examples ? ` (${examples})` : "";
    violations.push(`${name}: found ${found}${hint}`);
  }

  for (const [pattern, suggestion] of PHRASE_VIOLATIONS) {
    if (!pattern.test(text)) continue;

    const match = text.match(pattern)?.[0] ?? "";
    violations.push(`"${match.trim()}" -> ${suggestion}`);
  }

  return violations;
}

// ---------------------------------------------------------------------------
// Plugin export
// ---------------------------------------------------------------------------

export const ProseLint: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return;

      const command = output.args?.command as string;
      if (!command) return;

      if (!isProseCommand(command)) return;

      const violations = lintProse(command);
      if (violations.length === 0) return;

      throw new Error(
        [
          "PROSE LINT VIOLATION: Content violates writing style rules.",
          "Fix these issues and retry:",
          "",
          ...violations.map((v) => `  - ${v}`),
          "",
          "Reference: AGENTS.md (Anti-Patterns, Communication Voice)",
        ].join("\n"),
      );
    },
  };
};
