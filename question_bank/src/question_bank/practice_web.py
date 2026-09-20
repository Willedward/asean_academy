"""Local JSON practice API and replaceable placeholder frontend."""

from __future__ import annotations

import json
import mimetypes
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .practice import PracticeEngine, PracticeError

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ASEAN Academy · N1 practice</title>
  <link rel="stylesheet" href="/vendor/katex/katex.min.css">
  <style>
    :root{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#13243a;background:#f3f7fa;line-height:1.55}
    *{box-sizing:border-box}body{margin:0}.top{background:#102b3f;color:#fff;padding:18px 24px}.top-inner{max-width:920px;margin:auto;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-weight:800;letter-spacing:-.02em}.topic{color:#b7cfda;font-size:14px}.shell{max-width:920px;margin:32px auto;padding:0 20px}.notice{background:#fff5d9;border:1px solid #eed38b;border-radius:12px;padding:12px 15px;color:#684c00;margin-bottom:18px}.card{background:#fff;border:1px solid #dce6ec;border-radius:18px;padding:28px;box-shadow:0 14px 40px #22425c12}.start{max-width:600px;margin:70px auto}.start h1{font-size:34px;line-height:1.15;margin:0 0 12px}.muted{color:#647789}.field{display:grid;gap:7px;margin:20px 0}.field label{font-weight:700}.field input{font:inherit;padding:12px 14px;border:1px solid #a9bbc7;border-radius:10px;max-width:180px}.button{font:inherit;font-weight:700;border:0;border-radius:10px;padding:11px 17px;cursor:pointer;background:#087f78;color:#fff}.button:hover{background:#076c67}.button.secondary{background:#e9f0f3;color:#213b4d}.button.danger{background:#a63f4d}.button:disabled{opacity:.45;cursor:not-allowed}.progress{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:15px;color:#5a7080;font-size:14px}.bar{height:8px;background:#dce8ed;border-radius:20px;overflow:hidden;flex:1}.bar span{display:block;height:100%;background:#20a99f}.meta{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 22px}.badge{padding:5px 10px;background:#eaf4f4;border-radius:999px;font-size:12px;font-weight:700}.part{border-top:1px solid #e0e8ed;padding-top:22px;margin-top:22px}.part h2{font-size:15px;color:#597080}.prompt{font-size:18px}.answer{width:100%;font:inherit;font-size:17px;padding:13px;border:1px solid #9fb2be;border-radius:10px;margin-top:14px}.answer:focus{outline:3px solid #8ddbd555;border-color:#138c84}.asset{max-width:100%;display:block;margin:18px auto;border:1px solid #dbe4e9;border-radius:10px}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}.feedback{margin-top:18px;padding:14px;border-radius:10px}.feedback.correct{background:#e4f7ee;color:#12603f}.feedback.incorrect{background:#fff0f1;color:#8f2937}.feedback:empty{display:none}.hint,.solution{background:#f4f7f9;border-radius:11px;padding:15px;margin-top:12px}.solution{background:#eef7f5}.solution-step{padding:8px 0;border-bottom:1px solid #d6e6e2}.mark{font-size:12px;color:#637a75}.next-row{display:flex;justify-content:flex-end;margin-top:20px}.hidden{display:none!important}.complete{text-align:center;padding:55px 25px}.complete h1{font-size:34px}.error{color:#9b2738;margin-top:12px}@media(max-width:600px){.card{padding:20px}.start{margin:25px auto}.top-inner{align-items:flex-start;flex-direction:column}.start h1{font-size:28px}}
  </style>
</head>
<body>
  <header class="top"><div class="top-inner"><div class="brand">ASEAN Academy</div><div class="topic">Secondary 1 G3 Mathematics · N1</div></div></header>
  <main class="shell">
    <div id="draftNotice" class="notice hidden"><strong>Development content:</strong> these questions are drafts for local testing and still require mathematical and editorial review.</div>
    <section id="start" class="card start">
      <h1>Practise numbers and operations</h1>
      <p class="muted">This is a temporary interface for testing sessions, selection, hints and answer checking. The visual design can be replaced independently.</p>
      <div class="field"><label for="count">Questions in this session</label><input id="count" type="number" min="1" max="20" value="5"></div>
      <button id="startButton" class="button">Start practice</button>
      <div id="startError" class="error"></div>
    </section>
    <section id="practice" class="hidden">
      <div class="progress"><span id="progressText"></span><div class="bar"><span id="progressBar"></span></div></div>
      <article id="question" class="card"></article>
    </section>
    <section id="complete" class="card complete hidden"><h1>Session complete</h1><p id="completeText" class="muted"></p><button id="newSession" class="button">Start another session</button></section>
  </main>
  <script src="/vendor/katex/katex.min.js"></script>
  <script>
  let sessionId=null,current=null,hintStage=0;
  const $=id=>document.getElementById(id);
  function el(tag,cls,text){const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node}
  async function api(path,options={}){const response=await fetch(path,{...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});const body=await response.json().catch(()=>({error:{message:'Invalid server response.'}}));if(!response.ok)throw new Error(body.error?.message||'Request failed.');return body}
  function blocks(items,q){const root=el('span');for(const block of items||[]){if(block.type==='text'){root.append(el('span','',block.text))}else if(block.type==='inline_math'||block.type==='display_math'){const math=el(block.type==='display_math'?'div':'span');katex.render(block.latex,math,{throwOnError:false,displayMode:block.type==='display_math',strict:'warn'});root.append(math)}else if(block.type==='asset_ref'){const asset=q.assets.find(item=>item.asset_key===block.asset_key);if(asset){const image=el('img','asset');image.src='/content/'+asset.path;image.alt=asset.alt_text;root.append(image)}}}return root}
  function showDraft(value){$('draftNotice').classList.toggle('hidden',!value)}
  async function startSession(){
    $('startError').textContent='';$('startButton').disabled=true;
    try{const created=await api('/api/practice-sessions',{method:'POST',body:JSON.stringify({question_count:Number($('count').value)})});sessionId=created.session_id;showDraft(created.development_drafts);history.replaceState({},'',`?session=${encodeURIComponent(sessionId)}`);$('start').classList.add('hidden');$('practice').classList.remove('hidden');await loadNext()}catch(error){$('startError').textContent=error.message}finally{$('startButton').disabled=false}
  }
  async function loadNext(){
    current=await api(`/api/practice-sessions/${encodeURIComponent(sessionId)}/next`);
    if(current.status==='completed'){showComplete(current.session);return}
    hintStage=current.highest_hint_stage||0;renderQuestion();
  }
  function renderQuestion(){
    const q=current.question,target=$('question');target.textContent='';
    const resolved=current.session.resolved_count,total=current.session.question_count;
    $('progressText').textContent=`Question ${current.position} of ${total}`;$('progressBar').style.width=`${Math.round(resolved/total*100)}%`;
    target.append(el('h1','',q.title));const meta=el('div','meta');[`Difficulty ${q.difficulty}`,`Outcome ${q.primary_outcome}`,`${q.total_marks} marks`,current.selection_reason.replaceAll('_',' ')].forEach(value=>meta.append(el('span','badge',value)));target.append(meta,blocks(q.stem,q));
    for(const part of q.parts){const section=el('section','part');section.dataset.position=part.position;section.append(el('h2','',part.label?`Part (${part.label}) · ${part.marks} mark${part.marks===1?'':'s'}`:`${part.marks} mark${part.marks===1?'':'s'}`));const prompt=el('div','prompt');prompt.append(blocks(part.prompt,q));const input=el('input','answer');input.placeholder=part.input_placeholder;input.autocomplete='off';input.dataset.answer=part.position;const partFeedback=el('div','feedback');partFeedback.dataset.feedback=part.position;section.append(prompt,input,partFeedback);target.append(section)}
    const actions=el('div','actions'),hint1=el('button','button secondary','Hint 1'),hint2=el('button','button secondary','Hint 2'),submit=el('button','button','Check answers'),giveUp=el('button','button danger','Give up and show solution');hint2.disabled=hintStage<1;giveUp.classList.toggle('hidden',!current.solution_available);hint1.onclick=()=>revealHint(1,hint1,hint2);hint2.onclick=()=>revealHint(2,hint2,hint2);submit.onclick=()=>submitAnswers(submit,giveUp);giveUp.onclick=()=>giveUpQuestion(giveUp);actions.append(hint1,hint2,submit,giveUp);target.append(actions,el('div','feedback'));if(current.solution_available){target.lastChild.className='feedback incorrect';target.lastChild.textContent='The worked solution is now available if you want to give up.'}
  }
  async function revealHint(stage,button,hint2){
    button.disabled=true;
    try{const result=await api(`/api/practice-sessions/${encodeURIComponent(sessionId)}/questions/${encodeURIComponent(current.question.stable_key)}/hints/${stage}`,{method:'POST',body:'{}'});for(const partHint of result.parts){const section=document.querySelector(`[data-position="${partHint.position}"]`);let box=section.querySelector(`[data-hint="${stage}"]`);if(!box){box=el('div','hint');box.dataset.hint=stage;box.append(el('strong','',`Hint ${stage}: `),blocks(partHint.content,current.question));section.append(box)}}hintStage=Math.max(hintStage,stage);if(stage===1)hint2.disabled=false}catch(error){button.disabled=false;alert(error.message)}
  }
  async function submitAnswers(button,giveUp){
    button.disabled=true;const answers={};document.querySelectorAll('[data-answer]').forEach(input=>answers[input.dataset.answer]=input.value);
    try{const result=await api('/api/attempts',{method:'POST',body:JSON.stringify({session_id:sessionId,stable_key:current.question.stable_key,revision:current.question.revision,answers,idempotency_key:crypto.randomUUID()})});for(const part of result.parts){const box=document.querySelector(`[data-feedback="${part.position}"]`);box.className='feedback '+(part.correct?'correct':'incorrect');box.textContent=part.correct?`Correct · ${part.marks_awarded}/${part.marks_available} marks`:(part.error||'Not correct yet.')}
      if(result.correct){const next=el('div','next-row'),nextButton=el('button','button','Next question');nextButton.onclick=loadNext;next.append(nextButton);$('question').append(next);document.querySelectorAll('input,button').forEach(control=>control.disabled=true);nextButton.disabled=false}else{button.disabled=false;giveUp.classList.toggle('hidden',!result.solution_available)}
    }catch(error){button.disabled=false;alert(error.message)}
  }
  async function giveUpQuestion(button){
    button.disabled=true;
    try{const result=await api(`/api/practice-sessions/${encodeURIComponent(sessionId)}/questions/${encodeURIComponent(current.question.stable_key)}/give-up`,{method:'POST',body:'{}'});const box=el('div','solution');box.append(el('h2','','Worked solution'));for(const part of result.solution.parts){const heading=part.label?`Part (${part.label})`:`Part ${part.position}`;box.append(el('h3','',heading));const answer=el('div');answer.append(el('strong','','Answer: '));const math=el('span');katex.render(part.canonical_latex,math,{throwOnError:false});answer.append(math);box.append(answer);for(const step of part.steps){const row=el('div','solution-step');row.append(blocks(step.content,current.question));if(step.mark_type)row.append(el('div','mark',`${step.mark_type}${step.mark_value}`));box.append(row)}}const next=el('div','next-row'),nextButton=el('button','button','Next question');nextButton.onclick=loadNext;next.append(nextButton);$('question').append(box,next);document.querySelectorAll('input,button').forEach(control=>control.disabled=true);nextButton.disabled=false}catch(error){button.disabled=false;alert(error.message)}
  }
  function showComplete(summary){$('practice').classList.add('hidden');$('complete').classList.remove('hidden');$('completeText').textContent=`You completed ${summary.resolved_count} question${summary.resolved_count===1?'':'s'} in this local session.`;history.replaceState({},'',location.pathname)}
  function reset(){sessionId=null;current=null;$('complete').classList.add('hidden');$('practice').classList.add('hidden');$('start').classList.remove('hidden');showDraft(false)}
  $('startButton').onclick=startSession;$('newSession').onclick=reset;
  const resumed=new URLSearchParams(location.search).get('session');if(resumed){sessionId=resumed;$('start').classList.add('hidden');$('practice').classList.remove('hidden');loadNext().then(()=>showDraft(current?.session?.development_drafts)).catch(()=>reset())}
  </script>
</body>
</html>"""


SESSION_NEXT = re.compile(r"^/api/practice-sessions/([0-9a-f-]+)/next$")
HINT = re.compile(
    r"^/api/practice-sessions/([0-9a-f-]+)/questions/([a-z0-9-]+)/hints/([12])$"
)
GIVE_UP = re.compile(
    r"^/api/practice-sessions/([0-9a-f-]+)/questions/([a-z0-9-]+)/give-up$"
)


def handler_for(engine: PracticeEngine, bank_root: Path):
    bank_root = bank_root.resolve()
    repository_root = Path(__file__).resolve().parents[3]
    vendor_root = repository_root / "ocr_extractor/src/ocr_extractor/web/vendor/katex"

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, content_type="application/json", status=HTTPStatus.OK):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            if content_type.startswith("text/html"):
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                    "connect-src 'self'; object-src 'none'; base-uri 'none'",
                )
            self.end_headers()
            self.wfile.write(body)

        def _error(self, error: PracticeError):
            self._send(
                {"error": {"code": error.code, "message": str(error)}},
                status=error.status,
            )

        def _body(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise PracticeError("invalid_content_length", "Invalid request size.") from exc
            if length > 65536:
                raise PracticeError("request_too_large", "Request body is too large.", 413)
            try:
                value = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as exc:
                raise PracticeError("invalid_json", "Request body must be valid JSON.") from exc
            if not isinstance(value, dict):
                raise PracticeError("invalid_json", "Request body must be a JSON object.")
            return value

        def _file(self, root: Path, relative: str):
            path = (root / unquote(relative)).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self._send(path.read_bytes(), content_type)

        def do_GET(self):
            path = urlparse(self.path).path
            try:
                if path == "/":
                    self._send(INDEX_HTML, "text/html; charset=utf-8")
                elif match := SESSION_NEXT.fullmatch(path):
                    self._send(engine.next_question(match.group(1)))
                elif path.startswith("/content/"):
                    self._file(bank_root, path.removeprefix("/content/"))
                elif path.startswith("/vendor/katex/"):
                    self._file(vendor_root, path.removeprefix("/vendor/katex/"))
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            except PracticeError as exc:
                self._error(exc)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                payload = self._body()
                if path == "/api/practice-sessions":
                    result = engine.create_session(
                        question_count=int(payload.get("question_count", 5)),
                        difficulties=payload.get("difficulties"),
                        outcomes=payload.get("outcomes"),
                    )
                    self._send(result, status=HTTPStatus.CREATED)
                elif path == "/api/attempts":
                    self._send(
                        engine.submit_attempt(
                            session_id=str(payload.get("session_id", "")),
                            stable_key=str(payload.get("stable_key", "")),
                            revision=int(payload.get("revision", 0)),
                            answers=payload.get("answers"),
                            idempotency_key=payload.get("idempotency_key"),
                        ),
                        status=HTTPStatus.CREATED,
                    )
                elif match := HINT.fullmatch(path):
                    self._send(engine.reveal_hint(match.group(1), match.group(2), int(match.group(3))))
                elif match := GIVE_UP.fullmatch(path):
                    self._send(engine.give_up(match.group(1), match.group(2)))
                else:
                    self.send_error(HTTPStatus.NOT_FOUND)
            except (TypeError, ValueError) as exc:
                if isinstance(exc, PracticeError):
                    self._error(exc)
                else:
                    self._error(PracticeError("invalid_request", "Request fields are invalid."))

        def log_message(self, message, *args):
            print(f"practice: {message % args}")

    return Handler


def serve_practice(engine: PracticeEngine, bank_root: Path, host="127.0.0.1", port=8766):
    server = ThreadingHTTPServer((host, port), handler_for(engine, bank_root))
    print(f"N1 practice application: http://{host}:{port}")
    if engine.development_drafts:
        print("Development mode: draft questions are enabled and must not be published.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
