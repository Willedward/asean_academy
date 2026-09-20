"""Small localhost course-map preview for authors and frontend collaboration."""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def render_course_preview(report) -> str:
    course = report.course
    pools_by_lesson = {
        pool.lesson_key: pool
        for pool in report.pools.pools
        if pool.type == "lesson_practice"
    }
    unit_pools = [
        pool for pool in report.pools.pools if pool.type != "lesson_practice"
    ]
    lesson_cards = []
    for lesson in sorted(report.lessons, key=lambda item: item.position):
        pool = pools_by_lesson[lesson.stable_key]
        stage_counts = {}
        for item in pool.items:
            stage_counts[item.stage] = stage_counts.get(item.stage, 0) + 1
        stages = " · ".join(
            f"{html.escape(stage.title())}: {count}"
            for stage, count in stage_counts.items()
        )
        prerequisites = ", ".join(lesson.prerequisite_lessons) or "None"
        objectives = "".join(
            f"<li>{html.escape(objective)}</li>" for objective in lesson.objectives
        )
        lesson_cards.append(
            f"""
            <article class="lesson">
              <div class="lesson-index">{lesson.position:02d}</div>
              <div>
                <div class="eyebrow">Outcome {html.escape(', '.join(lesson.outcomes))}
                  <span class="status">{html.escape(lesson.status)}</span>
                </div>
                <h2>{html.escape(lesson.title)}</h2>
                <p>{html.escape(lesson.summary)}</p>
                <ul>{objectives}</ul>
                <div class="metadata">
                  {lesson.estimated_minutes} min · {pool.expected_question_count} practice
                  questions · {html.escape(stages)}
                </div>
                <div class="prerequisite">Prerequisites: {html.escape(prerequisites)}</div>
              </div>
            </article>
            """
        )
    unit_pool_cards = "".join(
        f"""
        <div class="pool">
          <strong>{html.escape(pool.stable_key)}</strong>
          <span>{html.escape(pool.type.replace('_', ' ').title())}</span>
          <b>{len(pool.items)} questions</b>
        </div>
        """
        for pool in unit_pools
    )
    warnings = "".join(
        f"<li><code>{html.escape(issue.path)}</code>: {html.escape(issue.message)}</li>"
        for issue in report.warnings
    )
    policy = course.mastery_policies[0]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(course.title)} — course preview</title>
  <style>
    :root {{ color-scheme: dark; --ink:#edf6f7; --muted:#9db2b8; --line:#29434a;
      --card:#12282e; --accent:#59dbc9; --amber:#ffcb6b; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:#07171c; color:var(--ink);
      font:16px/1.55 system-ui,sans-serif; }} main {{ width:min(1040px,92vw); margin:0 auto;
      padding:64px 0 96px; }} .eyebrow {{ color:var(--accent); font-size:.78rem;
      font-weight:800; letter-spacing:.09em; text-transform:uppercase; }} h1 {{ font-size:clamp(2rem,5vw,4rem);
      line-height:1.05; margin:.3rem 0 1rem; }} .lead {{ color:var(--muted); max-width:760px;
      font-size:1.1rem; }} .summary {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px;
      margin:32px 0; }} .metric,.pool {{ background:var(--card); border:1px solid var(--line);
      border-radius:14px; padding:16px; }} .metric b {{ display:block; font-size:1.6rem; color:var(--accent); }}
    .metric span,.pool span {{ color:var(--muted); display:block; }} .warning {{ background:#322712;
      border:1px solid #765c21; border-radius:14px; padding:16px 22px; }} .warning h2 {{ margin-top:0;
      color:var(--amber); }} .lesson {{ display:grid; grid-template-columns:64px 1fr; gap:20px;
      padding:26px 0; border-bottom:1px solid var(--line); }} .lesson-index {{ color:#55757d;
      font-size:1.8rem; font-weight:800; }} .lesson h2 {{ margin:.2rem 0; }} .lesson p,
    .metadata,.prerequisite {{ color:var(--muted); }} .status {{ margin-left:10px; border:1px solid #765c21;
      color:var(--amber); padding:3px 8px; border-radius:99px; }} .metadata {{ margin-top:14px;
      color:var(--accent); }} .prerequisite {{ font-size:.88rem; }} .pools {{ display:grid;
      grid-template-columns:repeat(2,1fr); gap:12px; }} .pool b {{ color:var(--accent); }}
    code {{ color:var(--accent); }} @media(max-width:700px) {{ .summary {{ grid-template-columns:1fr 1fr; }}
      .pools {{ grid-template-columns:1fr; }} .lesson {{ grid-template-columns:42px 1fr; }} }}
  </style>
</head>
<body><main>
  <div class="eyebrow">Local author preview · revision {course.revision} · {html.escape(course.status)}</div>
  <h1>{html.escape(course.title)}</h1>
  <p class="lead">{html.escape(course.description)}</p>
  <section class="summary">
    <div class="metric"><b>{len(report.lessons)}</b><span>lesson shells</span></div>
    <div class="metric"><b>{report.as_dict()['allocated_question_count']}</b><span>allocated questions</span></div>
    <div class="metric"><b>{policy.minimum_eventual_correct_percentage}%</b><span>proficiency threshold</span></div>
    <div class="metric"><b>{course.units[0].checkpoint_question_count}</b><span>checkpoint questions</span></div>
  </section>
  <section class="warning"><h2>Draft gate</h2><p>This content is structurally valid but cannot be
    published until the teaching sections and Mathematics are human-reviewed.</p><ul>{warnings}</ul></section>
  <section>{''.join(lesson_cards)}</section>
  <h2>Unit-level pools</h2><section class="pools">{unit_pool_cards}</section>
</main></body></html>"""


def serve_course(report, host: str, port: int):
    page = render_course_preview(report).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                body = json.dumps({"status": "ok", "course": report.course.stable_key}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
            elif self.path in {"/", "/index.html"}:
                body = page
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
            else:
                body = b"Not found"
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Course preview: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
