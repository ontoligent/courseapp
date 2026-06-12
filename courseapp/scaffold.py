"""`courseapp create` — scaffold a private-vault + public-site course pair.

Blueprint files live in `courseapp/templates/` and ship as package data; they are
read via importlib.resources so the global (pipx) install can stamp out new sites
anywhere. A small set of tokens is substituted at render time.
"""

import os
import sys
import subprocess
from importlib.resources import files

# Tokens substituted into template files at render time.
TOKEN_SITE_NAME = "__SITE_NAME__"
TOKEN_COURSEAPP_REF = "__COURSEAPP_REF__"

# What the generated public site's requirements.txt pins for CI. The repo isn't
# pushed yet, so this carries an <OWNER> placeholder the README explains.
DEFAULT_COURSEAPP_REF = "courseapp @ git+https://github.com/<OWNER>/courseapp@main"


def _templates():
    return files("courseapp.templates")


def _render(rel_path, replacements):
    """Read a template file from package data and apply token replacements."""
    text = (_templates() / rel_path).read_text(encoding="utf-8")
    for token, value in replacements.items():
        text = text.replace(token, value)
    return text


def _write(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"   + {path}")


def _prompt(value, label, default=None):
    """Use the provided flag value, else prompt; fall back to default non-interactively."""
    if value:
        return value
    if not sys.stdin.isatty():
        if default is not None:
            return default
        print(f"❌ Error: --{label} is required (no value and not running interactively).")
        sys.exit(1)
    suffix = f" [{default}]" if default else ""
    answer = input(f"{label}{suffix}: ").strip()
    return answer or default


def create_course(args):
    # ---- Resolve inputs (flags, then interactive/default fallbacks) ----
    title = _prompt(getattr(args, "title", None), "title")
    vault = _prompt(getattr(args, "vault", None), "vault")
    folder = _prompt(getattr(args, "folder", None), "folder")
    target = _prompt(getattr(args, "target", None), "target")

    vault = os.path.abspath(os.path.expanduser(vault))
    target = os.path.abspath(os.path.expanduser(target))
    attachments = getattr(args, "attachments", None) or os.path.join(vault, "attachments")
    attachments = os.path.abspath(os.path.expanduser(attachments))
    source_dir = os.path.join(vault, folder)

    site_tokens = {TOKEN_SITE_NAME: title, TOKEN_COURSEAPP_REF: DEFAULT_COURSEAPP_REF}

    print(f"\n📦 Creating course '{title}'")
    print(f"   public site : {target}")
    print(f"   vault source: {source_dir}")
    print(f"   attachments : {attachments}\n")

    # ---- Public site ----
    print("🌐 Public MkDocs site:")
    _write(os.path.join(target, "mkdocs.yml"), _render("public/mkdocs.yml", site_tokens))
    _write(os.path.join(target, "requirements.txt"), _render("public/requirements.txt", site_tokens))
    _write(os.path.join(target, "README.md"), _render("public/README.md", site_tokens))
    _write(os.path.join(target, ".gitignore"), _render("public/gitignore", {}))
    _write(os.path.join(target, ".github", "workflows", "deploy.yml"), _render("public/deploy.yml", {}))

    # config.yml carries BOTH paths the engine requires (the bootstrap script
    # omitted attachments, which broke publish). It is gitignored per template.
    config_yml = (
        f"obsidian_source_dir: {source_dir}\n"
        f"obsidian_attachments_dir: {attachments}\n"
    )
    _write(os.path.join(target, "config.yml"), config_yml)

    _git_init(target, "public site")

    # ---- Private vault ----
    print("\n🔒 Private vault:")
    _write(os.path.join(source_dir, ".jupytext.toml"), _render("vault/jupytext.toml", {}))
    _write(os.path.join(source_dir, "index.md"), _render("vault/index.md", site_tokens))
    os.makedirs(attachments, exist_ok=True)
    print(f"   + {attachments}/")

    vault_req = os.path.join(vault, "vault-requirements.txt")
    _write(vault_req, _render("vault/vault-requirements.txt", {}))

    if getattr(args, "git_vault", False):
        _git_init(vault, "vault")

    # ---- Vault authoring venv (slow) ----
    if getattr(args, "no_vault_venv", False):
        print("\n⏭️  Skipping vault authoring venv (--no-vault-venv).")
    else:
        _create_vault_venv(vault, vault_req)

    # ---- Next steps ----
    print("\n✅ Done. Next steps:")
    print(f"   cd {target}")
    print("   courseapp publish    # compile the vault into docs/")
    print("   courseapp serve      # preview at http://127.0.0.1:8000")


def _git_init(path, label):
    if os.path.isdir(os.path.join(path, ".git")):
        print(f"   • {label}: git repo already present, skipping init")
        return
    try:
        subprocess.run(["git", "init", "-b", "main", path], check=True,
                       capture_output=True, text=True)
        print(f"   • {label}: git initialized (branch main)")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"   ⚠️  {label}: git init skipped ({e})")


def _create_vault_venv(vault, vault_req):
    venv_dir = os.path.join(vault, ".venv")
    print(f"\n🐍 Vault Jupyter authoring venv → {venv_dir}")
    if os.path.isdir(venv_dir):
        print("   • venv already exists, skipping creation")
    else:
        print("   • creating venv...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    pip = os.path.join(venv_dir, "bin", "pip")
    print("   • installing authoring requirements (this is slow)...")
    try:
        subprocess.run([pip, "install", "-r", vault_req], check=True)
        print("   • authoring environment ready for JupyMD")
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  pip install failed ({e}); run manually:\n"
              f"        {pip} install -r {vault_req}")
