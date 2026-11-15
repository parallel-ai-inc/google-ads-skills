#!/usr/bin/env python3
"""Copy the shared engine into every skill, so each skill works when installed alone.

    python3 tools/build.py                 every skill
    python3 tools/build.py SKILL_NAME      one skill
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "engine", "gads")


def main():
    skills = os.path.join(ROOT, "skills")
    only = sys.argv[1:]
    for name in sorted(os.listdir(skills)):
        if only and name not in only:
            continue
        scripts = os.path.join(skills, name, "scripts")
        if not os.path.isdir(scripts):
            continue
        target = os.path.join(scripts, "gads")
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns("__pycache__"))
        print("engine -> skills/%s/scripts/gads" % name)


if __name__ == "__main__":
    main()
