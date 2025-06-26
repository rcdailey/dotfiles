# Memory Bank System Documentation

## Overview

The Memory Bank system enables Claude Code to maintain context across sessions for long-running
sessions. Each session is tracked in a separate markdown file that serves as a persistent log of
progress, decisions, and current state.

## Core Principles

- **Single Session Focus**: Only one session can be loaded at a time
- **User-Controlled Loading**: Claude never automatically loads sessions
- **Forward Progress**: Always append new information, never modify historical entries
- **Automatic Maintenance**: Claude manages file consolidation and updates
- **Learning Context**: Preserve decision rationale and lessons learned

## File Structure

```txt
.memory-bank/
├── feature-implementation.md  # Example session file
└── system-refactor.md         # Another example session file
```

### Naming Conventions

- **Session files**: Use kebab-case (`feature-implementation.md`, `system-refactor.md`)

## Discovery

**REQUIRED**: `${REPO_ROOT}` = absolute path to git repository root. Claude MUST use absolute path
to repo root, NEVER relative paths for memory-bank directory.

Claude looks for session files in `${REPO_ROOT}/.memory-bank/` directory only. The `.memory-bank/`
directory is created lazily when the first session is created in a repository.

## Implementation Guidance

### Session Discovery

**REQUIRED**: Use the Glob tool for session discovery to ensure optimal performance.

**Primary approach**:

1. Use `Glob` with pattern `${REPO_ROOT}/.memory-bank/*.md` to list all session files
2. Apply fuzzy matching logic directly on the returned filenames
3. Process results in memory using string matching operations

**Fallback approach**: Use `LS` tool to check if `${REPO_ROOT}/.memory-bank/` directory exists

**PROHIBITED**: Never use the Task tool for session discovery - it's inefficient for simple file
pattern matching and uses significant computational resources.

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

### Multiple Session Prohibition

**Strictly forbidden**: Loading multiple sessions simultaneously

**If user requests multiple sessions**: Claude must refuse, explaining single-session focus principle

## Update Protocol

### CRITICAL TRIGGERS (Claude MUST update immediately)

- Major milestones completed, phase transitions, important decisions
- Blockers encountered/resolved, substantial progress made
- Learning discoveries, failed attempts (when instructive)
- Session ending, user requests memory bank update

### REQUIRED STEPS (ALL must be completed)

**MANDATORY**: Claude MUST complete ALL steps, no exceptions.

1. Read entire session file before changes
2. Add Progress & Context Log entry with date and milestone
3. Update ALL Current-State sections: Status/Progress, Phase, Current Focus, Next Steps
4. Update Task Checklist: Mark completed [x], add new tasks
5. **VERIFICATION**: Re-read to confirm completeness
6. State "✅ Memory bank update complete"

### Update Components

**Current-State** (replaced): Next Steps, Resources, Current Focus, Phase
**Chronological** (append): Progress & Context Log, Task Checklist updates

### MANDATORY Verification

**MUST verify ALL items:**

- [ ] Progress Log entry added with date and milestone
- [ ] All completed tasks marked [x]
- [ ] Status/Progress reflects current reality
- [ ] Phase updated if transitioning
- [ ] Current Focus describes actual state
- [ ] Next Steps lists actionable items

**REQUIRED**: "✅ Memory bank verification complete"
**If fails**: MUST return to update steps

## File Consolidation Rules

### Automatic Consolidation

**Trigger**: Every time Claude adds new Progress & Context Log entries

**Time-Based Rollup Rules**:

- **Entries older than 1 week**: Consolidate to weekly summary entries
- **Entries older than 1 month**: Consolidate to monthly summary entries

**Process**: Identify entries in time ranges, create summary preserving key decisions, replace individual entries, maintain chronological order.

**Example**: "2024-01-08 to 2024-01-11 - Feature Implementation Week" with key outcomes.

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

## Session Creation

### User-Triggered Only

Claude never proactively suggests creating new sessions. Users must explicitly request session
creation.

### Creation Process

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

### Session Ending Protocol

**MANDATORY before concluding:**

1. Immediate memory bank update
2. Document status in Progress Log
3. Set Next Steps
4. Complete verification
5. Confirm "✅ Memory bank updated for session end"

**NO EXCEPTIONS**: MUST update even if user dismisses.
**Response**: "I need to update the memory bank first. 30 seconds."

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
