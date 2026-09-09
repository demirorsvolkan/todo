#!/usr/bin/env python3

import re
import subprocess
import sys


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
    tags = run_git(
        "tag",
        "--list",
        f"{component}/v*",
    ).splitlines()

    if not tags:
        return None

    def version_key(tag):
        match = re.search(r"/v(\d+)\.(\d+)\.(\d+)", tag)
        if not match:
            return (0, 0, 0)

        return tuple(map(int, match.groups()))

    return max(tags, key=version_key)


def get_tag_commit(tag):
    return run_git("rev-list", "-n", "1", tag)


def get_commits_since(tag):
    if tag:
        return run_git(
            "log",
            f"{tag}..HEAD",
            "--format=%H%n%s%n%b",
        )

    return run_git(
        "log",
        "--format=%H%n%s%n%b",
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
    if not commits.strip():
        return "none"

    # Explicit breaking-change footer
    if re.search(
        r"BREAKING CHANGE|BREAKING-CHANGE",
        commits,
        re.IGNORECASE,
    ):
        return "major"

    # Conventional Commits breaking-change marker: feat!: / fix!: / perf!:
    if re.search(
        r"(^|\n)(feat|fix|perf)(\(.+?\))?!:",
        commits,
        re.IGNORECASE,
    ):
        # The ! must be present immediately before the colon.
        if re.search(
            r"(^|\n)(feat|fix|perf)(\(.+?\))?!:",
            commits,
            re.IGNORECASE,
        ):
            matches = re.findall(
                r"(^|\n)(feat|fix|perf)(\(.+?\))?!:",
                commits,
                re.IGNORECASE,
            )
            if matches:
                return "major"

    if re.search(
        r"(^|\n)feat(\(.+?\))?:",
        commits,
        re.IGNORECASE,
    ):
        return "minor"

    if re.search(
        r"(^|\n)(fix|perf)(\(.+?\))?:",
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
        raise ValueError(f"Invalid version tag: {tag}")

    return tuple(map(int, match.groups()))


def next_version(current, bump):
    major, minor, patch = current

    if bump == "major":
        return f"{major + 1}.0.0"

    if bump == "minor":
        return f"{major}.{minor + 1}.0"

    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"

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
        version = "1.0.0"

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