# courseapp — How to create a new course and work on it

`courseapp` is now installed system-wide (via `pipx`). This guide walks through creating a fresh **private-vault + public-site** pair and the day-to-day loop of **publish → preview locally → push**.

------------------------------------------------------------------------

## 0. Use a clean terminal first (important)

`courseapp` lives at `~/.local/bin/courseapp` (the pipx install). The *old* in-site copy at `mkdocs-pub/.venv/bin/courseapp` will **shadow** it if that venv is active. So in a new terminal, make sure no venv is active:

``` bash
# if your prompt shows (.venv), deactivate it:
deactivate 2>/dev/null

# confirm you're using the installed tool, not the old one:
which courseapp          # → /Users/<you>/.local/bin/courseapp   ✅
courseapp --help         # should list: create, publish, serve, deploy
```

If `which` shows a path inside `mkdocs-pub/.venv`, open a fresh terminal.

------------------------------------------------------------------------

## 1. Decide the layout

A course is **two directories**:

| Dir | What it is | Privacy |
|------------------------|------------------------|------------------------|
| **vault** | The Obsidian vault you author in. You publish from a *subfolder* of it (e.g. `pub/`). | **private** |
| **site** | The MkDocs repo that gets deployed. Holds compiled `docs/` + config. | **public** |

Pick paths now. A tidy convention (sibling to the existing course):

```         
~/Repos/Courses/DS2023/my-course/
  vault/        ← Obsidian vault root        (private)
    pub/        ← the publishable subfolder
  site/         ← public MkDocs repo         (public)
```

------------------------------------------------------------------------

## 2. Create the pair

Run **one** command, filling in your values:

``` bash
courseapp create \
  --title  "My Course" \
  --vault  ~/Repos/Courses/DS2023/my-course/vault \
  --folder pub \
  --target ~/Repos/Courses/DS2023/my-course/site \
  --git-vault
```

What each flag means:

-   `--title` → the site name shown in the header.
-   `--vault` → the vault **root** (the folder Obsidian opens).
-   `--folder` → the subfolder inside the vault whose notes get published (`pub`).
-   `--target` → where the public site repo is created.
-   `--git-vault` → also `git init` the vault (optional; omit if you don't want the vault under git).

### About the authoring venv

By default, `create` also builds a **Jupyter authoring venv** at `<vault>/.venv` (jupytext + matplotlib/numpy/pandas/etc.) so the **JupyMD** Obsidian plugin has a working kernel. This step runs `pip install` and is **slow**.

-   Want it now: run the command as above.
-   Skip it for now (faster, add it later): append `--no-vault-venv`.

To add it later, just re-run `create` without `--no-vault-venv`, or set the venv up by hand from `<vault>/vault-requirements.txt`.

### If `create` prompts you

Leave off any flag and it will ask interactively. All four (`title`, `vault`, `folder`, `target`) are required one way or another.

------------------------------------------------------------------------

## 3. What you get

**Public site** (`--target`):

```         
site/
  mkdocs.yml                     # theme + site_name
  config.yml                     # paths to your vault (gitignored — local only)
  requirements.txt               # for CI (see §6)
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

> `config.yml` is the link between the two — it records your vault paths and is **gitignored**, so it never leaks into the public repo.

------------------------------------------------------------------------

## 4. The daily loop (publish → preview → push)

From the **site** directory:

``` bash
cd ~/Repos/Courses/DS2023/my-course/site

courseapp publish     # compile the vault's pub/ notes → docs/
courseapp serve       # live preview at http://127.0.0.1:8000
```

Edit notes in Obsidian, re-run `courseapp publish`, refresh the browser. Repeat until it looks right. Only notes whose frontmatter has `publish: true` are included. When happy:

``` bash
git add docs/
git commit -m "update notes"
git push              # CI deploys the docs/ you just reviewed
```

What you saw at `localhost:8000` is exactly what goes live — the deploy server only ever sees the compiled `docs/`, never your private vault.

### Prefer to deploy by hand (no CI)?

``` bash
courseapp deploy      # build docs/ → push straight to GitHub Pages
```

------------------------------------------------------------------------

## 5. Migrating your existing content

To move notes from the current `mkdocs-vault` into the new vault:

1.  Copy the note files into the new publishable folder:

    ``` bash
    cp -R ~/Repos/Courses/DS2023/mkdocs-test/mkdocs-vault/pub/. \
          ~/Repos/Courses/DS2023/my-course/vault/pub/
    ```

2.  Copy attachments:

    ``` bash
    cp -R ~/Repos/Courses/DS2023/mkdocs-test/mkdocs-vault/attachments/. \
          ~/Repos/Courses/DS2023/my-course/vault/attachments/
    ```

3.  Make sure each note you want public has `publish: true` in its frontmatter.

4.  `courseapp publish && courseapp serve` to check the result.

The old `mkdocs-vault` / `mkdocs-pub` pair stays untouched the whole time, so you can migrate gradually and compare against it.

------------------------------------------------------------------------

## 6. CI / GitHub (only when you're ready to host it)

Local `publish` / `serve` / `deploy` need **nothing** beyond the installed tool.

For **GitHub Actions** auto-deploy to work, the runner installs `courseapp` from GitHub, so two things must be true:

1.  The `courseapp` repo (`~/Repos/courseapp`) is pushed to GitHub.
2.  The new site's `requirements.txt` line `courseapp @ git+https://github.com/<OWNER>/courseapp@main` has `<OWNER>` replaced with your GitHub username/org.

Until then, just deploy locally with `courseapp deploy` — same result, no CI.

------------------------------------------------------------------------

## Troubleshooting

-   **`courseapp` runs the old version / `create` missing** → a venv is shadowing it. `deactivate`, open a fresh terminal, check `which courseapp`.
-   **`❌ config.yml is missing`** → run `publish`/`serve`/`deploy` from the **site** directory (the one with `mkdocs.yml`), not the vault.
-   **`mkdocs: command not found`** → should not happen with the installed tool (it calls mkdocs via its own interpreter). If it does, your `courseapp` is the old shadowed one — see the first item.