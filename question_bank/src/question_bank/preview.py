"""Local reviewer preview for authored question JSON."""

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .checking import check_answer
from .validation import validate_bank

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>N1 question bank preview</title>
  <link rel="stylesheet" href="/vendor/katex/katex.min.css">
  <style>
    :root{font-family:Inter,system-ui,sans-serif;color:#172033;background:#f3f6fb}*{box-sizing:border-box}
    body{margin:0}.shell{display:grid;grid-template-columns:280px 1fr;min-height:100vh}.side{background:#10233f;color:#fff;padding:24px;position:sticky;top:0;height:100vh;overflow:auto}.side h1{font-size:20px;margin:0 0 6px}.side p{color:#a8bad2;font-size:13px}.question-link{display:block;width:100%;text-align:left;border:0;border-radius:10px;padding:11px 12px;margin:7px 0;background:#193454;color:#dce8f7;cursor:pointer}.question-link.active{background:#46c2b8;color:#092330}.main{padding:34px;max-width:980px;width:100%;margin:auto}.card{background:#fff;border:1px solid #dce4ef;border-radius:16px;padding:24px;box-shadow:0 8px 26px #24405f12;margin-bottom:18px}.meta{display:flex;gap:8px;flex-wrap:wrap}.badge{background:#e9f2fb;border-radius:999px;padding:5px 9px;font-size:12px}.part{border-top:1px solid #e5eaf1;margin-top:20px;padding-top:20px}.prompt{font-size:17px;line-height:1.7}.asset{max-width:100%;margin:18px 0;border:1px solid #d8e0eb;border-radius:10px;background:#fff}.answer-row{display:flex;gap:9px;margin-top:14px}.answer-row input{flex:1;padding:12px;border:1px solid #aebbc9;border-radius:9px;font-size:16px}.button{border:0;border-radius:9px;padding:10px 14px;cursor:pointer;background:#176b87;color:#fff}.secondary{background:#e7edf4;color:#21344b}.feedback{min-height:24px;margin-top:9px;font-weight:600}.correct{color:#087b54}.incorrect{color:#b33646}.reveal{margin-top:12px;padding:13px;background:#f5f8fb;border-radius:9px}.reveal[hidden]{display:none}.solution-step{padding:7px 0}.mark{color:#607085;font-size:12px}.empty{padding:40px;text-align:center}.nav{display:flex;justify-content:space-between;gap:10px;margin-top:20px}@media(max-width:760px){.shell{display:block}.side{height:auto;position:static}.main{padding:18px}}
  </style>
</head>
<body><div class="shell"><aside class="side"><h1>N1 reviewer preview</h1><p>Draft questions, answers, hints and mark schemes.</p><div id="list"></div></aside><main class="main"><div id="content" class="empty">Loading questions…</div></main></div>
<script src="/vendor/katex/katex.min.js"></script>
<script>
let questions=[], index=0;
function node(tag, cls, text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function blocks(items,q){const root=node('span');for(const b of items){if(b.type==='text')root.append(node('span','',b.text));else if(b.type==='inline_math'||b.type==='display_math'){const m=node(b.type==='display_math'?'div':'span');katex.render(b.latex,m,{throwOnError:false,displayMode:b.type==='display_math'});root.append(m)}else{const a=q.assets.find(x=>x.asset_key===b.asset_key);if(a){const img=node('img','asset');img.src='/content/'+a.path;img.alt=a.alt_text;root.append(img)}}}return root}
function revealButton(label,content){const wrap=node('div');const button=node('button','button secondary',label);const box=node('div','reveal');box.hidden=true;box.append(content);button.onclick=()=>{box.hidden=!box.hidden};wrap.append(button,box);return wrap}
async function check(q,part,input,feedback){const response=await fetch('/api/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stable_key:q.stable_key,part_position:part.position,answer:input.value})});const result=await response.json();feedback.className='feedback '+(result.correct?'correct':'incorrect');feedback.textContent=result.correct?'Correct.':(result.error||'Not correct yet.')}
function render(){const q=questions[index], target=document.getElementById('content');target.textContent='';document.querySelectorAll('.question-link').forEach((b,i)=>b.classList.toggle('active',i===index));if(!q){target.className='empty';target.textContent='No question JSON files found.';return}target.className='';const head=node('section','card');head.append(node('h1','',q.title));const meta=node('div','meta');[`Key: ${q.stable_key}`,`Difficulty ${q.difficulty}`,`Outcome ${q.primary_outcome}`,`${q.total_marks} marks`,q.status].forEach(x=>meta.append(node('span','badge',x)));head.append(meta,blocks(q.stem,q));target.append(head);for(const p of q.parts){const card=node('section','card part');card.append(node('h2','',p.label?`Part (${p.label}) · ${p.marks} mark${p.marks===1?'':'s'}`:`${p.marks} mark${p.marks===1?'':'s'}`));const prompt=node('div','prompt');prompt.append(blocks(p.prompt,q));card.append(prompt);const row=node('div','answer-row'),input=node('input');input.placeholder=p.response.type==='numeric'?'Enter a numeric answer':'Enter a mathematical expression';const button=node('button','button','Check answer'),feedback=node('div','feedback');button.onclick=()=>check(q,p,input,feedback);row.append(input,button);card.append(row,feedback);for(const hint of p.hints){const body=node('div');body.append(blocks(hint.content,q));card.append(revealButton(`Show hint ${hint.stage}`,body))}const solution=node('div');for(const step of p.solution){const line=node('div','solution-step');line.append(blocks(step.content,q));if(step.mark_type)line.append(node('div','mark',`${step.mark_type}${step.mark_value}`));solution.append(line)}const answer=p.response.canonical_answer||p.response.canonical_expression;solution.prepend(node('p','',`Accepted answer: ${answer}`));card.append(revealButton('Show answer and solution',solution));target.append(card)}const nav=node('div','nav');const prev=node('button','button secondary','Previous'),next=node('button','button','Next');prev.disabled=index===0;next.disabled=index===questions.length-1;prev.onclick=()=>{index--;render()};next.onclick=()=>{index++;render()};nav.append(prev,next);target.append(nav)}
fetch('/api/questions').then(r=>r.json()).then(data=>{questions=data.questions;const list=document.getElementById('list');questions.forEach((q,i)=>{const b=node('button','question-link',`${q.stable_key} · ${q.title}`);b.onclick=()=>{index=i;render()};list.append(b)});render()}).catch(e=>{document.getElementById('content').textContent=e});
</script></body></html>"""


def handler_for(bank_root: Path):
    bank_root = bank_root.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    vendor_root = repository_root / "ocr_extractor/src/ocr_extractor/web/vendor/katex"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type="application/json", status=HTTPStatus.OK):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _file(self, root, relative):
            path = (root / unquote(relative)).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self._send(path.read_bytes(), content_type)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._send(INDEX_HTML, "text/html; charset=utf-8")
            elif path == "/api/questions":
                report = validate_bank(bank_root)
                payload = {
                    "questions": [q.model_dump(mode="json") for q in report.questions],
                    "validation": report.as_dict(),
                }
                self._send(json.dumps(payload).encode())
            elif path.startswith("/content/"):
                self._file(bank_root, path.removeprefix("/content/"))
            elif path.startswith("/vendor/katex/"):
                self._file(vendor_root, path.removeprefix("/vendor/katex/"))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self):
            if urlparse(self.path).path != "/api/check":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                report = validate_bank(bank_root)
                question = next(q for q in report.questions if q.stable_key == payload["stable_key"])
                part = next(p for p in question.parts if p.position == payload["part_position"])
                result = check_answer(part.response, str(payload.get("answer", "")))
                self._send(json.dumps(result))
            except (KeyError, StopIteration, TypeError, ValueError, json.JSONDecodeError) as exc:
                self._send(
                    json.dumps({"correct": False, "error": str(exc)}),
                    status=HTTPStatus.BAD_REQUEST,
                )

        def log_message(self, message, *args):
            print(f"preview: {message % args}")

    return Handler


def serve(bank_root: Path, host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), handler_for(bank_root))
    print(f"N1 preview: http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
