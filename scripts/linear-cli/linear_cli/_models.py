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

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        state = data.get("state") or {}
        assignee = data.get("assignee") or {}
        label_nodes = (data.get("labels") or {}).get("nodes", [])
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
    def from_graphql(cls, data: dict) -> Self:
        related = data.get("relatedIssue") or {}
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
    issues: list[dict] = field(default_factory=list)

    @classmethod
    def from_graphql(cls, data: dict) -> Self:
        member_nodes = (data.get("members") or {}).get("nodes", [])
        issue_nodes = (data.get("issues") or {}).get("nodes", [])
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            state=data.get("state"),
            start_date=data.get("startDate"),
            target_date=data.get("targetDate"),
            description=data.get("description"),
            members=[m.get("name", "") for m in member_nodes if m.get("name")],
            issues=issue_nodes,
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
