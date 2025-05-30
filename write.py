import os

OUTPUT_FILE = "app_snapshot.txt"
ROOT_DIR = "app"  # Change if your root is different (e.g., '.')

# Allowed file extensions
INCLUDE_EXTENSIONS = {".py", ".html", ".js", ".css"}

def generate_tree_structure(root_path):
    tree_lines = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        level = dirpath.replace(root_path, "").count(os.sep)
        indent = "  " * level
        tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")
        subindent = "  " * (level + 1)
        for f in filenames:
            tree_lines.append(f"{subindent}{f}")
    return "\n".join(tree_lines)

def write_file_snapshot(root_path, output_path):
    with open(output_path, "w", encoding="utf-8") as out:
        # Write tree structure first
        out.write("📁 APP STRUCTURE\n\n")
        out.write(generate_tree_structure(root_path))
        out.write("\n\n📄 FILE CONTENTS\n\n")

        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                ext = os.path.splitext(file_path)[1]
                if ext in INCLUDE_EXTENSIONS:
                    rel_path = os.path.relpath(file_path, root_path)
                    out.write(f"--- {rel_path} ---\n")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        out.write(content + "\n\n")
                    except Exception as e:
                        out.write(f"[Error reading file: {e}]\n\n")

if __name__ == "__main__":
    write_file_snapshot(ROOT_DIR, OUTPUT_FILE)
    print(f"✅ Snapshot saved to {OUTPUT_FILE}")
