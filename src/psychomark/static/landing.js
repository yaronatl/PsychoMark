"use strict";

// Presentation only. The real demo, recognition and grades use the existing API.
// These illustrative marks are never fed into the correction engine.
export function renderLanding() {
  const marks = [2, 1, 4, 3, 2, 4, 1, 3];
  const paperRows = marks.map((answer, index) => `
    <div class="paper-row"><span>${String(index + 1).padStart(2, "0")}</span>
      ${[1, 2, 3, 4].map(choice => `<span class="paper-bubble ${choice === answer ? "filled" : ""} ${index === 3 && choice === 2 ? "erased" : ""}">${choice}</span>`).join("")}
    </div>`).join("");

  return `
    <header class="site-header">
      <a class="brand" href="#/home" aria-label="PsychoMark, accueil"><img src="/assets/favicon.svg" width="32" height="32" alt=""><span>PsychoMark</span></a>
      <nav aria-label="Navigation de l’accueil">
        <button class="text-button" data-action="scroll-section" data-target="approach">L’approche</button>
        <a class="button" href="#/exams">Ouvrir mon espace</a>
      </nav>
    </header>

    <section class="hero" aria-labelledby="hero-title">
      <h1 id="hero-title">Moins de correction.<br><span>Plus de transmission.</span></h1>
      <p>Vos copies sur papier. Une correction à l’écran.<br class="desktop-break"> Un peu plus de temps pour ce qui compte : vos élèves.</p>
      <div class="hero-actions">
        <button class="button primary" data-action="demo">Découvrir la démonstration</button>
        <a class="quiet-link" href="#/new">Préparer un examen</a>
      </div>
      <p class="hero-note">Une première rencontre avec l’atelier, sur une copie d’exemple.</p>
    </section>

    <section class="product-scene" aria-label="Illustration du passage de la copie papier à sa correction">
      <div class="scene-caption"><span>Du papier à la clarté.</span><span>Un aperçu de l’atelier</span></div>
      <div class="scene-composition">
        <div class="answer-paper" aria-hidden="true">
          <div class="paper-heading"><span>PsychoMark</span><span>EXAMEN BLANC</span></div>
          <div class="paper-title">Une copie,<br>des possibilités.</div>
          <div class="paper-rule"><span>Section 1</span><span>Réponses</span></div>
          <div class="paper-answers">${paperRows}</div>
          <div class="paper-foot">Chaque marque mérite de l’attention.</div>
        </div>
        <div class="correction-preview">
          <div class="preview-bar"><span class="preview-dot" aria-hidden="true"></span> L’atelier de correction <span>Exemple illustratif</span></div>
          <div class="preview-body">
            <div class="preview-heading"><h2>Chaque réponse<br>compte.</h2><img src="/assets/favicon.svg" width="34" height="34" alt=""></div>
            <div class="preview-result"><span>Question 1</span><span>Réponse 2</span><span class="badge green">Correcte</span></div>
            <div class="preview-result"><span>Question 2</span><span>Réponse 1</span><span class="badge green">Correcte</span></div>
            <div class="preview-doubt"><div><span>Question 4</span><span class="badge amber">À vérifier</span></div><p>Deux marques, un doute.<br>Vous gardez le dernier mot.</p><div class="preview-choices" aria-label="Deux marques illustratives sur les choix 2 et 3"><span>1</span><span class="faint">2</span><span class="marked">3</span><span>4</span></div></div>
            <p class="preview-footnote">La note reste provisoire jusqu’à votre vérification.</p>
          </div>
        </div>
      </div>
      <div class="scene-bottom"><span>Le papier garde sa place. Le travail avance.</span><button class="text-button" data-action="demo">Ouvrir une vraie correction</button></div>
    </section>

    <section id="approach" class="approach" tabindex="-1" aria-labelledby="approach-title">
      <div class="approach-intro"><h2 id="approach-title">Un rituel plus simple.<br>Le même soin.</h2><p>Du premier corrigé à la dernière vérification, un fil clair pour accompagner vos examens blancs.</p></div>
      <ol class="workflow-list">
        <li><span class="step-index" aria-hidden="true">01</span><div><h3>Préparez le terrain.</h3><p>Choisissez le modèle de feuille, les sections et les questions. Renseignez vos bonnes réponses, à votre rythme.</p></div><span class="workflow-detail">Votre examen, votre format</span></li>
        <li><span class="step-index" aria-hidden="true">02</span><div><h3>Confiez vos copies à l’atelier.</h3><p>Importez les photos ou les scans correspondant au modèle. Les marques sont lues et comparées à votre corrigé.</p></div><span class="workflow-detail">Photos, scans et PDF</span></li>
        <li><span class="step-index" aria-hidden="true">03</span><div><h3>Accordez votre attention aux doutes.</h3><p>Consultez l’extrait de la copie, confirmez les réponses incertaines, puis retrouvez la note et le détail de la correction.</p></div><span class="workflow-detail">Une décision toujours traçable</span></li>
      </ol>
    </section>

    <section class="closing" aria-labelledby="closing-title">
      <div><h2 id="closing-title">Pensé pour le papier.<br>Au service de celles et ceux<br>qui transmettent.</h2><a class="button primary" href="#/exams">Entrer dans l’atelier</a></div>
      <div class="honest-note"><h3>Un atelier en construction.</h3><p>Cette première version se découvre sur des copies synthétiques. Avant d’utiliser vos feuilles, leur modèle doit être calibré et testé sur de vrais scans.</p><p>Une base pour travailler ensemble, avec une place prévue pour la vérification humaine.</p></div>
    </section>
    <footer class="site-footer"><a class="brand" href="#/home"><span>PsychoMark</span></a><span>Le soin du détail. Le goût de transmettre.</span><span>Première édition · Prototype</span></footer>
  `;
}
