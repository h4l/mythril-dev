#!/usr/bin/env python3
"""
Look up the tag and sha256 digest of the latest registry entry for a tag.

Image tags are ordered by the integer value of the match groups in the regex, so
regexes must contain one or more groups matching integers.

Usage: lock_base_images.py < images.json > image-versions.json

Examples:

  # Resolve the latest versions of two images: the latest Python 3.9.X-slim and
  # the latest debian:bullseye-<date>
  $ cat images.json
  {
    "python-slim": {
      "registry": "docker.io/library/python",
      "tagRegex": "^3\\.9\\.(\\d+)-slim$"
    },
    "debian": {
      "registry": "docker.io/library/debian",
      "tagRegex": "^bullseye-(\\d{8})$"
    }
  }
  $ ./lock_base_images.py < images.json
  {
    "python-slim": "docker.io/library/python:3.9.16-slim@sha256:5cde4e147c4165ad8dbf8a4df9631863766eeb0b79b890fafe6885b3b127af74",
    "debian": "docker.io/library/debian:bullseye-20230522@sha256:432f545c6ba13b79e2681f4cc4858788b0ab099fc1cca799cc0fae4687c69070"
  }
"""
from typing import Sequence
import json
import re
import subprocess
import sys


def list_tags(registry) -> Sequence[str]:
    return subprocess.check_output(["crane", "ls", registry]).decode().splitlines()


def lookup_digest(registry, tag) -> str:
    tag_ref = f"{registry}:{tag}"
    digest = subprocess.check_output(["crane", "digest", tag_ref]).decode().strip()
    if not re.match("^sha256:[a-f0-9]{64}$", digest):
        raise ValueError(f"Unexpected digest for {tag_ref}: {digest}")
    return digest


def get_latest_image(constraints):
    available_tags = list_tags(constraints["registry"])
    candidate_tags = [
        m for m in (re.match(constraints["tagRegex"], t) for t in available_tags) if m
    ]
    latest_tag = max(
        candidate_tags, key=lambda m: tuple(int(group) for group in m.groups())
    ).group(0)
    digest = lookup_digest(constraints["registry"], latest_tag)
    return {"registry": constraints["registry"], "tag": latest_tag, "digest": digest}


def format_image_reference(ref):
    return f"{ref['registry']}:{ref['tag']}@{ref['digest']}"


def main():
    base_images = json.load(sys.stdin)
    latest_versions = {
        name: format_image_reference(get_latest_image(constraints))
        for (name, constraints) in base_images.items()
    }
    print(json.dumps(latest_versions, indent=2))


if __name__ == "__main__":
    main()
