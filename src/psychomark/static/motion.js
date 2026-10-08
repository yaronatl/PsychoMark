import { TextMorph } from "./vendor/torph.mjs";

/** Morph a busy button's label, then release listeners/animations on completion. */
export function showBusyLabel(button, text) {
  const original = button.textContent;
  const originalWidth = button.style.minWidth;
  const width = button.getBoundingClientRect().width;
  const label = document.createElement("span");
  button.style.minWidth = `${width}px`;
  button.replaceChildren(label);
  button.setAttribute("aria-label", text);
  button.setAttribute("aria-busy", "true");
  const morph = new TextMorph({
    element: label,
    locale: "fr",
    duration: 220,
    ease: "cubic-bezier(0.16, 1, 0.3, 1)",
    scale: false,
    respectReducedMotion: true,
  });
  morph.update(original);
  morph.update(text);
  return () => {
    morph.destroy();
    button.textContent = original;
    button.style.minWidth = originalWidth;
    button.removeAttribute("aria-label");
    button.removeAttribute("aria-busy");
  };
}
