import argparse
import json
import re
import subprocess
import sys


STORY_PATTERN = re.compile(r"^US-\d+(?:\.\d+)+:\s")
TASK_PATTERN = re.compile(r"^US-\d+(?:\.\d+)+-T\d+:\s")


def gh(args, input_data=None):
    result = subprocess.run(
        ["gh", *args],
        input=json.dumps(input_data) if input_data is not None else None,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())

    return result.stdout


def api_get(endpoint):
    return json.loads(gh(["api", endpoint]))


def get_subissues(repo, issue_number):
    endpoint = (
        f"repos/{repo}/issues/{issue_number}/sub_issues"
    )

    pages = json.loads(
        gh(["api", "--paginate", "--slurp", endpoint])
    )

    if not pages:
        return []

    # --slurp returns an array containing each page.
    return [
        issue
        for page in pages
        for issue in page
    ]


def update_assignees(repo, issue_number, assignees):
    endpoint = f"repos/{repo}/issues/{issue_number}"

    gh([
        "api",
        endpoint,
        "--method", "PATCH",
        "--input", "-",
    ], input_data={"assignees": assignees})


def sync_story(repo, story_number, apply=False):
    story = api_get(
        f"repos/{repo}/issues/{story_number}"
    )

    title = story["title"]

    # Only process User Stories, never Tasks or Epics.
    if not STORY_PATTERN.match(title):
        print(f"[SKIP] #{story_number}: Not a User Story")
        return 0, 0

    story_assignees = sorted(
        user["login"] for user in story.get("assignees", [])
    )

    children = get_subissues(repo, story_number)

    tasks = [
        child for child in children
        if TASK_PATTERN.match(child["title"])
    ]

    if not tasks:
        print(f"[INFO] {title}: No child Tasks found.")
        return 0, 0

    print(f"\n{title} (#{story_number})")
    print(f"Target assignees: {story_assignees or 'None'}")

    updated = 0
    unchanged = 0

    for task in tasks:
        task_number = task["number"]
        task_title = task["title"]

        current = sorted(
            user["login"] for user in task.get("assignees", [])
        )

        if current == story_assignees:
            print(f"  [OK] #{task_number}: {task_title}")
            unchanged += 1
            continue

        print(
            f"  [{'UPDATE' if apply else 'DRY RUN'}] "
            f"#{task_number}: {task_title}"
        )
        print(f"      Current: {current or 'None'}")
        print(f"      Desired: {story_assignees or 'None'}")

        if apply:
            update_assignees(
                repo,
                task_number,
                story_assignees,
            )
            print("      Applied.")
            updated += 1

    return updated, unchanged


def get_all_stories(repo):
    issues = json.loads(
        gh([
            "issue", "list",
            "--repo", repo,
            "--state", "all",
            "--limit", "1000",
            "--json", "number,title",
        ])
    )

    return [
        issue for issue in issues
        if STORY_PATTERN.match(issue["title"])
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Strictly synchronize Task assignees "
                    "with their parent User Stories."
    )

    parser.add_argument(
        "issue_number",
        nargs="?",
        type=int,
        help="User Story issue number to synchronize.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Synchronize every User Story in the repository.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Without this flag, run a dry run.",
    )

    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation (requires --apply).",
    )

    args = parser.parse_args()

    if args.yes and not args.apply:
        parser.error("--yes requires --apply.")

    if args.all == (args.issue_number is not None):
        parser.error("Provide either an issue number or --all.")

    repo = "httpHadary/TRACE_Technical-Debt-Intelligence-Platform"

    stories = (
        get_all_stories(repo)
        if args.all
        else [{"number": args.issue_number}]
    )

    print(f"Repository: {repo}")
    print(f"User Stories: {len(stories)}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}")

    if args.apply and not args.yes:
        confirmation = input(
            "\nStrict synchronization replaces Task assignees "
            "with parent User Story assignees.\n"
            "Type SYNC to continue: "
        )

        if confirmation != "SYNC":
            print("Cancelled.")
            return

    total_updated = 0
    total_unchanged = 0
    failed = []

    for story in stories:
        number = story["number"]

        try:
            updated, unchanged = sync_story(
                repo,
                number,
                apply=args.apply,
            )
            total_updated += updated
            total_unchanged += unchanged

        except Exception as error:
            failed.append((number, str(error)))
            print(f"[FAILED] User Story #{number}: {error}")

    print("\nSynchronization summary")
    print("-----------------------")
    print(f"Updated:   {total_updated}")
    print(f"Unchanged: {total_unchanged}")
    print(f"Failed:    {len(failed)}")

    if failed:
        sys.exit(1)

    if not args.apply:
        print("\nDry run only. No GitHub issues were modified.")


if __name__ == "__main__":
    main()
