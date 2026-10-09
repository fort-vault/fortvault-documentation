import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ignored = new Set(['.git', 'output', 'tmp', '__pycache__', 'node_modules']);
function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    if (ignored.has(entry.name)) return [];
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) return walk(file);
    return entry.name.endsWith('.md') && !entry.isSymbolicLink() ? [file] : [];
  });
}

const errors = [];
const files = walk(root);
let links = 0;
for (const file of files) {
  const source = fs.readFileSync(file, 'utf8').replace(/```[\s\S]*?```/g, '');
  const targets = [
    ...Array.from(source.matchAll(/!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\s*\)/g), match => match[1]),
    ...Array.from(source.matchAll(/^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)/gm), match => match[1]),
  ];
  for (const target of targets) {
    const clean = target.replace(/^<|>$/g, '');
    if (/^(?:[a-z][a-z\d+.-]*:|#)/i.test(clean)) continue;
    const pathname = clean.split(/[?#]/, 1)[0];
    links++;
    let resolved;
    try { resolved = path.resolve(path.dirname(file), decodeURIComponent(pathname)); }
    catch { errors.push(`${path.relative(root, file)}: malformed link ${target}`); continue; }
    if (!fs.existsSync(resolved)) errors.push(`${path.relative(root, file)}: missing target ${target}`);
  }
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else {
  console.log(`Checked ${files.length} Markdown files and ${links} local file links: all targets exist.`);
}
// Anchors and remote URLs are intentionally outside this filesystem-only check.
