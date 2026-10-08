/* Source coordinates remain independent of screen zoom and touch target size. */
export function openCropEditor({image, bounds, previousBounds, title, viewport, onApply, onClose}) {
  const dialog=document.createElement("dialog");
  dialog.className="crop-editor";
  dialog.setAttribute("aria-labelledby","crop-title");
  const arrow=path=>`<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="${path}"/></svg>`;
  dialog.innerHTML=`<header><h2 id="crop-title"></h2><button type="button" class="button" data-crop="cancel">Annuler</button></header>
    <div class="crop-tools"><button type="button" class="button" data-crop="pan" aria-label="Déplacer la photo">Photo</button><button type="button" class="button" data-crop="adjust" aria-label="Modifier le cadre">Cadre</button><label>Zoom <select aria-label="Zoom de la photo">${[1,2,3,5,8,12].map(v=>`<option value="${v}">${v*100} %</option>`).join("")}</select></label><button type="button" class="button" data-crop="focus">Agrandir le cadre</button></div>
    <p class="crop-hint" role="status"></p>
    <div class="crop-viewport"><div class="crop-stage"><canvas aria-label="Photo à cadrer. Pincez pour zoomer. Des boutons d’ajustement sont disponibles sous l’image."></canvas>${["haut gauche","haut droit","bas gauche","bas droit"].map((name,i)=>`<button type="button" class="crop-handle" data-handle="${i}" aria-label="Ajuster le coin ${name}" hidden><span aria-hidden="true"></span></button>`).join("")}</div></div>
    <details class="crop-fine"><summary>Ajuster avec les boutons</summary><div class="crop-fine-tools"><label>À déplacer<select aria-label="Partie du cadre"><option value="frame">Tout le cadre</option><option value="left">Bord gauche</option><option value="right">Bord droit</option><option value="top">Bord haut</option><option value="bottom">Bord bas</option></select></label><label>Pas<select aria-label="Précision du déplacement"><option value="1">Fin · 1 px</option><option value="10">Large · 10 px</option></select></label></div>
    <div class="crop-nudges">${[["left","Vers la gauche","M19 12H5m7-7-7 7 7 7"],["up","Vers le haut","M12 19V5m-7 7 7-7 7 7"],["down","Vers le bas","M12 5v14m-7-7 7 7 7-7"],["right","Vers la droite","M5 12h14m-7-7 7 7-7 7"]].map(([dir,label,path])=>`<button type="button" class="button" data-nudge="${dir}" aria-label="${label}">${arrow(path)}</button>`).join("")}</div></details>
    <details class="crop-keyboard"><summary>Autres options et coordonnées</summary><div class="crop-extra"><button type="button" class="button" data-crop="new">Retracer le cadre</button><button type="button" class="button" data-crop="reuse" ${previousBounds?"":"disabled"}>Reprendre le dernier cadre</button></div><div class="corpus-coordinates">${["Gauche","Haut","Droite","Bas"].map((label,i)=>`<label class="field">${label}<input type="number" data-crop-bound="${i}" min="0" step="1"></label>`).join("")}</div><button type="button" class="button" data-crop="coordinates">Appliquer les coordonnées</button></details>
    <p class="error" role="alert" tabindex="-1"></p>
    <footer><span>Vérifiez la question et tous ses choix.</span><button type="button" class="button primary" data-crop="apply">Utiliser ce cadre</button></footer>`;
  dialog.querySelector("h2").textContent=title;
  document.body.append(dialog);
  const $=selector=>dialog.querySelector(selector),canvas=$("canvas"),stage=$(".crop-stage"),scroller=$(".crop-viewport");
  const width=image.naturalWidth,height=image.naturalHeight;
  canvas.width=width;canvas.height=height;
  const fields=[...dialog.querySelectorAll("[data-crop-bound]")],handles=[...dialog.querySelectorAll("[data-handle]")];
  fields.forEach((el,i)=>el.max=i%2?height:width);
  let draft=bounds?[...bounds]:null,gesture=null,pinch=null,blocked=false,coordinatesDirty=false,closed=false;
  let zoom=viewport?.zoom||1,mode=draft?"adjust":"draw";
  const pointers=new Map();
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  const valid=b=>b&&b.every(Number.isInteger)&&b[0]>=0&&b[1]>=0&&b[2]<=width&&b[3]<=height&&b[2]>b[0]&&b[3]>b[1];
  const corners=()=>[[draft[0],draft[1]],[draft[2],draft[1]],[draft[0],draft[3]],[draft[2],draft[3]]];
  function error(text) {$(".error").textContent=text;if(text)$(".error").focus();}
  function sourcePoint(x,y) {
    const rect=canvas.getBoundingClientRect();
    return [(x-rect.left)/rect.width*width,(y-rect.top)/rect.height*height];
  }
  function updateControls() {
    $("[data-crop=pan]").setAttribute("aria-pressed",String(mode==="pan"));
    $("[data-crop=adjust]").setAttribute("aria-pressed",String(mode!=="pan"));
    $("[data-crop=focus]").disabled=!draft;
    $(".crop-hint").textContent=mode==="draw"?"Glissez pour tracer un cadre. Deux doigts pour zoomer ou déplacer la photo.":mode==="pan"?"Glissez la photo ; pincez pour zoomer. Le cadre reste inchangé.":"Glissez le cadre ou ses grandes poignées. À côté, glissez la photo. Deux doigts pour zoomer.";
    const target=$("[aria-label='Partie du cadre']").value;
    dialog.querySelectorAll("[data-nudge]").forEach(button=>{
      const horizontal=["left","right"].includes(button.dataset.nudge);
      button.disabled=!draft||(target!=="frame"&&horizontal!==["left","right"].includes(target));
    });
  }
  function draw() {
    const ctx=canvas.getContext("2d");ctx.drawImage(image,0,0);
    handles.forEach(el=>el.hidden=!draft||mode!=="adjust");
    if(!draft)return;
    const scale=width/Math.max(1,canvas.getBoundingClientRect().width);
    ctx.strokeStyle="#944838";ctx.lineWidth=2*scale;
    ctx.strokeRect(draft[0],draft[1],draft[2]-draft[0],draft[3]-draft[1]);
    const target=$("[aria-label='Partie du cadre']").value;
    if(target!=="frame") {
      const [x0,y0,x1,y1]=draft;
      const lines={left:[x0,y0,x0,y1],right:[x1,y0,x1,y1],top:[x0,y0,x1,y0],bottom:[x0,y1,x1,y1]};
      const [a,b,c,d]=lines[target];ctx.lineWidth=5*scale;ctx.beginPath();ctx.moveTo(a,b);ctx.lineTo(c,d);ctx.stroke();
    }
    corners().forEach(([x,y],i)=>{
      // Offset handles 24 CSS px outward: fingers do not cover the exact corner.
      handles[i].style.left=`calc(${x/width*100}% + ${i%2?24:-24}px)`;
      handles[i].style.top=`calc(${y/height*100}% + ${i<2?-24:24}px)`;
    });
  }
  function sync() {fields.forEach((el,i)=>el.value=draft?.[i]??"");coordinatesDirty=false;updateControls();draw();}
  function zoomLabel() {
    const select=$("[aria-label='Zoom de la photo']");select.querySelector("[data-custom]")?.remove();
    if(![1,2,3,5,8,12].includes(zoom)) {const option=new Option(`${Math.round(zoom*100)} %`,String(zoom));option.dataset.custom="true";select.add(option);}
    select.value=String(zoom);
  }
  function setZoom(value,anchor=null,screen=null) {
    const rect=scroller.getBoundingClientRect();
    screen??=[rect.left+scroller.clientWidth/2,rect.top+scroller.clientHeight/2];
    anchor??=sourcePoint(...screen);
    zoom=clamp(value,1,12);stage.style.width=`${zoom*100}%`;
    const after=canvas.getBoundingClientRect();
    scroller.scrollLeft+=after.left+anchor[0]/width*after.width-screen[0];
    scroller.scrollTop+=after.top+anchor[1]/height*after.height-screen[1];
    zoomLabel();draw();
  }
  function focusCrop() {
    if(!draft)return;
    const fit=Math.min((scroller.clientWidth-104)/(draft[2]-draft[0]),(scroller.clientHeight-104)/(draft[3]-draft[1]));
    const baseWidth=canvas.getBoundingClientRect().width/zoom;
    setZoom(fit*width/baseWidth,[(draft[0]+draft[2])/2,(draft[1]+draft[3])/2]);
  }
  function cancelGesture() {if(gesture){const changed=gesture.kind!=="pan";if(changed)draft=gesture.before;gesture=null;if(changed)sync();}}
  function close() {
    if(closed)return;closed=true;observer.disconnect();
    const state={zoom,left:scroller.scrollLeft,top:scroller.scrollTop};
    dialog.close();dialog.remove();onClose(state);
  }
  function pair() {
    const [a,b]=[...pointers.values()];
    return {middle:[(a[0]+b[0])/2,(a[1]+b[1])/2],distance:Math.max(1,Math.hypot(a[0]-b[0],a[1]-b[1]))};
  }
  // Own touch navigation here; prevent native gestures from swallowing the next tap.
  scroller.addEventListener("touchstart",event=>event.preventDefault(),{passive:false});
  scroller.addEventListener("pointerdown",event=>{
    if(event.button!==0)return;
    error("");
    pointers.set(event.pointerId,[event.clientX,event.clientY]);scroller.setPointerCapture(event.pointerId);
    if(pointers.size===2) {
      cancelGesture();const p=pair();pinch={...p,zoom,anchor:sourcePoint(...p.middle)};blocked=true;return;
    }
    if(pointers.size!==1||blocked)return;
    const p=sourcePoint(event.clientX,event.clientY),before=draft?[...draft]:null;
    const handle=event.target.closest("[data-handle]");
    let kind="pan",corner=null,anchor=null;
    if(mode==="draw"&&event.target===canvas)kind="draw";
    else if(mode==="adjust"&&draft) {
      if(handle){kind="resize";const i=Number(handle.dataset.handle);corner=corners()[i];anchor=corners()[3-i];}
      else if(p[0]>=draft[0]&&p[0]<=draft[2]&&p[1]>=draft[1]&&p[1]<=draft[3])kind="move";
    }
    gesture={id:event.pointerId,start:p,client:[event.clientX,event.clientY],scroll:[scroller.scrollLeft,scroller.scrollTop],before,kind,corner,anchor,moved:false};
  });
  scroller.addEventListener("pointermove",event=>{
    if(!pointers.has(event.pointerId))return;
    pointers.set(event.pointerId,[event.clientX,event.clientY]);
    if(pinch&&pointers.size===2){const p=pair();setZoom(pinch.zoom*p.distance/pinch.distance,pinch.anchor,p.middle);return;}
    if(blocked||!gesture||event.pointerId!==gesture.id)return;
    const g=gesture;
    if(g.kind==="pan") {scroller.scrollLeft=g.scroll[0]+g.client[0]-event.clientX;scroller.scrollTop=g.scroll[1]+g.client[1]-event.clientY;return;}
    const p=sourcePoint(event.clientX,event.clientY);
    const dx=Math.round(p[0]-g.start[0]),dy=Math.round(p[1]-g.start[1]);
    if(!dx&&!dy)return;
    g.moved=true;
    if(g.kind==="move") {
      const b=g.before,x=clamp(dx,-b[0],width-b[2]),y=clamp(dy,-b[1],height-b[3]);
      draft=[b[0]+x,b[1]+y,b[2]+x,b[3]+y];
    }else {
      const a=g.kind==="resize"?g.anchor:[clamp(Math.round(g.start[0]),0,width),clamp(Math.round(g.start[1]),0,height)];
      const b=g.kind==="resize"?[clamp(g.corner[0]+dx,0,width),clamp(g.corner[1]+dy,0,height)]:[clamp(Math.round(p[0]),0,width),clamp(Math.round(p[1]),0,height)];
      draft=[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.max(a[0],b[0]),Math.max(a[1],b[1])];
    }
    sync();
  });
  function finish(event,cancelled) {
    if(!pointers.has(event.pointerId))return;
    pointers.delete(event.pointerId);
    if(gesture&&gesture.id===event.pointerId) {
      const g=gesture;
      if(cancelled||(!g.moved&&g.kind!=="pan")||!valid(draft))draft=g.before;
      else if(g.kind==="draw")mode="adjust";
      gesture=null;if(g.kind!=="pan")sync();
    }
    if(pinch&&pointers.size<2)pinch=null;
    if(!pointers.size)blocked=false;
    if(scroller.hasPointerCapture(event.pointerId))scroller.releasePointerCapture(event.pointerId);
  }
  scroller.addEventListener("pointerup",event=>finish(event,false));
  scroller.addEventListener("pointercancel",event=>finish(event,true));
  scroller.addEventListener("lostpointercapture",event=>finish(event,true));
  dialog.addEventListener("cancel",event=>{event.preventDefault();close();});
  dialog.addEventListener("input",event=>{if(event.target.matches("[data-crop-bound]"))coordinatesDirty=true;});
  $("[aria-label='Zoom de la photo']").addEventListener("change",event=>{cancelGesture();setZoom(Number(event.target.value));});
  $("[aria-label='Partie du cadre']").addEventListener("change",()=>{updateControls();draw();});
  function nudge(direction) {
    if(!draft)return;
    if(coordinatesDirty){error("Appliquez les coordonnées avant d’ajuster le cadre.");return;}
    const target=$("[aria-label='Partie du cadre']").value,step=Number($("[aria-label='Précision du déplacement']").value);
    const dx=direction==="left"?-step:direction==="right"?step:0,dy=direction==="up"?-step:direction==="down"?step:0;
    const [x0,y0,x1,y1]=draft;
    if(target==="frame") {const x=clamp(dx,-x0,width-x1),y=clamp(dy,-y0,height-y1);draft=[x0+x,y0+y,x1+x,y1+y];}
    else if(target==="left")draft[0]=clamp(x0+dx,0,x1-1);
    else if(target==="right")draft[2]=clamp(x1+dx,x0+1,width);
    else if(target==="top")draft[1]=clamp(y0+dy,0,y1-1);
    else if(target==="bottom")draft[3]=clamp(y1+dy,y0+1,height);
    sync();
  }
  dialog.addEventListener("click",event=>{
    const handle=event.target.closest("[data-handle]");
    if(handle) {$(".crop-fine").open=true;$("[aria-label='Partie du cadre']").focus();return;}
    const direction=event.target.closest("[data-nudge]")?.dataset.nudge;
    if(direction){error("");nudge(direction);return;}
    const action=event.target.closest("[data-crop]")?.dataset.crop;
    if(!action)return;
    if(action==="cancel"){close();return;}
    error("");
    if(action==="pan"||action==="adjust"||action==="new") {
      cancelGesture();mode=action==="pan"?"pan":action==="new"||!draft?"draw":"adjust";updateControls();draw();
      if(action==="new")$(".crop-keyboard").open=false;
    }
    if(action==="focus")focusCrop();
    if(action==="reuse"&&previousBounds) {draft=[...previousBounds];mode="adjust";sync();$(".crop-keyboard").open=false;focusCrop();}
    if(action==="coordinates") {
      const candidate=fields.map(el=>el.value===""?NaN:Number(el.value));
      if(!valid(candidate)){error("Renseignez quatre coordonnées entières délimitant un cadre dans la photo.");return;}
      draft=candidate;mode="adjust";sync();
    }
    if(action==="apply") {
      if(pointers.size){error("Terminez le geste avant de confirmer.");return;}
      if(coordinatesDirty){error("Appliquez les coordonnées avant de confirmer le cadre.");return;}
      if(!valid(draft)){error("Tracez un cadre autour des choix de la question.");return;}
      onApply([...draft]);close();
    }
  });
  const observer=new ResizeObserver(()=>{if(!closed)draw();});
  dialog.showModal();stage.style.width=`${zoom*100}%`;zoomLabel();
  if(viewport){scroller.scrollLeft=viewport.left;scroller.scrollTop=viewport.top;}
  sync();observer.observe(scroller);
  return {close};
}
