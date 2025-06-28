# Memory Bank System Documentation

## System Overview

The Memory Bank system enables Claude Code to maintain context across sessions for long-running sessions through separate markdown files that serve as persistent logs of progress, decisions, and current state.

## Core Operating Principles

Claude MUST:

- NEVER load multiple sessions simultaneously - only one session can be loaded at a time
- NEVER automatically load sessions - user must explicitly request loading
- ALWAYS append new information and never modify historical entries for forward progress
- AUTOMATICALLY manage file consolidation and updates for maintenance
- PRESERVE decision rationale and lessons learned for context continuity

## File Structure

```txt
.memory-bank/
├── feature-implementation.md  # Example session file
└── system-refactor.md         # Another example session file
```

### Naming Conventions

- **Session files**: Use kebab-case (`feature-implementation.md`, `system-refactor.md`)

## File Discovery Protocol

Claude MUST use absolute path to git repository root (`${REPO_ROOT}`) and NEVER use relative paths for memory-bank directory, looking for session files in `${REPO_ROOT}/.memory-bank/` directory only with lazy directory creation when first session is created.

### Session Discovery Requirements

Claude MUST:

- USE the Glob tool for session discovery to ensure optimal performance
- FOLLOW primary approach: Use `Glob` with pattern `${REPO_ROOT}/.memory-bank/*.md`, apply fuzzy matching logic directly on returned filenames, process results in memory using string matching operations
- USE fallback approach: Use `LS` tool to check if `${REPO_ROOT}/.memory-bank/` directory exists
- NEVER use the Task tool for session discovery as it's inefficient for simple file pattern matching and uses significant computational resources

## Fuzzy Matching Algorithm

When users provide session names that don't exactly match existing files, Claude uses fuzzy matching:

### Matching Priority

1. **Exact substring match** (case-insensitive): `feature` matches `feature-implementation.md`
2. **Word boundary match**: `system` prioritizes `system-refactor.md` over `my-system-notes.md`
3. **Filename stem match**: `implementation` matches any `*-implementation.md` files

### Outcomes

- **Single match**: Auto-load with confirmation
- **Multiple matches**: Present numbered selection list
- **No matches**: Fail with guidance to available sessions
- **Too many matches** (>5): Request more specific input

## Loading Workflows

### Load Specific Session

**User command**: "Load memory bank feature" or "Load memory bank implementation"

**Claude actions**:

1. Use session discovery approach from Implementation Guidance section
2. Apply fuzzy matching algorithm if no exact match
3. Read the entire session file into context
4. Summarize current state and wait for user confirmation

### Load Without Specific Session

**User command**: "Load memory bank"

**Claude actions**:

1. List all available session files in numbered format
2. Ask user to select by name or number
3. Proceed with loading workflow once selection is made

### Session Loading Restrictions

Claude MUST refuse multiple session loading requests and explain single-session focus principle when users request multiple sessions simultaneously.

## Update Protocol

### Update Triggers

Claude MUST update immediately when:

- Major milestones completed, phase transitions, important decisions
- Blockers encountered/resolved, substantial progress made
- Learning discoveries, failed attempts (when instructive)
- Session ending, user requests memory bank update

### Update Process

Claude MUST complete ALL steps with no exceptions:

1. Read entire session file before changes
2. Check for consolidation triggers before adding new entries
3. Add Progress & Context Log entry with date and milestone using neutral, factual tone
4. Update ALL Current-State sections: Status/Progress, Phase, Current Focus, Next Steps
5. Update Task Checklist: Mark completed [x], add new tasks
6. Re-read to confirm completeness
7. State "Memory bank update complete"

### Update Components

- **Current-State** (replaced): Next Steps, Resources, Current Focus, Phase
- **Chronological** (append): Progress & Context Log, Task Checklist updates

### Update Verification

Claude MUST verify ALL items:

- [ ] Progress Log entry added with date and milestone
- [ ] All completed tasks marked [x]
- [ ] Status/Progress reflects current reality
- [ ] Phase updated if transitioning
- [ ] Current Focus describes actual state
- [ ] Next Steps lists actionable items

Claude MUST state "Memory bank verification complete" and return to update steps if verification fails.

## File Consolidation Protocol

Claude MUST consolidate every time new Progress & Context Log entries are added, following these rules:

- **Same-day entries**: When >3 entries exist for same date, consolidate to single daily summary
- **Recent entries**: When >10 entries exist within 7 days, consolidate by day
- **Older entries**: Apply weekly/monthly consolidation for entries >1 week old

Claude MUST preserve all technical details and decisions during consolidation, remove redundancy and improve organization while maintaining chronological order (example: "2024-01-08 - Lambda Configuration" with key technical changes and decisions).

## Phase Management

### Automatic Phase Transitions

Claude automatically updates the Phase field when detecting:

- **Planning → Implementation**: Moving from design discussions to actual coding
- **Implementation → Testing**: Beginning validation and troubleshooting
- **Testing → Complete**: All objectives achieved and validated

### Phase Indicators

- **Planning**: Discussing approach, analyzing requirements, designing solutions
- **Implementation**: Writing code, creating configurations, making changes
- **Testing**: Validating functionality, troubleshooting issues, performance testing
- **Complete**: All objectives met, session concluded

## Rabbit Trail Detection

### Detection Signals

**Flag These Deviations**:

- User requests completely unrelated objectives
- Abandoning current task for new work
- Extended discussions not blocking progress

**Allow These**:

- Addressing dependent issues or blockers
- Reasonable scope adjustments
- Brief tangents that inform current work

**Approach**: Start with minimal interference, evolve based on usage patterns.

## Session Creation Protocol

Claude NEVER proactively suggests creating new sessions and MUST wait for explicit user requests, then follow this process:

1. User requests new session creation
2. Claude creates `${REPO_ROOT}/.memory-bank/` directory if it doesn't exist
3. Claude creates file from template with user-provided session name
4. Claude fills in initial context based on current planning discussion
5. Session becomes active and ready for progress tracking

## Error Recovery

### Repository Synchronization

If memory bank state doesn't match repository reality:

**User command**: "Synchronize memory bank with repository state"

**Claude actions**:

1. Analyze repository state vs memory bank records
2. Identify discrepancies
3. Add corrective Progress & Context Log entry explaining differences
4. Update current state sections to match reality

**Note**: This is expensive and should be avoided through proper memory bank maintenance.

## Best Practices

### For Claude

- **Stay current**: Update memory bank throughout work sessions using MANDATORY Update Protocol
- **Be concise**: Consolidate information to manage file size
- **Preserve context**: Don't lose important decisions during consolidation
- **Monitor focus**: Watch for scope creep and remind user when detected

### Progress Capture Requirements

Claude MUST:

- USE neutral, factual tone without celebratory language or achievement framing
- PRESERVE all technical details, decisions, and rationale during updates
- AVOID formatting combinations (bold + caps) except for established acronyms
- FOCUS on changes made, blockers encountered, and decisions reached
- NEVER use emoji, success celebrations, or redundant congratulations
- ORGANIZE technical details in appropriate current-state sections with Progress Log capturing chronological milestones and decisions while avoiding information duplication

### Session Ending Requirements

Claude MUST complete before concluding with NO EXCEPTIONS even if user dismisses:

1. Immediate memory bank update
2. Document status in Progress Log
3. Set Next Steps
4. Complete verification
5. Confirm "Memory bank updated for session end"

Claude MUST respond "I need to update the memory bank first. 30 seconds." if user dismisses update requirement.

### For Users

- **Single session focus**: Work on one session per Claude session
- **Explicit loading**: Always specify which session to load
- **Regular updates**: Ask Claude to update memory bank before ending sessions
- **New sessions for tangents**: Start fresh Claude sessions for unrelated work

## Troubleshooting

### Common Issues

- **Session won't load**: Try fuzzy matching with partial name or "Load memory bank"
- **Multiple sessions loaded**: Restart Claude session, load single session
- **File too large**: Let consolidation handle size or manually archive
- **Fuzzy match too broad**: Use more specific terms

### File Maintenance

- **Backup important sessions**: Copy critical files before major changes
- **Archive completed sessions**: Move finished projects to archive directory
- **Monitor file sizes**: Trust consolidation rules, but verify effectiveness over time
