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

TEAM_MEMBERS_QUERY = """
query TeamMembers($teamId: String!) {
  team(id: $teamId) {
    members {
      nodes {
        id
        name
        displayName
        email
        active
      }
    }
  }
}
"""

STATES_QUERY = """
query States($filter: WorkflowStateFilter) {
  workflowStates(filter: $filter) {
    nodes {
      id
      name
      type
      color
      position
    }
  }
}
"""

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

LABEL_CHILDREN_QUERY = """
query LabelChildren($filter: IssueLabelFilter) {
  issueLabels(filter: $filter) {
    nodes {
      id
      name
      color
    }
  }
}
"""

ISSUES_QUERY = """
query Issues(
  $filter: IssueFilter
  $first: Int
  $after: String
) {
  issues(
    first: $first
    after: $after
    filter: $filter
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      id
      identifier
      title
      description
      priority
      url
      createdAt
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
          name
        }
      }
    }
  }
}
"""

ISSUE_SEARCH_QUERY = """
query IssueSearch(
  $query: String!
  $filter: IssueFilter
  $first: Int
  $after: String
) {
  issueSearch(
    query: $query
    first: $first
    after: $after
    filter: $filter
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      id
      identifier
      title
      description
      priority
      url
      createdAt
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
          name
        }
      }
    }
  }
}
"""

ISSUE_QUERY = """
query Issue($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    url
    createdAt
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
  }
}
"""

ISSUE_CREATE_MUTATION = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
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

COMMENTS_QUERY = """
query Comments($issueId: String!, $first: Int, $after: String) {
  issue(id: $issueId) {
    comments(first: $first, after: $after) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        body
        createdAt
        updatedAt
        user {
          name
        }
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

ATTACHMENT_LINK_URL_MUTATION = """
mutation AttachmentLinkURL($issueId: String!, $url: String!, $title: String) {
  attachmentLinkURL(issueId: $issueId, url: $url, title: $title) {
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
query Projects($filter: ProjectFilter) {
  projects(filter: $filter, first: 50) {
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

PROJECT_QUERY = """
query Project($id: String!) {
  project(id: $id) {
    id
    name
    description
    state
    startDate
    targetDate
    members {
      nodes {
        name
      }
    }
    issues {
      nodes {
        identifier
        title
        state {
          name
        }
      }
    }
  }
}
"""

DOCUMENTS_QUERY = """
query Documents {
  documents(first: 50) {
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
