from __future__ import annotations

import argparse

from niyet.annotations import validate_annotation_file


parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()

problems = validate_annotation_file(args.path)
if problems:
    for problem in problems:
        print(f"row {problem.row}: {problem.message}")
    raise SystemExit(1)

print("annotation file looks valid")
