"use strict";
const token = document.querySelector('meta[name="review-token"]').content;
const $ = id => document.getElementById(id);
let documents = [], current = null, index = 0, blocks = [], dirty = false, renderingErrors = false;
const assetURL = path => `/asset?${new URLSearchParams({path, token})}`;
function element(tag, text, className) {
  const e = document.createElement(tag); if (text !== undefined) e.textContent = text;
  if (className) e.className = className; return e;
}
function message(text, error = false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; }
async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers: {'X-Review-Token': token, 'Content-Type': 'application/json'}});
  const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed'); return data;
}
function leave() { return !dirty || window.confirm('Leave this question and discard unsaved changes?'); }
function renderPreview() {
  $('preview').replaceChildren(); renderingErrors = false;
  for (const block of blocks) {
    if (block.type === 'text') $('preview').append(element('p', block.text));
    else if (block.type === 'math') {
      const e = element('div'); $('preview').append(e);
      try { katex.render(block.latex || '', e, {throwOnError: true, trust: false, strict: 'warn', displayMode: true, maxExpand: 1000, maxSize: 10}); }
      catch (error) { e.textContent = `LaTeX error: ${error.message}`; e.className = 'math-error'; renderingErrors = true; }
    } else if (block.type === 'image') {
      const img = element('img'); img.src = assetURL(block.source_path); img.alt = 'Original diagram or unrecognized region'; $('preview').append(img);
    } else if (block.type === 'table') {
      const table = element('table');
      for (const row of block.rows) { const tr = element('tr'); for (const cell of row) tr.append(element('td', cell)); table.append(tr); }
      $('preview').append(table);
    }
  }
}
function editBlocks() {
  $('editor').replaceChildren();
  blocks.forEach((block, i) => {
    const section = element('div', undefined, 'block'), head = element('div', undefined, 'block-head');
    const select = element('select'); select.setAttribute('aria-label', `Block ${i+1} type`);
    for (const kind of ['text','math','table','image']) { const option = element('option', kind); option.value = kind; select.append(option); }
    select.value = block.type; select.onchange = () => { block.type = select.value; dirty = true; editBlocks(); renderPreview(); };
    const score = block.confidence === null ? 'confidence unknown' : `${Math.round(block.confidence*100)}% OCR confidence`;
    head.append(select, element('span', `Block ${i+1} · ${score}`));
    const link = element('a', 'View source region'); link.href = assetURL(block.source_path); link.target = '_blank'; link.rel = 'noopener'; head.append(link);
    for (const [name, action] of [
      ['↑', () => { if (i > 0) [blocks[i-1], blocks[i]] = [blocks[i], blocks[i-1]]; }],
      ['↓', () => { if (i+1 < blocks.length) [blocks[i+1], blocks[i]] = [blocks[i], blocks[i+1]]; }],
      ['Split / copy', () => { const copy = structuredClone(block); copy.id = crypto.randomUUID(); blocks.splice(i+1, 0, copy); }],
      ['Remove', () => { if (blocks.length > 1) blocks.splice(i, 1); }],
    ]) { const button = element('button', name); button.type = 'button'; button.onclick = () => { action(); dirty = true; editBlocks(); renderPreview(); }; head.append(button); }
    section.append(head);
    if (block.type !== 'image') {
      const input = element('textarea'); input.rows = block.type === 'table' ? 5 : 3;
      input.setAttribute('aria-label', `Block ${i+1} content`);
      input.value = block.type === 'math' ? block.latex || '' : block.type === 'table' ? JSON.stringify(block.rows, null, 2) : block.text;
      input.oninput = () => {
        dirty = true;
        if (block.type === 'table') {
          try { const rows = JSON.parse(input.value); if (!Array.isArray(rows) || !rows.every(r => Array.isArray(r) && r.every(c => typeof c === 'string'))) throw new Error(); block.rows = rows; input.setCustomValidity(''); }
          catch { input.setCustomValidity('Use an array of rows, each containing strings'); }
        } else if (block.type === 'math') block.latex = input.value;
        else block.text = input.value;
        renderPreview();
      }; section.append(input);
      if (block.type === 'table') section.append(element('p', 'Edit rows as JSON arrays of cell strings. The original table crop remains available.', 'muted'));
    }
    if (block.review_reasons.length) section.append(element('p', block.review_reasons.join(' · ').replaceAll('_',' '), 'muted'));
    $('editor').append(section);
  });
}
function renderQueue() {
  $('queue').replaceChildren();
  current.items.forEach((item, i) => {
    const button = element('button'); button.type = 'button'; button.className = i === index ? 'selected' : '';
    button.append(element('span', `Question ${item.question.question_number}`), element('small', item.review_stale ? 'review outdated' : item.review?.decision || 'needs review'));
    button.onclick = () => { if (leave()) selectQuestion(i); }; $('queue').append(button);
  });
}
function selectQuestion(i) {
  index = i; dirty = false; message(''); renderQueue();
  const item = current.items[index];
  if (!item) { $('title').textContent = 'No question boundaries found'; $('subtitle').textContent = 'Inspect the source pages in the sidebar. This paper needs manual segmentation.'; return; }
  const question = item.question;
  blocks = structuredClone(item.review && !item.review_stale ? item.review.content : question.content);
  $('title').textContent = `Question ${question.question_number}`;
  $('subtitle').textContent = `${question.paper || 'Source worksheet'} · ${item.review?.decision || 'Needs review'} · ${blocks.length} content blocks`;
  $('source').replaceChildren();
  for (const asset of question.assets) {
    const link = element('a', `${asset.kind === 'solution' ? 'Solution' : 'Question'} · page ${asset.page_number} · open full size`);
    link.href = assetURL(asset.path); link.target = '_blank'; link.rel = 'noopener';
    const img = element('img'); img.src = link.href; img.alt = `Original ${asset.kind} crop, page ${asset.page_number}`;
    $('source').append(link, img);
  }
  $('warnings').textContent = question.review_reasons.join('\n');
  $('raw').textContent = 'Raw OCR (preserved):\n' + (question.raw_ocr_text || question.question_text);
  $('notes').value = item.review?.notes || ''; $('reviewer').value = item.review?.reviewer || localStorage.getItem('reviewer') || '';
  if (item.review_stale) message('The extraction changed after this review. Check the new source before saving.', true);
  if (!blocks.length) message('This older export has no content blocks. Re-extract it with the hybrid backend before editing.', true);
  editBlocks(); renderPreview();
}
async function loadDocument() {
  const document = documents[Number($('document').value)]; if (!document) return;
  current = await api(`/api/document?${new URLSearchParams({document: document.document.id, run: document.run_key})}`);
  $('document-warnings').textContent = document.document.review_reasons.length ? document.document.review_reasons.join('\n').replaceAll('_',' ') + '\n' + JSON.stringify(document.document.metadata_evidence, null, 2) : '';
  $('pages').replaceChildren();
  for (const page of current.result.pages) {
    const details = element('details'), summary = element('summary', `Page ${page.page_number} · ${page.page_type}`);
    const link = element('a', 'Open original page'); link.href = assetURL(page.image_path); link.target = '_blank'; link.rel = 'noopener';
    const img = element('img'); img.src = link.href; img.loading = 'lazy'; img.alt = `Original page ${page.page_number}`;
    details.append(summary, element('p', page.warnings.join(', ').replaceAll('_',' '), 'muted'), link, img); $('pages').append(details);
  }
  $('review-form').hidden = !current.items.length;
  $('editor').replaceChildren(); $('source').replaceChildren(); $('preview').replaceChildren();
  selectQuestion(0);
}
$('document').onchange = () => { if (leave()) loadDocument().catch(e => message(e.message, true)); };
$('next').onclick = () => { if (current?.items.length && leave()) selectQuestion((index+1) % current.items.length); };
$('notes').oninput = $('reviewer').oninput = () => { dirty = true; };
$('review-form').onsubmit = async event => {
  event.preventDefault(); const item = current?.items[index]; if (!item) return;
  const decision = event.submitter.dataset.decision;
  if ([...document.querySelectorAll('#editor textarea')].some(input => !input.reportValidity())) return;
  if (decision === 'checked' && renderingErrors) return message('Correct the LaTeX rendering errors before marking this checked.', true);
  const request = {document_id: current.result.document.id, question_id: item.question.id, run_key: current.result.run_key,
    source_fingerprint: item.fingerprint, previous_review_id: item.review?.id || null,
    reviewer: $('reviewer').value, notes: $('notes').value, decision, content: blocks};
  const buttons = [...document.querySelectorAll('#review-form button')]; buttons.forEach(b => b.disabled = true);
  try {
    item.review = await api('/api/reviews', {method: 'POST', body: JSON.stringify(request)});
    item.review_stale = false; dirty = false; localStorage.setItem('reviewer', request.reviewer); renderQueue();
    message('Review saved. The extraction and source evidence are preserved.');
  } catch (e) { message(e.message, true); }
  finally { buttons.forEach(b => b.disabled = false); }
};
window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
(async () => {
  documents = await api('/api/documents');
  documents.forEach((d,i) => { const option = element('option', `${d.document.original_filename} (${d.questions})`); option.value = i; $('document').append(option); });
  if (!documents.length) message('No extractions found in this output directory. Run ocr-extract extract first.', true);
  else await loadDocument();
})().catch(e => message(e.message, true));
