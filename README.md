# courseapp

A system-installed CLI that fires up and builds **private Obsidian vault → public MkDocs site** course pairs — in the spirit of Quarto and Jupyter Book.

`courseapp` is installed **once** on your system (it bundles the MkDocs toolchain). Each course it creates is just content + a local `config.yml` — no per-site virtual environment.

This guide takes you from nothing all the way to **two GitHub repos** — a private vault and a public, auto-deploying site.

---

## The model

- **Private source** — an Obsidian vault folder. Only notes whose frontmatter says `publish: true` are compiled; everything else stays private. Notebooks are authored in-vault via the [JupyMD](https://github.com/d-eniz/jupymd) plugin (its own Jupyter venv).
- **Public target** — a standalone MkDocs (Material) repo. It holds only what the CLI compiled — the committed `docs/` — and deploys to GitHub Pages.
- **The bridge** — a gitignored `config.yml` inside the public repo that maps your local vault + attachments paths. It never leaves your machine.

```
  PRIVATE                                   PUBLIC
  vault/  ──(courseapp publish)──▶  site/docs/  ──(courseapp deploy)──▶  GitHub Pages
  (Obsidian)                        (committed)                          (live site)
```

---

## 1. Install

**Prerequisites:** Python ≥ 3.10, `git`, and `pipx`. No Homebrew or system-Python changes — pipx puts courseapp in its own isolated environment and drops a launcher on your `PATH`.

```bash
# install pipx if you don't have it
python3 -m pip install --user pipx
pipx ensurepath          # adds ~/.local/bin to PATH (open a new terminal after)

# install courseapp (works on macOS, Linux, Windows)
pipx install git+https://github.com/ontoligent/courseapp
```

Verify in a **fresh** terminal:

```bash
which courseapp          # → ~/.local/bin/courseapp
courseapp --help         # lists: create, publish, serve, deploy
```

> Developing courseapp itself? Clone the repo and `pipx install -e ./courseapp` instead — code edits then take effect live.

---

## 2. The layout

A course is **two directories**:

| Dir | What it is | Privacy |
|---|---|---|
| **vault** | The Obsidian vault you author in. You publish from a *subfolder* of it (e.g. `pub/`). | **private** |
| **site** | The MkDocs repo that gets deployed. Holds compiled `docs/` + config. | **public** |

A tidy convention:

```
~/Repos/Courses/my-course/
  vault/        ← Obsidian vault root        (private)
    pub/        ← the publishable subfolder
  site/         ← public MkDocs repo         (public)
```

---

## 3. Create the pair

One command stamps out both sides:

```bash
courseapp create \
  --title  "My Course" \
  --vault  ~/Repos/Courses/my-course/vault \
  --folder pub \
  --target ~/Repos/Courses/my-course/site \
  --git-vault
```

| Flag | Meaning |
|---|---|
| `--title` | Site name shown in the header. |
| `--vault` | The vault **root** (the folder Obsidian opens). |
| `--folder` | Subfolder inside the vault whose notes get published (e.g. `pub`). |
| `--target` | Where the public site repo is created. |
| `--git-vault` | Also `git init` the vault (recommended — you'll push it in step 6). |
| `--no-vault-venv` | Skip building the Jupyter authoring venv (see below). |

Leave off any of the first four and `create` will prompt you for it.

**The authoring venv.** By default `create` builds a Jupyter venv at `<vault>/.venv` (jupytext + matplotlib/numpy/pandas/etc.) so the JupyMD plugin has a working kernel. This runs `pip install` and is **slow** — add `--no-vault-venv` to skip it and set it up later from `<vault>/vault-requirements.txt`.

### What you get

**Public site** (`--target`):
```
site/
  mkdocs.yml                     # theme + site_name
  config.yml                     # vault paths (gitignored — local only)
  requirements.txt               # CI installs courseapp from this
  README.md
  .gitignore
  .github/workflows/deploy.yml   # CI: deploy on push to main
```

**Private vault** (`--vault`):
```
vault/
  pub/
    .jupytext.toml               # md ⇄ ipynb pairing for JupyMD
    index.md                     # seed note (publish: true)
  attachments/
  vault-requirements.txt
  .venv/                         # authoring venv (unless --no-vault-venv)
```

> `config.yml` is the link between the two. It records your vault paths and is **gitignored**, so it never leaks into the public repo.

---

## 4. The daily loop (publish → preview → push)

Work from the **site** directory:

```bash
cd ~/Repos/Courses/my-course/site

courseapp publish     # compile the vault's pub/ notes → docs/
courseapp serve       # live preview at http://127.0.0.1:8000
```

Edit notes in Obsidian, re-run `courseapp publish`, refresh the browser. Only notes with `publish: true` in their frontmatter are included. When it looks right:

```bash
git add docs/
git commit -m "Update notes"
git push              # CI deploys the docs/ you just reviewed
```

What you saw at `localhost:8000` is exactly what goes live — the deploy server only ever sees the compiled `docs/`, never your private vault.

Prefer to deploy by hand (no CI)?

```bash
courseapp deploy      # build docs/ → push straight to GitHub Pages
```

---

## 5. Migrating existing notes

To move notes from an existing vault into the new one:

```bash
# 1. copy the publishable notes
cp -R /path/to/old-vault/pub/.          ~/Repos/Courses/my-course/vault/pub/
# 2. copy attachments
cp -R /path/to/old-vault/attachments/.  ~/Repos/Courses/my-course/vault/attachments/
```

Then make sure each note you want public has `publish: true` in its frontmatter, and run `courseapp publish && courseapp serve` to check. Your old vault stays untouched, so you can migrate gradually and compare.

---

## 6. Put both on GitHub

Two repos with **opposite visibility**: the vault is private, the site is public.

### 6a. Vault → **private** repo

The vault holds unpublished notes, so its repo **must be private**.

First add a `.gitignore` so the authoring venv and OS junk aren't committed:

```bash
cd ~/Repos/Courses/my-course/vault
cat > .gitignore <<'EOF'
.venv/
.DS_Store
.obsidian/workspace*.json
EOF
git add -A
git commit -m "Initial vault"
```

Create an **empty private repo** on GitHub (web UI → New → Private, or `gh repo create my-course-vault --private`), then:

```bash
git remote add origin https://github.com/<you>/my-course-vault.git
git push -u origin main
```

### 6b. Site → **public** repo + GitHub Pages

The site was already `git init`'d by `create`, with `docs/` committed and `config.yml` gitignored. Make sure your latest build is committed:

```bash
cd ~/Repos/Courses/my-course/site
courseapp publish
git add -A
git commit -m "Initial site"
```

Create an **empty public repo** on GitHub, then push:

```bash
git remote add origin https://github.com/<you>/my-course-site.git
git push -u origin main
```

Pushing to `main` triggers `.github/workflows/deploy.yml`, which installs courseapp (from this public repo — no edits needed, the ref is baked into `requirements.txt`) and runs `courseapp deploy`. That builds `docs/` and pushes a **`gh-pages`** branch.

Finally, turn on Pages: **repo Settings → Pages → Source: "Deploy from a branch" → `gh-pages` / `/ (root)` → Save.** After the first successful Action your site is live at:

```
https://<you>.github.io/my-course-site/
```

> **From here on,** your whole workflow is: edit in Obsidian → `courseapp publish` → commit `docs/` → `git push`. CI redeploys automatically. The vault and the live site never touch each other.

---

## Command reference

| Command | Run from | Does |
|---|---|---|
| `courseapp create` | anywhere | Scaffold a new vault + site pair. |
| `courseapp publish` | site dir | Compile the vault's published notes into `docs/`. |
| `courseapp serve` | site dir | Local live-reloading preview at `:8000`. |
| `courseapp deploy` | site dir | Build `docs/` and push to GitHub Pages by hand. |

---

## Troubleshooting

- **`command not found: courseapp`** → run `pipx ensurepath` and open a new terminal. `~/.local/bin` must be on your `PATH`.
- **`courseapp` runs an old version / `create` missing** → an active virtualenv is shadowing the pipx install. `deactivate`, open a fresh terminal, and check `which courseapp` points at `~/.local/bin/courseapp`.
- **`❌ config.yml is missing`** → run `publish`/`serve`/`deploy` from the **site** directory (the one with `mkdocs.yml`), not the vault.
- **CI runs but the site 404s** → make sure GitHub Pages is set to the **`gh-pages`** branch (step 6b), and that the Action finished successfully (Actions tab).
- **CI fails pushing `gh-pages`** → in the site repo, **Settings → Actions → General → Workflow permissions** must allow **Read and write**.
