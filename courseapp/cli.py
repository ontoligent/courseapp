import argparse
import sys
import os
import subprocess

def main():
    parser = argparse.ArgumentParser(description="CourseApp CLI Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    create_p = subparsers.add_parser(
        "create", help="Scaffold a new private-vault + public-site course pair."
    )
    create_p.add_argument("--title", help="Course title (site_name).")
    create_p.add_argument("--vault", help="Absolute path to the Obsidian vault root.")
    create_p.add_argument("--folder", help="Publishable subfolder name inside the vault.")
    create_p.add_argument("--target", help="Path where the public MkDocs site is created.")
    create_p.add_argument("--attachments", help="Attachments dir (default: <vault>/attachments).")
    create_p.add_argument("--no-vault-venv", action="store_true",
                          help="Skip creating the vault Jupyter authoring venv.")
    create_p.add_argument("--git-vault", action="store_true",
                          help="Also 'git init' the private vault folder.")

    subparsers.add_parser("publish", help="Run privacy filter and compile transclusions.")
    subparsers.add_parser("serve", help="Launch local live-reloading server.")
    subparsers.add_parser("deploy", help="Build and deploy the committed docs to GitHub Pages.")

    args = parser.parse_args()

    if args.command == "create":
        from courseapp.scaffold import create_course
        create_course(args)
    elif args.command == "publish":
        from courseapp.engine import publish
        print("🔒 Compiling and filtering assets...")
        publish()
    elif args.command == "serve":
        if not os.path.exists("mkdocs.yml"):
            print("❌ Error: Active mkdocs.yml layout map cannot be found here.")
            sys.exit(1)
        print("🚀 Launching dev server on http://127.0.0.1:8000...")
        subprocess.run(["mkdocs", "serve"])
    elif args.command == "deploy":
        if not os.path.exists("mkdocs.yml"):
            print("❌ Error: Active mkdocs.yml layout map cannot be found here.")
            sys.exit(1)
        print("🚀 Building and deploying to GitHub Pages...")
        subprocess.run(["mkdocs", "gh-deploy", "--force"])
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
