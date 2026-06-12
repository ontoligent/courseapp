# courseapp

A system-installed CLI that fires up and builds **private Obsidian vault → public MkDocs site** course pairs — in the spirit of Quarto and Jupyter Book.

`courseapp` is installed once on your system (it bundles the MkDocs toolchain). Each course site it creates is just content + a local `config.yml` — no per-site virtual environment.

## Install

```bash
python3 -m pip install --user pipx
pipx ensurepath
pipx install -e ~/Repos/courseapp      # editable: code edits take effect live
```

## Commands

```bash
courseapp create     # scaffold a new private-vault + public-site pair
courseapp publish    # compile the vault into ./docs (run from a site dir)
courseapp serve      # local live-reloading preview (run from a site dir)
courseapp deploy     # build + push the committed docs/ to GitHub Pages
```

## The model

- **Private source:** an Obsidian vault folder. Notes marked `publish: true` are compiled; everything else stays private. Notebooks are authored in-vault via the [JupyMD](https://github.com/d-eniz/jupymd) plugin (its own Jupyter venv).
- **Public target:** a standalone MkDocs (Material) repo. It holds only files the CLI compiled — the committed `docs/` — and deploys to GitHub Pages.
- **The bridge:** a gitignored `config.yml` in the public repo mapping the local vault and attachments paths.

## Deploy model

Compile locally, commit `docs/`, let CI deploy it:

```bash
courseapp publish          # vault -> docs/
git add -A && git commit -m "Update site"
git push                   # CI runs `courseapp deploy`
```
