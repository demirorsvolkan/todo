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
    Supported tag formats:

        frontend/v2.0.7
        frontend/v2.0.7-sha.abcdef1

        backend/v2.0.7
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

    return max(
        versioned_tags,
        key=lambda item: item[0],
    )[1]


def get_tag_commit(tag):
    return run_git(
        "rev-list",
        "-n",
        "1",
        tag,
    )


def get_component_changes(tag, component):
    """
    Checks whether the component has any actual file changes
    since the latest component tag.
    """

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
    """
    Returns commits affecting the component in chronological order.

    Each commit contains:

        hash
        subject
        body

    Chronological order is required because a later revert can
    cancel the effect of an earlier commit.
    """

    path = COMPONENTS[component]

    revision = f"{tag}..HEAD" if tag else "HEAD"

    output = run_git(
        "log",
        "--reverse",
        revision,
        "--format=%H%x1f%s%x1f%b%x1e",
        "--",
        path,
    )

    if not output:
        return []

    commits = []

    for record in output.split("\x1e"):
        record = record.strip()

        if not record:
            continue

        parts = record.split("\x1f", 2)

        if len(parts) != 3:
            continue

        commit_hash, subject, body = parts

        commits.append(
            {
                "hash": commit_hash.strip().lower(),
                "subject": subject.strip(),
                "body": body.strip(),
            }
        )

    return commits


def get_reverted_commit_hash(commit):
    """
    Detects the commit targeted by a standard `git revert`.

    Standard Git output contains:

        This reverts commit <SHA>.

    Returns the SHA or None.
    """

    match = re.search(
        r"This reverts commit\s+([0-9a-fA-F]{7,40})\.?",
        commit["body"],
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).lower()


def find_commit(commits_by_hash, short_hash):
    """
    Finds a commit using either its full SHA or an abbreviated SHA.
    """

    short_hash = short_hash.lower()

    if short_hash in commits_by_hash:
        return commits_by_hash[short_hash]

    matches = [
        commit
        for commit_hash, commit in commits_by_hash.items()
        if commit_hash.startswith(short_hash)
        or short_hash.startswith(commit_hash)
    ]

    if len(matches) == 1:
        return matches[0]

    return None


def resolve_original_commit(
    target_commit,
    commits_by_hash,
    visited=None,
):
    """
    Resolves a revert chain back to the original non-revert commit.

    Example:

        feat A
        Revert feat A
        Revert Revert feat A

    The second revert targets the first revert commit.
    This function resolves that chain back to `feat A`.
    """

    if visited is None:
        visited = set()

    target_hash = target_commit["hash"]

    if target_hash in visited:
        return None

    visited.add(target_hash)

    reverted_hash = get_reverted_commit_hash(target_commit)

    if not reverted_hash:
        return target_commit

    parent = find_commit(
        commits_by_hash,
        reverted_hash,
    )

    if not parent:
        return None

    return resolve_original_commit(
        parent,
        commits_by_hash,
        visited,
    )


def get_active_commits(commits):
    """
    Determines which original commits are still active after
    applying all revert operations.

    Normal commit:
        active

    Revert commit:
        toggles the activity of the original commit it reverts

    Revert of a revert:
        activates the original commit again

    Revert commits themselves never participate in version bumping.
    """

    commits_by_hash = {
        commit["hash"]: commit
        for commit in commits
    }

    active_commits = {}

    for commit in commits:
        reverted_hash = get_reverted_commit_hash(commit)

        # Normal commit
        if not reverted_hash:
            active_commits[commit["hash"]] = commit
            continue

        # Revert commit
        target = find_commit(
            commits_by_hash,
            reverted_hash,
        )

        if not target:
            # Not a standard/recognizable revert target.
            # Ignore it for version calculation.
            continue

        original = resolve_original_commit(
            target,
            commits_by_hash,
        )

        if not original:
            continue

        original_hash = original["hash"]

        # Toggle the original commit.
        if original_hash in active_commits:
            del active_commits[original_hash]
        else:
            active_commits[original_hash] = original

    return list(active_commits.values())


def get_bump(commits):
    """
    Conventional Commit rules:

    feat:               -> minor
    fix:                -> patch
    perf:               -> patch

    feat!:              -> major
    fix!:               -> major
    perf!:              -> major

    BREAKING CHANGE     -> major

    Everything else     -> none
    """

    if not commits:
        return "none"

    commit_text = "\n".join(
        f"{commit['subject']}\n{commit['body']}"
        for commit in commits
    )

    # BREAKING CHANGE has the highest priority.
    if re.search(
        r"BREAKING[ -]CHANGE",
        commit_text,
        re.IGNORECASE,
    ):
        return "major"

    # Conventional Commit with !.
    if re.search(
        r"(^|\n)(feat|fix|perf)(\([^)\n]+\))?!:",
        commit_text,
        re.IGNORECASE,
    ):
        return "major"

    # feat -> minor.
    if re.search(
        r"(^|\n)feat(\([^)\n]+\))?:",
        commit_text,
        re.IGNORECASE,
    ):
        return "minor"

    # fix / perf -> patch.
    if re.search(
        r"(^|\n)(fix|perf)(\([^)\n]+\))?:",
        commit_text,
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

    # No actual component changes since the previous tag.
    #
    # Example:
    #
    #   feat
    #   Revert feat
    #
    # If nothing else changed in the component, the final
    # filesystem state is the same as the previous tag.
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

    commits = get_component_commits(
        latest_tag,
        component,
    )

    # Remove the effects of reverted commits.
    active_commits = get_active_commits(commits)

    bump = get_bump(active_commits)

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