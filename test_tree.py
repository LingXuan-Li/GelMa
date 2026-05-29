from pathlib import Path

IGNORE_DIRS = {".venv", "__pycache__", "node_modules"}

def print_tree(path: Path, prefix=""):
    entries = sorted(
        [p for p in path.iterdir() if p.name not in IGNORE_DIRS],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        name = entry.name + ("/" if entry.is_dir() else "")

        print(prefix + connector + name)

        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)

import os

MPL_HEADER = """# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 LingXuan-Li

"""

def has_mpl_header(content: str) -> bool:
    return "Mozilla Public License" in content


def add_header_to_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if has_mpl_header(content):
        return  # すでにあるのでスキップ

    new_content = MPL_HEADER + content

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated: {file_path}")


def walk_project(root: str):
    for dirpath, dirnames, filenames in os.walk(root):

        # .venv を完全に除外
        dirnames[:] = [d for d in dirnames if d != ".venv"]

        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(dirpath, filename)
                add_header_to_file(file_path)


if __name__ == "__main__":
    walk_project(".")
    root = Path(".")
    print(root.resolve().name)
    print_tree(root)