# linear-cli design rules

LLM agents are the only users. Agents learn the CLI from `linear --help` and the skill at
`home/dot_config/opencode/exact_skills/linear-cli/SKILL.md`. Update both in the same change as the
behavior they describe.

## Output

- Commands print compact text: the fields an agent needs to answer without a follow-up call or shell
  post-processing, and no fields that only add tokens.
- MUST NOT add `--json` options. JSON costs more tokens, and a need for it means the text output
  lacks a field. Add the field to the text output.
- `linear api` is the only JSON output. It is the raw GraphQL fallback for data that no command
  provides.
- Output format and flags may change freely; there is no backward-compatibility contract.

## Gap analysis

When reviewing OpenCode sessions for CLI gaps, treat these as evidence of a missing capability:

- `linear api` calls.
- Workarounds on command output: `rg`/`sed`/`cut` filtering, shell loops over IDs, or piping
  `issue list` into a text search.

Close a gap with a first-class command, option, or output field. One-off aggregations (counts, joins
across projects) belong in `linear api` and are not gaps.
