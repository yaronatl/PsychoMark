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
  let disposed=false,busy=false,dirty=false,item=null,index=0,photo=null,points=[],manualBounds=null,zoom=1;
  let reviewer="", boundsDirty=false;
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
    $("#corpus-conclusion").textContent=decision?`${statusLabels[decision.status]}${decision.choices.length?` · choix ${decision.choices.join(", ")}`:""}`:"Décrivez chaque case pour établir la lecture.";
  }
  function renderQuestion() {
    if(!active())return;
    const q=current(),a=q.annotation;
    manualBounds=a?.manual_bounds?[...a.manual_bounds]:null;points=[];zoom=1;photo=null;picking=false;boundsDirty=false;
    root.innerHTML=`<a class="back" href="#/annotations">Annotations</a>`+frame(`Feuille ${item.physical_sheet_id}`,`${item.completed} / ${item.total} questions observées. ${splitLabels[item.split]}.`,
      `<a class="button" href="/api/corpus/${item.id}/export" download>Exporter cette copie</a>`)+
      `<div class="corpus-toolbar"><label class="field">Question<select id="corpus-question">${item.questions.map((r,i)=>`<option value="${i}" ${i===index?"selected":""}>Section ${esc(r.section)} · Question ${r.question}${r.annotation?" — enregistrée":""}</option>`).join("")}</select></label><div class="actions"><button class="button small" type="button" data-corpus="previous" ${index===0?"disabled":""}>Précédente</button><button class="button small" type="button" data-corpus="next" ${index===item.questions.length-1?"disabled":""}>Suivante</button></div></div>
      <div class="corpus-layout"><section class="corpus-images" aria-label="Images de la question"><h2>Section ${esc(q.section)} · Question ${q.question}</h2>
        <div class="corpus-crops"><figure><figcaption>Modèle vierge</figcaption><img src="${cropURL('reference')}" alt="Emplacement des choix sur le modèle vierge"></figure>
        ${q.has_crop||manualBounds?`<figure><figcaption>${manualBounds?"Extrait placé manuellement":"Extrait proposé par le moteur"}</figcaption><img src="${cropURL('copy')}" alt="Marques sur la copie, sans annotation du moteur"></figure>`:'<div class="notice warning"><div><strong>Aucun extrait positionné</strong>Examinez l’original ci-dessous. Vous pouvez y délimiter cette question manuellement.</div></div>'}</div>
        <details id="corpus-source" ${!q.has_crop||manualBounds?"open":""}><summary>Voir l’original et placer un extrait</summary><div class="corpus-source-tools block-gap"><label>Zoom <select id="corpus-zoom"><option value="1">Vue entière</option><option value="2">200 %</option><option value="3">300 %</option></select></label><button class="button small" type="button" data-corpus="start-crop">Délimiter cette question</button><button class="button small" type="button" data-corpus="clear-crop">Retirer mon cadre</button></div><p id="corpus-crop-help" class="muted" role="status">Le cadre doit contenir tous les choix de cette seule question.</p><div class="corpus-source-scroll"><canvas id="corpus-source-canvas" width="${item.source_size[0]}" height="${item.source_size[1]}" aria-label="Photo originale. Pour délimiter une question, choisissez deux coins opposés. Saisie clavier disponible ci-dessous."></canvas></div>
        <details class="block-gap"><summary>Coordonnées du cadre / saisie clavier</summary><div class="corpus-coordinates">${["Gauche","Haut","Droite","Bas"].map((label,i)=>`<label class="field">${label}<input type="number" data-bound="${i}" min="0" max="${item.source_size[i%2]}" step="1" value="${manualBounds?.[i]??""}"></label>`).join("")}</div><button class="button small" type="button" data-corpus="apply-bounds">Appliquer les coordonnées</button></details></details>
      </section><aside class="card corpus-observation"><form id="corpus-observation"><h2>Ce que vous voyez</h2><p class="muted">Décrivez les marques, sans chercher la bonne réponse à l’examen. Une trace douteuse peut rester ambiguë.</p>
        <label class="field">Votre identifiant de relecture<input name="reviewer" maxlength="80" pattern="[A-Za-z0-9](?:[A-Za-z0-9_]|-){0,79}" value="${esc(reviewer)}" placeholder="Ex. correcteur-1" required><small>Un alias sans espace suffit. Ne renseignez pas le nom de l’élève.</small></label>
        <fieldset class="block-gap"><legend>Marques visibles</legend>${Array.from({length:q.choices},(_,i)=>`<label class="corpus-mark">Choix ${i+1}<select data-mark="${i}" required><option value="">À examiner</option>${Object.entries(markLabels).map(([value,label])=>`<option value="${value}" ${a?.marks?.[i]===value?"selected":""}>${label}</option>`).join("")}</select></label>`).join("")}</fieldset>
        <p id="corpus-conclusion" class="corpus-conclusion" aria-live="polite"></p>
        <label class="field">Position de la question<select name="geometry" aria-label="Position de la question" required><option value="">À vérifier</option><option value="confirmed" ${a?.geometry==="confirmed"?"selected":""}>L’extrait contient bien cette question</option><option value="source_only" ${a?.geometry==="source_only"?"selected":""}>J’ai lu directement sur la photo entière</option><option value="incorrect" ${a?.geometry==="incorrect"?"selected":""}>L’extrait est mal placé</option></select></label>
        <label class="field block-gap">Note de relecture <span class="muted">(facultatif)</span><textarea name="notes" rows="2" maxlength="1000">${esc(a?.notes||"")}</textarea></label>
        <button class="button primary full block-gap" type="submit">Enregistrer et continuer</button><p class="muted block-gap">L’observation reste modifiable et chaque modification est historisée. Aucun résultat automatique ni corrigé n’est affiché ici.</p>
      </form></aside></div>
      <details class="card block-gap"><summary>Historique des observations (${item.history.length})</summary><ol class="history">${item.history.map(h=>`<li>${esc(h.after?.reviewer||"")} · section ${esc(h.section)} · question ${h.question} · ${esc(h.after?.recorded_at||"")}</li>`).join("")||'<li>Aucune observation enregistrée.</li>'}</ol></details>`;
    updateConclusion();loadPhoto();
  }
  function loadPhoto() {
    const token=index;
    photo=new Image();const image=photo;
    image.onload=()=>{if(active()&&index===token&&photo===image)draw();};
    image.onerror=()=>error("La photo n’a pas pu être affichée. Rechargez la page avant d’annoter.");image.src=imageURL("source");
  }
  function draw() {
    const canvas=$("#corpus-source-canvas");if(!canvas||!photo?.complete||!photo.naturalWidth)return;
    const context=canvas.getContext("2d");context.drawImage(photo,0,0);
    canvas.style.width=`${zoom*100}%`;
    context.strokeStyle="#bd3e26";context.lineWidth=Math.max(2,canvas.width/700);
    if(manualBounds)context.strokeRect(manualBounds[0],manualBounds[1],manualBounds[2]-manualBounds[0],manualBounds[3]-manualBounds[1]);
    points.forEach(([x,y])=>{context.beginPath();context.arc(x,y,5,0,2*Math.PI);context.stroke();});
  }
  function applyBounds(bounds) {
    const [x0,y0,x1,y1]=bounds,[w,h]=item.source_size;
    if(bounds.some(v=>!Number.isInteger(v))||x0<0||y0<0||x1>w||y1>h||x1<=x0||y1<=y0)throw new Error("Le cadre doit être dans l’image et avoir une largeur et une hauteur positives.");
    manualBounds=bounds;points=[];dirty=true;boundsDirty=false;
    root.querySelectorAll("[data-bound]").forEach(el=>{el.value=bounds[Number(el.dataset.bound)];});
    $("[name=geometry]").value="";
    $("#corpus-crop-help").textContent="Cadre prêt. Vérifiez la question encadrée, puis confirmez sa position dans l’observation.";draw();
  }
  let picking=false;
  root.addEventListener("click",event=>{
    if(busy)return;
    const button=event.target.closest("[data-corpus]");
    try {
      if(button?.dataset.corpus==="previous"||button?.dataset.corpus==="next") {
        if(!keepOrDiscard())return;reviewer=$("[name=reviewer]").value;index+=button.dataset.corpus==="next"?1:-1;renderQuestion();
      }
      if(button?.dataset.corpus==="start-crop") {picking=true;points=[];$("#corpus-crop-help").textContent="Cliquez sur un premier coin, puis sur le coin opposé autour de tous les choix de cette question.";draw();}
      if(button?.dataset.corpus==="clear-crop") {manualBounds=null;points=[];picking=false;dirty=true;boundsDirty=false;$("[name=geometry]").value="";root.querySelectorAll("[data-bound]").forEach(el=>el.value="");draw();message("Cadre manuel retiré. Confirmez à nouveau la position avant d’enregistrer.");}
      if(button?.dataset.corpus==="apply-bounds") {
        const fields=[...root.querySelectorAll("[data-bound]")];
        if(fields.some(el=>el.value===""))throw new Error("Renseignez les quatre coordonnées.");
        applyBounds(fields.map(el=>Number(el.value)));picking=false;
      }
      if(event.target.id==="corpus-source-canvas"&&picking) {
        const rect=event.target.getBoundingClientRect();
        points.push([Math.max(0,Math.min(item.source_size[0],Math.round((event.clientX-rect.left)/rect.width*item.source_size[0]))),Math.max(0,Math.min(item.source_size[1],Math.round((event.clientY-rect.top)/rect.height*item.source_size[1])))]);
        if(points.length===2) {const [a,b]=points;picking=false;applyBounds([Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])]);}
        else {dirty=true;$("#corpus-crop-help").textContent="Premier coin placé. Cliquez sur le coin opposé.";draw();}
      }
    }catch(e){error(e.message);}
  });
  root.addEventListener("input",event=>{
    if(event.target.closest("#corpus-import,#corpus-observation")||event.target.matches("[data-bound]"))dirty=true;
    if(event.target.matches("[data-bound]"))boundsDirty=true;
  });
  root.addEventListener("change",event=>{
    const el=event.target;
    if(el.matches("[data-mark]"))updateConclusion();
    if(el.id==="corpus-question") {
      const selected=Number(el.value);el.value=String(index);
      if(!keepOrDiscard())return;reviewer=$("[name=reviewer]").value;index=selected;renderQuestion();
    }
    if(el.id==="corpus-zoom") {zoom=Number(el.value);draw();}
    if(el.matches('#corpus-import [name="file"]')) {
      const zip=el.files[0]?.name.toLowerCase().endsWith(".zip");
      $("#corpus-model-field").hidden=zip;$("[name=template_id]").disabled=zip;
      $("[name=split]").disabled=zip;if(zip)$("[name=split]").value="development";
      $("#corpus-split-help").textContent=zip?"Un diagnostic est un cas déjà examiné : il reste en développement.":"Toutes les photos d’une même feuille restent dans le même usage.";
    }
  });
  root.addEventListener("submit",event=>{
    event.preventDefault();if(busy)return;
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
      if(!decision){error("Décrivez chaque case avant d’enregistrer.");return;}
      if(picking||points.length){error("Terminez le cadre ou retirez-le avant d’enregistrer.");return;}
      if(boundsDirty){error("Appliquez les coordonnées du cadre avant d’enregistrer.");return;}
      const body={expected_revision:item.revision,section:q.section,question:q.question,reviewer:form.get("reviewer").trim(),...decision,marks,geometry:form.get("geometry"),manual_bounds:manualBounds,notes:form.get("notes")};
      run(async()=>{message("Enregistrement de l’observation…");const updated=await request(`/${item.id}/annotations`,{method:"PATCH",body:JSON.stringify(body)});if(!active())return;item=updated;dirty=false;reviewer=body.reviewer;
        const next=item.questions.findIndex((r,i)=>i>index&&!r.annotation);if(next!==-1)index=next;
        renderQuestion();message("Observation enregistrée. Les notes des examens restent inchangées.");$("[data-mark]").focus({preventScroll:true});});
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
  return {canReload:()=>!dirty&&!busy,dispose:()=>{disposed=true;}};
}
