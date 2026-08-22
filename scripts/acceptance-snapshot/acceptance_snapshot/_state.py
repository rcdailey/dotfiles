"""Private session state and snapshot transitions."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Generator
from dataclasses import asdict, dataclass
from pathlib import Path

from acceptance_snapshot._errors import SnapshotError
from acceptance_snapshot._git import (
    capture_tree,
    changed_paths,
    repository_root,
    resolve_tree,
    tree_diff,
)

_SCHEMA_VERSION = 1


@dataclass
class SnapshotState:
    """Persisted state for one acceptance-agent session."""

    version: int
    repository: str
    base_tree: str
    audited_tree: str | None = None
    pending_tree: str | None = None
    iteration: int = 0

    @property
    def previous_tree(self) -> str:
        """Return the tree against which the pending iteration is compared."""
        return self.audited_tree or self.base_tree


@dataclass(frozen=True)
class BeginResult:
    """A pending acceptance iteration."""

    iteration: int
    previous_tree: str
    pending_tree: str
    changes: str


@dataclass(frozen=True)
class FinishResult:
    """The outcome of finalizing an audited iteration."""

    iteration: int
    audited_tree: str
    current_tree: str
    changes: str

    @property
    def stable(self) -> bool:
        """Return whether the repository still matches the audited tree."""
        return self.audited_tree == self.current_tree


def _session_id() -> str:
    value = os.environ.get("OPENCODE_SESSION_ID")
    if not value:
        raise SnapshotError("OPENCODE_SESSION_ID is not set")
    return value


def _secure_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise SnapshotError(f"unsafe state path: {path}")
        if info.st_uid != os.getuid():
            raise SnapshotError(f"state path is owned by another user: {path}")
        path.chmod(0o700)


def state_directory() -> Path:
    """Return the private directory for this OpenCode session."""
    root = Path(tempfile.gettempdir()) / "opencode-acceptance"
    _secure_directory(root)
    key = hashlib.sha256(_session_id().encode()).hexdigest()
    directory = root / key
    _secure_directory(directory)
    objects = directory / "objects"
    _secure_directory(objects)
    return directory


def _state_path(directory: Path) -> Path:
    return directory / "state.json"


def _load_state(directory: Path) -> SnapshotState | None:
    path = _state_path(directory)
    if not path.exists():
        return None
    try:
        values = json.loads(path.read_text())
        state = SnapshotState(**values)
    except (OSError, TypeError, ValueError) as exc:
        raise SnapshotError(f"invalid snapshot state: {exc}") from exc
    if type(state.version) is not int or state.version != _SCHEMA_VERSION:
        raise SnapshotError(f"unsupported snapshot state version: {state.version}")
    if not isinstance(state.repository, str) or not state.repository:
        raise SnapshotError("invalid snapshot repository")
    if not isinstance(state.base_tree, str) or not state.base_tree:
        raise SnapshotError("invalid snapshot base tree")
    for name, value in (
        ("audited tree", state.audited_tree),
        ("pending tree", state.pending_tree),
    ):
        if value is not None and (not isinstance(value, str) or not value):
            raise SnapshotError(f"invalid snapshot {name}")
    if type(state.iteration) is not int or state.iteration < 0:
        raise SnapshotError("invalid snapshot iteration")
    return state


def _save_state(directory: Path, state: SnapshotState) -> None:
    descriptor, temporary_name = tempfile.mkstemp(dir=directory, prefix="state.")
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as file:
            json.dump(asdict(state), file, sort_keys=True)
            file.write("\n")
        os.replace(temporary, _state_path(directory))
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def _locked(directory: Path) -> Generator[None, None, None]:
    lock_path = directory / "lock"
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _validated_state(
    directory: Path,
    repository: Path,
    base: str | None,
) -> SnapshotState:
    state = _load_state(directory)
    if state is None:
        return SnapshotState(
            version=_SCHEMA_VERSION,
            repository=str(repository),
            base_tree=resolve_tree(repository, base or "HEAD"),
        )
    if state.repository != str(repository):
        raise SnapshotError(f"session belongs to {state.repository}, not {repository}")
    if base and state.base_tree != resolve_tree(repository, base):
        raise SnapshotError("Base differs from the existing acceptance session")
    return state


def begin(base: str | None) -> BeginResult:
    """Capture the candidate for a new acceptance iteration."""
    repository = repository_root()
    directory = state_directory()
    with _locked(directory):
        state = _validated_state(directory, repository, base)
        pending_tree = capture_tree(repository, directory, "pending.index")
        state.pending_tree = pending_tree
        _save_state(directory, state)
        changes = changed_paths(
            repository,
            directory,
            state.previous_tree,
            pending_tree,
        )
        return BeginResult(
            iteration=state.iteration + 1,
            previous_tree=state.previous_tree,
            pending_tree=pending_tree,
            changes=changes,
        )


def finish() -> FinishResult:
    """Finalize the audited candidate and detect concurrent changes."""
    repository = repository_root()
    directory = state_directory()
    with _locked(directory):
        state = _validated_state(directory, repository, None)
        if not state.pending_tree:
            raise SnapshotError("no pending acceptance iteration; run begin first")
        current_tree = capture_tree(repository, directory, "verify.index")
        audited_tree = state.pending_tree
        changes = changed_paths(
            repository,
            directory,
            audited_tree,
            current_tree,
        )
        state.audited_tree = audited_tree
        state.pending_tree = None
        state.iteration += 1
        _save_state(directory, state)
        return FinishResult(
            iteration=state.iteration,
            audited_tree=audited_tree,
            current_tree=current_tree,
            changes=changes,
        )


def pending_diff(paths: tuple[str, ...]) -> str:
    """Return a targeted diff for the pending iteration."""
    repository = repository_root()
    directory = state_directory()
    with _locked(directory):
        state = _validated_state(directory, repository, None)
        if not state.pending_tree:
            raise SnapshotError("no pending acceptance iteration; run begin first")
        return tree_diff(
            repository,
            directory,
            state.previous_tree,
            state.pending_tree,
            paths,
        )
