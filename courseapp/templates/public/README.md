# __SITE_NAME__

Open-source repository hosting course materials and programming reference guides.

## Technology Stack
* **Content:** Written in plain Markdown using [Obsidian](https://obsidian.md), with notebooks via [JupyMD](https://github.com/d-eniz/jupymd).
* **Engine:** Compiled and served by [`courseapp`](https://github.com/d-eniz) — a system-installed [MkDocs](https://mkdocs.org) / [Material](https://squidfunk.github.io/mkdocs-material/) site generator.

## Working on this site
```bash
courseapp publish    # compile the private vault into docs/
courseapp serve      # preview at http://127.0.0.1:8000
courseapp deploy     # publish the committed docs/ to GitHub Pages
```
