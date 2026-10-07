// Publish the pinned vanilla module locally; the Python app needs no Node runtime.
// Capture Torph's own injected stylesheet to allow precisely that style via CSP.
import { createHash } from "node:crypto";
import { copyFile, mkdir, writeFile } from "node:fs/promises";
import { TextMorph } from "torph";

const output = new URL("../src/psychomark/static/vendor/", import.meta.url);
let stylesheet = "";
globalThis.document = {
  createElement(tag) {
    if (tag !== "style") throw new Error(`Unexpected Torph build element: ${tag}`);
    return { dataset: {}, textContent: "" };
  },
  head: { appendChild(style) { stylesheet = style.textContent; } },
};
new TextMorph({ element: { setAttribute() {} }, respectReducedMotion: false });
delete globalThis.document;
if (!stylesheet.includes("[torph-root]")) throw new Error("Torph stylesheet was not captured");
await mkdir(output, { recursive: true });
await copyFile(new URL("../node_modules/torph/dist/index.mjs", import.meta.url), new URL("torph.mjs", output));
await copyFile(new URL("../node_modules/torph/LICENSE", import.meta.url), new URL("torph-LICENSE.txt", output));
await writeFile(new URL("torph-style-hash.txt", output), createHash("sha256").update(stylesheet).digest("base64") + "\n");
console.log("Torph module, MIT license and exact stylesheet CSP hash published locally.");
