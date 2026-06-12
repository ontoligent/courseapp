import os
import re
import sys
import shutil
import pathlib
import yaml

CONFIG_FILE = "config.yml"

# Resolved at publish time by publish(); kept module-level so the helper
# functions below can share them without threading every path through each call.
SOURCE_DIR = None
TARGET_DIR = None
ATTACHMENTS_DIR = None

def load_environment_paths():
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ Error: Local configuration file '{CONFIG_FILE}' is missing.")
        sys.exit(1)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        if not config_data:
            print("❌ Error: config.yml file is completely empty.")
            sys.exit(1)

        src = config_data.get("obsidian_source_dir")
        attachments = config_data.get("obsidian_attachments_dir")

        if not src or not attachments:
            print("❌ Error: Missing configuration parameters in config.yml.")
            print("   Ensure both 'obsidian_source_dir' and 'obsidian_attachments_dir' exist.")
            sys.exit(1)

        return src, "./docs", attachments
    except Exception as e:
        print(f"❌ Fatal configuration parser error: {e}")
        sys.exit(1)

def reset_target_directory():
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR, exist_ok=True)

    js_dir = os.path.join(TARGET_DIR, "javascripts")
    os.makedirs(js_dir, exist_ok=True)

    mathjax_config = """window.MathJax = {
  tex: {
    inlineMath: [["\\\\(", "\\\\)"]],
    displayMath: [["\\\\[", "\\\\]"]]
  },
  options: { ignoreHtmlClass: ".*", processHtmlClass: "arithmatex" }
};"""
    with open(os.path.join(js_dir, "mathjax.js"), "w", encoding="utf-8") as f:
        f.write(mathjax_config)
    print("🔄 Public site target directories initialized smoothly.")

def find_file_in_vault(note_name, search_base):
    # Only append .md extension if the filename doesn't contain a specific suffix type
    if not pathlib.Path(note_name).suffix:
        note_name += ".md"

    for root, _, files in os.walk(str(search_base)):
        if note_name in files:
            return pathlib.Path(root) / note_name
    return None

def strip_yaml_frontmatter(text):
    return re.sub(r'^---[\s\S]*?---\n', '', text, count=1)

# Add 'current_rel_path' as a third parameter
def interpolate_transclusions(content, src_base, current_rel_path):
    pattern = re.compile(r'!\[\[([^\]]+)\]\]')

    def replace_match(match):
        raw_embed = match.group(1)

        # ROUTE 1: Image Resource Hook
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
        if raw_embed.lower().endswith(image_extensions):
            image_name = os.path.basename(raw_embed)

            target_path = find_file_in_vault(image_name, ATTACHMENTS_DIR)

            if target_path:
                public_img_dir = os.path.join(TARGET_DIR, "images")
                os.makedirs(public_img_dir, exist_ok=True)
                shutil.copy2(target_path, os.path.join(public_img_dir, image_name))

                # --- NEW DETECT DEPTH LOGIC ---
                # Count how many parent directories exist above this file
                depth = len(pathlib.Path(current_rel_path).parents) - 1
                path_prefix = "../" * depth

                # Dynamically returns 'images/...' or '../images/...' or '../../images/...'
                return f"![{image_name}]({path_prefix}images/{image_name})"
            else:
                return f"\n*⚠️ [Image Asset Missing from Attachments: {image_name}]*\n"

        # ROUTE 2: Structural Text Sub-Note Transclusions
        embed_parts = raw_embed.split('#')
        note_name = embed_parts.pop(0).strip()

        section_target = None
        if embed_parts:
            section_target = embed_parts.pop(0).strip()

        target_path = find_file_in_vault(note_name, src_base)
        if not target_path:
            return f"\n*⚠️ [Transclusion Missing: {note_name}]*\n"

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                target_content = f.read()

            if "publish: false" in target_content:
                return f"\n*🔒 [Embedded content is marked private]*\n"

            clean_text = strip_yaml_frontmatter(target_content)

            if section_target:
                esc_target = re.escape(section_target)
                header_pattern = re.compile(r'^(#+)\s+' + esc_target + r'\s*$', re.MULTILINE)
                header_match = header_pattern.search(clean_text)

                if header_match:
                    start_pos = header_match.start()
                    header_level = len(header_match.group(1))
                    next_pattern_str = r'^#{1,' + str(header_level) + r'}\s+'
                    next_header_pattern = re.compile(next_pattern_str, re.MULTILINE)
                    next_match = next_header_pattern.search(clean_text, header_match.end())

                    if next_match:
                        clean_text = clean_text[start_pos:next_match.start()]
                    else:
                        clean_text = clean_text[start_pos:]
                else:
                    return f"\n*⚠️ [Section heading '{section_target}' not found in {note_name}]*\n"

            # Pass current_rel_path down to recursive transclusion calls too
            return interpolate_transclusions(clean_text, src_base, current_rel_path)

        except Exception as e:
            return f"\n*⚠️ [Transclusion Processing Error inside match: {e}]*\n"

    return pattern.sub(replace_match, content)

def process_and_filter_vault():
    md_count, ipynb_count = 0, 0
    src_path, tgt_path = pathlib.Path(SOURCE_DIR), pathlib.Path(TARGET_DIR)

    print(f"🔍 Scanning notes source directory: {src_path}")

    for root, _, files in os.walk(src_path):
        for file in files:
            if file.endswith(".md"):
                file_src_path = pathlib.Path(root) / file
                try:
                    with open(file_src_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if "publish: true" in content and "publish: false" not in content:
                        print(f"📄 Compiling public document: {file}")
                        rel_path = file_src_path.relative_to(src_path)
                        file_tgt_path = tgt_path / rel_path
                        os.makedirs(file_tgt_path.parent, exist_ok=True)

                        # Process and resolve all image links & text transclusions nested inside
                        finalized_markdown = interpolate_transclusions(content, src_path, rel_path)

                        with open(file_tgt_path, "w", encoding="utf-8") as out_file:
                            out_file.write(finalized_markdown)
                        md_count += 1

                        # Copy accompanying raw dataset Jupyter Notebook files normally
                        ipynb_src_path = file_src_path.with_suffix(".ipynb")
                        if ipynb_src_path.exists():
                            ipynb_tgt_path = file_tgt_path.with_suffix(".ipynb")
                            shutil.copy2(ipynb_src_path, ipynb_tgt_path)
                            ipynb_count += 1
                except Exception as e:
                    print(f"❌ Security compilation leak prevented on file {file}: {e}")

    print(f"\n🔒 Multi-Path Compilation Sync Succeeded!")
    print(f"   - Markdown Notes Processed: {md_count}")
    print(f"   - Native Notebook Artifacts Linked: {ipynb_count}")

def publish():
    """Resolve paths from the local config.yml, then compile the vault into ./docs.

    Paths are loaded here (not at import) so the module can be imported from any
    directory — e.g. during `courseapp create`, where no config.yml exists yet.
    """
    global SOURCE_DIR, TARGET_DIR, ATTACHMENTS_DIR
    SOURCE_DIR, TARGET_DIR, ATTACHMENTS_DIR = load_environment_paths()
    reset_target_directory()
    process_and_filter_vault()

if __name__ == "__main__":
    publish()
