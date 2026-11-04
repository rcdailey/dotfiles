# Current tool to candidate tool migration

Copy to `YYYY-MM-DD-<slug>.md`, dated by the first research session. Replace every placeholder and
delete sections marked optional when empty. On each revisit, update Status, Sources read at, and the
affected sections in place; git history keeps earlier findings.

- Date: YYYY-MM-DD
- Status: Blocked | Viable | Adopted | Rejected (YYYY-MM-DD of last revisit)
- Sources read at: upstream repositories with commit and release, or product versions
- Current setup: tool in use now and the config path that defines it

## Goal

What the switch should achieve, and which differences are acceptable (for example, rebuilding
config).

## Findings

Facts about the candidate that shape the blockers, each with a file:line or URL reference.

## Blocker 1: name

What is missing and its effect. Then the evidence, any workaround, and what would remove it. Repeat
per blocker; delete the section when there are none.

## Tracked issues

Optional. Upstream issues whose state changes the verdict: `repo #N (state): summary`.

## Next check

Numbered steps that re-verify each blocker on the next revisit.
