# Memory Bank System Documentation

## System Overview

The Memory Bank system enables Claude Code to maintain context across sessions for long-running
sessions through separate markdown files that serve as persistent logs of progress, decisions, and
current state.

## Core Operating Principles

Claude MUST:

- NEVER load multiple sessions simultaneously - only one session can be loaded at a time
- NEVER automatically load sessions - user must explicitly request loading
- ALWAYS append new information and never modify historical entries for forward progress
- AUTOMATICALLY manage file consolidation and updates for maintenance
- PRESERVE decision rationale and lessons learned for context continuity
- MAINTAIN template structure compliance at all times
- CONDENSE all sections meaningfully, not just Progress & Context Log

## File Structure

```txt
.memory-bank/
├── feature-implementation.md  # Example session file
└── system-refactor.md         # Another example session file
```

### Naming Conventions

- **Session files**: Use kebab-case (`feature-implementation.md`, `system-refactor.md`)

## File Discovery Protocol

Claude MUST use absolute path to git repository root (`${REPO_ROOT}`) and NEVER use relative paths
for memory-bank directory, looking for session files in `${REPO_ROOT}/.memory-bank/` directory only
with lazy directory creation when first session is created.

### Session Discovery Requirements

Claude MUST:

- USE the Glob tool for session discovery to ensure optimal performance
- FOLLOW primary approach: Use `Glob` with pattern `${REPO_ROOT}/.memory-bank/*.md`, apply fuzzy
  matching logic directly on returned filenames, process results in memory using string matching
  operations
- USE fallback approach: Use `LS` tool to check if `${REPO_ROOT}/.memory-bank/` directory exists
- NEVER use the Task tool for session discovery as it's inefficient for simple file pattern matching
  and uses significant computational resources

## Fuzzy Matching Algorithm

When users provide session names that don't exactly match existing files, Claude uses fuzzy
matching:

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

Claude MUST refuse multiple session loading requests and explain single-session focus principle when
users request multiple sessions simultaneously.

## Update Protocol

### Update Triggers

Claude MUST update immediately when:

- Major milestones completed, phase transitions, important decisions
- Blockers encountered/resolved, substantial progress made
- Learning discoveries, failed attempts (when instructive)
- Session ending, user requests memory bank update

### Update Process

**CRITICAL**: This is a mandatory 8-step sequential process. Each step MUST be completed before
proceeding to the next. NO selective execution or step skipping allowed.

#### Step 1: Pre-Update File Read

- Read entire session file before making any changes
- Understand current state and existing entries
- **Cannot proceed to Step 2 without completing this step**

#### Step 2: Mandatory Consolidation

- Apply Consolidation Decision Tree (see below)
- If triggers apply, consolidate entries BEFORE adding new content
- **Cannot proceed to Step 3 without completing consolidation check**

#### Step 3: Progress Log Entry

- Add Progress & Context Log entry with date and milestone
- Use neutral, factual tone
- **Cannot proceed to Step 4 without adding this entry**

#### Step 4: Current-State Updates

- Update ALL Current-State sections (Status/Progress, Phase, Current Focus, Next Steps)
- **Cannot proceed to Step 5 without updating ALL sections**

#### Step 5: Task Checklist Updates

- Mark completed tasks [x]
- Add new tasks discovered during work
- **Cannot proceed to Step 6 without task updates**

#### Step 6: Completeness Verification

- Re-read entire file to confirm all changes are present
- **Cannot proceed to Step 7 without re-reading file**

#### Step 7: Mandatory Verification

- Complete verification checklist (see Update Verification section)
- **Cannot proceed to Step 8 without passing verification**

#### Step 8: Update Completion

- State "Memory bank update complete" ONLY after verification passes
- **Process is not complete until this statement is made**

**SEQUENCING ENFORCEMENT**: If any step is incomplete, Claude MUST return to that step and complete
it before proceeding. The process is LINEAR and MANDATORY.

### Update Components

- **Current-State** (replaced): Next Steps, Resources, Current Focus, Phase
- **Chronological** (append): Progress & Context Log, Task Checklist updates

## Rule Compliance Warning

**CRITICAL BEHAVIORAL PATTERN ALERT**: The following patterns indicate selective rule compliance and
are FORBIDDEN:

### Prohibited Behaviors

- **Consolidation Avoidance**: Ignoring consolidation step because it seems "optional"
- **Partial Updates**: Updating only Current Focus/Next Steps while ignoring Status/Progress/Phase
- **Verification Skipping**: Treating verification as optional rather than mandatory
- **Process Shortcuts**: Jumping to step 8 without completing steps 1-7
- **Selective Execution**: Choosing which rules to follow based on convenience

### Compliance Enforcement

**If these patterns are detected, Claude MUST**:

1. **Immediately halt** current activity
2. **Return to Step 1** of Update Process
3. **Complete the full 8-step process** with no exceptions
4. **State "Correcting rule compliance failure"** before restarting

### Root Cause Analysis

**Why selective compliance occurs**:

- Treating consolidation as "maintenance" rather than mandatory step
- Viewing verification as "optional confirmation" rather than required gate
- Prioritizing speed over process integrity
- Assuming partial updates are "good enough"

**The solution**: Every step is mandatory, every time, with no exceptions. Process integrity is
non-negotiable.

### Update Verification

**MANDATORY VERIFICATION**: Claude MUST explicitly verify ALL items before declaring update
complete.

**VERIFICATION CHECKLIST** (must check each item):

- [ ] **Template structure compliance** verified (only authorized top-level sections)
- [ ] **Comprehensive consolidation performed** (all sections evaluated, not just Progress Log)
- [ ] **Progress Log entry added** with date and milestone
- [ ] **All completed tasks marked [x]** in Task Checklist
- [ ] **Status/Progress updated** to reflect current reality
- [ ] **Phase updated** if transitioning between phases
- [ ] **Current Focus updated** to describe actual current state
- [ ] **Next Steps updated** with actionable items
- [ ] **Resources section updated** if new tools/files/references added
- [ ] **File size targets met** (session <500 lines, Resources <150 lines)

**VERIFICATION ENFORCEMENT**:

- Claude MUST state "Memory bank verification complete" ONLY after ALL items pass
- If ANY verification item fails, Claude MUST return to step 4 and complete missing updates
- The update process is NOT complete until verification passes
- Claude MUST NOT proceed with other tasks until verification is complete

**VERIFICATION FAILURE PROTOCOL**:

- State "Verification failed - returning to update steps"
- Identify which items failed verification
- Complete the missing updates
- Re-run verification checklist
- Only proceed after stating "Memory bank verification complete"

## Template Structure Compliance

**MANDATORY**: Claude MUST maintain exact template structure hierarchy at all times.

### Template Structure Enforcement

Claude MUST:

- MAINTAIN exact template top-level section structure (Status, Objective, Current Focus, Task
  Checklist, Next Steps, Resources, Progress & Context Log)
- NEVER create unauthorized top-level sections beyond template structure
- PLACE all implementation details, architecture decisions, tool references, and detailed
  documentation under **Resources** as sub-sections
- VERIFY template compliance during every update process
- RESTRUCTURE existing sessions that violate template hierarchy

### Authorized Top-Level Sections

**ONLY these sections allowed**:

- **Status**: Current phase and progress metrics
- **Objective**: What we're achieving and why
- **Current Focus**: Current actionable item
- **Task Checklist**: Organized task lists with completion tracking
- **Next Steps**: Actionable items for next session
- **Resources**: ALL supporting information as sub-sections
- **Progress & Context Log**: Chronological entries only

### Resources Sub-Section Organization

**All detailed content MUST be organized under Resources**:

- **Resources/Implementation Plans**: Detailed migration plans, architecture decisions
- **Resources/Tool References**: App-scout, scripts, methodology documentation
- **Resources/Configuration Patterns**: Solution patterns, lessons learned
- **Resources/Configuration Files**: File paths, commands, references
- **Resources/Network Configuration**: Network settings, IPs, domains
- **Resources/Node Details**: Hardware specifications, device paths
- **Resources/Storage Strategy**: Storage configurations, mount points
- **Resources/Service Information**: Categories, complexity considerations, timelines

### Structure Violation Correction

**When template violations detected, Claude MUST**:

1. **Immediately restructure** violating sections under Resources
2. **Maintain all content** while correcting hierarchy
3. **Update verification checklist** to include template compliance
4. **State "Template structure corrected"** after restructuring

## File Consolidation Protocol

**MANDATORY**: Consolidation MUST occur across ALL sections every time updates are made, not just
Progress & Context Log.

### Comprehensive Consolidation Decision Tree

**Step 1**: Evaluate ALL sections for consolidation opportunities

**Step 2**: Apply consolidation rules by section type:

#### Progress & Context Log Consolidation

1. **Same-day entries** (>3 entries for same date):
   - **Trigger**: 4+ entries with same date
   - **Action**: Consolidate to single daily summary
   - **Example**: "2025-07-10 - CUPS Configuration" (combined 4 entries about printer setup)

2. **Recent entries** (>10 entries within 7 days):
   - **Trigger**: 11+ entries within past 7 days
   - **Action**: Consolidate by day, keeping technical details
   - **Example**: "2025-07-03 - Database Migration" (combined 3 entries from same day)

3. **Older entries** (>1 week old with >5 entries per week):
   - **Trigger**: More than 5 entries in any week older than 7 days
   - **Action**: Weekly consolidation with monthly rollup for >4 weeks old
   - **Example**: "2025-06-24 to 2025-06-30 - Authentication Refactor" (weekly summary)

#### Resources Section Consolidation

1. **Duplicate information** across sub-sections:
   - **Trigger**: Same information appearing in multiple Resources sub-sections
   - **Action**: Consolidate to single authoritative location with cross-references

2. **Verbose explanations** (>50 lines per sub-section):
   - **Trigger**: Any Resources sub-section exceeding 50 lines
   - **Action**: Extract detailed content to external documentation, keep essential references

3. **Outdated content** (>4 weeks old, no longer relevant):
   - **Trigger**: Implementation details for completed phases
   - **Action**: Archive or condense to decision summary only

#### Task Checklist Consolidation

**EXEMPT**: Task Checklist section is EXEMPT from all consolidation rules to maintain detailed
tracking capabilities and progress visibility. Task Checklist MUST remain in its original detailed
format regardless of file size or consolidation triggers.

**Step 3**: If any consolidation triggers apply, consolidate BEFORE adding new content

**Step 4**: Preserve ALL technical details, decisions, and rationale during consolidation

### File Size Management

**Target file sizes**:

- **Active sessions**: 300-500 lines maximum
- **Resources section**: 100-150 lines maximum
- **Progress Log**: 50-100 lines maximum
- **Task Checklist**: EXEMPT from size limits (detailed tracking required)

**Consolidation triggers**:

- **File exceeds 500 lines**: Mandatory comprehensive consolidation (excluding Task Checklist)
- **Any section exceeds target**: Section-specific consolidation required (excluding Task Checklist)
- **Weekly maintenance**: Regular consolidation regardless of size (excluding Task Checklist)

### Consolidation Examples

**Before consolidation**:

```txt
2025-07-10 - Started CUPS removal
2025-07-10 - Identified printer configurations
2025-07-10 - Removed LaunchDaemons
2025-07-10 - Updated chezmoi ignore patterns
```

**After consolidation**:

```txt
2025-07-10 - CUPS Removal Complete
Removed CUPS printer system: identified configs in LaunchDaemons, removed daemon files, updated chezmoi ignore patterns to exclude printer-related files. Decision: Full removal preferred over selective cleanup.
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

Claude NEVER proactively suggests creating new sessions and MUST wait for explicit user requests,
then follow this process:

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
- ORGANIZE technical details in appropriate current-state sections with Progress Log capturing
  chronological milestones and decisions while avoiding information duplication

### Session Ending Requirements

Claude MUST complete before concluding with NO EXCEPTIONS even if user dismisses:

1. Immediate memory bank update
2. Document status in Progress Log
3. Set Next Steps
4. Complete verification
5. Confirm "Memory bank updated for session end"

Claude MUST respond "I need to update the memory bank first. 30 seconds." if user dismisses update
requirement.

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
