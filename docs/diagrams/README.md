# Diagram Sources

`src/*.mmd` are the editable Mermaid sources. The `*.png` files in this directory are generated
renders — do not edit them by hand.

## Regenerate PNGs

```bash
cd docs/img
for f in src/*.mmd; do
  base=$(basename "$f" .mmd)
  mmdc -i "$f" -o "${base}.png" -b white -s 2 -p .puppeteer.json
done
```

Requires `mmdc` (Mermaid CLI):

```bash
npm i -g @mermaid-js/mermaid-cli
```

The `.puppeteer.json` config disables the Chrome sandbox so mmdc works in headless/root
environments:

```json
{ "args": ["--no-sandbox", "--disable-setuid-sandbox"] }
```
