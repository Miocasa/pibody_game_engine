import os
import hashlib
import json
import fnmatch

BASE_DIR = os.path.join(".", "pibody") # scan pibody in the root of the repo
OUTPUT_FILE = "manifest.json"

# Patterns or folders to ignore
IGNORE_PATTERNS = [
    ".gitignore",
    ".vscode/*",
    ".micropico",
    ".git/*",
    ".github/*",
    "node_modules/*",
    "__pycache__/*",
    "*.log",
    "*.tmp",
    "main.py",
    "README.md",
    OUTPUT_FILE  # ignore the manifest file itself
]

def should_ignore(path):
    for pattern in IGNORE_PATTERNS:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False

def compute_hash(filepath, algo='sha256'):
    hasher = hashlib.new(algo)
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_manifest(base_dir):
    manifest = {}
    for root, _, files in os.walk(base_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, base_dir).replace("\\", "/")
            if should_ignore(rel_path):
                continue
            file_hash = compute_hash(filepath)
            manifest[rel_path] = file_hash
    return manifest

if __name__ == "__main__":
    manifest_data = generate_manifest(BASE_DIR)
    with open(os.path.join(BASE_DIR, OUTPUT_FILE), 'w') as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Manifest written to {OUTPUT_FILE}")

