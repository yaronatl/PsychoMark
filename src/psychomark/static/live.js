/* Development only. Source changes never discard an unsaved exam or active upload. */
(() => {
  let previous = null;
  let pending = false;
  let checking = false;
  const notice = document.createElement("div");
  notice.className = "dev-update";
  notice.setAttribute("role", "status");
  notice.hidden = true;
  notice.textContent = "Mise à jour disponible. Enregistrez vos modifications pour actualiser l’interface.";
  document.body.append(notice);
  async function check() {
    if (checking || document.hidden) return;
    checking = true;
    try {
      const response = await fetch("/api/dev/revision", {cache:"no-store"});
      if (!response.ok) return;
      const {revision} = await response.json();
      if (previous !== null && previous !== revision) pending = true;
      previous = revision;
      if (pending) {
        if (window.psychomarkCanReload?.()) location.reload();
        else notice.hidden = false;
      }
    } catch { /* A restarting development server will become available again. */ }
    finally { checking = false; }
  }
  check();
  setInterval(check, 1500);
})();
