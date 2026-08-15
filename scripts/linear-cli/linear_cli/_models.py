"""Dataclasses mapping Linear GraphQL response fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self


def priority_label(p: int) -> str:
    """Map Linear priority integer to human-readable label."""
    return {0: "None", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}.get(p, str(p))


@dataclass
class User:
    """Linear user."""

    id: str | None
    name: str | None
    display_name: str | None
    email: str | None
    active: bool

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        """Build from a GraphQL viewer/user node."""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            display_name=data.get("displayName"),
            email=data.get("email"),
            active=bool(data.get("active", True)),
        )


@dataclass
class Team:
    """Linear team."""

    id: str | None
    key: str | None
    name: str | None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        return cls(
            id=data.get("id"),
            key=data.get("key"),
            name=data.get("name"),
        )


@dataclass
class State:
    """Linear workflow state."""

    id: str | None
    name: str | None
    type: str | None
    color: str | None
    position: float | None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        pos = data.get("position")
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            type=data.get("type"),
            color=data.get("color"),
            position=float(pos) if pos is not None else None,
        )


@dataclass
class Label:
    """Linear issue label."""

    id: str | None
    name: str | None
    color: str | None
    is_group: bool = False
    parent_name: str | None = None
    children: list[str] = field(default_factory=list)

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        parent = data.get("parent") or {}
        child_nodes = (data.get("children") or {}).get("nodes", [])
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            color=data.get("color"),
            is_group=bool(data.get("isGroup")),
            parent_name=parent.get("name"),
            children=[c.get("name", "") for c in child_nodes if c.get("name")],
        )


@dataclass
class Issue:
    """Linear issue."""

    id: str | None
    identifier: str | None
    title: str | None
    description: str | None
    state_name: str | None
    state_type: str | None
    priority: int
    assignee_name: str | None
    labels: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    url: str | None = None
    estimate: float | None = None
    parent_identifier: str | None = None
    parent_title: str | None = None
    children: list[dict] = field(default_factory=list)
    comment_count: int = 0
    project_name: str | None = None
    project_state: str | None = None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        state = data.get("state") or {}
        assignee = data.get("assignee") or {}
        label_nodes = (data.get("labels") or {}).get("nodes", [])
        raw_estimate = data.get("estimate")
        parent = data.get("parent") or {}
        child_nodes = (data.get("children") or {}).get("nodes", [])
        comment_nodes = (data.get("comments") or {}).get("nodes", [])
        project = data.get("project") or {}
        comment_count = len(comment_nodes)
        return cls(
            id=data.get("id"),
            identifier=data.get("identifier"),
            title=data.get("title"),
            description=data.get("description"),
            state_name=state.get("name"),
            state_type=state.get("type"),
            priority=int(data.get("priority", 0)),
            assignee_name=assignee.get("name"),
            labels=[ln.get("name", "") for ln in label_nodes if ln.get("name")],
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            url=data.get("url"),
            estimate=float(raw_estimate) if raw_estimate is not None else None,
            parent_identifier=parent.get("identifier"),
            parent_title=parent.get("title"),
            children=child_nodes,
            comment_count=comment_count,
            project_name=project.get("name"),
            project_state=project.get("state"),
        )


@dataclass
class Comment:
    """Linear issue comment."""

    id: str | None
    body: str | None
    user_name: str | None
    created_at: str | None
    updated_at: str | None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        user = data.get("user") or {}
        return cls(
            id=data.get("id"),
            body=data.get("body"),
            user_name=user.get("name"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


@dataclass
class Relation:
    """Linear issue relation."""

    id: str | None
    type: str | None
    related_identifier: str | None
    related_title: str | None

    @classmethod
    def from_graphql(cls, data: dict, *, inverse: bool = False) -> Self:
        # Linear stores each relation once, on the source issue. Reading it from the target's
        # inverseRelations means the other issue is under "issue" rather than "relatedIssue".
        related = data.get("issue" if inverse else "relatedIssue") or {}
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            related_identifier=related.get("identifier"),
            related_title=related.get("title"),
        )


@dataclass
class Attachment:
    """Linear issue attachment (URL link)."""

    id: str | None
    title: str | None
    url: str | None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            url=data.get("url"),
        )


@dataclass
class Project:
    """Linear project."""

    id: str | None
    name: str | None
    state: str | None
    start_date: str | None
    target_date: str | None
    description: str | None = None
    members: list[str] = field(default_factory=list)
    teams: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    milestones: list[dict] = field(default_factory=list)
    project_updates: list[dict] = field(default_factory=list)

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        member_nodes = (data.get("members") or {}).get("nodes", [])
        team_nodes = (data.get("teams") or {}).get("nodes", [])
        issue_nodes = (data.get("issues") or {}).get("nodes", [])
        milestone_nodes = (data.get("projectMilestones") or {}).get("nodes", [])
        update_nodes = (data.get("projectUpdates") or {}).get("nodes", [])
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            state=data.get("state"),
            start_date=data.get("startDate"),
            target_date=data.get("targetDate"),
            description=data.get("description"),
            members=[m.get("name", "") for m in member_nodes if m.get("name")],
            teams=team_nodes,
            issues=issue_nodes,
            milestones=milestone_nodes,
            project_updates=update_nodes,
        )


@dataclass
class Milestone:
    """Linear project milestone."""

    id: str | None
    name: str | None
    description: str | None
    target_date: str | None
    status: str | None
    progress: float | None
    project_name: str | None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        project = data.get("project") or {}
        raw_progress = data.get("progress")
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            target_date=data.get("targetDate"),
            status=data.get("status"),
            progress=float(raw_progress) if raw_progress is not None else None,
            project_name=project.get("name"),
        )


@dataclass
class Document:
    """Linear document."""

    id: str | None
    title: str | None
    content: str | None
    updated_at: str | None
    project_name: str | None
    creator_name: str | None = None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        project = data.get("project") or {}
        creator = data.get("creator") or {}
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            content=data.get("content"),
            updated_at=data.get("updatedAt"),
            project_name=project.get("name"),
            creator_name=creator.get("name"),
        )


@dataclass
class ProjectUpdate:
    """Linear project update."""

    id: str | None
    body: str | None
    health: str | None
    created_at: str | None
    user_name: str | None
    project_name: str | None = None

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        user = data.get("user") or {}
        project = data.get("project") or {}
        return cls(
            id=data.get("id"),
            body=data.get("body"),
            health=data.get("health"),
            created_at=data.get("createdAt"),
            user_name=user.get("name"),
            project_name=project.get("name"),
        )
