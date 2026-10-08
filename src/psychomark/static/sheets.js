/* Visual geometry editor. Python remains the authority for calibration and reading. */
import { showBusyLabel } from "./motion.js";

const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const labels = {single:"Réponse unique", blank:"Sans marque", multiple:"Plusieurs marques", uncertain:"À vérifier", unreadable:"Illisible"};
const accept = '.png,.jpg,.jpeg,.tif,.tiff,.pdf';
const pair = (a,b) => [a,b];
const field = (name,label,value,min,max,step="1") => `<label class="field">${label}<input name="${name}" type="number" value="${value}" min="${min}" max="${max}" step="${step}" required></label>`;

async function request(path, options={}) {
  const response = await fetch(`/api/sheets${path}`, {...options, headers: options.body instanceof FormData ? {} : {"Content-Type":"application/json"}});
  const data = await response.json().catch(()=>({}));
  if(!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(d=>`${d.loc.slice(1).join(" / ")} : ${d.msg}`).join("\n") : data.detail;
    throw new Error(detail || "Le serveur n’a pas pu terminer cette opération.");
  }
  return data;
}
function uploadBody(file) {
  if(!file)throw new Error("Choisissez un fichier.");
  if(file.size>64*1024*1024)throw new Error("Le fichier dépasse 64 Mio.");
  const body = new FormData();body.append("file",file);return body;
}

export async function sheetList() {
  const sheets = await request("");
  return `<div class="page-head"><div><h1>Mes feuilles</h1><p>Définissez une fois les cases à lire. Réutilisez ensuite la feuille dans vos examens.</p></div><a class="button primary" href="#/sheets/new">Ajouter une feuille</a></div>`+
    `<div class="notice"><div><strong>Un modèle décrit la feuille, pas l’examen</strong>Repérez toutes les questions imprimées ici. Vous choisirez les sections réellement utilisées et le corrigé à la création de chaque examen.</div></div>`+
    (sheets.length ? `<div class="card table-card table-wrap"><table><thead><tr><th>Feuille</th><th>Grilles</th><th>État</th><th>Action</th></tr></thead><tbody>${sheets.map(s=>`<tr><td><strong>${esc(s.name)}</strong></td><td>${s.sections.length}</td><td>${s.published ? 'Modèle enregistré · à valider sur vos copies' : 'Brouillon'}</td><td><a class="button small" href="#/sheets/${s.id}">${s.published?'Ouvrir':'Continuer'}</a></td></tr>`).join("")}</tbody></table></div>` : `<div class="card empty"><h2>Votre première feuille</h2><p>Préparez un scan vierge, net et à plat. L’assistant vous guidera pour placer les grilles et essayer la lecture sur une copie remplie.</p><a class="button" href="#/sheets/new">Commencer</a></div>`);
}

export function mountSheetBuilder(container, identifier) {
  const root = document.createElement("div");root.className="sheet-builder";container.replaceChildren(root);
  let sheet=null, sections=[], points=[], editing=null, image=null, dirty=false, busy=false, disposed=false, result=null, zoom=1;
  const active = () => !disposed && root.isConnected;
  const $ = selector => root.querySelector(selector);
  const imageURL = kind => `/api/sheets/${sheet.id}/image/${kind}?v=${sheet.revision}&test=${sheet.test||""}`;
  const error = message => {if(active()){const el=$("#sheet-error");el.textContent=message;if(message)el.scrollIntoView({block:"center"});}};
  const mutate = () => {dirty=true;result=null;$("#sheet-verification")?.replaceChildren();};
  const controller = {canReload:()=>!dirty&&!busy, dispose:()=>{disposed=true;}};

  async function run(button, label, task) {
    if(busy)return;
    busy=true;error("");
    const release=button ? showBusyLabel(button,label) : ()=>{};
    root.querySelectorAll("button,input,select").forEach(el=>{el.dataset.wasDisabled=String(el.disabled);el.disabled=true;});
    try {await task();} catch(e) {error(explain(e.message));}
    finally {busy=false;release();if(active())root.querySelectorAll("[data-was-disabled]").forEach(el=>{el.disabled=el.dataset.wasDisabled==="true";delete el.dataset.wasDisabled;});}
  }
  function explain(message) {
    if(message.includes("printed frame"))return "Le cadre imprimé d’une grille n’est pas retrouvé. Placez les deux coins sur son contour. Les feuilles sans cadre ne sont pas encore prises en charge. Détail : "+message;
    if(message.includes("bubble")||message.includes("overlap")||message.includes("axes"))return "Vérifiez les centres, la taille des cases et les limites des grilles. Utilisez une feuille vierge, sans réponse coloriée. Détail : "+message;
    if(message.includes("features"))return "La feuille manque de repères nets pour l’alignement. Essayez un scan de meilleure qualité. Détail : "+message;
    return message;
  }
  function base(title,description) {
    document.title=`${title} — PsychoMark`;
    return `<a class="back" href="#/sheets">Mes feuilles</a><div class="page-head"><div><h1>${esc(title)}</h1><p>${description}</p></div></div><div id="sheet-error" class="error" role="alert"></div>`;
  }
  function renderImport() {
    root.innerHTML=base("Ajouter une feuille","Un scan vierge, quelques repères, puis un essai de lecture.")+`<ol class="sheet-steps"><li aria-current="step">1. Importer</li><li>2. Placer les grilles</li><li>3. Vérifier et essayer</li></ol>
      <form id="sheet-import" class="card sheet-import"><h2>Commencez par la feuille vierge</h2><p>Utilisez le PDF original ou un scan droit, net, sans réponse coloriée. Les grilles doivent avoir un cadre imprimé et des cases régulièrement espacées.</p><label class="field">Fichier de la feuille<input name="file" type="file" accept="${accept}" required></label><p class="muted">PNG, JPG, TIFF ou PDF d’une seule page · 64 Mio maximum. Une photo en perspective convient à l’essai, mais utilisez une référence à plat pour créer le modèle.</p><button class="button primary" type="submit">Importer la feuille</button></form>`;
  }
  function numberValue(name) {return Number($(`[name="${name}"]`).value);}
  function pointNames() {return ["Coin supérieur gauche du cadre", "Coin inférieur droit du cadre", "Centre réponse 1, question 1", "Centre réponse 1, dernière question", "Centre dernière réponse, question 1"];}
  function instructions() {
    const names=pointNames();
    $("#sheet-guide").textContent=points.length<5 ? `Repère ${points.length+1}/5 — ${names[points.length]}. Cliquez sur la feuille.` : "Les cinq repères sont placés. Ajustez la taille des cases, puis ajoutez la grille.";
    $("#sheet-point-fields").innerHTML=points.map((p,i)=>`<fieldset><legend>${names[i]}</legend><div class="sheet-pair">${field(`point-${i}-x`,"X (px)",p[0],0,sheet.width,.1)}${field(`point-${i}-y`,"Y (px)",p[1],0,sheet.height,.1)}</div></fieldset>`).join("");
  }
  function candidate() {
    if(points.length!==5)return null;
    const q=numberValue("questions"), c=numberValue("choices");
    return {id:$("[name=section]").value.trim(),questions:q,choices:c,
      bounds:[...points[0],points[1][0]-points[0][0],points[1][1]-points[0][1]],first_center:points[2],
      question_step:pair((points[3][0]-points[2][0])/(q-1),(points[3][1]-points[2][1])/(q-1)),
      choice_step:pair((points[4][0]-points[2][0])/(c-1),(points[4][1]-points[2][1])/(c-1)),
      bubble_radius:pair(numberValue("radius-x"),numberValue("radius-y"))};
  }
  function draw() {
    const canvas=$("#sheet-canvas");if(!canvas||!image?.complete||!image.naturalWidth)return;
    const ctx=canvas.getContext("2d");ctx.drawImage(image,0,0);
    const all=sections.filter(s=>s.id!==editing);const current=candidate();if(current)all.push(current);
    for(const s of all) {
      const color=s===current?"#a46121":"#365d43";ctx.strokeStyle=color;ctx.lineWidth=2;ctx.strokeRect(...s.bounds);
      ctx.fillStyle=color;ctx.font="20px sans-serif";ctx.fillText(`S${s.id}`,s.bounds[0],Math.max(20,s.bounds[1]-8));
      if(s.questions>100||s.choices>10||s.bubble_radius.some(r=>r<=0||!Number.isFinite(r)))continue;
      for(let q=0;q<s.questions;q++)for(let c=0;c<s.choices;c++) {
        const x=s.first_center[0]+q*s.question_step[0]+c*s.choice_step[0],y=s.first_center[1]+q*s.question_step[1]+c*s.choice_step[1];
        if(!Number.isFinite(x+y))continue;
        ctx.beginPath();ctx.ellipse(x,y,...s.bubble_radius,0,0,Math.PI*2);ctx.stroke();
      }
    }
    points.forEach((p,i)=>{ctx.fillStyle="#944838";ctx.beginPath();ctx.arc(...p,4,0,Math.PI*2);ctx.fill();ctx.font="16px sans-serif";ctx.fillText(String(i+1),p[0]+7,p[1]-7);});
  }
  function renderSections() {
    $("#sheet-sections").innerHTML=sections.length ? sections.map(s=>`<li><span><strong>Section ${esc(s.id)}</strong><small>${s.questions} questions · ${s.choices} choix</small></span><div><button type="button" class="button small" data-sheet-action="edit" data-id="${esc(s.id)}">Ajuster</button> <button type="button" class="text-button" data-sheet-action="remove" data-id="${esc(s.id)}" aria-label="Retirer la section ${esc(s.id)}">Retirer</button></div></li>`).join("") : '<li class="muted">Aucune grille ajoutée pour le moment.</li>';
    $("#sheet-check").disabled=!sections.length;
  }
  function renderEditor() {
    if(!active())return;
    root.innerHTML=base(sheet.name,"Placez chaque grille imprimée. Les réponses de l’examen seront renseignées plus tard.")+`<ol class="sheet-steps"><li>1. Feuille importée</li><li aria-current="step">2. Placer les grilles</li><li>3. Vérifier et essayer</li></ol>
      <label class="field sheet-name">Nom de la feuille<input name="sheet-name" maxlength="120" value="${esc(sheet.name)}" required></label>
      <div class="sheet-layout"><div class="sheet-workbench"><div class="sheet-toolbar"><label>Zoom <select id="sheet-zoom"><option value="1">Vue entière</option><option value="1.5">150 %</option><option value="2">200 %</option><option value="3">300 %</option></select></label><button type="button" class="button small" data-sheet-action="undo">Annuler le dernier repère</button></div><p id="sheet-guide" role="status" aria-live="polite"></p><div class="sheet-canvas-scroll"><canvas id="sheet-canvas" width="${sheet.width}" height="${sheet.height}" aria-label="Feuille vierge : cliquez pour placer les cinq repères. Les coordonnées sont aussi modifiables dans le formulaire."></canvas></div><p class="muted">Grilles ajoutées en vert, grille en cours en ocre. Le zoom permet de viser le centre des petites cases.</p></div>
      <aside class="card sheet-controls"><form id="sheet-grid"><h2>Décrire une grille</h2><label class="field">Numéro de section<input name="section" value="1" pattern="[A-Za-z0-9]([A-Za-z0-9_]|-){0,79}" maxlength="80" required></label><div class="sheet-pair">${field("questions","Questions imprimées",30,2,100)}${field("choices","Choix par question",4,2,10)}</div><p class="muted">Comptez les questions présentes sur le papier, même si l’examen en utilise moins. Les questions peuvent être en ligne ou en colonne.</p><div class="sheet-pair">${field("radius-x","Demi-largeur case (px)",7,2,100,.1)}${field("radius-y","Demi-hauteur case (px)",10,2,100,.1)}</div><details><summary>Coordonnées précises / saisie clavier</summary><p class="muted">Origine en haut à gauche de l’image. X va vers la droite, Y vers le bas.</p><div id="sheet-point-fields"></div><button type="button" class="button small" data-sheet-action="manual">Ajouter un repère par coordonnées</button></details><div class="actions block-gap"><button class="button" id="sheet-add-grid" type="submit">Ajouter la grille</button><button class="text-button" type="button" data-sheet-action="reset">Recommencer les repères</button></div></form><hr><h2>Grilles de la feuille</h2><ul id="sheet-sections" class="sheet-section-list"></ul><button type="button" class="button primary full" id="sheet-check" data-sheet-action="check">Vérifier et sauvegarder les zones</button><p class="muted">Cette étape enregistre le brouillon et lance les contrôles Python.</p></aside></div><div id="sheet-verification"></div>`;
    $("#sheet-zoom").value=String(zoom);$("#sheet-canvas").style.width=`${zoom*100}%`;
    instructions();renderSections();loadImage();
    if(sheet.calibration&&!dirty)renderVerification();
  }
  function loadImage() {
    image=new Image();image.onload=()=>{if(active())draw();};image.onerror=()=>error("Impossible d’afficher la feuille. Rechargez la page.");image.src=imageURL("blank");
  }
  function testForm() {
    return `<form id="sheet-test" class="card block-gap"><h2>Essayer sur une copie remplie</h2><p>Importez une copie de cette même feuille. Comparez chaque réponse détectée aux marques sur l’original. Aucun corrigé ni note n’est utilisé pour cet essai.</p><label class="field">Copie à essayer<input type="file" name="test-file" accept="${accept}" required></label><button class="button" type="submit">Analyser cette copie</button><div id="sheet-test-results"></div></form>`;
  }
  function renderVerification() {
    $("#sheet-verification").innerHTML=`<section class="card block-gap"><h2>Vérifier les cases repérées</h2><p>Les contrôles géométriques ont réussi. Ouvrez l’image en grand et vérifiez que chaque ellipse verte est bien à l’intérieur de sa case, sur toutes les grilles.</p><details open><summary>Aperçu calculé par Python</summary><a href="${imageURL("preview")}" target="_blank" rel="noopener">Ouvrir l’aperçu en grand</a><img class="sheet-preview" src="${imageURL("preview")}" alt="Toutes les zones de lecture calculées par Python sur la feuille vierge"></details></section>${testForm()}<form id="sheet-publish" class="card block-gap"><h2>Enregistrer le modèle</h2><p>Un essai sur plusieurs copies reste nécessaire pour évaluer sa fiabilité. L’enregistrement rend ce modèle disponible pour les examens ; il ne certifie pas sa précision.</p><label class="decision-label"><input type="checkbox" name="checked" required> J’ai vérifié l’emplacement de toutes les cases sur l’aperçu.</label><button class="button primary" type="submit">Enregistrer le modèle</button></form>`;
    if(result)renderResult();
  }
  function renderPublished() {
    if(!active())return;
    root.innerHTML=base(sheet.name,"Ce modèle est enregistré et disponible dans la création d’examen.")+`<div class="notice"><div><strong>Modèle à valider sur vos copies</strong>Sa géométrie est enregistrée. Les essais ci-dessous vous permettent de vérifier la lecture, sans annoncer un taux de précision.</div><a class="button primary" href="#/new/${sheet.id}">Créer un examen avec cette feuille</a></div><div class="card"><h2>${sections.length} grille${sections.length>1?'s':''} configurée${sections.length>1?'s':''}</h2><p>${sections.map(s=>`Section ${esc(s.id)} : ${s.questions} questions, ${s.choices} choix`).join(' · ')}</p><p class="muted">Pour modifier les positions, créez un nouveau modèle. Les examens existants garderont cette version.</p><details><summary>Voir les zones enregistrées</summary><img class="sheet-preview" src="${imageURL("preview")}" alt="Zones de lecture enregistrées"></details></div>${testForm()}`;
    if(result)renderResult();
  }
  function renderResult() {
    const target=$("#sheet-test-results");if(!target||!result)return;
    const pending=result.answers.filter(a=>["uncertain","multiple","unreadable"].includes(a.status)).length;
    target.innerHTML=`<h3 class="block-gap">Lecture de la copie : ${pending} question${pending>1?'s':''} à examiner</h3><p>Ce nombre signale les ambiguïtés détectées. Il ne mesure pas les erreurs de lecture : comparez aussi les réponses indiquées comme uniques.</p>${result.status==="unreadable"?'<div class="notice warning">Le moteur n’a pas pu lire cette copie correctement. Vérifiez le modèle, la netteté et le cadrage du fichier.</div>':''}<div class="actions"><a class="button small" href="${imageURL("original")}" target="_blank" rel="noopener">Voir l’original</a><a class="button small" href="${imageURL("test")}" target="_blank" rel="noopener">Voir la copie annotée</a></div><div class="table-wrap sheet-results"><table><thead><tr><th>Section</th><th>Question</th><th>Réponse lue</th><th>État</th></tr></thead><tbody>${result.answers.map(a=>`<tr><td>${esc(a.section)}</td><td>${a.question}</td><td>${a.answer??'—'}</td><td>${labels[a.status]||esc(a.status)}</td></tr>`).join('')}</tbody></table></div>`;
  }
  function resetPoints() {points=[];editing=null;$("#sheet-add-grid").textContent="Ajouter la grille";instructions();draw();}
  root.addEventListener("input",event=>{
    if(!event.target.closest("#sheet-grid")&&event.target.name!=="sheet-name")return;
    mutate();
    if(event.target.name.startsWith("point-")) {const [,i,axis]=event.target.name.split("-");points[Number(i)][axis==="x"?0:1]=Number(event.target.value);}
    draw();
  });
  root.addEventListener("change",event=>{
    if(event.target.id==="sheet-zoom") {zoom=Number(event.target.value);$("#sheet-canvas").style.width=`${zoom*100}%`;}
  });
  root.addEventListener("click",event=>{
    if(busy)return;
    if(event.target.id==="sheet-canvas"&&points.length<5) {
      const rect=event.target.getBoundingClientRect();points.push([Math.round((event.clientX-rect.left)*sheet.width/rect.width*10)/10,Math.round((event.clientY-rect.top)*sheet.height/rect.height*10)/10]);mutate();instructions();draw();return;
    }
    const button=event.target.closest("[data-sheet-action]");if(!button)return;
    const action=button.dataset.sheetAction;
    if(action==="undo"){points.pop();mutate();instructions();draw();}
    if(action==="manual"&&points.length<5){points.push([0,0]);mutate();instructions();draw();}
    if(action==="reset")resetPoints();
    if(action==="remove"){sections=sections.filter(s=>s.id!==button.dataset.id);mutate();if(editing===button.dataset.id)resetPoints();renderSections();draw();}
    if(action==="edit") {
      const s=sections.find(s=>s.id===button.dataset.id);editing=s.id;
      points=[[s.bounds[0],s.bounds[1]],[s.bounds[0]+s.bounds[2],s.bounds[1]+s.bounds[3]],s.first_center.slice(),pair(s.first_center[0]+(s.questions-1)*s.question_step[0],s.first_center[1]+(s.questions-1)*s.question_step[1]),pair(s.first_center[0]+(s.choices-1)*s.choice_step[0],s.first_center[1]+(s.choices-1)*s.choice_step[1])];
      for(const [name,value] of Object.entries({section:s.id,questions:s.questions,choices:s.choices,"radius-x":s.bubble_radius[0],"radius-y":s.bubble_radius[1]}))$(`[name="${name}"]`).value=value;
      $("#sheet-add-grid").textContent="Appliquer les ajustements";instructions();draw();$("[name=section]").focus();
    }
    if(action==="check")run(button,"Vérification…",async()=>{
      if(points.length)throw new Error("Ajoutez la grille en cours ou recommencez ses repères avant de vérifier.");
      sheet=await request(`/${sheet.id}/calibration`,{method:"PUT",body:JSON.stringify({expected_revision:sheet.revision,name:$("[name=sheet-name]").value,sections})});
      dirty=false;result=null;if(active()){renderVerification();$("#sheet-verification").scrollIntoView({block:"start"});}
    });
  });
  root.addEventListener("submit",event=>{
    event.preventDefault();event.stopPropagation();if(busy)return;
    const form=event.target,button=form.querySelector('[type="submit"]');
    if(form.id==="sheet-grid") {
      const s=candidate();if(!s){error("Placez les cinq repères sur la feuille avant d’ajouter la grille.");return;}
      if(sections.some(other=>other.id===s.id&&other.id!==editing)){error("Ce numéro de section existe déjà.");return;}
      if(s.bounds[2]<=0||s.bounds[3]<=0){error("Le second coin doit être en bas à droite du premier.");return;}
      sections=sections.filter(other=>other.id!==editing);sections.push(s);mutate();resetPoints();renderSections();draw();error("");
      let next=1;while(sections.some(s=>s.id===String(next)))next++;$("[name=section]").value=String(next);return;
    }
    if(form.id==="sheet-import")run(button,"Importation…",async()=>{
      const created=await request("",{method:"POST",body:uploadBody(form.elements.file.files[0])});dirty=false;location.hash=`/sheets/${created.id}`;
    });
    if(form.id==="sheet-test")run(button,"Analyse en cours…",async()=>{
      const data=await request(`/${sheet.id}/test?revision=${sheet.revision}`,{method:"POST",body:uploadBody(form.elements["test-file"].files[0])});sheet=data.sheet;result=data.extraction;if(active())renderResult();
    });
    if(form.id==="sheet-publish")run(button,"Enregistrement…",async()=>{
      sheet=await request(`/${sheet.id}/publish`,{method:"POST",body:JSON.stringify({expected_revision:sheet.revision,checked_overlay:form.elements.checked.checked})});dirty=false;renderPublished();
    });
  });
  async function load() {
    if(identifier==="new"){renderImport();return;}
    root.innerHTML=base("Ouvrir la feuille","Chargement…");
    await run(null,"",async()=>{
      sheet=await request(`/${identifier}`);sections=structuredClone(sheet.sections);
      if(sheet.test)result=await request(`/${identifier}/test`);
      if(!active())return;if(sheet.published)renderPublished();else renderEditor();
    });
  }
  load();return controller;
}
