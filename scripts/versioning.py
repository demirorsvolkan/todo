#!/usr/bin/env python3

import re
import subprocess


COMPONENTS = {
    "backend": "backend",
    "frontend": "frontend",
}


def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_latest_tag(component):
    """
    Only supports the tag format:

        frontend/v2.0.7-sha.abcdef1
        backend/v2.0.7-sha.abcdef1

    Version tags without 'v' are NOT accepted.
    """

    tags = run_git(
        "tag",
        "--list",
        f"{component}/*",
    ).splitlines()

    versioned_tags = []

    for tag in tags:
        match = re.search(
            r"/v(\d+)\.(\d+)\.(\d+)(?:-sha\.[0-9a-fA-F]+)?$",
            tag,
        )

        if match:
            version = tuple(map(int, match.groups()))
            versioned_tags.append((version, tag))

    if not versioned_tags:
        return None

    return max(versioned_tags, key=lambda item: item[0])[1]


def get_tag_commit(tag):
    return run_git(
        "rev-list",
        "-n",
        "1",
        tag,
    )


def get_component_changes(tag, component):
    path = COMPONENTS[component]

    if tag:
        output = run_git(
            "diff",
            "--name-only",
            tag,
            "HEAD",
            "--",
            path,
        )
    else:
        output = run_git(
            "ls-files",
            path,
        )

    return output.splitlines() if output else []


def get_component_commits(tag, component):
    path = COMPONENTS[component]

    if tag:
        return run_git(
            "log",
            f"{tag}..HEAD",
            "--format=%H%n%s%n%b",
            "--",
            path,
        )

    return run_git(
        "log",
        "--format=%H%n%s%n%b",
        "--",
        path,
    )


def get_bump(commits):
    """
    Conventional Commit rules:

    feat:       -> minor
    fix:        -> patch
    perf:       -> patch
    feat!:      -> major
    fix!:       -> major
    perf!:      -> major
    BREAKING CHANGE -> major
    Everything else -> none
    """

    if not commits.strip():
        return "none"

    if re.search(
        r"BREAKING[ -]CHANGE",
        commits,
        re.IGNORECASE,
    ):
        return "major"

    if re.search(
        r"(^|\n)(feat|fix|perf)(\([^)\n]+\))?!:",
        commits,
        re.IGNORECASE,
    ):
        return "major"

    if re.search(
        r"(^|\n)feat(\([^)\n]+\))?:",
        commits,
        re.IGNORECASE,
    ):
        return "minor"

    if re.search(
        r"(^|\n)(fix|perf)(\([^)\n]+\))?:",
        commits,
        re.IGNORECASE,
    ):
        return "patch"

    return "none"


def parse_version(tag):
    if not tag:
        return (0, 0, 0)

    match = re.search(
        r"/v(\d+)\.(\d+)\.(\d+)",
        tag,
    )

    if not match:
        raise ValueError(
            f"Invalid version tag: {tag}"
        )

    return tuple(map(int, match.groups()))


def next_version(current, bump):
    major, minor, patch = current

    if bump == "major":
        return f"v{major + 1}.0.0"

    if bump == "minor":
        return f"v{major}.{minor + 1}.0"

    if bump == "patch":
        return f"v{major}.{minor}.{patch + 1}"

    return None


def analyze_component(component):
    latest_tag = get_latest_tag(component)

    changes = get_component_changes(
        latest_tag,
        component,
    )

    commits = get_component_commits(
        latest_tag,
        component,
    )

    bump = get_bump(commits)

    if not changes:
        release = False
        version = None

    elif not latest_tag:
        release = True
        version = "v1.0.0"

    elif bump == "none":
        release = False
        version = None

    else:
        release = True
        version = next_version(
            parse_version(latest_tag),
            bump,
        )

    return {
        "release": release,
        "version": version,
        "bump": bump,
        "previous_tag": latest_tag,
        "previous_commit": (
            get_tag_commit(latest_tag)
            if latest_tag
            else ""
        ),
        "changed_files": len(changes),
    }


def main():
    for component in COMPONENTS:
        result = analyze_component(component)

        print(
            f"{component}_release="
            f"{str(result['release']).lower()}"
        )

        print(
            f"{component}_version="
            f"{result['version'] or ''}"
        )

        print(
            f"{component}_bump="
            f"{result['bump']}"
        )

        print(
            f"{component}_previous_tag="
            f"{result['previous_tag'] or ''}"
        )

        print(
            f"{component}_previous_commit="
            f"{result['previous_commit']}"
        )

        print(
            f"{component}_changed_files="
            f"{result['changed_files']}"
        )


if __name__ == "__main__":
    main()

