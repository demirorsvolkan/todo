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
            "--format=%H%n%s%n%b%n---COMMIT---",
            "--",
            path,
        )

    return run_git(
        "log",
        "--format=%H%n%s%n%b%n---COMMIT---",
        "--",
        path,
    )


def get_reverted_commit_hash(commit):
    """
    Returns the commit hash targeted by a Git revert commit.

    Example:

        This reverts commit abc123456789...
    """

    match = re.search(
        r"This reverts commit\s+([0-9a-fA-F]{7,40})",
        commit,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def get_commit_hash(commit):
    lines = commit.splitlines()

    if not lines:
        return None

    return lines[0].strip()


def get_active_commits(commits):
    """
    Processes commits from oldest to newest.

    Normal commits are added as active.

    Revert commits remove the targeted commit from the
    active set.

    Revert-of-revert does NOT reactivate the original commit.
    """

    if not commits.strip():
        return []

    records = [
        record.strip()
        for record in commits.split("---COMMIT---")
        if record.strip()
    ]

    active_commits = {}

    # git log returns newest -> oldest.
    # Revert processing must happen oldest -> newest.
    for record in reversed(records):
        commit_hash = get_commit_hash(record)

        if not commit_hash:
            continue

        reverted_hash = get_reverted_commit_hash(record)

        if reverted_hash:
            try:
                reverted_hash = run_git(
                    "rev-parse",
                    reverted_hash,
                )
            except subprocess.CalledProcessError:
                continue

            # A revert only removes the targeted commit.
            # It never adds/reactivates anything.
            active_commits.pop(
                reverted_hash,
                None,
            )

            continue

        active_commits[commit_hash] = record

    return list(active_commits.values())


def get_bump(commits):
    """
    Conventional Commit rules:

    feat:               -> minor
    fix:                -> patch
    perf:               -> patch
    feat!:              -> major
    fix!:              -> major
    perf!:              -> major
    BREAKING CHANGE     -> major
    Everything else     -> none

    Reverted commits are ignored.
    """

    active_commits = get_active_commits(commits)

    if not active_commits:
        return "none"

    active_text = "\n".join(active_commits)

    if re.search(
        r"BREAKING[ -]CHANGE",
        active_text,
        re.IGNORECASE,
    ):
        return "major"

    if re.search(
        r"(^|\n)(feat|fix|perf)(\([^)\n]+\))?!:",
        active_text,
        re.IGNORECASE,
    ):
        return "major"

    if re.search(
        r"(^|\n)feat(\([^)\n]+\))?:",
        active_text,
        re.IGNORECASE,
    ):
        return "minor"

    if re.search(
        r"(^|\n)(fix|perf)(\([^)\n]+\))?:",
        active_text,
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

    # No changes since the previous tag:
    # no need to inspect commit history or calculate a bump.
    if not changes:
        return {
            "release": False,
            "version": None,
            "bump": "none",
            "previous_tag": latest_tag,
            "previous_commit": (
                get_tag_commit(latest_tag)
                if latest_tag
                else ""
            ),
            "changed_files": 0,
        }

    # Only inspect commit history when there are actual
    # changes in this component.
    commits = get_component_commits(
        latest_tag,
        component,
    )

    bump = get_bump(commits)

    if not latest_tag:
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