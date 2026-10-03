"""Combine name lookups and reads into one aliased GraphQL request.

Each Linear request costs a full network round trip (about 100-200ms), so commands collect every
lookup they need into a ``Batch`` and send it once instead of resolving names one at a time.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from linear_cli._errors import LinearError, die
from linear_cli._graphql import execute

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_VAR_RE = re.compile(r"\$(\w+)")


def is_uuid(value: str) -> bool:
    """Return whether a reference is a UUID rather than a name or identifier."""
    return _UUID_RE.match(value) is not None


def project_filter(ref: str) -> dict:
    """Return a ProjectFilter matching a project UUID or its name, case-insensitively."""
    if is_uuid(ref):
        return {"id": {"eq": ref}}
    return {"name": {"eqIgnoreCase": ref}}


def team_filter(key: str) -> dict:
    """Return a TeamFilter matching a team key, case-insensitively."""
    return {"key": {"eqIgnoreCase": key}}


def user_filter(ref: str) -> dict:
    """Return a user filter for 'me' or a user UUID."""
    if ref.lower() == "me":
        return {"isMe": {"eq": True}}
    return {"id": {"eq": ref}}


def resolve_project_id(ref: str) -> str:
    """Return a project UUID, looking the name up only when ``ref`` is not already a UUID."""
    if is_uuid(ref):
        return ref
    batch = Batch()
    get_project = batch.project_id(ref)
    batch.run()
    return get_project()


class Batch:
    """One GraphQL query assembled from independent aliased fields.

    ``add`` registers a field and returns its alias; ``run`` sends the query once and stores the
    response in ``data``. The lookup helpers return getters that read ``data`` and die with the
    command's not-found message, so callers register everything first, call ``run``, then read.
    """

    def __init__(self) -> None:
        self._decls: list[str] = []
        self._fields: list[str] = []
        self._variables: dict[str, Any] = {}
        self.data: dict = {}

    def __bool__(self) -> bool:
        return bool(self._fields)

    def add(self, field: str, variables: dict[str, tuple[str, Any]] | None = None) -> str:
        """Register ``field`` under a fresh alias; ``$name`` refers to ``variables[name]``.

        ``variables`` maps each placeholder to its GraphQL type and value.
        """
        alias = f"q{len(self._fields)}"
        for name, (gql_type, value) in (variables or {}).items():
            self._decls.append(f"${alias}_{name}: {gql_type}")
            self._variables[f"{alias}_{name}"] = value
        self._fields.append(f"{alias}: " + _VAR_RE.sub(rf"${alias}_\1", field))
        return alias

    def run(self) -> dict:
        """Send every registered field in one request; dies on API errors."""
        if not self._fields:
            return self.data
        decls = f"({', '.join(self._decls)})" if self._decls else ""
        query = f"query{decls} {{\n  " + "\n  ".join(self._fields) + "\n}"
        try:
            self.data = execute(query, self._variables or None)
        except LinearError as exc:
            die(str(exc))
        return self.data

    def nodes(self, alias: str) -> list[dict]:
        """Return the nodes of a connection field after ``run``."""
        return (self.data.get(alias) or {}).get("nodes", [])

    def _first_id(self, alias: str, missing: str) -> Callable[[], str]:
        def get() -> str:
            nodes = self.nodes(alias)
            if not nodes:
                die(missing)
            return nodes[0]["id"]

        return get

    def team(self, key: str, selection: str = "id") -> str:
        """Register a team lookup by key and return its alias."""
        return self.add(
            f"teams(filter: $filter) {{ nodes {{ {selection} }} }}",
            {"filter": ("TeamFilter", team_filter(key))},
        )

    def team_node(self, key: str, selection: str = "id") -> Callable[[], dict]:
        """Register a team lookup by key; the getter returns the team node."""
        alias = self.team(key, selection)

        def get() -> dict:
            nodes = self.nodes(alias)
            if not nodes:
                die(f"team '{key}' not found")
            return nodes[0]

        return get

    def team_id(self, key: str) -> Callable[[], str]:
        """Register a team lookup by key; the getter returns its UUID."""
        return self._first_id(self.team(key), f"team '{key}' not found")

    def project(self, ref: str, selection: str = "id") -> str:
        """Register a project lookup by name or UUID and return its alias."""
        return self.add(
            f"projects(filter: $filter, first: 1) {{ nodes {{ {selection} }} }}",
            {"filter": ("ProjectFilter", project_filter(ref))},
        )

    def project_node(self, ref: str, selection: str = "id") -> Callable[[], dict]:
        """Register a project lookup; the getter returns the project node."""
        alias = self.project(ref, selection)

        def get() -> dict:
            nodes = self.nodes(alias)
            if not nodes:
                die(f"project '{ref}' not found")
            return nodes[0]

        return get

    def project_id(self, ref: str) -> Callable[[], str]:
        """Register a project lookup by name or UUID; the getter returns its UUID."""
        return self._first_id(self.project(ref), f"project '{ref}' not found")

    def state_id(self, name: str, team: dict) -> Callable[[], str]:
        """Register a workflow state lookup by name within a TeamFilter."""
        alias = self.add(
            "workflowStates(filter: $filter) { nodes { id } }",
            {
                "filter": (
                    "WorkflowStateFilter",
                    {"team": team, "name": {"eqIgnoreCase": name}},
                )
            },
        )
        return self._first_id(alias, f"state '{name}' not found")

    def label_id(self, name: str) -> Callable[[], str]:
        """Register a workspace label lookup by name, case-insensitively."""
        alias = self.add(
            "issueLabels(filter: $filter) { nodes { id } }",
            {"filter": ("IssueLabelFilter", {"name": {"eqIgnoreCase": name}})},
        )
        return self._first_id(alias, f"label '{name}' not found")

    def milestone(self, name: str, project: dict, selection: str = "id") -> Callable[[], dict]:
        """Register a milestone lookup by name within a ProjectFilter; returns the node."""
        # first: 1 keeps nested selections (e.g. a milestone's issues) within Linear's
        # complexity limit, which multiplies by the default page size of 50.
        alias = self.add(
            f"projectMilestones(filter: $filter, first: 1) {{ nodes {{ {selection} }} }}",
            {
                "filter": (
                    "ProjectMilestoneFilter",
                    {"project": project, "name": {"eqIgnoreCase": name}},
                )
            },
        )

        def get() -> dict:
            nodes = self.nodes(alias)
            if not nodes:
                die(f"milestone '{name}' not found in project")
            return nodes[0]

        return get

    def milestone_scope(self, name: str) -> Callable[[], tuple[str, str]]:
        """Register a workspace-wide milestone lookup; the getter returns (project, milestone).

        The getter dies when the name exists in more than one project; the caller must then
        pass an explicit project.
        """
        alias = self.add(
            "projectMilestones(filter: $filter) { nodes { id project { id name } } }",
            {"filter": ("ProjectMilestoneFilter", {"name": {"eqIgnoreCase": name}})},
        )

        def get() -> tuple[str, str]:
            nodes = self.nodes(alias)
            if not nodes:
                die(f"milestone '{name}' not found")
            if len(nodes) > 1:
                names = sorted((n.get("project") or {}).get("name") or "?" for n in nodes)
                die(f"milestone '{name}' exists in projects: {', '.join(names)}; pass --project")
            node = nodes[0]
            return (node.get("project") or {})["id"], node["id"]

        return get

    def issue(self, ref: str, selection: str = "id") -> Callable[[], dict]:
        """Register an issue lookup by identifier or UUID; the getter returns the node.

        A missing issue fails the whole request with Linear's "Entity not found" error.
        """
        alias = self.add(f"issue(id: $id) {{ {selection} }}", {"id": ("String!", ref)})

        def get() -> dict:
            node = self.data.get(alias)
            if not node:
                die(f"issue '{ref}' not found")
            return node

        return get

    def user_id(self, ref: str) -> Callable[[], str]:
        """Register 'me' resolution; other references are user UUIDs and pass through."""
        if ref.lower() != "me":
            return lambda: ref
        alias = self.add("viewer { id }")

        def get() -> str:
            uid = (self.data.get(alias) or {}).get("id")
            if not uid:
                die("could not resolve viewer id")
            return uid

        return get
