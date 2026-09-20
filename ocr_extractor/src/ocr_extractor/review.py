"""Loopback-only human review workbench with immutable extraction/review history."""

import hashlib
import json
import mimetypes
import secrets
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4

from pydantic import Field, ValidationError, model_validator

from .files import atomic_json
from .models import ContentBlock, ExtractionResult, Model
from .pdf import ExtractionError


def fingerprint(question):
    return hashlib.sha256(question.model_dump_json().encode()).hexdigest()


class ReviewInput(Model):
    document_id: UUID
    question_id: UUID
    run_key: str = Field(pattern=r"^[a-f0-9]{24}$")
    source_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    previous_review_id: UUID | None = None
    reviewer: str = Field(min_length=1, max_length=120)
    decision: Literal["draft", "checked", "rejected"] = "draft"
    notes: str = Field(default="", max_length=20000)
    content: list[ContentBlock] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def valid_review(self):
        if not self.reviewer.strip():
            raise ValueError("Enter the reviewer's name")
        if len({block.id for block in self.content}) != len(self.content):
            raise ValueError("Block IDs must be unique")
        if self.decision == "checked":
            for block in self.content:
                if block.type == "text" and not block.text.strip():
                    raise ValueError("A checked text block cannot be empty")
                if block.type == "math" and (
                    not block.latex or block.latex.count("{") != block.latex.count("}")
                ):
                    raise ValueError("A checked math block needs balanced LaTeX")
                if block.type == "table" and not block.rows:
                    raise ValueError("A checked table needs rows")
        return self


class ReviewRecord(ReviewInput):
    id: UUID
    created_at: str


class ReviewStore:
    def __init__(self, output: Path, repository=None):
        self.output = output.resolve()
        self.repository = repository

    def results(self):
        latest = {}
        # Exclude model/response caches, demo inputs and arbitrary JSON files.
        for path in self.output.glob("*/*/questions.json"):
            try:
                result = ExtractionResult.model_validate_json(path.read_text())
            except (ValueError, OSError):
                continue
            key = str(result.document.id)
            if key not in latest or latest[key].created_at < result.created_at:
                latest[key] = result
        return latest

    def result(self, document_id, run_key):
        document_id = UUID(str(document_id))
        if len(run_key) != 24 or any(c not in "0123456789abcdef" for c in run_key):
            raise ValueError("Invalid run key")
        path = self.output / str(document_id) / run_key / "questions.json"
        if not path.resolve().is_relative_to(self.output):
            raise ValueError("Invalid manifest path")
        return ExtractionResult.model_validate_json(path.read_text())

    def latest_review(self, result, question):
        path = self.output / "reviews" / str(result.document.id) / result.run_key / str(question.id)
        reviews = [ReviewRecord.model_validate_json(p.read_text()) for p in path.glob("*.json")]
        return max(reviews, key=lambda r: r.created_at) if reviews else None

    def save(self, request: ReviewInput):
        result = self.result(request.document_id, request.run_key)
        question = next((q for q in result.questions if q.id == request.question_id), None)
        if question is None:
            raise ValueError("Question not found in this extraction")
        if request.source_fingerprint != fingerprint(question):
            raise ExtractionError("review_conflict", "Extraction changed; reload before saving.")
        previous = self.latest_review(result, question)
        if request.previous_review_id != (previous.id if previous else None):
            raise ExtractionError("review_conflict", "Another review was saved; reload first.")
        # Content may be split/reordered by a reviewer, but every block must retain
        # an existing source region; paths and evidence cannot be supplied freely.
        evidence = {
            (b.source_path, b.source_sha256, b.page_number, b.bbox.model_dump_json())
            for b in question.content
        }
        for block in request.content:
            if (
                block.source_path,
                block.source_sha256,
                block.page_number,
                block.bbox.model_dump_json(),
            ) not in evidence:
                raise ValueError("A correction must retain an original source region")
        record = ReviewRecord(
            **request.model_dump(),
            id=uuid4(),
            created_at=datetime.now(UTC).isoformat(),
        )
        if self.repository:
            self.repository.save_review(record)
        destination = (
            self.output
            / "reviews"
            / str(record.document_id)
            / record.run_key
            / str(record.question_id)
            / f"{record.id}.json"
        )
        atomic_json(destination, record.model_dump(mode="json"))
        return record

    def allowed_assets(self):
        allowed = set()
        for result in self.results().values():
            allowed.update(p.image_path for p in result.pages)
            allowed.update(a.path for q in result.questions for a in q.assets)
            allowed.update(b.source_path for q in result.questions for b in q.content)
            allowed.update(a.path for a in result.unpaired_solutions)
        return allowed


def make_server(output: Path, port: int, repository=None):
    store = ReviewStore(output, repository)
    token = secrets.token_urlsafe(32)
    static = Path(str(files("ocr_extractor").joinpath("web"))).resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # URLs contain the local session token for image requests.

        def send(self, status, body, mime="application/json"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                (
                    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                    "img-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
                ),
            )
            self.end_headers()
            self.wfile.write(body)

        def authorized(self, params):
            supplied = self.headers.get("X-Review-Token") or params.get("token", [""])[0]
            return secrets.compare_digest(supplied, token)

        def local_host(self):
            return self.headers.get("Host") in {
                f"localhost:{self.server.server_port}",
                f"127.0.0.1:{self.server.server_port}",
            }

        def do_GET(self):
            if not self.local_host():
                return self.send(403, {"error": "Local access only"})
            url = urlsplit(self.path)
            params = parse_qs(url.query)
            if url.path == "/":
                return self.send(
                    200,
                    (static / "index.html").read_text().replace("__REVIEW_TOKEN__", token),
                    "text/html; charset=utf-8",
                )
            if url.path.startswith("/static/"):
                path = (static / url.path.removeprefix("/static/")).resolve()
                if not path.is_relative_to(static) or not path.is_file():
                    return self.send(404, {"error": "Not found"})
                return self.send(
                    200,
                    path.read_bytes(),
                    mimetypes.guess_type(path)[0] or "application/octet-stream",
                )
            if not self.authorized(params):
                return self.send(403, {"error": "Reload the workbench to start a session"})
            try:
                if url.path == "/api/documents":
                    return self.send(
                        200,
                        [
                            {
                                "document": r.document.model_dump(mode="json"),
                                "run_key": r.run_key,
                                "questions": len(r.questions),
                                "warnings": r.warnings,
                            }
                            for r in store.results().values()
                        ],
                    )
                if url.path == "/api/document":
                    result = store.result(params["document"][0], params["run"][0])
                    records = []
                    for question in result.questions:
                        review = store.latest_review(result, question)
                        records.append(
                            {
                                "question": question.model_dump(mode="json"),
                                "fingerprint": fingerprint(question),
                                "review": review.model_dump(mode="json") if review else None,
                                "review_stale": bool(
                                    review and review.source_fingerprint != fingerprint(question)
                                ),
                            }
                        )
                    return self.send(
                        200, {"result": result.model_dump(mode="json"), "items": records}
                    )
                if url.path == "/asset":
                    name = params["path"][0]
                    path = (store.output / name).resolve()
                    if name not in store.allowed_assets() or not path.is_relative_to(store.output):
                        return self.send(403, {"error": "Asset is not part of this extraction"})
                    return self.send(200, path.read_bytes(), "image/png")
                return self.send(404, {"error": "Not found"})
            except (ValueError, OSError, KeyError):
                return self.send(404, {"error": "Extraction or asset not found"})

        def do_POST(self):
            expected_origin = f"http://{self.headers.get('Host')}"
            if (
                not self.local_host()
                or self.headers.get("Origin") != expected_origin
                or not (self.authorized({}))
            ):
                return self.send(403, {"error": "Invalid local review session"})
            if self.path != "/api/reviews":
                return self.send(404, {"error": "Not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 2_000_000:
                    return self.send(413, {"error": "Review is too large"})
                request = ReviewInput.model_validate_json(self.rfile.read(size))
                record = store.save(request)
                return self.send(200, record.model_dump(mode="json"))
            except ExtractionError as exc:
                return self.send(409, {"error": str(exc)})
            except ValidationError as exc:
                return self.send(400, {"error": "; ".join(e["msg"] for e in exc.errors())})
            except (ValueError, OSError):
                return self.send(400, {"error": "Invalid review or missing extraction"})
            except Exception:
                return self.send(500, {"error": "Could not persist review; check local storage"})

    return HTTPServer(("127.0.0.1", port), Handler)


def serve(output: Path, port: int, repository=None):
    if not 0 <= port <= 65535:
        raise ExtractionError("invalid_port", "Port must be between 0 and 65535")
    server = make_server(output, port, repository)
    print(f"Review workbench: http://localhost:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
