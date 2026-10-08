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
  let flow=false,proposed=false,flowDirection="right";
  try {flow=sessionStorage.getItem("psychomark-annotation-flow")==="true";const direction=sessionStorage.getItem("psychomark-flow-direction");if(["right","left","down"].includes(direction))flowDirection=direction;}catch {}
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
    manualBounds=a?.manual_bounds?[...a.manual_bounds]:null;proposed=false;
    root.classList.toggle("corpus-flow",flow);
    root.innerHTML=`<a class="back" href="#/annotations">Toutes les copies</a>`+frame(`Feuille ${item.physical_sheet_id}`,`${item.completed} / ${item.total} questions observées. ${splitLabels[item.split]}.`)+
      `<div class="corpus-toolbar"><label class="field">Question<select id="corpus-question">${item.questions.map((r,i)=>`<option value="${i}" ${i===index?"selected":""}>Section ${esc(r.section)} · Question ${r.question}${r.annotation?" — enregistrée":""}</option>`).join("")}</select></label><div class="actions"><button class="button" type="button" data-corpus="previous" ${index===0?"disabled":""} aria-label="Précédente"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg><span class="corpus-prev-label">Précédente</span></button><button class="button" type="button" data-corpus="next" ${index===item.questions.length-1?"disabled":""}>Passer</button></div></div>
      <div class="corpus-flow-toggle"><label><input type="checkbox" id="corpus-flow" ${flow?"checked":""}> Mode enchaîné</label><span>Cadre suivant proposé · Entrée confirme le cadre et enregistre</span><select aria-label="Sens d’enchaînement" id="corpus-flow-direction" ${flow?"":"hidden"}>${[["right","Vers la droite"],["left","Vers la gauche"],["down","Vers le bas"]].map(([v,l])=>`<option value="${v}" ${v===flowDirection?"selected":""}>${l}</option>`).join("")}</select></div>
      <div class="corpus-layout"><section class="corpus-images" aria-label="Images de la question"><h2 id="corpus-reading" tabindex="-1">Section ${esc(q.section)} · Question ${q.question}</h2>
        <div class="corpus-crops"><canvas id="corpus-context" hidden aria-label="Contexte de la photo avec le cadre de la question"></canvas><figure id="corpus-copy-figure"><figcaption id="corpus-crop-caption">${manualBounds?"Extrait placé manuellement":"Extrait proposé · position à vérifier"}</figcaption><img id="corpus-copy-image" ${q.has_crop?`src="${cropURL('copy')}"`:"hidden"} alt="Marques sur la copie, sans annotation du moteur"><canvas id="corpus-manual-preview" hidden aria-label="Aperçu du cadre manuel sur la photo originale"></canvas><div id="corpus-no-crop" ${q.has_crop?"hidden":""}><p>Aucun extrait positionné</p><button class="button primary" type="button" data-corpus="crop">Cadrer cette question</button></div></figure></div>
        <div class="corpus-image-actions"><button class="button" type="button" data-corpus="crop">${q.has_crop?"Ajuster le cadre":"Ouvrir la photo"}</button><button class="button" type="button" data-corpus="clear-crop" ${manualBounds?"":"hidden"}>Retirer mon cadre</button></div>
        <div class="corpus-inline-move" hidden><span>Ajuster le cadre</span>${[["left","gauche","M19 12H5m7-7-7 7 7 7"],["up","haut","M12 19V5m-7 7 7-7 7 7"],["down","bas","M12 5v14m-7-7 7 7 7-7"],["right","droite","M5 12h14m-7-7 7 7-7 7"]].map(([v,label,path])=>`<button type="button" class="button" data-move="${v}" aria-label="Déplacer le cadre : ${label}" title="Déplacer vers ${label}"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="${path}"/></svg></button>`).join("")}</div>
        <details class="corpus-reference"><summary>Comparer avec le modèle vierge</summary><img src="${cropURL('reference')}" alt="Emplacement des choix sur le modèle vierge"></details>
      </section><section class="corpus-observation" aria-label="Observation humaine"><form id="corpus-observation" novalidate>
        <label class="corpus-confirm"><input type="checkbox" id="corpus-position" ${a?.geometry==="confirmed"?"checked":""} ${q.has_crop?"":"disabled"}><span>C’est bien la question ${q.question} de la section ${esc(q.section)}, avec tous ses choix.</span></label>
        <fieldset class="corpus-fast"><legend>Un seul choix marqué ?</legend><p class="muted">Touchez son numéro : les autres cases seront notées sans marque.</p><div class="corpus-quick">${Array.from({length:q.choices},(_,i)=>`<button type="button" class="button" data-quick="${i+1}" aria-label="Seul le choix ${i+1} est marqué" aria-pressed="false">${i+1}</button>`).join("")}</div><button type="button" class="button full" data-quick="0" aria-pressed="false">Aucune case marquée</button></fieldset>
        <details id="corpus-mark-details" ${a&&!["single","blank"].includes(a.status)?"open":""}><summary>Plusieurs marques ou une trace douteuse</summary><p class="muted">Décrivez chaque case. Une trace douteuse reste ambiguë.</p><fieldset><legend>Marques visibles</legend>${Array.from({length:q.choices},(_,i)=>`<label class="corpus-mark">Choix ${i+1}<select data-mark="${i}" aria-label="Marque du choix ${i+1}"><option value="">À examiner</option>${Object.entries(markLabels).map(([value,label])=>`<option value="${value}" ${a?.marks?.[i]===value?"selected":""}>${label}</option>`).join("")}</select></label>`).join("")}</fieldset></details>
        <p id="corpus-conclusion" class="corpus-conclusion" aria-live="polite"></p>

        <details id="corpus-more" ${!reviewer?"open":""}><summary>Relecture et options${reviewer?` · ${esc(reviewer)}`:""}</summary><label class="field">Votre identifiant de relecture<input name="reviewer" aria-label="Votre identifiant de relecture" maxlength="80" pattern="[A-Za-z0-9](?:[A-Za-z0-9_]|-){0,79}" value="${esc(reviewer)}" placeholder="Ex. correcteur-1"><small>Un alias, retenu dans cet onglet. Aucun nom d’élève.</small></label>
        <label class="field">Position de la question<select name="geometry" aria-label="Position de la question"><option value="">À vérifier</option><option value="confirmed" ${a?.geometry==="confirmed"?"selected":""}>L’extrait contient bien cette question</option><option value="source_only" ${a?.geometry==="source_only"?"selected":""}>J’ai lu directement sur la photo entière</option><option value="incorrect" ${a?.geometry==="incorrect"?"selected":""}>L’extrait est mal placé</option></select></label>
        <label class="field">Note de relecture (facultatif)<textarea name="notes" rows="2" maxlength="2000">${esc(a?.notes||"")}</textarea></label></details>
        <div class="corpus-savebar"><button class="button" type="button" data-corpus="last" ${lastSavedIndex===null?"hidden":""}>Revoir la dernière</button><button class="button primary" type="submit" id="corpus-save">${flow?"Confirmer et continuer":"Enregistrer et continuer"}</button></div>
      </form></section></div>
      <div class="corpus-secondary"><p class="muted corpus-shortcuts">Clavier : chiffres ou pavé numérique pour les choix, 0 pour aucune marque, Entrée pour enregistrer, C pour cadrer, flèches pour déplacer (Maj : 10 px). Les raccourcis sont inactifs pendant la saisie d’un champ.</p><a class="button" href="/api/corpus/${item.id}/export" download>Exporter cette copie</a>
      <details class="block-gap"><summary>Historique des observations (${item.history.length})</summary><ol class="history">${item.history.map(h=>`<li>${esc(h.after?.reviewer||"")} · section ${esc(h.section)} · question ${h.question} · ${esc(h.after?.recorded_at||"")}</li>`).join("")||'<li>Aucune observation enregistrée.</li>'}</ol></details></div>`;
    updateConclusion();loadPhoto();
  }
  function proposeNext() {
    if(!flow||manualBounds||current().annotation||!photo?.naturalWidth)return;
    const prior=item.questions[index-1],q=current(),a=prior?.annotation;
    if(!a?.manual_bounds||a.geometry!=="confirmed"||prior.section!==q.section||prior.question+1!==q.question)return;
    const [x0,y0,x1,y1]=a.manual_bounds,dx=flowDirection==="right"?x1-x0:flowDirection==="left"?x0-x1:0,dy=flowDirection==="down"?y1-y0:0;
    if(x0+dx<0||x1+dx>photo.naturalWidth||y1+dy>photo.naturalHeight) {message("Le cadre suivant sort de la photo. Cadrez cette question avec C ou le bouton de cadrage.");return;}
    manualBounds=[x0+dx,y0+dy,x1+dx,y1+dy];proposed=true;
    $("#corpus-position").disabled=false;$("#corpus-position").checked=false;$("[name=geometry]").value="";
  }
  function moveFrame(direction,step=1) {
    if(!manualBounds||!photo?.naturalWidth)return;
    const [x0,y0,x1,y1]=manualBounds;
    const dx=direction==="left"?-step:direction==="right"?step:0,dy=direction==="up"?-step:direction==="down"?step:0;
    const x=Math.max(-x0,Math.min(photo.naturalWidth-x1,dx)),y=Math.max(-y0,Math.min(photo.naturalHeight-y1,dy));
    manualBounds=[x0+x,y0+y,x1+x,y1+y];dirty=true;proposed=true;
    $("#corpus-position").checked=false;$("[name=geometry]").value="";drawPreview();
  }
  function drawPreview() {
    if(!active()||!photo?.naturalWidth||!manualBounds)return;
    const canvas=$("#corpus-manual-preview");if(!canvas)return;
    const [x0,y0,x1,y1]=manualBounds;
    canvas.width=x1-x0;canvas.height=y1-y0;
    canvas.getContext("2d").drawImage(photo,x0,y0,x1-x0,y1-y0,0,0,x1-x0,y1-y0);
    canvas.hidden=false;$("#corpus-copy-image").hidden=true;$("#corpus-no-crop").hidden=true;
    $("#corpus-crop-caption").textContent=proposed?"Cadre proposé · à vérifier":"Extrait placé manuellement";
    $(".corpus-inline-move").hidden=!flow;
    const context=$("#corpus-context");context.hidden=!flow;
    if(flow) {
      const w=x1-x0,h=y1-y0,left=Math.max(0,x0-2*w),top=Math.max(0,y0-h/2),right=Math.min(photo.naturalWidth,x1+2*w),bottom=Math.min(photo.naturalHeight,y1+h/4);
      context.width=Math.ceil(right-left);context.height=Math.ceil(bottom-top);
      const ctx=context.getContext("2d");ctx.drawImage(photo,left,top,right-left,bottom-top,0,0,context.width,context.height);
      ctx.strokeStyle="#944838";ctx.lineWidth=Math.max(1,context.height/100);ctx.strokeRect(x0-left,y0-top,w,h);
    }
    $("[data-corpus=clear-crop]").hidden=false;
  }
  function loadPhoto() {
    if(photo?.naturalWidth){proposeNext();drawPreview();return;}
    if(photo)return;
    photo=new Image();
    photo.onload=()=>{if(active()){proposeNext();drawPreview();}};
    photo.onerror=()=>{photo=null;error("La photo n’a pas pu être affichée. Rechargez la page avant d’annoter.");};
    photo.src=imageURL("source");
  }
  function editCrop() {
    if(editor)return;
    if(!photo?.naturalWidth){error("La photo est encore en chargement. Réessayez dans un instant.");loadPhoto();return;}
    const q=current();
    editor=openCropEditor({image:photo,bounds:manualBounds,previousBounds,viewport:editorViewport,title:`Section ${q.section} · Question ${q.question}`,
      onApply:bounds=>{manualBounds=bounds;previousBounds=[...bounds];dirty=true;proposed=false;drawPreview();$("#corpus-position").disabled=false;$("#corpus-position").checked=true;$("[name=geometry]").value="confirmed";},
      onClose:viewport=>{editorViewport=viewport;editor=null;if(active())$("#corpus-reading").focus({preventScroll:true});}});
  }
  function goTo(next) {
    if(!keepOrDiscard())return;
    reviewer=$("[name=reviewer]").value.trim();index=next;renderQuestion();
    $("#corpus-reading").focus({preventScroll:true});$(".corpus-toolbar").scrollIntoView({block:"start",behavior:"instant"});
  }
  root.addEventListener("click",event=>{
    if(busy)return;
    const move=event.target.closest("[data-move]");if(move){moveFrame(move.dataset.move);return;}
    const quick=event.target.closest("[data-quick]");if(quick){quickAnswer(Number(quick.dataset.quick));return;}
    const action=event.target.closest("[data-corpus]")?.dataset.corpus;
    if(action==="previous"&&index>0)goTo(index-1);
    if(action==="next"&&index<item.questions.length-1)goTo(index+1);
    if(action==="last"&&lastSavedIndex!==null)goTo(lastSavedIndex);
    if(action==="crop")editCrop();
    if(action==="clear-crop") {
      manualBounds=null;proposed=false;dirty=true;$("#corpus-context").hidden=true;$(".corpus-inline-move").hidden=true;$("[name=geometry]").value="";$("#corpus-position").checked=false;
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
    if(el.id==="corpus-flow") {
      flow=el.checked;root.classList.toggle("corpus-flow",flow);
      try {sessionStorage.setItem("psychomark-annotation-flow",String(flow));}catch {}
      $("#corpus-flow-direction").hidden=!flow;$("#corpus-save").textContent=flow?"Confirmer et continuer":"Enregistrer et continuer";
      $("#corpus-context").hidden=true;$(".corpus-inline-move").hidden=true;proposeNext();drawPreview();
      $("#corpus-reading").focus({preventScroll:true});
    }
    if(el.id==="corpus-flow-direction") {flowDirection=el.value;try {sessionStorage.setItem("psychomark-flow-direction",flowDirection);}catch {}message("Sens modifié pour les prochaines propositions. Le cadre actuel est conservé.");}
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
    if(!item||busy||editor||event.altKey||event.ctrlKey||event.metaKey||event.isComposing)return;
    if(event.target.closest("input,select,textarea,summary,a,[contenteditable]"))return;
    const direction={ArrowLeft:"left",ArrowRight:"right",ArrowUp:"up",ArrowDown:"down"}[event.key];
    if(direction&&manualBounds){event.preventDefault();moveFrame(direction,event.shiftKey?10:1);return;}
    if(event.repeat)return;
    const digit=/^(Digit|Numpad)[0-9]$/.test(event.code)?Number(event.code.slice(-1)):/^[0-9]$/.test(event.key)?Number(event.key):null;
    if(digit!==null&&digit<=current().choices){event.preventDefault();quickAnswer(digit);return;}
    if(event.key.toLowerCase()==="c"){event.preventDefault();editCrop();return;}
    if(event.key==="Enter"&&(!event.target.closest("button")||event.target.closest("[data-quick],[data-move]"))){event.preventDefault();$("#corpus-observation").requestSubmit();}

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
      if(flow&&!form.get("geometry")) {
        const visibleImage=$("#corpus-copy-image");
        const visible=manualBounds&&photo?.naturalWidth||(!visibleImage.hidden&&visibleImage.complete&&visibleImage.naturalWidth);
        if(visible)form.set("geometry","confirmed");
      }
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
