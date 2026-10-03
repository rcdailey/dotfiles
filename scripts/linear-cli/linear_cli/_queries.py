"""GraphQL query and mutation strings for the Linear API."""

from __future__ import annotations

VIEWER_QUERY = """
query {
  viewer {
    id
    name
    displayName
    email
    active
  }
}
"""

TEAMS_QUERY = """
query {
  teams {
    nodes {
      id
      key
      name
    }
  }
}
"""

USER_FIELDS = "id name displayName email active"

STATE_FIELDS = "id name type color position"

STATES_QUERY = f"query States {{ workflowStates {{ nodes {{ {STATE_FIELDS} }} }} }}"

LABELS_QUERY = """
query Labels($filter: IssueLabelFilter, $first: Int, $after: String) {
  issueLabels(filter: $filter, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      id
      name
      color
      isGroup
      parent {
        id
        name
      }
    }
  }
}
"""

LABEL_GROUPS_QUERY = """
query LabelGroups($filter: IssueLabelFilter) {
  issueLabels(filter: $filter) {
    nodes {
      id
      name
      color
    }
  }
}
"""

# Fields echo_issue_summary renders; keep list queries to exactly this set.
ISSUE_SUMMARY_FIELDS = """
      id
      identifier
      title
      priority
      estimate
      url
      createdAt
      startedAt
      completedAt
      updatedAt
      state { name type }
      assignee { name }
      labels { nodes { name } }
"""

ISSUE_CONNECTION = f"pageInfo {{ hasNextPage endCursor }} nodes {{ {ISSUE_SUMMARY_FIELDS} }}"

ISSUES_QUERY = f"""
query Issues($filter: IssueFilter, $first: Int, $after: String) {{
  issues(first: $first, after: $after, filter: $filter) {{ {ISSUE_CONNECTION} }}
}}
"""

ISSUE_SEARCH_QUERY = f"""
query SearchIssues($term: String!, $filter: IssueFilter, $first: Int, $after: String) {{
  searchIssues(term: $term, first: $first, after: $after, filter: $filter) {{
    {ISSUE_CONNECTION}
  }}
}}
"""

COMMENT_FIELDS = """
        id
        body
        createdAt
        updatedAt
        parent { id }
        user { name }
        externalUser { name }
        botActor { name }
        syncedWith { service }
"""

# $withComments embeds the first page of full comments under the "commentThread" alias; the plain
# "comments" field then carries only IDs for the count, matching the --json shape without it.
ISSUE_QUERY = """
query Issue($id: String!, $withComments: Boolean!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    estimate
    url
    createdAt
    startedAt
    completedAt
    updatedAt
    state {
      name
      type
    }
    assignee {
      name
    }
    labels {
      nodes {
        id
        name
      }
    }
    team {
      id
      key
    }
    project {
      id
      name
      state
    }
    projectMilestone {
      id
      name
    }
    parent {
      identifier
      title
    }
    children {
      nodes {
        identifier
        title
        state { name }
        priority
        assignee { name }
        labels { nodes { name } }
        estimate
        createdAt
        startedAt
        completedAt
        updatedAt
      }
    }
    comments @skip(if: $withComments) {
      nodes { id }
    }
    commentThread: comments(first: 100) @include(if: $withComments) {
      pageInfo { hasNextPage endCursor }
      nodes { COMMENT_FIELDS }
    }
  }
}
""".replace("COMMENT_FIELDS", COMMENT_FIELDS)

ISSUE_UPDATE_MUTATION = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue {
      id
      identifier
      title
      url
    }
  }
}
"""

COMMENT_CREATE_MUTATION = """
mutation CommentCreate($issueId: String!, $body: String!, $parentId: String) {
  commentCreate(input: { issueId: $issueId, body: $body, parentId: $parentId }) {
    success
    comment {
      id
      body
      createdAt
    }
  }
}
"""

COMMENTS_QUERY = f"""
query Comments($issueId: String!, $first: Int, $after: String) {{
  issue(id: $issueId) {{
    comments(first: $first, after: $after) {{
      pageInfo {{ hasNextPage endCursor }}
      nodes {{ {COMMENT_FIELDS} }}
    }}
  }}
}}
"""

ISSUE_HISTORY_QUERY = """
query IssueHistory($id: String!, $first: Int, $after: String) {
  issue(id: $id) {
    history(first: $first, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        createdAt
        actor { name }
        botActor { name }
        fromState { name }
        toState { name }
        fromAssignee { name }
        toAssignee { name }
        fromPriority
        toPriority
        fromEstimate
        toEstimate
        fromTitle
        toTitle
        addedLabels { name }
        removedLabels { name }
        fromProject { name }
        toProject { name }
        fromProjectMilestone { name }
        toProjectMilestone { name }
        fromCycle { number }
        toCycle { number }
        fromParent { identifier }
        toParent { identifier }
        fromTeam { key }
        toTeam { key }
        fromDueDate
        toDueDate
        updatedDescription
        attachment { title url }
        relationChanges { identifier type }
        archived
        trashed
      }
    }
  }
}
"""

COMMENT_UPDATE_MUTATION = """
mutation CommentUpdate($id: String!, $body: String!) {
  commentUpdate(id: $id, input: { body: $body }) {
    success
    comment {
      id
      body
      updatedAt
    }
  }
}
"""

ISSUE_RELATIONS_QUERY = """
query IssueRelations($id: String!) {
  issue(id: $id) {
    relations {
      nodes {
        id
        type
        relatedIssue {
          identifier
          title
        }
      }
    }
    inverseRelations {
      nodes {
        id
        type
        issue {
          identifier
          title
        }
      }
    }
  }
}
"""

ISSUE_RELATION_CREATE_MUTATION = """
mutation IssueRelationCreate($input: IssueRelationCreateInput!) {
  issueRelationCreate(input: $input) {
    success
    issueRelation {
      id
      type
    }
  }
}
"""

ISSUE_RELATION_DELETE_MUTATION = """
mutation IssueRelationDelete($id: String!) {
  issueRelationDelete(id: $id) {
    success
  }
}
"""

ATTACHMENTS_QUERY = """
query Attachments($id: String!) {
  issue(id: $id) {
    attachments {
      nodes {
        id
        title
        url
      }
    }
  }
}
"""

ATTACHMENT_CREATE_MUTATION = """
mutation AttachmentCreate($input: AttachmentCreateInput!) {
  attachmentCreate(input: $input) {
    success
    attachment {
      id
      title
      url
    }
  }
}
"""

ATTACHMENT_DELETE_MUTATION = """
mutation AttachmentDelete($id: String!) {
  attachmentDelete(id: $id) {
    success
  }
}
"""

PROJECTS_QUERY = """
query Projects($filter: ProjectFilter, $first: Int, $after: String) {
  projects(filter: $filter, first: $first, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      id
      name
      state
      startDate
      targetDate
    }
  }
}
"""

PROJECT_CREATE_MUTATION = """
mutation ProjectCreate($input: ProjectCreateInput!) {
  projectCreate(input: $input) {
    success
    project {
      id
      name
      url
    }
  }
}
"""

PROJECT_UPDATE_MUTATION = """
mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
  projectUpdate(id: $id, input: $input) {
    success
    project {
      id
      name
      description
    }
  }
}
"""

PROJECT_UPDATE_FIELDS = "id body health createdAt user { name }"

# Every issue is fetched so milestone counts are exact; the view prints only a sorted slice.
PROJECT_ISSUE_CONNECTION = """
    pageInfo { hasNextPage endCursor }
    nodes {
      identifier title createdAt startedAt completedAt updatedAt
      state { name type }
      projectMilestone { id }
    }
"""

# Selection for `projects view`, embedded in a by-name or by-UUID projects lookup.
PROJECT_FIELDS = """
    id
    name
    url
    description
    content
    state
    startDate
    targetDate
    externalLinks {
      nodes {
        label
        url
      }
    }
    members {
      nodes {
        name
      }
    }
    teams {
      nodes {
        key
        name
        states {
          nodes {
            name
            type
            position
          }
        }
      }
    }
    issues(first: 250) { PROJECT_ISSUE_CONNECTION }
    projectMilestones {
      nodes {
        id
        name
        targetDate
        status
        progress
      }
    }
    projectUpdates(first: 3, orderBy: createdAt) {
      nodes { PROJECT_UPDATE_FIELDS }
    }
""".replace("PROJECT_UPDATE_FIELDS", PROJECT_UPDATE_FIELDS).replace(
    "PROJECT_ISSUE_CONNECTION", PROJECT_ISSUE_CONNECTION
)

# Continues the project's issue pages after the first page embedded in PROJECT_FIELDS.
PROJECT_ISSUES_QUERY = f"""
query ProjectIssues($id: String!, $first: Int, $after: String) {{
  project(id: $id) {{ issues(first: $first, after: $after) {{ {PROJECT_ISSUE_CONNECTION} }} }}
}}
"""

MILESTONE_FIELDS = "id name description targetDate status progress"

MILESTONE_CREATE_MUTATION = """
mutation ProjectMilestoneCreate($input: ProjectMilestoneCreateInput!) {
  projectMilestoneCreate(input: $input) {
    success
    projectMilestone {
      id
      name
    }
  }
}
"""

MILESTONE_UPDATE_MUTATION = """
mutation ProjectMilestoneUpdate($id: String!, $input: ProjectMilestoneUpdateInput!) {
  projectMilestoneUpdate(id: $id, input: $input) {
    success
    projectMilestone {
      id
      name
    }
  }
}
"""

MILESTONE_DELETE_MUTATION = """
mutation ProjectMilestoneDelete($id: String!) {
  projectMilestoneDelete(id: $id) {
    success
  }
}
"""

PROJECT_UPDATES_ALL_QUERY = """
query ProjectUpdatesAll($first: Int, $after: String) {
  projectUpdates(first: $first, after: $after, orderBy: createdAt) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      body
      health
      createdAt
      user { name }
      project { name }
    }
  }
}
"""

DOCUMENTS_QUERY = """
query Documents($filter: DocumentFilter) {
  documents(first: 50, filter: $filter) {
    nodes {
      id
      title
      updatedAt
      project {
        name
      }
    }
  }
}
"""

PROJECT_UPDATE_CREATE_MUTATION = """
mutation ProjectUpdateCreate($input: ProjectUpdateCreateInput!) {
  projectUpdateCreate(input: $input) {
    success
    projectUpdate {
      id
      health
      createdAt
      url
    }
  }
}
"""

DOCUMENT_QUERY = """
query Document($id: String!) {
  document(id: $id) {
    id
    title
    content
    updatedAt
    project {
      name
    }
    creator {
      name
    }
  }
}
"""
