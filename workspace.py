#!/usr/bin/env python3
"""Project and workflow workspace backed by a separate SQLite database."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import http.client
import ipaddress
import json
import os
import socket
import ssl
import sqlite3
import uuid
from typing import Any, Iterator
from urllib.parse import quote, urlsplit

from pre_output_audit import validate_audit_record

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DB_PATH = os.path.join(BASE_DIR, "workspace.db")
CORRECTION_CATEGORIES = tuple("ABCDEF")
SOURCE_LIMIT_BYTES = 2 * 1024 * 1024
CLAIM_CLASSES = ("evidence", "inference", "hypothesis", "opinion")
CLAIM_SUPPORT_STATUSES = (
    "supported",
    "partly_supported",
    "unsupported",
    "conflicting_evidence",
    "unverified",
    "not_applicable",
)
OUTPUT_REVIEW_GATES = {
    "safety": "Safety",
    "privacy": "Privacy",
    "fairness": "Fairness",
    "technical_accuracy": "Technical accuracy",
}

MODULES: dict[str, tuple[str, ...]] = {
    "projects": (),
    "notes": ("projects",),
    "sources": ("projects",),
    "corrections": ("projects",),
    "workflows": ("projects",),
    "tasks": ("projects", "workflows"),
    "agent_coordination": ("tasks",),
}
TASK_MODULES = {
    "review_sources": "sources",
    "record_note": "notes",
    "organize_corrections": "corrections",
    "manual_review": "tasks",
}


class WorkspaceError(ValueError):
    """Raised when a workspace operation violates its data contract."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        decoded = json.loads(value)
        return decoded if isinstance(decoded, dict) else {}
    return {}


def validate_workflow_definition(
    definition: Any, agent_ids: set[str] | None = None
) -> list[str]:
    """Return structural/configuration errors for the supported workflow format."""
    errors: list[str] = []
    if not isinstance(definition, dict):
        return ["Workflow definition must be a JSON object."]
    allowed_root = {"name", "version", "modules", "steps"}
    extra = sorted(set(definition) - allowed_root)
    missing = sorted({"name", "version", "modules", "steps"} - set(definition))
    if extra:
        errors.append(f"Unsupported top-level properties: {', '.join(extra)}.")
    if missing:
        errors.append(f"Missing top-level properties: {', '.join(missing)}.")
    if not isinstance(definition.get("name"), str) or not definition.get("name", "").strip():
        errors.append("name must be a non-empty string.")
    if definition.get("version") != "1.0":
        errors.append("version must be the supported string '1.0'.")

    modules = definition.get("modules")
    module_set: set[str] = set()
    if not isinstance(modules, list) or any(not isinstance(m, str) for m in modules):
        errors.append("modules must be an array of registered module names.")
    else:
        if len(modules) != len(set(modules)):
            errors.append("modules cannot contain duplicates.")
        module_set = set(modules)
        unknown_modules = sorted(module_set - set(MODULES))
        if unknown_modules:
            errors.append(f"Unknown modules: {', '.join(unknown_modules)}.")
        for module in sorted(module_set & set(MODULES)):
            missing_modules = sorted(set(MODULES[module]) - module_set)
            if missing_modules:
                errors.append(
                    f"Module {module!r} requires: {', '.join(missing_modules)}."
                )
        for required in ("projects", "workflows", "tasks"):
            if required not in module_set:
                errors.append(f"Every workflow must include module {required!r}.")

    steps = definition.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty array.")
        return errors

    seen: set[str] = set()
    for index, step in enumerate(steps):
        location = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{location} must be an object.")
            continue
        allowed_step = {
            "id", "title", "task_type", "config", "depends_on", "assigned_agent_id"
        }
        extra_step = sorted(set(step) - allowed_step)
        if extra_step:
            errors.append(f"{location} has unsupported properties: {', '.join(extra_step)}.")
        step_id = step.get("id")
        if not isinstance(step_id, str) or not step_id.strip():
            errors.append(f"{location}.id must be a non-empty string.")
            step_id = ""
        elif step_id in seen:
            errors.append(f"{location}.id duplicates {step_id!r}.")
        if step_id:
            seen.add(step_id)
        if not isinstance(step.get("title"), str) or not step.get("title", "").strip():
            errors.append(f"{location}.title must be a non-empty string.")

        task_type = step.get("task_type")
        if not isinstance(task_type, str) or task_type not in TASK_MODULES:
            errors.append(f"{location}.task_type is not a registered task type.")
        elif TASK_MODULES[task_type] not in module_set:
            errors.append(
                f"{location} requires module {TASK_MODULES[task_type]!r}."
            )

        config = step.get("config", {})
        if not isinstance(config, dict):
            errors.append(f"{location}.config must be an object.")
            config = {}
        if task_type == "record_note":
            if set(config) - {"title", "body"}:
                errors.append(f"{location}.config for record_note accepts title and body only.")
            for field in ("title", "body"):
                if not isinstance(config.get(field), str) or not config.get(field, "").strip():
                    errors.append(f"{location}.config.{field} must be a non-empty string.")
        elif task_type == "organize_corrections":
            if set(config) - {"category"}:
                errors.append(f"{location}.config for organize_corrections accepts category only.")
            category = config.get("category")
            if category is not None and category not in CORRECTION_CATEGORIES:
                errors.append(f"{location}.config.category must be one of A, B, C, D, E, F.")
        elif task_type == "manual_review":
            if set(config) - {"prompt"}:
                errors.append(f"{location}.config for manual_review accepts prompt only.")
            if not isinstance(config.get("prompt"), str) or not config.get("prompt", "").strip():
                errors.append(f"{location}.config.prompt must be a non-empty string.")
        elif task_type == "review_sources" and config:
            errors.append(f"{location}.config for review_sources must be empty.")

        dependencies = step.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not isinstance(dep, str) for dep in dependencies):
            errors.append(f"{location}.depends_on must be an array of earlier step IDs.")
        else:
            if len(dependencies) != len(set(dependencies)):
                errors.append(f"{location}.depends_on cannot contain duplicates.")
            for dependency in dependencies:
                if dependency not in seen or dependency == step_id:
                    errors.append(
                        f"{location} dependency {dependency!r} must refer to an earlier step."
                    )

        assigned_agent = step.get("assigned_agent_id")
        if assigned_agent is not None:
            if not isinstance(assigned_agent, str) or not assigned_agent:
                errors.append(f"{location}.assigned_agent_id must be a registered agent ID.")
            elif agent_ids is not None and assigned_agent not in agent_ids:
                errors.append(f"{location} references unknown agent {assigned_agent!r}.")
            if "agent_coordination" not in module_set:
                errors.append(f"{location} assignment requires module 'agent_coordination'.")
    return errors


def validate_https_source_url(url: str) -> tuple[str, str, int, str]:
    if not isinstance(url, str) or not url.strip() or any(ord(char) < 32 for char in url):
        raise WorkspaceError("Enter a valid HTTPS URL.")
    try:
        parsed = urlsplit(url.strip())
        hostname = parsed.hostname
        parsed_port = parsed.port
        port = 443 if parsed_port is None else parsed_port
    except ValueError as exc:
        raise WorkspaceError("The source URL is malformed.") from exc
    if parsed.scheme.lower() != "https" or not hostname:
        raise WorkspaceError("Source URLs must use HTTPS and include a hostname.")
    if parsed.username is not None or parsed.password is not None:
        raise WorkspaceError("Source URLs cannot contain embedded credentials.")
    if port != 443:
        raise WorkspaceError("Only the standard HTTPS port 443 is allowed.")
    if parsed.fragment:
        raise WorkspaceError("Source URLs cannot contain fragments.")
    try:
        host_ascii = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise WorkspaceError("The source hostname is invalid.") from exc
    if host_ascii == "localhost" or host_ascii.endswith(".localhost"):
        raise WorkspaceError("Source retrieval is restricted to public network addresses.")
    try:
        ip = ipaddress.ip_address(host_ascii.strip("[]"))
    except ValueError:
        ip = None
    if ip is not None and not ip.is_global:
        raise WorkspaceError("Source retrieval is restricted to public network addresses.")
    return host_ascii, parsed.path or "/", port, parsed.query


def retrieve_https_source(url: str) -> tuple[str, str]:
    """Fetch bounded text from a public HTTPS host without following redirects."""
    hostname, path, port, query = validate_https_source_url(url)
    try:
        addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise WorkspaceError(f"Could not resolve source host: {exc}") from exc
    public_ips: list[str] = []
    seen: set[str] = set()
    for record in addresses:
        address = record[4][0].split("%", 1)[0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            raise WorkspaceError("The source host resolved to an invalid network address.")
        if not ip.is_global:
            raise WorkspaceError("Source retrieval is restricted to public network addresses.")
        if address not in seen:
            public_ips.append(address)
            seen.add(address)
    if not public_ips:
        raise WorkspaceError("The source host did not resolve to a usable address.")

    request_target = quote(path, safe="/%:@!$&'()*+,;=-._~%")
    if query:
        request_target += "?" + quote(query, safe="/?@!$&'()*+,;=:-._~%")
    host_header = f"[{hostname}]" if ":" in hostname else hostname
    context = ssl.create_default_context()
    last_error: Exception | None = None
    for address in public_ips:
        raw_socket: socket.socket | None = None
        tls_socket: ssl.SSLSocket | None = None
        response: http.client.HTTPResponse | None = None
        try:
            raw_socket = socket.create_connection((address, port), timeout=8)
            try:
                ipaddress.ip_address(hostname)
                server_name = None
            except ValueError:
                server_name = hostname
            tls_socket = context.wrap_socket(raw_socket, server_hostname=server_name)
            tls_socket.settimeout(10)
            request_bytes = (
                f"GET {request_target} HTTP/1.1\r\n"
                f"Host: {host_header}\r\n"
                "User-Agent: Agent-Docs-Research-Workspace/1.0\r\n"
                "Accept: text/*, application/json, application/xml, application/*+xml\r\n"
                "Accept-Encoding: identity\r\n"
                "Connection: close\r\n\r\n"
            ).encode("ascii")
            tls_socket.sendall(request_bytes)
            response = http.client.HTTPResponse(tls_socket, method="GET")
            response.begin()
            if 300 <= response.status < 400:
                raise WorkspaceError("Redirects are not followed during source retrieval.")
            if response.status < 200 or response.status >= 300:
                raise WorkspaceError(f"Source returned HTTP {response.status}.")
            content_type = response.getheader("Content-Type", "application/octet-stream")
            media_type = content_type.split(";", 1)[0].strip().lower()
            if not (
                media_type.startswith("text/")
                or media_type in {"application/json", "application/xml"}
                or media_type.endswith("+xml")
            ):
                raise WorkspaceError(f"Unsupported source content type: {media_type}.")
            length_header = response.getheader("Content-Length")
            if length_header and int(length_header) > SOURCE_LIMIT_BYTES:
                raise WorkspaceError("Source content exceeds the 2 MiB retrieval limit.")
            body = response.read(SOURCE_LIMIT_BYTES + 1)
            if len(body) > SOURCE_LIMIT_BYTES:
                raise WorkspaceError("Source content exceeds the 2 MiB retrieval limit.")
            charset = "utf-8"
            for parameter in content_type.split(";")[1:]:
                key, separator, value = parameter.strip().partition("=")
                if separator and key.lower() == "charset":
                    charset = value.strip().strip('"')
            try:
                content = body.decode(charset, errors="replace")
            except LookupError:
                content = body.decode("utf-8", errors="replace")
            return content_type[:255], content
        except WorkspaceError:
            raise
        except (OSError, ssl.SSLError, http.client.HTTPException, ValueError) as exc:
            last_error = exc
        finally:
            if response is not None:
                response.close()
            if tls_socket is not None:
                tls_socket.close()
            elif raw_socket is not None:
                raw_socket.close()
    raise WorkspaceError(f"Could not retrieve source over HTTPS: {last_error}")


class WorkspaceStore:
    def __init__(self, db_path: str = WORKSPACE_DB_PATH) -> None:
        self.db_path = db_path
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        parent = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(parent, exist_ok=True)
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, objective TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    url TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', content_type TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending',
                    error TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, retrieved_at TEXT
                );
                CREATE TABLE IF NOT EXISTS claims (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    text TEXT NOT NULL,
                    epistemic_class TEXT NOT NULL CHECK(epistemic_class IN ('evidence','inference','hypothesis','opinion')),
                    support_status TEXT NOT NULL CHECK(support_status IN (
                        'supported','partly_supported','unsupported','conflicting_evidence','unverified','not_applicable'
                    )),
                    support_summary TEXT NOT NULL DEFAULT '',
                    uncertainty TEXT NOT NULL DEFAULT '',
                    verification_criterion TEXT NOT NULL DEFAULT '',
                    attribution TEXT NOT NULL DEFAULT '',
                    sources_reviewed INTEGER NOT NULL DEFAULT 0 CHECK(sources_reviewed IN (0,1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS claim_sources (
                    claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
                    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                    PRIMARY KEY (claim_id, source_id)
                );
                CREATE TABLE IF NOT EXISTS output_audits (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    status TEXT NOT NULL CHECK(status IN ('release','revise','block')),
                    record TEXT NOT NULL,
                    findings TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS corrections (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    category TEXT NOT NULL CHECK(category IN ('A','B','C','D','E','F')),
                    title TEXT NOT NULL, body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    name TEXT NOT NULL, definition TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL REFERENCES workflows(id),
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    status TEXT NOT NULL, started_at TEXT NOT NULL, completed_at TEXT,
                    error TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS agent_definitions (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, specialty TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                    step_id TEXT NOT NULL, position INTEGER NOT NULL, title TEXT NOT NULL,
                    task_type TEXT NOT NULL, config TEXT NOT NULL, status TEXT NOT NULL,
                    assigned_agent_id TEXT REFERENCES agent_definitions(id),
                    output TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    UNIQUE(run_id, step_id)
                );
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id TEXT PRIMARY KEY, sender_agent_id TEXT REFERENCES agent_definitions(id),
                    recipient_agent_id TEXT REFERENCES agent_definitions(id),
                    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                    run_id TEXT REFERENCES workflow_runs(id) ON DELETE SET NULL,
                    task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                    body TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL,
                    entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_notes_project ON notes(project_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_sources_project ON sources(project_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_claims_project ON claims(project_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_output_audits_project ON output_audits(project_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_corrections_project ON corrections(project_id, category);
                CREATE INDEX IF NOT EXISTS idx_tasks_run ON tasks(run_id, position);
                CREATE INDEX IF NOT EXISTS idx_events_created ON audit_events(created_at);
                """
            )

    @staticmethod
    def _record_event(
        db: sqlite3.Connection, action: str, entity_type: str, entity_id: str,
        detail: dict[str, Any] | None = None, actor: str = "human",
    ) -> None:
        db.execute(
            "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_id("evt"), actor, action, entity_type, entity_id,
             json.dumps(detail or {}, ensure_ascii=False), utc_now()),
        )

    @staticmethod
    def _require_project(db: sqlite3.Connection, project_id: str) -> sqlite3.Row:
        row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row is None:
            raise WorkspaceError("Project not found.")
        return row

    def create_project(self, name: str, objective: str, description: str = "") -> str:
        name, objective, description = name.strip(), objective.strip(), description.strip()
        if not name or not objective:
            raise WorkspaceError("Project name and objective are required.")
        project_id, now = new_id("prj"), utc_now()
        with self._connection() as db:
            db.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, 'active', ?, ?)",
                (project_id, name, objective, description, now, now),
            )
            self._record_event(db, "created", "project", project_id, {"name": name})
        return project_id

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC, name"
            )]

    def get_project(self, project_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            return dict(row) if row else None

    def update_project(
        self, project_id: str, name: str, objective: str, description: str = ""
    ) -> None:
        name, objective, description = name.strip(), objective.strip(), description.strip()
        if not name or not objective:
            raise WorkspaceError("Project name and objective are required.")
        now = utc_now()
        with self._connection() as db:
            self._require_project(db, project_id)
            db.execute(
                "UPDATE projects SET name=?,objective=?,description=?,updated_at=? WHERE id=?",
                (name, objective, description, now, project_id),
            )
            self._record_event(db, "updated", "project", project_id, {"name": name})

    def create_note(
        self, project_id: str, title: str, body: str, actor: str = "human"
    ) -> str:
        title, body = title.strip(), body.strip()
        if not title or not body:
            raise WorkspaceError("Note title and body are required.")
        note_id, now = new_id("nte"), utc_now()
        with self._connection() as db:
            self._require_project(db, project_id)
            db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, ?)",
                       (note_id, project_id, title, body, now))
            db.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
            self._record_event(db, "created", "note", note_id,
                               {"project_id": project_id}, actor=actor)
        return note_id

    def list_notes(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            return [dict(row) for row in db.execute(
                "SELECT * FROM notes WHERE project_id=? ORDER BY created_at DESC", (project_id,)
            )]

    def add_source(self, project_id: str, url: str, title: str = "") -> str:
        validate_https_source_url(url)
        source_id, now = new_id("src"), utc_now()
        with self._connection() as db:
            self._require_project(db, project_id)
            db.execute(
                "INSERT INTO sources (id,project_id,url,title,status,created_at) VALUES (?,?,?,?,?,?)",
                (source_id, project_id, url.strip(), title.strip(), "pending", now),
            )
            db.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
            self._record_event(db, "added", "source", source_id,
                               {"project_id": project_id})
        return source_id

    def finish_source_retrieval(
        self, source_id: str, content_type: str = "", content: str = "", error: str = ""
    ) -> None:
        status = "failed" if error else "retrieved"
        with self._connection() as db:
            row = db.execute("SELECT project_id FROM sources WHERE id=?", (source_id,)).fetchone()
            if row is None:
                raise WorkspaceError("Source not found.")
            now = utc_now()
            db.execute(
                "UPDATE sources SET content_type=?,content=?,status=?,error=?,retrieved_at=? WHERE id=?",
                (content_type, content, status, error, now, source_id),
            )
            db.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, row["project_id"]))
            self._record_event(db, status, "source", source_id, {"project_id": row["project_id"]})

    def get_source(self, project_id: str, source_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM sources WHERE id=? AND project_id=?",
                             (source_id, project_id)).fetchone()
            return dict(row) if row else None

    def list_sources(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            return [dict(row) for row in db.execute(
                "SELECT id,project_id,url,title,content_type,status,error,created_at,retrieved_at "
                "FROM sources WHERE project_id=? ORDER BY created_at DESC", (project_id,)
            )]

    def list_source_material(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            return [dict(row) for row in db.execute(
                "SELECT id,url,title,content_type,status,content FROM sources "
                "WHERE project_id=? ORDER BY created_at", (project_id,)
            )]

    def create_claim(
        self,
        project_id: str,
        text: str,
        epistemic_class: str,
        support_status: str,
        source_ids: list[str] | tuple[str, ...] = (),
        support_summary: str = "",
        uncertainty: str = "",
        verification_criterion: str = "",
        attribution: str = "",
        sources_reviewed: bool = False,
    ) -> str:
        text = text.strip()
        epistemic_class = epistemic_class.strip().lower()
        support_status = support_status.strip().lower()
        support_summary = support_summary.strip()
        uncertainty = uncertainty.strip()
        verification_criterion = verification_criterion.strip()
        attribution = attribution.strip()
        if not text:
            raise WorkspaceError("Claim text is required.")
        if epistemic_class not in CLAIM_CLASSES:
            raise WorkspaceError("Choose evidence, inference, hypothesis, or opinion.")
        if support_status not in CLAIM_SUPPORT_STATUSES:
            raise WorkspaceError("Choose a valid claim support status.")
        normalized_source_ids = list(dict.fromkeys(
            source_id.strip() for source_id in source_ids if isinstance(source_id, str) and source_id.strip()
        ))
        claim_id, now = new_id("clm"), utc_now()
        with self._connection() as db:
            self._require_project(db, project_id)
            if normalized_source_ids:
                placeholders = ",".join("?" for _ in normalized_source_ids)
                rows = db.execute(
                    f"SELECT id FROM sources WHERE project_id=? AND id IN ({placeholders})",
                    (project_id, *normalized_source_ids),
                ).fetchall()
                found_ids = {row["id"] for row in rows}
                missing = [source_id for source_id in normalized_source_ids if source_id not in found_ids]
                if missing:
                    raise WorkspaceError("Every linked source must belong to this project.")
            db.execute(
                "INSERT INTO claims (id,project_id,text,epistemic_class,support_status,"
                "support_summary,uncertainty,verification_criterion,attribution,sources_reviewed,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (claim_id, project_id, text, epistemic_class, support_status, support_summary,
                 uncertainty, verification_criterion, attribution, int(bool(sources_reviewed)), now, now),
            )
            db.executemany(
                "INSERT INTO claim_sources (claim_id,source_id) VALUES (?,?)",
                [(claim_id, source_id) for source_id in normalized_source_ids],
            )
            db.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
            self._record_event(
                db, "created", "claim", claim_id,
                {"project_id": project_id, "epistemic_class": epistemic_class,
                 "source_count": len(normalized_source_ids)},
            )
        return claim_id

    def list_claims(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            claims = [dict(row) for row in db.execute(
                "SELECT * FROM claims WHERE project_id=? ORDER BY created_at DESC,id",
                (project_id,),
            )]
            for claim in claims:
                claim["sources"] = [dict(row) for row in db.execute(
                    "SELECT s.id,s.title,s.url,s.status FROM claim_sources cs "
                    "JOIN sources s ON s.id=cs.source_id WHERE cs.claim_id=? ORDER BY s.title,s.url",
                    (claim["id"],),
                )]
                claim["sources_reviewed"] = bool(claim["sources_reviewed"])
            return claims

    @staticmethod
    def _pre_output_findings(
        claims: list[dict[str, Any]], gates: dict[str, Any]
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []

        def add(severity: str, code: str, message: str, claim: dict[str, Any] | None = None) -> None:
            finding = {"severity": severity, "code": code, "message": message}
            if claim is not None:
                finding["claim_id"] = claim["id"]
                finding["claim_text"] = claim["text"]
            findings.append(finding)

        if not claims:
            add("blocker", "no_claims", "No claims are recorded for this project.")
        for gate_name, gate_label in OUTPUT_REVIEW_GATES.items():
            gate = gates.get(gate_name, {})
            if gate.get("status") == "fail":
                issues = "; ".join(gate.get("issues", []))
                message = f"{gate_label} gate failed."
                if issues:
                    message += f" Issues: {issues}"
                add("blocker", f"{gate_name}_gate_failed", message)

        for claim in claims:
            linked_sources = claim.get("sources", [])
            claim_class = claim.get("epistemic_class")
            support_status = claim.get("support_status")
            if claim_class == "evidence" and not linked_sources:
                add("blocker", "evidence_without_source", "Evidence claims must link to at least one source.", claim)
            if support_status in {"supported", "partly_supported"} and not linked_sources:
                add("blocker", "support_without_source", "A supported claim must link to its supporting source material.", claim)
            if support_status in {"unsupported", "conflicting_evidence", "unverified"}:
                add("blocker", "claim_support_unresolved", f"Claim support status is {support_status.replace('_', ' ')}.", claim)
            elif support_status == "partly_supported":
                add("review", "partial_support", "Claim is only partly supported; preserve its limits in any output.", claim)
            if support_status == "supported" and not claim.get("support_summary", "").strip():
                add("blocker", "support_summary_missing", "A supported claim needs a summary of what the linked material supports.", claim)
            if linked_sources and not claim.get("sources_reviewed"):
                add("blocker", "source_review_missing", "A reviewer has not attested to checking the linked sources against this claim.", claim)
            for source in linked_sources:
                if source.get("status") != "retrieved":
                    add("blocker", "source_not_retrieved", f"Linked source is {source.get('status', 'unavailable')}; retrieve and review it before relying on the claim.", claim)
            if claim_class in {"inference", "hypothesis", "opinion"} and not claim.get("uncertainty", "").strip():
                add("blocker", "uncertainty_missing", f"{claim_class.title()} claims need an uncertainty or limitation statement.", claim)
            if claim_class == "inference" and not claim.get("support_summary", "").strip():
                add("blocker", "reasoning_basis_missing", "An inference needs a recorded reasoning basis tied to its evidence.", claim)
            if claim_class == "hypothesis" and not claim.get("verification_criterion", "").strip():
                add("blocker", "hypothesis_test_missing", "A hypothesis needs a criterion that could confirm or falsify it.", claim)
            if claim_class == "opinion" and not claim.get("attribution", "").strip():
                add("blocker", "opinion_attribution_missing", "An opinion or recommendation needs an identified author or decision owner.", claim)

        return findings

    def create_pre_output_audit(
        self, project_id: str, record: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise WorkspaceError("Audit record must be an object.")
        record = dict(record)
        audit_id, now = new_id("aud"), utc_now()
        record["audit_id"] = audit_id
        record["timestamp_utc"] = now
        errors = validate_audit_record(record)
        gates = record.get("gates", {})
        if isinstance(gates, dict):
            for gate_name, gate in gates.items():
                if isinstance(gate, dict) and gate.get("status") == "pass":
                    if not gate.get("checks"):
                        errors.append(f"gates.{gate_name} with pass status must include at least one check.")
                    if not gate.get("evidence"):
                        errors.append(f"gates.{gate_name} with pass status must include supporting evidence.")
        if errors:
            raise WorkspaceError("Invalid pre-output audit record:\n" + "\n".join(errors))

        claims = self.list_claims(project_id)
        findings = self._pre_output_findings(claims, gates)
        blockers = [item for item in findings if item["severity"] == "blocker"]
        if record["disposition"] == "release" and blockers:
            with self._connection() as db:
                self._require_project(db, project_id)
                self._record_event(
                    db, "blocked_release", "pre_output_audit", audit_id,
                    {"project_id": project_id,
                     "finding_codes": sorted({item["code"] for item in blockers})},
                    actor=record["actor"],
                )
            raise WorkspaceError(
                "Release is blocked by claim-ledger findings. Choose revise or block, "
                "or resolve the findings before recording a release."
            )
        record["notes"] = list(record["notes"])
        for finding in findings:
            if finding["severity"] == "review" and finding["message"] not in record["notes"]:
                record["notes"].append(finding["message"])
        with self._connection() as db:
            self._require_project(db, project_id)
            db.execute(
                "INSERT INTO output_audits (id,project_id,status,record,findings,created_at) "
                "VALUES (?,?,?,?,?,?)",
                (audit_id, project_id, record["disposition"],
                 json.dumps(record, ensure_ascii=False),
                 json.dumps(findings, ensure_ascii=False), now),
            )
            self._record_event(
                db, record["disposition"], "pre_output_audit", audit_id,
                {"project_id": project_id, "status": record["disposition"],
                 "finding_count": len(findings)},
                actor=record["actor"],
            )
        return {
            "id": audit_id, "project_id": project_id, "status": record["disposition"],
            "record": record, "findings": findings, "created_at": now,
        }

    def list_pre_output_audits(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            audits = []
            for row in db.execute(
                "SELECT * FROM output_audits WHERE project_id=? ORDER BY created_at DESC,id DESC",
                (project_id,),
            ):
                audit = dict(row)
                audit["record"] = json.loads(audit["record"])
                audit["findings"] = json.loads(audit["findings"])
                audits.append(audit)
            return audits

    def create_correction(
        self, project_id: str, category: str, title: str, body: str
    ) -> str:
        category, title, body = category.upper().strip(), title.strip(), body.strip()
        if category not in CORRECTION_CATEGORIES:
            raise WorkspaceError("Correction category must be A, B, C, D, E, or F.")
        if not title or not body:
            raise WorkspaceError("Correction title and details are required.")
        correction_id, now = new_id("cor"), utc_now()
        with self._connection() as db:
            self._require_project(db, project_id)
            db.execute("INSERT INTO corrections VALUES (?, ?, ?, ?, ?, 'open', ?)",
                       (correction_id, project_id, category, title, body, now))
            db.execute("UPDATE projects SET updated_at=? WHERE id=?", (now, project_id))
            self._record_event(db, "created", "correction", correction_id,
                               {"project_id": project_id, "category": category})
        return correction_id

    def list_corrections(
        self, project_id: str, category: str | None = None
    ) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            if category in CORRECTION_CATEGORIES:
                rows = db.execute(
                    "SELECT * FROM corrections WHERE project_id=? AND category=? ORDER BY created_at DESC",
                    (project_id, category),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM corrections WHERE project_id=? ORDER BY category, created_at DESC",
                    (project_id,),
                )
            return [dict(row) for row in rows]

    def list_agents(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM agent_definitions ORDER BY name"
            )]

    def create_agent(self, name: str, specialty: str) -> str:
        name, specialty = name.strip(), specialty.strip()
        if not name or not specialty:
            raise WorkspaceError("Agent name and specialty are required.")
        agent_id, now = new_id("agt"), utc_now()
        try:
            with self._connection() as db:
                db.execute("INSERT INTO agent_definitions VALUES (?, ?, ?, ?)",
                           (agent_id, name, specialty, now))
                self._record_event(db, "defined", "agent", agent_id, {"name": name})
        except sqlite3.IntegrityError as exc:
            raise WorkspaceError("An agent with that name already exists.") from exc
        return agent_id

    def send_agent_message(
        self, body: str, sender_agent_id: str | None = None,
        recipient_agent_id: str | None = None, project_id: str | None = None,
        run_id: str | None = None, task_id: str | None = None,
    ) -> str:
        body = body.strip()
        if not body:
            raise WorkspaceError("Message text is required.")
        message_id, now = new_id("msg"), utc_now()
        with self._connection() as db:
            for agent_id in (sender_agent_id, recipient_agent_id):
                if agent_id and not db.execute(
                    "SELECT 1 FROM agent_definitions WHERE id=?", (agent_id,)
                ).fetchone():
                    raise WorkspaceError("Selected agent does not exist.")
            if project_id:
                self._require_project(db, project_id)
            db.execute(
                "INSERT INTO agent_messages VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (message_id, sender_agent_id, recipient_agent_id, project_id, run_id,
                 task_id, body, now),
            )
            self._record_event(db, "sent", "agent_message", message_id,
                               {"project_id": project_id, "run_id": run_id, "task_id": task_id})
        return message_id

    def list_agent_messages(self, project_id: str | None = None) -> list[dict[str, Any]]:
        with self._connection() as db:
            query = (
                "SELECT m.*, s.name AS sender_name, r.name AS recipient_name "
                "FROM agent_messages m LEFT JOIN agent_definitions s ON s.id=m.sender_agent_id "
                "LEFT JOIN agent_definitions r ON r.id=m.recipient_agent_id"
            )
            if project_id:
                rows = db.execute(query + " WHERE m.project_id=? ORDER BY m.created_at DESC",
                                  (project_id,))
            else:
                rows = db.execute(query + " ORDER BY m.created_at DESC")
            return [dict(row) for row in rows]

    def save_workflow(self, project_id: str, definition: Any) -> str:
        with self._connection() as db:
            self._require_project(db, project_id)
            agent_ids = {row[0] for row in db.execute("SELECT id FROM agent_definitions")}
        errors = validate_workflow_definition(definition, agent_ids)
        if errors:
            raise WorkspaceError("\n".join(errors))
        workflow_id, now = new_id("wfl"), utc_now()
        with self._connection() as db:
            db.execute("INSERT INTO workflows VALUES (?, ?, ?, ?, ?)",
                       (workflow_id, project_id, definition["name"].strip(),
                        json.dumps(definition, ensure_ascii=False), now))
            self._record_event(db, "saved", "workflow", workflow_id,
                               {"project_id": project_id, "name": definition["name"]})
        return workflow_id

    def list_workflows(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as db:
            self._require_project(db, project_id)
            rows = db.execute("SELECT * FROM workflows WHERE project_id=? ORDER BY created_at DESC",
                              (project_id,))
            return [{**dict(row), "definition": _json_dict(row["definition"])} for row in rows]

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM workflows WHERE id=?", (workflow_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["definition"] = _json_dict(result["definition"])
            return result

    def start_workflow(self, project_id: str, workflow_id: str) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        if not workflow or workflow["project_id"] != project_id:
            raise WorkspaceError("Workflow not found for this project.")
        definition = workflow["definition"]
        with self._connection() as db:
            agent_ids = {row[0] for row in db.execute("SELECT id FROM agent_definitions")}
        errors = validate_workflow_definition(definition, agent_ids)
        if errors:
            raise WorkspaceError("\n".join(errors))
        run_id, now = new_id("run"), utc_now()
        with self._connection() as db:
            db.execute("INSERT INTO workflow_runs VALUES (?, ?, ?, 'running', ?, NULL, '')",
                       (run_id, workflow_id, project_id, now))
            for position, step in enumerate(definition["steps"]):
                db.execute(
                    "INSERT INTO tasks (id,run_id,project_id,step_id,position,title,task_type,config,"
                    "status,assigned_agent_id,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (new_id("tsk"), run_id, project_id, step["id"], position,
                     step["title"], step["task_type"],
                     json.dumps(step.get("config", {}), ensure_ascii=False), "queued",
                     step.get("assigned_agent_id"), now, now),
                )
            self._record_event(db, "started", "workflow_run", run_id,
                               {"project_id": project_id, "workflow_id": workflow_id})
        self._advance_run(run_id)
        return self.get_run(run_id)  # type: ignore[return-value]

    def _execute_task(self, task: dict[str, Any]) -> dict[str, Any] | None:
        config = _json_dict(task["config"])
        project_id = task["project_id"]
        if task["task_type"] == "review_sources":
            sources = self.list_source_material(project_id)
            material = []
            remaining = 100_000
            for source in sources:
                body = source["content"] if source["status"] == "retrieved" else ""
                excerpt = body[:min(20_000, remaining)]
                remaining -= len(excerpt)
                material.append({
                    "id": source["id"], "title": source["title"], "url": source["url"],
                    "content_type": source["content_type"], "status": source["status"],
                    "content": excerpt,
                    "truncated": len(excerpt) < len(body),
                })
            return {
                "total": len(sources),
                "retrieved": sum(source["status"] == "retrieved" for source in sources),
                "pending": sum(source["status"] == "pending" for source in sources),
                "failed": sum(source["status"] == "failed" for source in sources),
                "sources": material,
            }
        if task["task_type"] == "record_note":
            note_id = self.create_note(
                project_id, config["title"], config["body"], actor="workflow"
            )
            return {"note_id": note_id, "title": config["title"]}
        if task["task_type"] == "organize_corrections":
            corrections = self.list_corrections(project_id, config.get("category"))
            counts = {category: 0 for category in CORRECTION_CATEGORIES}
            for correction in corrections:
                counts[correction["category"]] += 1
            return {"total": len(corrections), "by_category": counts}
        if task["task_type"] == "manual_review":
            return {"awaiting_human_review": True, "prompt": config["prompt"]}
        raise WorkspaceError(f"Unregistered task type {task['task_type']!r}.")

    def _advance_run(self, run_id: str) -> None:
        while True:
            with self._connection() as db:
                run = db.execute("SELECT * FROM workflow_runs WHERE id=?", (run_id,)).fetchone()
                if run is None:
                    raise WorkspaceError("Workflow run not found.")
                if run["status"] != "running":
                    return
                row = db.execute(
                    "SELECT * FROM tasks WHERE run_id=? AND status='queued' ORDER BY position LIMIT 1",
                    (run_id,),
                ).fetchone()
                if row is None:
                    now = utc_now()
                    db.execute("UPDATE workflow_runs SET status='completed',completed_at=? WHERE id=?",
                               (now, run_id))
                    self._record_event(db, "completed", "workflow_run", run_id)
                    return
                task = dict(row)
                now = utc_now()
                db.execute("UPDATE tasks SET status='running',updated_at=? WHERE id=?",
                           (now, task["id"]))
                self._record_event(db, "started", "task", task["id"],
                                   {"run_id": run_id, "step_id": task["step_id"]})
            try:
                output = self._execute_task(task)
                if task["task_type"] == "manual_review":
                    with self._connection() as db:
                        now = utc_now()
                        db.execute(
                            "UPDATE tasks SET status='awaiting_review',output=?,updated_at=? WHERE id=?",
                            (json.dumps(output or {}, ensure_ascii=False), now, task["id"]),
                        )
                        db.execute("UPDATE workflow_runs SET status='awaiting_review' WHERE id=?",
                                   (run_id,))
                        self._record_event(db, "awaiting_review", "task", task["id"],
                                           {"run_id": run_id})
                    return
                with self._connection() as db:
                    now = utc_now()
                    db.execute(
                        "UPDATE tasks SET status='completed',output=?,updated_at=? WHERE id=?",
                        (json.dumps(output or {}, ensure_ascii=False), now, task["id"]),
                    )
                    self._record_event(db, "completed", "task", task["id"], {"run_id": run_id})
            except Exception as exc:
                with self._connection() as db:
                    now = utc_now()
                    message = str(exc)[:1000]
                    db.execute("UPDATE tasks SET status='failed',error=?,updated_at=? WHERE id=?",
                               (message, now, task["id"]))
                    db.execute("UPDATE tasks SET status='skipped',updated_at=? WHERE run_id=? AND status='queued'",
                               (now, run_id))
                    db.execute("UPDATE workflow_runs SET status='failed',completed_at=?,error=? WHERE id=?",
                               (now, message, run_id))
                    self._record_event(db, "failed", "task", task["id"],
                                       {"run_id": run_id, "error": message})
                return

    def complete_human_review(self, task_id: str, review: str) -> dict[str, Any]:
        review = review.strip()
        if not review:
            raise WorkspaceError("Enter a human review result before continuing.")
        with self._connection() as db:
            row = db.execute("SELECT run_id,status FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None or row["status"] != "awaiting_review":
                raise WorkspaceError("Task is not awaiting human review.")
            run_id, now = row["run_id"], utc_now()
            db.execute("UPDATE tasks SET status='completed',output=?,updated_at=? WHERE id=?",
                       (json.dumps({"human_review": review}, ensure_ascii=False), now, task_id))
            db.execute("UPDATE workflow_runs SET status='running' WHERE id=?", (run_id,))
            self._record_event(db, "reviewed", "task", task_id, {"run_id": run_id})
        self._advance_run(run_id)
        return self.get_run(run_id)  # type: ignore[return-value]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM workflow_runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["tasks"] = []
            for task_row in db.execute("SELECT * FROM tasks WHERE run_id=? ORDER BY position", (run_id,)):
                task = dict(task_row)
                task["config"] = _json_dict(task["config"])
                task["output"] = _json_dict(task["output"])
                result["tasks"].append(task)
            return result

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connection() as db:
            rows = db.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,))
            result = []
            for row in rows:
                event = dict(row)
                event["detail"] = _json_dict(event["detail"])
                result.append(event)
            return result
