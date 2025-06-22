# Memory Bank System Documentation

## Overview

The Memory Bank system enables Claude Code to maintain context across sessions for
long-running sessions. Each session is tracked in a separate markdown file that
serves as a persistent log of progress, decisions, and current state.

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

Claude looks for session files in `${REPO_ROOT}/.memory-bank/` directory only. The `.memory-bank/` directory is created lazily when the first session is created in a repository.

## Loading Workflows

### Load Specific Session

**User command**: "Load memory bank feature-implementation" or "Load memory bank
feature-implementation.md"

**Claude actions**:

1. Read the entire session file into context
2. Summarize current state: "Here's what we did last, here's what's next"
3. Wait for user confirmation to proceed or deviate from planned next steps

### Load Without Specific Session

**User command**: "Load memory bank"

**Claude actions**:

1. List all available session files in numbered format
2. Ask user to select by name or number
3. Proceed with loading workflow once selection is made

### Multiple Session Prohibition

**Strictly forbidden**: Loading multiple sessions simultaneously

**If user requests multiple sessions**: Claude must refuse under all circumstances,
explaining the single-session focus principle

## Automatic Update System

### Update Triggers

Claude automatically updates the loaded session when:

- **Major milestones completed**: Finishing significant phases or key objectives
- **Important decisions made**: Architectural choices, approach changes, problem-solving
  decisions
- **Blockers encountered/resolved**: Issues that stop progress and their solutions
- **Substantial progress made**: Before conversation concludes with meaningful work
- **Learning discoveries**: Important insights, patterns, or lessons learned
- **Failed attempts**: When they help avoid repeating ineffective approaches

### Update Components

**Current-State Sections** (replaced with new information):

- **Next Steps**: Current actionable items
- **Resources**: Currently relevant files, commands, references
- **Current Focus**: What we're working on right now
- **Phase**: Current stage (Planning/Implementation/Testing/Complete)

**Chronological Sections** (append new entries):

- **Progress & Context Log**: Chronological record of what happened and why
- **Task Checklist**: Check completed items, add new discovered tasks

## File Consolidation Rules

### Automatic Consolidation

**Trigger**: Every time Claude adds new Progress & Context Log entries

**Time-Based Rollup Rules**:

- **Entries older than 1 week**: Consolidate to weekly summary entries
- **Entries older than 1 month**: Consolidate to monthly summary entries

**Consolidation Process**:

1. Identify entries within consolidation time ranges
2. Create summary entry preserving key decisions and context
3. Replace individual entries with consolidated summary
4. Maintain chronological order

**Example Consolidation**:

Before:

```markdown
### 2024-01-08 - Started feature implementation
### 2024-01-09 - Added database schema
### 2024-01-10 - Implemented API endpoints
### 2024-01-11 - Completed unit tests
```

After (one week later):

```markdown
### 2024-01-08 to 2024-01-11 - Feature Implementation Week
Completed full feature implementation. Key decisions: Used database schema
migration, implemented REST API endpoints. All unit tests passing,
feature ready for integration testing.
```

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

### Conservative Detection Approach

Start with minimal interference, evolve based on real usage patterns.

### Initial Detection Signals

**Clear Deviations** (flag these):

- User explicitly requests working on completely unrelated objectives
- Abandoning current task entirely for new work
- Extended discussions on topics not blocking current progress

**Allow Flexibility** (don't flag these):

- Addressing dependent issues or blockers
- Reasonable scope adjustments within session boundaries
- Brief tangents that inform the current work

### Evolutionary Improvement

**Pattern Documentation**: When rabbit trails are detected, Claude can suggest:
"Should I document this pattern in the memory bank system-docs for future reference?"

**Example Documentation Format**:

```markdown
### Rabbit Trail Pattern: [Brief Description]
**Detected**: [Date]
**Context**: [What we were working on]
**Deviation**: [What the tangent was]
**Resolution**: [How it was handled]
**Learning**: [Why this pattern should be detected/allowed]
```

## Session Creation

### User-Triggered Only

Claude never proactively suggests creating new sessions. Users must explicitly
request session creation.

### Creation Process

1. User requests new session creation
2. Claude creates `.memory-bank/` directory if it doesn't exist
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

- **Stay current**: Update memory bank throughout work sessions
- **Be concise**: Consolidate information to manage file size
- **Preserve context**: Don't lose important decisions during consolidation
- **Monitor focus**: Watch for scope creep and remind user when detected

### For Users

- **Single session focus**: Work on one session per Claude session
- **Explicit loading**: Always specify which session to load
- **Regular updates**: Ask Claude to update memory bank before ending sessions
- **New sessions for tangents**: Start fresh Claude sessions for unrelated work

## Troubleshooting

### Common Issues

**Session won't load**: Check file exists and uses correct naming convention
**Multiple sessions loaded**: Restart Claude session, load single session
**File too large**: Let consolidation rules handle size, or manually archive old content
**Context lost**: Use repository synchronization as last resort

### File Maintenance

**Backup important sessions**: Copy critical files before major changes
**Archive completed sessions**: Move finished projects to archive directory
**Monitor file sizes**: Trust consolidation rules, but verify effectiveness over time