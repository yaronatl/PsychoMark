"use strict";

const main = document.querySelector("#main");
const state = {templates: [], draft: null, exam: null, copy: null, filter: "all", selected: null, busy: false, dirty: false};
window.psychomarkCanReload = () => !state.busy && !state.dirty;
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const number = value => value == null ? "—" : new Intl.NumberFormat("fr-FR", {maximumFractionDigits: 2}).format(value);
const date = value => new Date(value).toLocaleDateString("fr-FR", {day:"numeric", month:"short", year:"numeric"});
const badge = (text, color="gray") => `<span class="badge ${color}">${esc(text)}</span>`;
const questionKey = row => `${row.section}:${row.question}`;
const template = id => state.templates.find(t => t.id === id);
const templateLabel = t => t.synthetic ? `Démonstration · ${t.sections.length} sections` : t.id;
const verdictLabel = {correct:"Correcte", incorrect:"Incorrecte", blank:"Sans réponse", pending:"À vérifier"};
const verdictColor = {correct:"green", incorrect:"red", blank:"gray", pending:"amber"};
const detectionLabel = {single:"Réponse unique", blank:"Aucune marque détectée", multiple:"Plusieurs marques", uncertain:"Lecture incertaine", unreadable:"Zone illisible"};

async function api(path, options={}) {
  const headers = options.body instanceof FormData ? {} : {"Content-Type":"application/json"};
  let response;
  try { response = await fetch(path, {...options, headers:{...headers, ...options.headers}}); }
  catch { throw new Error("Le serveur ne répond pas. Vérifie qu’il est démarré, puis réessaie."); }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? "La configuration est incomplète ou invalide. Vérifie les sections et le corrigé." : data.detail;
    throw new Error(detail || `La requête a échoué (${response.status}).`);
  }
  return data;
}

let toastTimer;
function toast(message) {
  const el = document.querySelector("#toast"); el.textContent = message; el.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => {el.hidden = true;}, 5500);
}
function errorIn(id, message) { const el = document.getElementById(id); if (el) el.textContent = message; else toast(message); }
function navigate(path) { if (location.hash === `#${path}`) route(); else location.hash = path; }
function heading(eyebrow, title, description, actions="") {
  return `<div class="page-head"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1><p>${esc(description)}</p></div><div class="actions">${actions}</div></div>`;
}
function demoNotice() {
  return `<div class="notice"><span class="notice-symbol" aria-hidden="true">i</span><div><strong>Commencez avec une copie de démonstration</strong>Les modèles de démonstration utilisent des données synthétiques. Vos propres feuilles nécessitent un modèle calibré.</div>${state.templates.some(t=>t.id==="demo_eight_sections_v1") ? '<button class="button small" data-action="demo">Essayer la démonstration →</button>' : ""}</div>`;
}

function renderDashboard(exams) {
  const copies = exams.reduce((n,e)=>n+e.copy_count,0);
  main.innerHTML = heading("VOTRE ESPACE DE TRAVAIL", "Mes examens", "Préparez votre corrigé. Importez les copies. Concentrez-vous sur les réponses à vérifier.", '<a class="button primary" href="#/new">＋ Créer un examen</a>') +
    `<div class="stats"><div class="card"><div class="stat-label">Examens enregistrés</div><div class="stat-value">${exams.length}</div><div class="stat-foot">Configurations et corrigés réutilisables</div></div><div class="card"><div class="stat-label">Copies analysées</div><div class="stat-value">${copies}</div><div class="stat-foot">Résultats conservés sur cette machine</div></div><div class="card"><div class="stat-label">Modèles de feuille</div><div class="stat-value">${state.templates.length}</div><div class="stat-foot">Choisis explicitement pour chaque examen</div></div></div>` + demoNotice() +
    `<div class="section-head"><h2>Vos examens <span class="count">${exams.length}</span></h2><span class="subtle">Les plus récents en premier</span></div>` +
    (exams.length ? `<div class="card table-card table-wrap"><table><thead><tr><th>Examen</th><th>Configuration</th><th>Copies</th><th>Modifié le</th><th><span class="subtle">Action</span></th></tr></thead><tbody>${exams.map(record=>{
      const e=record.exam, total=Object.values(e.sections).reduce((n,q)=>n+q.length,0);
      return `<tr><td><a href="#/exam/${record.id}"><strong>${esc(e.name)}</strong></a><small>${esc(templateLabel(template(e.template_id)||{id:e.template_id}))}</small></td><td>${Object.keys(e.sections).length} sections · ${total} questions</td><td>${record.copy_count}</td><td>${date(record.updated_at)}</td><td><a class="button small" href="#/exam/${record.id}">Ouvrir →</a></td></tr>`;
    }).join("")}</tbody></table></div>` : `<div class="card empty"><div class="empty-icon" aria-hidden="true">▦</div><h2>Votre premier examen commence ici</h2><p>Choisissez une feuille, indiquez les questions utilisées et renseignez les bonnes réponses.</p><a class="button primary" href="#/new">Créer mon premier examen</a></div>`);
}

function newDraft(t) {
  const first=t.sections[0];
  return {name:"", template_id:t.id, sections:{[first.id]:Array.from({length:Math.min(first.questions,12)},(_,i)=>i+1)}, answer_key:{[first.id]:{}}};
}
function ranges(questions) {
  return questions.map((q,i)=> i===0 || q!==questions[i-1]+1 ? String(q) : q===questions.at(-1) || questions[i+1]!==q+1 ? `-${q}` : "").filter(Boolean).join(", ").replace(/, -/g,"-");
}
function parseQuestions(text, max) {
  const values=[];
  for (const part of text.split(",").map(x=>x.trim())) {
    if (!/^\d+(?:\s*-\s*\d+)?$/.test(part)) throw new Error("Utilise des numéros ou des plages, par exemple 1-20, 23.");
    const [start,end=start]=part.split("-").map(Number);
    if (start<1 || end<start || end>max) throw new Error(`Les questions doivent être comprises entre 1 et ${max}.`);
    for (let q=start;q<=end;q++) {if(values.includes(q)) throw new Error("Une question est sélectionnée plusieurs fois."); values.push(q);}
  }
  return values.sort((a,b)=>a-b);
}
function completion() {
  let count=0, total=0;
  for(const [sid,qs] of Object.entries(state.draft.sections)) for(const q of qs) {total++;if(state.draft.answer_key[sid]?.[q])count++;}
  return {count,total};
}
function updateCompletion() {
  const {count,total}=completion(), el=document.querySelector("#key-completion"), button=document.querySelector("#save-exam");
  if(el)el.textContent=`${count} / ${total} réponses renseignées`;
  if(button)button.disabled=state.busy || !state.draft.name.trim() || total===0 || count!==total;
}
function renderEditor() {
  const d=state.draft,t=template(d.template_id),editing=Boolean(state.exam);
  main.innerHTML=`<a class="back" href="${editing?`#/exam/${state.exam.id}`:"#/exams"}">← ${editing?"Retour à l’examen":"Mes examens"}</a>`+
    heading("CONFIGURATION",editing?"Modifier l’examen":"Créer un examen","Définissez les questions à lire et le corrigé qui servira à noter les copies.")+
    `<div class="steps"><span><b>1</b> Examen</span><span><b>2</b> Sections</span><span><b>3</b> Corrigé</span></div>`+
    (editing?`<div class="notice warning">Les copies déjà analysées conservent leur corrigé d’origine. Les prochains imports utiliseront cette nouvelle version.</div>`:"")+
    `<form id="exam-form"><div class="card"><h2>Informations de l’examen</h2><div class="form-grid"><label class="field" for="exam-name">Nom de l’examen<input id="exam-name" maxlength="200" placeholder="Ex. Examen blanc — Groupe du mardi" value="${esc(d.name)}" required></label><label class="field" for="template-select">Modèle de feuille<select id="template-select">${state.templates.map(t=>`<option value="${esc(t.id)}" ${t.id===d.template_id?"selected":""}>${esc(templateLabel(t))}</option>`).join("")}</select><small>${t.synthetic?"Modèle synthétique : utilisez la copie de démonstration correspondante.":"Les copies doivent correspondre à ce modèle calibré."}</small></label></div></div>
    <div class="card block-gap"><h2>Sections et questions utilisées</h2><p class="muted">Activez les sections de l’examen. Les autres zones de la feuille seront ignorées.</p>${t.sections.map(s=>`<div class="section-config"><label class="section-toggle"><input type="checkbox" data-section-toggle="${esc(s.id)}" ${d.sections[s.id]?"checked":""}> Section ${esc(s.id)}</label><label class="field">Questions<input aria-label="Questions de la section ${esc(s.id)}" data-section-questions="${esc(s.id)}" value="${d.sections[s.id]?esc(ranges(d.sections[s.id])):`1-${Math.min(12,s.questions)}`}" ${d.sections[s.id]?"":"disabled"}></label><span class="max">${s.questions} questions maximum · ${s.choices} choix</span></div>`).join("")}<p class="subtle block-gap">Exemples : 1-20 pour vingt questions ; 1-10, 15 pour une sélection non consécutive.</p></div>
    <div class="card block-gap"><h2>Bonnes réponses</h2><p class="muted">Barème : +1 par bonne réponse, 0 pour une erreur ou une absence. Les cas incertains seront à vérifier.</p>${Object.entries(d.sections).map(([sid,qs])=>{
      const s=t.sections.find(s=>s.id===sid);
      return `<section class="key-section"><h3>Section ${esc(sid)} <span class="count">${qs.length} questions</span></h3><div class="paste-row"><label class="field">Saisie rapide, dans l’ordre des questions<input id="paste-${esc(sid)}" placeholder="Ex. 2 1 4 3…" aria-label="Coller le corrigé de la section ${esc(sid)}"></label><button type="button" class="button small" data-action="paste-key" data-section="${esc(sid)}">Remplir les réponses</button></div><div class="key-grid">${qs.map(q=>`<div class="answer-field"><label for="key-${esc(sid)}-${q}">Question ${q}</label><select id="key-${esc(sid)}-${q}" data-key-section="${esc(sid)}" data-key-question="${q}"><option value="">—</option>${Array.from({length:s.choices},(_,i)=>`<option value="${i+1}" ${d.answer_key[sid]?.[q]===i+1?"selected":""}>${i+1}</option>`).join("")}</select></div>`).join("")}</div></section>`;
    }).join("") || '<p class="muted">Activez au moins une section.</p>'}</div><div id="form-error" class="error" role="alert"></div><div class="form-footer"><span id="key-completion" class="form-progress"></span><div class="actions"><a class="button ghost" href="${editing?`#/exam/${state.exam.id}`:"#/exams"}">Annuler</a><button id="save-exam" type="submit" class="button primary">Enregistrer l’examen →</button></div></div></form>`;
  updateCompletion();
}

function renderExam(record) {
  state.exam=record;const e=record.exam, t=template(e.template_id), total=Object.values(e.sections).reduce((n,q)=>n+q.length,0);
  main.innerHTML=`<a class="back" href="#/exams">← Mes examens</a>`+
    heading(`EXAMEN · VERSION ${record.revision}`,e.name,`${Object.keys(e.sections).length} sections · ${total} questions · 1 point par bonne réponse`,'<a class="button" href="#/edit/'+record.id+'">Modifier le corrigé</a>')+
    (t?.synthetic?'<div class="notice warning"><span class="notice-symbol" aria-hidden="true">i</span><div><strong>Feuille de démonstration</strong>Cet examen utilise un modèle synthétique. Une photo de feuille NITE ou Adar nécessite son propre modèle calibré.</div></div>':"")+
    `<div class="card"><h2>Importer les copies</h2><div class="uploader" id="drop-zone"><span class="upload-icon" aria-hidden="true">↑</span><h3>Déposez vos fichiers ici</h3><p>Photos JPG, PNG, TIFF ou PDF multipages · 64 Mio maximum par fichier</p><input id="copy-files" type="file" multiple accept=".jpg,.jpeg,.png,.tif,.tiff,.pdf"><button class="button primary" data-action="choose-files">Choisir des fichiers</button><div id="upload-status" class="upload-status" role="status" aria-live="polite"></div></div><div id="upload-error" class="error" role="alert"></div></div>
    <div class="section-head"><h2>Copies de l’examen <span class="count">${record.copies.length}</span></h2><span class="subtle">Cliquez sur une copie pour la vérifier</span></div>`+
    (record.copies.length?`<div class="card table-card table-wrap"><table><thead><tr><th>Copie</th><th>État</th><th>Note / 20</th><th>À vérifier</th><th>Action</th></tr></thead><tbody>${record.copies.map(c=>`<tr><td><a href="#/copy/${c.id}"><strong>${esc(c.filename)}</strong></a><small>Page ${c.page} · Corrigé v${c.exam_revision}</small></td><td>${badge(c.grade.status==="final"?"Correction terminée":"À vérifier",c.grade.status==="final"?"green":"amber")}</td><td><strong>${number(c.grade.out_of_20)}</strong></td><td>${c.grade.pending}</td><td><a class="button small" href="#/copy/${c.id}">Voir la correction →</a></td></tr>`).join("")}</tbody></table></div>`:`<div class="card empty"><h2>Prêt pour la première copie</h2><p>Le corrigé est enregistré. Importez un fichier pour obtenir les réponses détectées et la correction.</p></div>`);
}

function renderCopy(copy) {
  state.copy=copy;const g=copy.grade;
  const filtered=g.rows.filter(r=>state.filter!=="pending" || r.verdict==="pending");
  let row=filtered.find(r=>questionKey(r)===state.selected)||filtered[0];
  state.selected=row?questionKey(row):null;
  const grouped={};for(const r of g.rows){const s=grouped[r.section] ||= {total:0,correct:0,pending:0};s.total++;if(r.verdict==="correct")s.correct++;if(r.verdict==="pending")s.pending++;}
  main.innerHTML=`<a class="back" href="#/exam/${copy.exam_id}">← ${esc(copy.exam.name)}</a>`+
    heading("CORRECTION DE LA COPIE",copy.filename,`Page ${copy.page} · Corrigé version ${copy.exam_revision} · ${g.total} questions`,
      `<div class="download-group"><a class="button" href="/api/copies/${copy.id}/export/csv" download>↓ CSV</a><a class="button" href="/api/copies/${copy.id}/export/json" download>↓ JSON</a></div>`)+
    `<div class="stats copy-stats"><div class="card score-card"><div class="stat-label">${g.pending?"Note à confirmer":"Note de la copie"}</div><div class="stat-value">${number(g.out_of_20)} <small>/ 20</small></div><div class="stat-foot">${g.pending?`${g.min_points} à ${g.max_possible_points} points possibles / ${g.total}`:`${g.points} / ${g.total} points · ${number(g.percentage)} %`}</div></div><div class="card"><div class="stat-label">Bonnes réponses</div><div class="stat-value">${g.correct}</div><div class="stat-foot">${g.pending?"Déjà établies":"Sur l’ensemble de la copie"}</div></div><div class="card"><div class="stat-label">Erreurs et absences</div><div class="stat-value">${g.incorrect+g.blank}</div><div class="stat-foot">${g.incorrect} erreurs · ${g.blank} sans réponse</div></div><div class="card"><div class="stat-label">À vérifier</div><div class="stat-value">${g.pending}</div><div class="stat-foot">${g.pending?"Décisions humaines nécessaires":"Aucune ambiguïté en attente"}</div></div></div>`+
    (g.pending?`<div class="notice warning"><div><strong>La note reste provisoire</strong>${g.pending} réponse${g.pending>1?"s":""} nécessite${g.pending>1?"nt":""} une vérification. Examinez les extraits puis confirmez la réponse, l’absence ou les marques multiples.</div></div>`:`<div class="notice"><div><strong>Correction terminée · ${number(g.out_of_20)} / 20</strong>Toutes les questions ont une décision. Vous pouvez encore rectifier une lecture si nécessaire.</div></div>`)+
    `<div class="section-summary">${Object.entries(grouped).map(([sid,s])=>`<span><strong>Section ${esc(sid)}</strong> ${s.correct}/${s.total} correctes${s.pending?` · ${s.pending} à vérifier`:""}</span>`).join("")}</div>
    <div class="review-layout"><div><div class="card table-card"><div class="review-tabs"><button data-action="filter" data-filter="all" class="${state.filter==="all"?"active":""}">Toutes les questions (${g.total})</button><button data-action="filter" data-filter="pending" class="${state.filter==="pending"?"active":""}">À vérifier (${g.pending})</button></div><div class="table-wrap"><table class="review-table"><thead><tr><th>Question</th><th>Lue / retenue</th><th>Attendue</th><th>Correction</th></tr></thead><tbody>${filtered.map(r=>`<tr data-action="select-question" data-question="${r.question}" data-section="${esc(r.section)}" class="${questionKey(r)===state.selected?"selected":""}"><td><button class="question-link" data-action="select-question" data-question="${r.question}" data-section="${esc(r.section)}">S${esc(r.section)} · Q${r.question}</button>${r.reviewed?'<small>Vérifiée manuellement</small>':""}</td><td>${r.answer?`<span class="answer-number">${r.answer}</span>`:`<span class="subtle">${r.verdict==="pending"?"À confirmer":r.decision==="multiple"?"Multiple":"—"}</span>`}</td><td><span class="answer-number">${r.expected}</span></td><td>${badge(verdictLabel[r.verdict],verdictColor[r.verdict])}</td></tr>`).join("")||'<tr><td colspan="4"><p class="muted">Aucune réponse à vérifier.</p></td></tr>'}</tbody></table></div></div>
    <details class="card full-sheet"><summary>Voir la copie complète</summary><div class="actions block-gap"><a class="button small" href="/api/copies/${copy.id}/image/original" download="copie-originale.png">↓ Image originale</a><a class="button small" href="/api/copies/${copy.id}/image/annotated" download="copie-annotee.png">↓ Image annotée</a></div><img src="/api/copies/${copy.id}/image/annotated" alt="Copie complète avec les zones de lecture annotées" loading="lazy"></details></div>
    <aside class="card review-panel">${row?reviewPanel(copy,row):'<h2>Tout est vérifié</h2><p class="muted">La note est maintenant disponible. Revenez à toutes les questions pour consulter le détail.</p>'}</aside></div>`+
    (copy.history.length?`<details class="card block-gap"><summary>Historique des vérifications (${copy.history.length})</summary><ol class="history">${copy.history.map(h=>`<li>Section ${esc(h.section)}, question ${h.question} : ${h.decision.decision==="choice"?`réponse ${h.decision.answer}`:({blank:"absence confirmée",multiple:"marques multiples confirmées",automatic:"retour à la lecture automatique"}[h.decision.decision])} · ${esc(new Date(h.created_at).toLocaleString("fr-FR"))}</li>`).join("")}</ol></details>`:"");
}
function reviewPanel(copy,row) {
  const count=copy.choices[row.section];
  const selection=row.decision==="single"||row.decision==="choice"?`choice:${row.answer}`:row.reviewed||row.decision==="blank"?row.decision:null;
  return `<h2>Section ${esc(row.section)} · Question ${row.question}</h2><p class="muted">Lecture initiale : ${esc(detectionLabel[row.detected_status])}${row.detected_answer?` (${row.detected_answer})`:""}.</p>`+
    (copy.aligned?`<div class="crop-view"><img src="/api/copies/${copy.id}/crop/${encodeURIComponent(row.section)}/${row.question}" alt="Extrait original de la question ${row.question}, section ${esc(row.section)}, avant annotation"></div>`:`<div class="notice warning">L’image n’a pas pu être alignée. Consultez la copie complète ; si elle est illisible, importez une meilleure image.</div>`)+
    `<form id="review-form"><fieldset><legend>Réponse retenue</legend><div class="choice-row">${Array.from({length:count},(_,i)=>`<label class="choice-pill"><input type="radio" name="decision" value="choice:${i+1}" ${selection===`choice:${i+1}`?"checked":""}><span>${i+1}</span></label>`).join("")}</div><label class="decision-label"><input type="radio" name="decision" value="blank" ${selection==="blank"?"checked":""}> Aucune réponse · 0 point</label><label class="decision-label"><input type="radio" name="decision" value="multiple" ${selection==="multiple"?"checked":""}> Plusieurs réponses · 0 point</label></fieldset><div id="review-error" class="error" role="alert"></div><button class="button primary full" type="submit">Valider et recalculer</button>${row.reviewed?'<button class="button ghost full block-gap" type="button" data-action="reset-review">Rétablir la lecture automatique</button>':""}</form><p class="muted block-gap">La lecture initiale est conservée. Chaque modification est enregistrée dans l’historique.</p>`;
}

let routeVersion=0;
async function route() {
  state.dirty=false;
  const version=++routeVersion, path=(location.hash.slice(1)||"/exams").split("/").filter(Boolean);
  document.querySelector("#nav-new").classList.toggle("active",["new","edit"].includes(path[0]));
  document.querySelector("#nav-exams").classList.toggle("active",!["new","edit"].includes(path[0]));
  main.innerHTML='<div class="loading" role="status">Chargement…</div>';
  try {
    if(!state.templates.length)state.templates=await api("/api/templates");
    if(version!==routeVersion)return;
    if(path[0]==="new") {state.exam=null;state.draft=newDraft(state.templates[0]);renderEditor();}
    else if(path[0]==="edit") {const e=await api(`/api/exams/${path[1]}`);if(version!==routeVersion)return;state.exam=e;state.draft=structuredClone(e.exam);renderEditor();}
    else if(path[0]==="exam") {const e=await api(`/api/exams/${path[1]}`);if(version!==routeVersion)return;renderExam(e);}
    else if(path[0]==="copy") {const c=await api(`/api/copies/${path[1]}`);if(version!==routeVersion)return;state.filter="all";state.selected=null;renderCopy(c);}
    else {const e=await api("/api/exams");if(version!==routeVersion)return;renderDashboard(e);}
  } catch(error) {if(version===routeVersion)main.innerHTML=`<div class="card error-page"><h1>Impossible d’ouvrir cette page</h1><p class="error">${esc(error.message)}</p><a class="button" href="#/exams">Retour aux examens</a></div>`;}
}

main.addEventListener("input", event=>{
  if(event.target.closest("#exam-form, #review-form"))state.dirty=true;
  if(event.target.id==="exam-name"){state.draft.name=event.target.value;updateCompletion();}
});
main.addEventListener("change", event=>{
  const el=event.target;
  if(el.closest("#exam-form, #review-form"))state.dirty=true;
  try {
    if(el.id==="template-select") {const name=state.draft.name;state.draft=newDraft(template(el.value));state.draft.name=name;renderEditor();toast("Le modèle a changé : les sections et le corrigé ont été réinitialisés.");}
    if(el.dataset.sectionToggle) {const id=el.dataset.sectionToggle,s=template(state.draft.template_id).sections.find(s=>s.id===id);if(el.checked){state.draft.sections[id]=Array.from({length:Math.min(s.questions,12)},(_,i)=>i+1);state.draft.answer_key[id]={};}else{delete state.draft.sections[id];delete state.draft.answer_key[id];}renderEditor();}
    if(el.dataset.sectionQuestions) {const id=el.dataset.sectionQuestions,s=template(state.draft.template_id).sections.find(s=>s.id===id),qs=parseQuestions(el.value,s.questions);state.draft.sections[id]=qs;state.draft.answer_key[id]=Object.fromEntries(qs.filter(q=>state.draft.answer_key[id]?.[q]).map(q=>[q,state.draft.answer_key[id][q]]));renderEditor();}
    if(el.dataset.keySection) {const sid=el.dataset.keySection,q=el.dataset.keyQuestion;if(el.value)state.draft.answer_key[sid][q]=Number(el.value);else delete state.draft.answer_key[sid][q];updateCompletion();}
    if(el.id==="copy-files")uploadFiles(el.files);
  } catch(error) {errorIn("form-error",error.message); if(el.dataset.sectionQuestions)el.value=ranges(state.draft.sections[el.dataset.sectionQuestions]);}
});

main.addEventListener("click", async event=>{
  const target=event.target.closest("[data-action]");if(!target)return;
  const action=target.dataset.action;
  if(action==="paste-key")state.dirty=true;
  if(state.busy && ["demo","choose-files","reset-review"].includes(action))return;
  try {
    if(action==="demo") {state.busy=true;target.disabled=true;target.textContent="Analyse en cours…";const result=await api("/api/demo",{method:"POST"});navigate(result.copies.length?`/copy/${result.copies[0].id}`:`/exam/${result.exam_id}`);}
    if(action==="paste-key") {const sid=target.dataset.section,s=template(state.draft.template_id).sections.find(s=>s.id===sid),raw=document.getElementById(`paste-${sid}`).value.trim();const parts=raw.split(/[\s,;]+/);if(parts.some(p=>!/^\d+$/.test(p)))throw new Error("Saisis uniquement des numéros de réponses séparés par des espaces, virgules ou points-virgules.");const values=parts.map(Number);if(values.length!==state.draft.sections[sid].length||values.some(v=>v<1||v>s.choices))throw new Error(`Il faut ${state.draft.sections[sid].length} réponses, chacune entre 1 et ${s.choices}.`);state.draft.answer_key[sid]=Object.fromEntries(state.draft.sections[sid].map((q,i)=>[q,values[i]]));renderEditor();}
    if(action==="choose-files")document.getElementById("copy-files").click();
    if(action==="filter") {state.filter=target.dataset.filter;state.selected=null;renderCopy(state.copy);}
    if(action==="select-question") {state.selected=`${target.dataset.section}:${target.dataset.question}`;renderCopy(state.copy);}
    if(action==="reset-review")await saveReview("automatic",null);
  } catch(error){if(action==="paste-key")errorIn("form-error",error.message);else toast(error.message);}
  finally{if(action==="demo"){state.busy=false;target.disabled=false;target.textContent="Essayer la démonstration →";}}
});

main.addEventListener("submit", async event=>{
  event.preventDefault();if(state.busy)return;
  if(event.target.id==="exam-form") {
    try {state.busy=true;updateCompletion();const editing=Boolean(state.exam);const result=await api(editing?`/api/exams/${state.exam.id}`:"/api/exams",{method:editing?"PUT":"POST",body:JSON.stringify(editing?{expected_revision:state.exam.revision,exam:state.draft}:state.draft)});toast("Examen et corrigé enregistrés.");navigate(`/exam/${result.id}`);}
    catch(error){errorIn("form-error",error.message);}
    finally{state.busy=false;if(document.querySelector("#exam-form"))updateCompletion();}
  } else if(event.target.id==="review-form") {
    const value=new FormData(event.target).get("decision");
    if(!value){errorIn("review-error","Choisis une réponse ou confirme l’absence de réponse.");return;}
    const [decision,answer]=value.split(":");
    try{await saveReview(decision,answer?Number(answer):null);}catch(error){errorIn("review-error",error.message);}
  }
});

async function saveReview(decision, answer) {
  const row=state.copy.grade.rows.find(r=>questionKey(r)===state.selected);
  state.busy=true;
  const button=document.querySelector('#review-form button[type="submit"]');if(button)button.disabled=true;
    try {const copy=await api(`/api/copies/${state.copy.id}/reviews`,{method:"PATCH",body:JSON.stringify({expected_revision:state.copy.revision,section:row.section,question:row.question,decision,answer})});state.dirty=false;renderCopy(copy);toast(decision==="automatic"?"Lecture automatique rétablie.":"Vérification enregistrée. La note a été recalculée.");}
  finally{state.busy=false;if(button)button.disabled=false;}
}
async function uploadFiles(files) {
  if(state.busy||!files.length)return;
  const examId=state.exam.id;state.busy=true;let created=0;const errors=[];
  const button=document.querySelector('[data-action="choose-files"]');if(button)button.disabled=true;
  try {
    for(const [index,file] of Array.from(files).entries()) {
      const status=document.getElementById("upload-status");if(status)status.textContent=`Analyse du fichier ${index+1}/${files.length} : ${file.name}…`;
      if(file.size>64*1024*1024){errors.push(`${file.name} : le fichier dépasse 64 Mio.`);continue;}
      const form=new FormData();form.append("file",file);
      try {const result=await api(`/api/exams/${examId}/copies`,{method:"POST",body:form});created+=result.copies.length;errors.push(...result.errors.map(e=>`${file.name}, page ${e.page} : ${e.message}`));}
      catch(error){errors.push(`${file.name} : ${error.message}`);}
    }
    if(location.hash===`#/exam/${examId}`){renderExam(await api(`/api/exams/${examId}`));errorIn("upload-error",errors.join("\n"));}
    toast(`${created} copie${created>1?"s":""} analysée${created>1?"s":""}.${errors.length?` ${errors.length} erreur(s) à consulter.`:""}`);
  } finally {state.busy=false;if(button)button.disabled=false;}
}
for(const type of ["dragover","dragleave","drop"])main.addEventListener(type,event=>{
  const zone=event.target.closest("#drop-zone");if(!zone)return;
  event.preventDefault();zone.classList.toggle("dragging",type==="dragover");
  if(type==="drop")uploadFiles(event.dataTransfer.files);
});
window.addEventListener("hashchange",route);
route();
