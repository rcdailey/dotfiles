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

Claude looks for session files in `${REPO_ROOT}/.memory-bank/` directory only. The `.memory-bank/`
directory is created lazily when the first session is created in a repository.

## Implementation Guidance

### Session Discovery

**REQUIRED**: Use the Glob tool for session discovery to ensure optimal performance.

**Primary approach**:
1. Use `Glob` with pattern `.memory-bank/*.md` to list all session files
2. Apply fuzzy matching logic directly on the returned filenames
3. Process results in memory using string matching operations

**Fallback approach**: Use `LS` tool to check if `.memory-bank/` directory exists

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

## MANDATORY Update Protocol

### CRITICAL TRIGGERS (Claude MUST update immediately)

Claude MUST update the loaded session when ANY of these occur:

- **Major milestones completed**: Finishing significant phases or key objectives
- **Phase transitions**: Moving between Planning/Implementation/Testing/Complete
- **Important decisions made**: Architectural choices, approach changes, problem-solving decisions
- **Blockers encountered/resolved**: Issues that stop progress and their solutions
- **Substantial progress made**: Before conversation concludes with meaningful work
- **Learning discoveries**: Important insights, patterns, or lessons learned
- **Failed attempts**: When they help avoid repeating ineffective approaches
- **Session ending**: Before any session concludes, regardless of reason
- **User requests**: When user explicitly asks to "save to memory bank" or "update memory bank"

### REQUIRED UPDATE STEPS (ALL must be completed)

**MANDATORY PROTOCOL**: Claude MUST complete ALL steps below, no exceptions.

1. **Read entire session file** before making any changes
2. **Add Progress & Context Log entry** with current date and milestone description
3. **Update ALL Current-State sections**:
   - Status/Progress line
   - Phase field  
   - Current Focus
   - Next Steps
4. **Update Task Checklist**: Mark completed items as [x], add new discovered tasks
5. **VERIFICATION**: Re-read updated sections to confirm completeness
6. **Confirmation**: State "✅ Memory bank update complete" before proceeding

### Update Components

**Current-State Sections** (replaced with new information):

- **Next Steps**: Current actionable items
- **Resources**: Currently relevant files, commands, references
- **Current Focus**: What we're working on right now
- **Phase**: Current stage (Planning/Implementation/Testing/Complete)

**Chronological Sections** (append new entries):

- **Progress & Context Log**: Chronological record of what happened and why
- **Task Checklist**: Check completed items, add new discovered tasks

### Update Verification Checklist

**MANDATORY**: After ANY memory bank update, Claude MUST verify ALL items below:

- [ ] New Progress & Context Log entry added with current date and clear milestone description
- [ ] All completed tasks marked as [x] in checklists
- [ ] Status/Progress field reflects current reality (not outdated information)
- [ ] Phase field updated if transitioning between stages
- [ ] Current Focus describes actual current state (not previous focus)
- [ ] Next Steps lists specific actionable items for next session

**REQUIRED CONFIRMATION**: Claude must explicitly state "✅ Memory bank verification complete" 
before proceeding with any other work.

**If verification fails**: Claude MUST return to update steps and fix all incomplete items.

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

**Example**: Daily entries become "2024-01-08 to 2024-01-11 - Feature Implementation Week" 
with key decisions and outcomes preserved.

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

- **Stay current**: Update memory bank throughout work sessions using MANDATORY Update Protocol
- **Be concise**: Consolidate information to manage file size
- **Preserve context**: Don't lose important decisions during consolidation
- **Monitor focus**: Watch for scope creep and remind user when detected

### Session Ending Protocol

**MANDATORY**: Before any session concludes, Claude MUST complete the following steps:

1. **Immediate memory bank update** with all completed work documented
2. **Document current status** and achievements in Progress & Context Log
3. **Set Next Steps** for future sessions with specific actionable items
4. **Complete verification checklist** to ensure nothing was missed
5. **Confirm session readiness** to end with "✅ Memory bank updated for session end"

**No exceptions**: Even if user says "we're done" or "stop working," memory bank MUST be updated 
first. This ensures no progress is lost and future sessions can continue seamlessly.

**User dismissal handling**: If user insists on ending without updates, Claude must respond: 
"I need to update the memory bank first to preserve our progress. This will take 30 seconds."

### For Users

- **Single session focus**: Work on one session per Claude session
- **Explicit loading**: Always specify which session to load
- **Regular updates**: Ask Claude to update memory bank before ending sessions
- **New sessions for tangents**: Start fresh Claude sessions for unrelated work

## Troubleshooting

### Common Issues

- **Session won't load**: Try fuzzy matching with partial name, or use "Load memory bank" to see all available sessions
- **Multiple sessions loaded**: Restart Claude session, load single session  
- **File too large**: Let consolidation rules handle size, or manually archive old content
- **Context lost**: Use repository synchronization as last resort
- **Fuzzy match too broad**: Use more specific terms (e.g., "feature" instead of "f")
- **No fuzzy matches**: Session may not exist; check available sessions or create new session during active work

### File Maintenance

- **Backup important sessions**: Copy critical files before major changes
- **Archive completed sessions**: Move finished projects to archive directory  
- **Monitor file sizes**: Trust consolidation rules, but verify effectiveness over time
