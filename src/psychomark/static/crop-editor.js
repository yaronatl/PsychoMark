/* A transient source-image crop. Only explicit Apply commits it to the observation. */
export function openCropEditor({image, bounds, previousBounds, title, viewport, onApply, onClose}) {
  const dialog=document.createElement("dialog");
  dialog.className="crop-editor";
  dialog.setAttribute("aria-labelledby","crop-title");
  dialog.innerHTML=`<header><div><h2 id="crop-title"></h2><p>Encadrez tous les choix de cette seule question.</p></div><button type="button" class="button" data-crop="cancel">Annuler</button></header>
    <div class="crop-tools"><button type="button" class="button" data-crop="draw" aria-pressed="true">Cadrer</button><button type="button" class="button" data-crop="pan" aria-pressed="false">Déplacer la photo</button><label>Zoom <select aria-label="Zoom de la photo"><option value="1">100 %</option><option value="2">200 %</option><option value="3">300 %</option><option value="5">500 %</option></select></label><button type="button" class="button" data-crop="reuse" ${previousBounds?"":"disabled"}>Reprendre le dernier cadre</button></div>
    <p class="crop-hint" role="status">Glissez pour tracer. Glissez dans le cadre pour le déplacer, sur un coin pour le redimensionner.</p>
    <div class="crop-viewport"><canvas aria-label="Photo à cadrer. Une saisie des coordonnées est disponible sous l’image."></canvas></div>
    <details class="crop-keyboard"><summary>Coordonnées / alternative au glissement</summary><div class="corpus-coordinates">${["Gauche","Haut","Droite","Bas"].map((label,i)=>`<label class="field">${label}<input type="number" data-crop-bound="${i}" min="0" step="1"></label>`).join("")}</div><button type="button" class="button" data-crop="coordinates">Appliquer les coordonnées</button></details>
    <p class="error" role="alert" tabindex="-1"></p>
    <footer><span>Vérifiez le numéro et les choix avant de confirmer.</span><button type="button" class="button primary" data-crop="apply">Utiliser ce cadre</button></footer>`;
  dialog.querySelector("h2").textContent=title;
  document.body.append(dialog);
  const $=selector=>dialog.querySelector(selector),canvas=$("canvas"),scroller=$(".crop-viewport");
  const width=image.naturalWidth,height=image.naturalHeight;
  canvas.width=width;canvas.height=height;
  let draft=bounds?[...bounds]:null,gesture=null,mode="draw",coordinatesDirty=false,closed=false;
  let zoom=viewport?.zoom||1;
  const fields=[...dialog.querySelectorAll("[data-crop-bound]")];
  fields.forEach((el,i)=>el.max=i%2?height:width);
  const valid=b=>b&&b.every(Number.isInteger)&&b[0]>=0&&b[1]>=0&&b[2]<=width&&b[3]<=height&&b[2]>b[0]&&b[3]>b[1];
  function error(text) {$(".error").textContent=text;if(text)$(".error").focus();}
  function draw() {
    const ctx=canvas.getContext("2d");ctx.drawImage(image,0,0);
    if(draft) {
      const [x0,y0,x1,y1]=draft,scale=width/Math.max(1,canvas.getBoundingClientRect().width);
      ctx.strokeStyle="#944838";ctx.lineWidth=2*scale;
      ctx.strokeRect(x0,y0,x1-x0,y1-y0);
      for(const [x,y] of [[x0,y0],[x1,y0],[x0,y1],[x1,y1]]) {
        ctx.fillStyle="#fff";ctx.fillRect(x-5*scale,y-5*scale,10*scale,10*scale);
        ctx.strokeRect(x-5*scale,y-5*scale,10*scale,10*scale);
      }
    }
  }
  function sync() {
    fields.forEach((el,i)=>el.value=draft?.[i]??"");
    coordinatesDirty=false;draw();
  }
  function setZoom(value) {
    const oldWidth=canvas.getBoundingClientRect().width,oldHeight=canvas.getBoundingClientRect().height;
    const centerX=(scroller.scrollLeft+scroller.clientWidth/2)/Math.max(1,oldWidth);
    const centerY=(scroller.scrollTop+scroller.clientHeight/2)/Math.max(1,oldHeight);
    zoom=value;canvas.style.width=`${zoom*100}%`;
    scroller.scrollLeft=centerX*canvas.getBoundingClientRect().width-scroller.clientWidth/2;
    scroller.scrollTop=centerY*canvas.getBoundingClientRect().height-scroller.clientHeight/2;
    draw();
  }
  function point(event) {
    const rect=canvas.getBoundingClientRect();
    return [Math.max(0,Math.min(width,Math.round((event.clientX-rect.left)/rect.width*width))),Math.max(0,Math.min(height,Math.round((event.clientY-rect.top)/rect.height*height)))];
  }
  function cancelGesture() {
    if(!gesture)return;
    draft=gesture.before;gesture=null;sync();
  }
  function close() {
    if(closed)return;closed=true;
    const state={zoom,left:scroller.scrollLeft,top:scroller.scrollTop};
    dialog.close();dialog.remove();onClose(state);
  }
  canvas.addEventListener("pointerdown",event=>{
    if(mode==="pan"||event.button!==0)return;
    if(gesture){cancelGesture();return;}
    if(!event.isPrimary)return;
    event.preventDefault();error("");
    const p=point(event),before=draft?[...draft]:null;
    let kind="draw",anchor=p;
    if(draft) {
      const rect=canvas.getBoundingClientRect(),radius=22*width/rect.width;
      const [x0,y0,x1,y1]=draft;
      const corners=[[x0,y0,x1,y1],[x1,y0,x0,y1],[x0,y1,x1,y0],[x1,y1,x0,y0]];
      // Closest corner wins; touch targets may overlap on a very small frame.
      const corner=corners.map(c=>({c,d:Math.hypot(p[0]-c[0],p[1]-c[1])})).sort((a,b)=>a.d-b.d)[0];
      if(corner.d<=radius){kind="resize";anchor=corner.c.slice(2);}
      else if(p[0]>x0&&p[0]<x1&&p[1]>y0&&p[1]<y1)kind="move";
    }
    gesture={id:event.pointerId,start:p,before,kind,anchor,moved:false};
    canvas.setPointerCapture(event.pointerId);
  });
  canvas.addEventListener("pointermove",event=>{
    if(!gesture||event.pointerId!==gesture.id)return;
    const p=point(event),g=gesture;
    if(Math.hypot(p[0]-g.start[0],p[1]-g.start[1])<1)return;
    g.moved=true;
    if(g.kind==="move") {
      const b=g.before;
      const dx=Math.max(-b[0],Math.min(width-b[2],p[0]-g.start[0]));
      const dy=Math.max(-b[1],Math.min(height-b[3],p[1]-g.start[1]));
      draft=[b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy];
    }else draft=[Math.min(g.anchor[0],p[0]),Math.min(g.anchor[1],p[1]),Math.max(g.anchor[0],p[0]),Math.max(g.anchor[1],p[1])];
    sync();
  });
  canvas.addEventListener("pointerup",event=>{
    if(!gesture||event.pointerId!==gesture.id)return;
    if(!gesture.moved||!valid(draft))draft=gesture.before;
    gesture=null;canvas.releasePointerCapture(event.pointerId);sync();
  });
  canvas.addEventListener("pointercancel",cancelGesture);
  canvas.addEventListener("lostpointercapture",cancelGesture);
  dialog.addEventListener("cancel",event=>{event.preventDefault();close();});
  dialog.addEventListener("input",event=>{if(event.target.matches("[data-crop-bound]"))coordinatesDirty=true;});
  $("select").addEventListener("change",event=>setZoom(Number(event.target.value)));
  dialog.addEventListener("click",event=>{
    const action=event.target.closest("[data-crop]")?.dataset.crop;
    if(!action)return;
    if(action==="cancel"){close();return;}
    error("");
    if(action==="draw"||action==="pan") {
      cancelGesture();mode=action;canvas.classList.toggle("is-panning",mode==="pan");
      for(const name of ["draw","pan"])$(`[data-crop=${name}]`).setAttribute("aria-pressed",String(name===mode));
      $(".crop-hint").textContent=mode==="pan"?"Faites défiler la photo avec le doigt. Revenez à Cadrer pour modifier le rectangle.":"Glissez pour tracer. Glissez dans le cadre pour le déplacer, sur un coin pour le redimensionner.";
    }
    if(action==="reuse"&&previousBounds) {draft=[...previousBounds];sync();$(".crop-hint").textContent="Cadre repris : déplacez-le sur la question actuelle avant de confirmer.";}
    if(action==="coordinates") {
      const candidate=fields.map(el=>el.value===""?NaN:Number(el.value));
      if(!valid(candidate)){error("Renseignez quatre coordonnées entières délimitant un cadre dans la photo.");return;}
      draft=candidate;sync();
    }
    if(action==="apply") {
      if(gesture){error("Terminez le glissement avant de confirmer.");return;}
      if(coordinatesDirty){error("Appliquez les coordonnées avant de confirmer le cadre.");return;}
      if(!valid(draft)){error("Tracez un cadre autour des choix de la question.");return;}
      onApply([...draft]);close();
    }
  });
  dialog.showModal();
  $("select").value=String(zoom);canvas.style.width=`${zoom*100}%`;
  if(viewport){scroller.scrollLeft=viewport.left;scroller.scrollTop=viewport.top;}
  sync();
  return {close};
}
