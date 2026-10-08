import { openCropEditor } from "./crop-editor.js";

/* Human observations for development: never an answer key or a grading decision. */
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const splitLabels = {development:"Développement", train:"Apprentissage", calibration:"Réglage des seuils", test:"Test réservé"};
const markLabels = {empty:"Aucune marque", marked:"Marque nette", ambiguous:"Trace ambiguë", unreadable:"Case illisible"};
const statusLabels = {blank:"Aucune réponse", single:"Une réponse nette", multiple:"Plusieurs réponses nettes", uncertain:"Lecture ambiguë", unreadable:"Lecture impossible"};

async function request(path="", options={}) {
  let response;
  try { response=await fetch(`/api/corpus${path}`, {...options, headers: options.body instanceof FormData ? {} : {"Content-Type":"application/json"}}); }
  catch { throw new Error("Le serveur ne répond pas. Votre saisie reste affichée ; réessayez l’enregistrement."); }
  const body=await response.json().catch(()=>({}));
  if(!response.ok) {
    const detail=Array.isArray(body.detail) ? body.detail.map(x=>x.msg).join(" · ") : body.detail;
    throw new Error(detail || "Impossible de terminer cette opération.");
  }
  return body;
}

function conclusion(marks) {
  if(marks.some(m=>!m))return null;
  const choices=marks.flatMap((m,i)=>m==="marked"?[i+1]:[]);
  const status=marks.includes("unreadable")?"unreadable":marks.includes("ambiguous")?"uncertain":choices.length>1?"multiple":choices.length===1?"single":"blank";
  return {status,choices};
}

export function mountCorpus(container, identifier, templates) {
  const root=document.createElement("div");root.className="corpus";container.replaceChildren(root);
  let disposed=false,busy=false,dirty=false,item=null,index=0,photo=null,manualBounds=null;
  let reviewer="",editor=null,previousBounds=null,editorViewport=null,lastSavedIndex=null;
  try {reviewer=sessionStorage.getItem("psychomark-reviewer")||"";}catch { /* Storage can be unavailable. */ }
  if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(reviewer))reviewer="";
  const active=()=>!disposed&&root.isConnected;
  const $=selector=>root.querySelector(selector);
  const current=()=>item.questions[index];
  const imageURL=view=>`/api/corpus/${item.id}/image/${view}`;
  const cropURL=view=>`/api/corpus/${item.id}/crop/${encodeURIComponent(current().section)}/${current().question}?view=${view}&v=${item.revision}`;
  const message=text=>{if(active())$("#corpus-message").textContent=text;};
  function frame(title,description,actions="") {
    document.title=`${title} — PsychoMark`;
    return `<div class="page-head"><div><h1>${esc(title)}</h1><p>${description}</p></div><div class="actions">${actions}</div></div><div id="corpus-error" class="error" role="alert" tabindex="-1"></div><p id="corpus-message" class="corpus-message" role="status" aria-live="polite"></p>`;
  }
  function error(text) {if(active()){const el=$("#corpus-error");el.textContent=text;if(text)el.focus();}}
  async function run(task) {
    if(busy)return;busy=true;root.setAttribute("aria-busy","true");error("");
    root.querySelectorAll("button,input,select,textarea").forEach(el=>{el.dataset.corpusDisabled=String(el.disabled);el.disabled=true;});
    try {await task();}catch(e){message("");error(e.message);}
    finally {busy=false;root.removeAttribute("aria-busy");if(active())root.querySelectorAll("[data-corpus-disabled]").forEach(el=>{el.disabled=el.dataset.corpusDisabled==="true";delete el.dataset.corpusDisabled;});}
  }
  function keepOrDiscard() {
    if(busy)return false;
    if(dirty&&!confirm("Cette observation n’est pas enregistrée. La quitter ?"))return false;
    dirty=false;return true;
  }
  function renderList(records) {
    root.innerHTML=frame("Annotations","Constituez des exemples fiables en décrivant ce qui est visible sur les copies.",'<a class="button" href="/api/corpus/export" download>Exporter le manifeste</a><a class="button primary" href="#/annotations/new">Ajouter une copie</a>')+
      `<div class="notice"><div><strong>Observer les marques, sans consulter le corrigé</strong>Ces observations préparent les essais du moteur. Elles ne changent aucune note et ne déclenchent aucun entraînement.</div></div>`+
      (records.length?`<div class="card table-card table-wrap"><table><thead><tr><th>Feuille papier</th><th>Usage</th><th>Observations</th><th>Repérage</th><th>Action</th></tr></thead><tbody>${records.map(r=>`<tr><td><strong>${esc(r.physical_sheet_id)}</strong><small>Groupe ${esc(r.group_id)}</small></td><td>${splitLabels[r.split]}</td><td>${r.completed} / ${r.total}</td><td>${r.aligned?"Zones proposées à vérifier":"Lecture sur l’original"}</td><td><a class="button small" href="#/annotations/${r.id}">Annoter</a></td></tr>`).join("")}</tbody></table></div>`:
      `<div class="card empty"><h2>Une première copie à observer</h2><p>Importez une photo ou un ZIP de diagnostic. Vous pourrez confirmer les marques question par question, même si le repérage automatique a échoué.</p><a class="button primary" href="#/annotations/new">Ajouter une copie</a></div>`);
  }
  function renderImport() {
    root.innerHTML=`<a class="back" href="#/annotations">Annotations</a>`+frame("Ajouter une copie","Une feuille papier garde le même identifiant dans toutes ses photos.")+`
      <form id="corpus-import" class="card corpus-import">
        <label class="field">Photo ou diagnostic<input name="file" type="file" accept=".png,.jpg,.jpeg,.tif,.tiff,.pdf,.zip" required></label>
        <p class="muted">Image, PDF d’une page ou ZIP de diagnostic PsychoMark · 64 Mio maximum.</p>
        <label class="field" id="corpus-model-field">Modèle de feuille<select name="template_id">${templates.map(t=>`<option value="${esc(t.id)}">${esc(t.name||t.id)}</option>`).join("")}</select><small>Un ZIP de diagnostic contient déjà son modèle.</small></label>
        <div class="form-grid block-gap"><label class="field">Identifiant de la feuille papier<input name="physical_sheet_id" aria-label="Identifiant de la feuille papier" maxlength="80" pattern="[A-Za-z0-9](?:[A-Za-z0-9_]|-){0,79}" placeholder="Ex. feuille-001" required><small>Un code sans nom d’élève. Réutilisez-le pour une autre photo de ce même papier.</small></label>
        <label class="field">Usage des exemples<select name="split"><option value="development">Développement — cas que nous examinons</option><option value="train">Apprentissage — futur entraînement</option><option value="calibration">Réglage des seuils — exemples séparés</option><option value="test">Test réservé — ne pas utiliser pour régler le moteur</option></select><small id="corpus-split-help">Toutes les photos d’une même feuille restent dans le même usage.</small></label></div>
        <details class="block-gap"><summary>Regrouper des feuilles liées</summary><label class="field block-gap">Groupe à garder ensemble<input name="group_id" maxlength="80" pattern="[A-Za-z0-9](?:[A-Za-z0-9_]|-){0,79}" placeholder="Par défaut : identifiant de la feuille"><small>Utilisez le même groupe pour des feuilles d’un même scripteur ou d’une même série de photos. Le groupe reste dans un seul usage.</small></label></details>
        <label class="decision-label block-gap"><input type="checkbox" name="training_allowed"> Je confirme pouvoir utiliser cette copie pour l’apprentissage du moteur.</label>
        <p class="muted">Laisser cette case vide permet l’annotation, sans rendre la copie admissible à l’entraînement.</p>
        <button class="button primary" type="submit">Importer et annoter</button>
      </form>`;
  }
  function marksFromForm() {return [...root.querySelectorAll("[data-mark]")].map(el=>el.value);}
  function updateConclusion() {
    const decision=conclusion(marksFromForm());
    $("#corpus-conclusion").textContent=decision?`${statusLabels[decision.status]}${decision.choices.length?` · choix ${decision.choices.join(", ")}`:""}`:"Aucune observation saisie";
    root.querySelectorAll("[data-quick]").forEach(button=>{
      const value=Number(button.dataset.quick);
      button.setAttribute("aria-pressed",String(Boolean(decision&&(value===0?decision.status==="blank":decision.status==="single"&&decision.choices[0]===value))));
    });
  }
  function quickAnswer(choice) {
    root.querySelectorAll("[data-mark]").forEach((el,i)=>el.value=i+1===choice?"marked":"empty");
    dirty=true;updateConclusion();error("");
  }
  function renderQuestion() {
    if(!active())return;
    document.body.classList.add("corpus-review");
    const q=current(),a=q.annotation;
    manualBounds=a?.manual_bounds?[...a.manual_bounds]:null;
    root.innerHTML=`<a class="back" href="#/annotations">Toutes les copies</a>`+frame(`Feuille ${item.physical_sheet_id}`,`${item.completed} / ${item.total} questions observées. ${splitLabels[item.split]}.`)+
      `<div class="corpus-toolbar"><label class="field">Question<select id="corpus-question">${item.questions.map((r,i)=>`<option value="${i}" ${i===index?"selected":""}>Section ${esc(r.section)} · Question ${r.question}${r.annotation?" — enregistrée":""}</option>`).join("")}</select></label><div class="actions"><button class="button" type="button" data-corpus="previous" ${index===0?"disabled":""} aria-label="Précédente"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg><span class="corpus-prev-label">Précédente</span></button><button class="button" type="button" data-corpus="next" ${index===item.questions.length-1?"disabled":""}>Passer</button></div></div>
      <div class="corpus-layout"><section class="corpus-images" aria-label="Images de la question"><h2 id="corpus-reading" tabindex="-1">Section ${esc(q.section)} · Question ${q.question}</h2>
        <div class="corpus-crops"><figure id="corpus-copy-figure"><figcaption id="corpus-crop-caption">${manualBounds?"Extrait placé manuellement":"Extrait proposé · position à vérifier"}</figcaption><img id="corpus-copy-image" ${q.has_crop?`src="${cropURL('copy')}"`:"hidden"} alt="Marques sur la copie, sans annotation du moteur"><canvas id="corpus-manual-preview" hidden aria-label="Aperçu du cadre manuel sur la photo originale"></canvas><div id="corpus-no-crop" ${q.has_crop?"hidden":""}><p>Aucun extrait positionné</p><button class="button primary" type="button" data-corpus="crop">Cadrer cette question</button></div></figure></div>
        <div class="corpus-image-actions"><button class="button" type="button" data-corpus="crop">${q.has_crop?"Ajuster le cadre":"Ouvrir la photo"}</button><button class="button" type="button" data-corpus="clear-crop" ${manualBounds?"":"hidden"}>Retirer mon cadre</button></div>
        <details class="corpus-reference"><summary>Comparer avec le modèle vierge</summary><img src="${cropURL('reference')}" alt="Emplacement des choix sur le modèle vierge"></details>
      </section><section class="corpus-observation" aria-label="Observation humaine"><form id="corpus-observation" novalidate>
        <label class="corpus-confirm"><input type="checkbox" id="corpus-position" ${a?.geometry==="confirmed"?"checked":""} ${q.has_crop?"":"disabled"}><span>C’est bien la question ${q.question} de la section ${esc(q.section)}, avec tous ses choix.</span></label>
        <fieldset class="corpus-fast"><legend>Un seul choix marqué ?</legend><p class="muted">Touchez son numéro : les autres cases seront notées sans marque.</p><div class="corpus-quick">${Array.from({length:q.choices},(_,i)=>`<button type="button" class="button" data-quick="${i+1}" aria-label="Seul le choix ${i+1} est marqué" aria-pressed="false">${i+1}</button>`).join("")}</div><button type="button" class="button full" data-quick="0" aria-pressed="false">Aucune case marquée</button></fieldset>
        <details id="corpus-mark-details" ${a&&!["single","blank"].includes(a.status)?"open":""}><summary>Plusieurs marques ou une trace douteuse</summary><p class="muted">Décrivez chaque case. Une trace douteuse reste ambiguë.</p><fieldset><legend>Marques visibles</legend>${Array.from({length:q.choices},(_,i)=>`<label class="corpus-mark">Choix ${i+1}<select data-mark="${i}" aria-label="Marque du choix ${i+1}"><option value="">À examiner</option>${Object.entries(markLabels).map(([value,label])=>`<option value="${value}" ${a?.marks?.[i]===value?"selected":""}>${label}</option>`).join("")}</select></label>`).join("")}</fieldset></details>
        <p id="corpus-conclusion" class="corpus-conclusion" aria-live="polite"></p>

        <details id="corpus-more" ${!reviewer?"open":""}><summary>Relecture et options${reviewer?` · ${esc(reviewer)}`:""}</summary><label class="field">Votre identifiant de relecture<input name="reviewer" aria-label="Votre identifiant de relecture" maxlength="80" pattern="[A-Za-z0-9](?:[A-Za-z0-9_]|-){0,79}" value="${esc(reviewer)}" placeholder="Ex. correcteur-1"><small>Un alias, retenu dans cet onglet. Aucun nom d’élève.</small></label>
        <label class="field">Position de la question<select name="geometry" aria-label="Position de la question"><option value="">À vérifier</option><option value="confirmed" ${a?.geometry==="confirmed"?"selected":""}>L’extrait contient bien cette question</option><option value="source_only" ${a?.geometry==="source_only"?"selected":""}>J’ai lu directement sur la photo entière</option><option value="incorrect" ${a?.geometry==="incorrect"?"selected":""}>L’extrait est mal placé</option></select></label>
        <label class="field">Note de relecture (facultatif)<textarea name="notes" rows="2" maxlength="2000">${esc(a?.notes||"")}</textarea></label></details>
        <div class="corpus-savebar"><button class="button" type="button" data-corpus="last" ${lastSavedIndex===null?"hidden":""}>Revoir la dernière</button><button class="button primary" type="submit">Enregistrer et continuer</button></div>
      </form></section></div>
      <div class="corpus-secondary"><p class="muted corpus-shortcuts">Clavier : 1–9, 0 pour aucune marque, Entrée pour enregistrer. Les raccourcis sont inactifs pendant la saisie d’un champ.</p><a class="button" href="/api/corpus/${item.id}/export" download>Exporter cette copie</a>
      <details class="block-gap"><summary>Historique des observations (${item.history.length})</summary><ol class="history">${item.history.map(h=>`<li>${esc(h.after?.reviewer||"")} · section ${esc(h.section)} · question ${h.question} · ${esc(h.after?.recorded_at||"")}</li>`).join("")||'<li>Aucune observation enregistrée.</li>'}</ol></details></div>`;
    updateConclusion();loadPhoto();
  }
  function drawPreview() {
    if(!active()||!photo?.naturalWidth||!manualBounds)return;
    const canvas=$("#corpus-manual-preview");if(!canvas)return;
    const [x0,y0,x1,y1]=manualBounds;
    canvas.width=x1-x0;canvas.height=y1-y0;
    canvas.getContext("2d").drawImage(photo,x0,y0,x1-x0,y1-y0,0,0,x1-x0,y1-y0);
    canvas.hidden=false;$("#corpus-copy-image").hidden=true;$("#corpus-no-crop").hidden=true;
    $("#corpus-crop-caption").textContent="Extrait placé manuellement";
    $("[data-corpus=clear-crop]").hidden=false;
  }
  function loadPhoto() {
    if(photo?.naturalWidth){drawPreview();return;}
    if(photo)return;
    photo=new Image();
    photo.onload=()=>{if(active())drawPreview();};
    photo.onerror=()=>{photo=null;error("La photo n’a pas pu être affichée. Rechargez la page avant d’annoter.");};
    photo.src=imageURL("source");
  }
  function editCrop() {
    if(editor)return;
    if(!photo?.naturalWidth){error("La photo est encore en chargement. Réessayez dans un instant.");loadPhoto();return;}
    const q=current();
    editor=openCropEditor({image:photo,bounds:manualBounds,previousBounds,viewport:editorViewport,title:`Section ${q.section} · Question ${q.question}`,
      onApply:bounds=>{manualBounds=bounds;previousBounds=[...bounds];dirty=true;drawPreview();$("#corpus-position").disabled=false;$("#corpus-position").checked=true;$("[name=geometry]").value="confirmed";},
      onClose:viewport=>{editorViewport=viewport;editor=null;if(active())$("[data-corpus=crop]").focus({preventScroll:true});}});
  }
  function goTo(next) {
    if(!keepOrDiscard())return;
    reviewer=$("[name=reviewer]").value.trim();index=next;renderQuestion();
    $("#corpus-reading").focus({preventScroll:true});$(".corpus-toolbar").scrollIntoView({block:"start",behavior:"instant"});
  }
  root.addEventListener("click",event=>{
    if(busy)return;
    const quick=event.target.closest("[data-quick]");if(quick){quickAnswer(Number(quick.dataset.quick));return;}
    const action=event.target.closest("[data-corpus]")?.dataset.corpus;
    if(action==="previous"&&index>0)goTo(index-1);
    if(action==="next"&&index<item.questions.length-1)goTo(index+1);
    if(action==="last"&&lastSavedIndex!==null)goTo(lastSavedIndex);
    if(action==="crop")editCrop();
    if(action==="clear-crop") {
      manualBounds=null;dirty=true;$("[name=geometry]").value="";$("#corpus-position").checked=false;
      // has_crop includes a saved manual crop; only the server can resolve its automatic fallback.
      $("#corpus-position").disabled=true;$("#corpus-manual-preview").hidden=true;$("#corpus-copy-image").hidden=true;$("#corpus-no-crop").hidden=false;
      $("[data-corpus=clear-crop]").hidden=true;message("Cadre retiré. Recadrez la question ou indiquez une lecture sur la photo entière.");
    }
  });
  root.addEventListener("input",event=>{
    if(event.target.closest("#corpus-import,#corpus-observation"))dirty=true;
  });
  root.addEventListener("change",event=>{
    const el=event.target;
    if(el.matches("[data-mark]")){dirty=true;updateConclusion();}
    if(el.id==="corpus-position"){$("[name=geometry]").value=el.checked?"confirmed":"";dirty=true;}
    if(el.name==="geometry"){$("#corpus-position").checked=el.value==="confirmed";dirty=true;}
    if(el.id==="corpus-question") {const selected=Number(el.value);el.value=String(index);goTo(selected);}
    if(el.matches('#corpus-import [name="file"]')) {
      const zip=el.files[0]?.name.toLowerCase().endsWith(".zip");
      $("#corpus-model-field").hidden=zip;$("[name=template_id]").disabled=zip;
      $("[name=split]").disabled=zip;if(zip)$("[name=split]").value="development";
      $("#corpus-split-help").textContent=zip?"Un diagnostic est un cas déjà examiné : il reste en développement.":"Toutes les photos d’une même feuille restent dans le même usage.";
    }
  });
  root.addEventListener("keydown",event=>{
    if(!item||busy||editor||event.repeat||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey||event.isComposing)return;
    if(event.target.closest("input,select,textarea,summary,a,[contenteditable=true]"))return;
    if(/^[0-9]$/.test(event.key)&&Number(event.key)<=current().choices){event.preventDefault();quickAnswer(Number(event.key));}
    if(event.key==="Enter"&&!event.target.closest("button")){event.preventDefault();$("#corpus-observation").requestSubmit();}
  });
  root.addEventListener("submit",event=>{
    event.preventDefault();if(busy||editor)return;
    if(event.target.id==="corpus-import") {
      const form=new FormData(event.target),file=form.get("file");
      if(!file?.size){error("Choisissez un fichier non vide.");return;}
      if(file.size>64*1024*1024){error("Le fichier dépasse 64 Mio.");return;}
      form.set("training_allowed",String(form.get("training_allowed")==="on"));
      if(!form.get("split"))form.set("split","development");
      run(async()=>{message("Import et préparation des questions…");const imported=await request("",{method:"POST",body:form});if(!active())return;dirty=false;busy=false;location.hash=`#/annotations/${imported.id}`;});
    }
    if(event.target.id==="corpus-observation") {
      const q=current(),form=new FormData(event.target),marks=marksFromForm(),decision=conclusion(marks);
      if(!decision){$("#corpus-mark-details").open=true;error("Choisissez une réponse rapide ou décrivez chaque case avant d’enregistrer.");return;}
      const alias=form.get("reviewer").trim();
      if(!/^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$/.test(alias)){$("#corpus-more").open=true;error("Renseignez votre alias de relecture, sans espace, avant d’enregistrer.");return;}
      if(!form.get("geometry")){error("Vérifiez la question affichée et confirmez sa position avant d’enregistrer.");return;}
      const body={expected_revision:item.revision,section:q.section,question:q.question,reviewer:alias,...decision,marks,geometry:form.get("geometry"),manual_bounds:manualBounds,notes:form.get("notes")};
      run(async()=>{message("Enregistrement de l’observation…");const updated=await request(`/${item.id}/annotations`,{method:"PATCH",body:JSON.stringify(body)});if(!active())return;
        item=updated;dirty=false;reviewer=alias;lastSavedIndex=index;
        try {sessionStorage.setItem("psychomark-reviewer",reviewer);}catch { /* Annotation is already safely saved on the server. */ }
        const next=item.questions.findIndex((r,i)=>i>index&&!r.annotation),first=item.questions.findIndex(r=>!r.annotation);
        if(next!==-1)index=next;else if(first!==-1)index=first;
        renderQuestion();message(first===-1?"Toutes les questions sont observées. Vous pouvez les relire ou exporter cette copie.":"Observation enregistrée.");
        $("#corpus-reading").focus({preventScroll:true});$(".corpus-toolbar").scrollIntoView({block:"start",behavior:"instant"});});
    }
  });
  async function initialize() {
    root.innerHTML=frame("Annotations","Chargement des copies…");
    await run(async()=>{
      if(identifier==="new")renderImport();
      else if(identifier){const loaded=await request(`/${identifier}`);if(!active())return;item=loaded;index=Math.max(0,item.questions.findIndex(q=>!q.annotation));renderQuestion();}
      else {const records=await request();if(active())renderList(records);}
    });
  }
  initialize();
  return {canReload:()=>!dirty&&!busy&&!editor,dispose:()=>{disposed=true;editor?.close();document.body.classList.remove("corpus-review");}};
}
