import json
import os
import re
import subprocess
import time
from urllib.parse import quote


PROFILE_PATH = os.path.expanduser(
    "~/.agent-browser-linkedin"
)


def build_search_url(keyword):
    """
    Build a LinkedIn job search URL.
    """
    encoded_keyword = quote(keyword)

    return (
        "https://www.linkedin.com/jobs/search-results/"
        f"?keywords={encoded_keyword}"
    )


def run_agent_browser(*args):
    """
    Run agent-browser using the persistent LinkedIn profile.
    """
    command = [
        "npx",
        "agent-browser",
        "--profile",
        PROFILE_PATH,
        *args,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "agent-browser command failed.\n"
            f"Command: {' '.join(command)}\n"
            f"Return code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout


def get_snapshot_json(retries=8, delay=2):
    """
    Get accessibility snapshot as JSON.

    Retry when agent-browser is temporarily busy.
    """
    last_error = None

    for attempt in range(retries):
        try:
            output = run_agent_browser(
                "snapshot",
                "-i",
                "--urls",
                "--json",
            )

            data = json.loads(output)

            if not data.get("success"):
                raise RuntimeError(
                    "Snapshot returned success=false."
                )

            return data

        except Exception as error:
            last_error = error

            print(
                f"Snapshot attempt {attempt + 1} failed."
            )

            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(delay)

    raise RuntimeError(
        f"Could not get snapshot.\n{last_error}"
    )


def extract_title_from_button_name(name):
    """
    Extract a cleaner job title from a LinkedIn job result.
    """
    if " (Verified job)" in name:
        return name.split(
            " (Verified job)"
        )[0].strip()

    match = re.search(
        r"Dismiss (.+?) job",
        name,
    )

    if match:
        return match.group(1).strip()

    return name.strip()


def find_job_titles(snapshot, limit=5):
    """
    Find the first N job titles from search results.
    """
    refs = snapshot["data"]["refs"]

    titles = []

    for _, info in refs.items():
        role = info.get("role", "")
        name = info.get("name", "")

        if role != "button":
            continue

        if not name:
            continue

        if "Dismiss " not in name:
            continue

        if name.startswith("Dismiss "):
            continue

        if " job" not in name:
            continue

        title = extract_title_from_button_name(
            name
        )

        if title not in titles:
            titles.append(title)

        if len(titles) >= limit:
            break

    return titles


def find_current_ref_for_title(snapshot, title):
    """
    Find the current accessibility ref for a job title.
    """
    refs = snapshot["data"]["refs"]

    for ref, info in refs.items():
        if info.get("role") != "button":
            continue

        name = info.get("name", "")

        if not name:
            continue

        if name.startswith("Dismiss "):
            continue

        if " job" not in name:
            continue

        current_title = extract_title_from_button_name(
            name
        )

        if current_title == title:
            return ref

    return None


def extract_selected_job(snapshot, expected_title):
    """
    Extract selected job title and LinkedIn job URL
    from the job detail panel.
    """
    snapshot_text = snapshot["data"]["snapshot"]

    pattern = re.compile(
        r'link "([^"]+)" '
        r'\[ref=e\d+, '
        r'url=(https://www\.linkedin\.com/jobs/view/\d+/[^]]*)\]'
    )

    matches = pattern.findall(
        snapshot_text
    )

    for title, url in matches:
        if title != expected_title:
            continue

        clean_match = re.match(
            r"(https://www\.linkedin\.com/jobs/view/\d+/)",
            url,
        )

        if clean_match:
            url = clean_match.group(1)

        return {
            "title": title,
            "url": url,
        }

    return None


def click_job_safely(ref):
    """
    Scroll to and click a job result.
    """
    try:
        run_agent_browser(
            "scrollintoview",
            f"@{ref}",
        )

        time.sleep(0.5)

        run_agent_browser(
            "click",
            f"@{ref}",
        )

        return True

    except Exception as error:
        print(
            f"Normal click failed: {error}"
        )

        return False


def check_login_status():
    """
    Check whether the LinkedIn profile is logged in.
    """
    try:
        run_agent_browser(
            "open",
            "https://www.linkedin.com/jobs/",
            "--headed",
        )

    except Exception:
        print(
            "Login check open timed out."
        )
        print(
            "The page may still have opened."
        )

    time.sleep(3)

    try:
        run_agent_browser(
            "wait",
            "--load",
            "domcontentloaded",
        )

    except Exception:
        print(
            "Login page load wait timed out."
        )

    time.sleep(2)

    snapshot = get_snapshot_json()

    refs = snapshot["data"]["refs"]

    for _, info in refs.items():
        name = info.get(
            "name",
            "",
        ).lower()

        if (
            "sign in" in name
            or "邮箱或手机" in name
            or name == "登录"
        ):
            return False

    return True


def search_linkedin_jobs(
    keyword,
    limit=5,
):
    """
    Search LinkedIn jobs using agent-browser.

    Args:
        keyword:
            Example: "Java Engineer"

        limit:
            Maximum number of jobs to return.

    Returns:
        [
            {
                "title": "...",
                "url": "..."
            }
        ]
    """
    print(
        f"\nSearching LinkedIn for: {keyword}"
    )

    print(
        f"Requested jobs: {limit}"
    )

    search_url = build_search_url(
        keyword
    )

    # LinkedIn can load slowly.
    # A timeout does not always mean navigation failed.
    try:
        run_agent_browser(
            "open",
            search_url,
            "--headed",
        )

    except Exception:
        print(
            "Open command timed out."
        )
        print(
            "The page may still have opened."
        )

    time.sleep(3)

    try:
        run_agent_browser(
            "wait",
            "--load",
            "domcontentloaded",
        )

    except Exception:
        print(
            "Page load wait timed out."
        )
        print(
            "Continuing..."
        )

    time.sleep(3)

    print(
        "Checking current page..."
    )

    try:
        current_url = run_agent_browser(
            "get",
            "url",
        ).strip()

        print(
            f"Current URL: {current_url}"
        )

    except Exception as error:
        print(
            f"Could not get current URL: {error}"
        )

    print(
        "Reading job results..."
    )

    try:
        initial_snapshot = (
            get_snapshot_json()
        )

    except Exception as error:
        print(
            f"Could not read LinkedIn page: {error}"
        )
        return []

    titles = find_job_titles(
        initial_snapshot,
        limit,
    )

    if not titles:
        print(
            "No job results found."
        )
        return []

    print(
        f"Found {len(titles)} candidate jobs."
    )

    results = []

    for index, title in enumerate(
        titles,
        start=1,
    ):
        print(
            f"\nReading job {index}: {title}"
        )

        try:
            # Fresh snapshot every time,
            # because refs can change.
            snapshot = (
                get_snapshot_json()
            )

            ref = (
                find_current_ref_for_title(
                    snapshot,
                    title,
                )
            )

            if not ref:
                print(
                    "Could not find current ref."
                )
                continue

            success = click_job_safely(
                ref
            )

            if not success:
                print(
                    "Refreshing snapshot and retrying..."
                )

                snapshot = (
                    get_snapshot_json()
                )

                ref = (
                    find_current_ref_for_title(
                        snapshot,
                        title,
                    )
                )

                if not ref:
                    print(
                        "Could not find ref after retry."
                    )
                    continue

                try:
                    run_agent_browser(
                        "scrollintoview",
                        f"@{ref}",
                    )

                    time.sleep(1)

                    run_agent_browser(
                        "click",
                        f"@{ref}",
                    )

                except Exception as error:
                    print(
                        f"Retry click failed: {error}"
                    )
                    continue

            # Give right-side detail panel time to load.
            time.sleep(2)

            selected_job = None

            for _ in range(5):
                detail_snapshot = (
                    get_snapshot_json()
                )

                selected_job = (
                    extract_selected_job(
                        detail_snapshot,
                        title,
                    )
                )

                if selected_job:
                    break

                time.sleep(1)

            if not selected_job:
                print(
                    "Could not find job detail link."
                )
                continue

            results.append(
                selected_job
            )

        except Exception as error:
            print(
                f"Could not read {title}: {error}"
            )

    return results


def print_results(jobs):
    """
    Print extracted job results.
    """
    print(
        "\n" + "=" * 60
    )

    print(
        "LinkedIn Job Results"
    )

    print(
        "=" * 60
    )

    if not jobs:
        print(
            "No jobs could be extracted."
        )
        return

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        print(
            f"\n{index}. {job['title']}"
        )

        print(
            f"   {job['url']}"
        )


def main():
    """
    Standalone test.

    Later the AI Agent will call
    search_linkedin_jobs() directly.
    """
    print(
        "=" * 60
    )

    print(
        "LinkedIn Job Search Tool"
    )

    print(
        "=" * 60
    )

    print(
        "\nChecking LinkedIn login..."
    )

    try:
        logged_in = check_login_status()

    except Exception as error:
        print(
            f"Could not check login status:\n{error}"
        )
        return

    if not logged_in:
        print(
            "\nLinkedIn is not logged in."
        )

        print(
            "Run this command and log in manually:"
        )

        print(
            "\nnpx agent-browser "
            "--profile ~/.agent-browser-linkedin "
            "open https://www.linkedin.com "
            "--headed"
        )

        return

    print(
        "LinkedIn login detected."
    )

    jobs = search_linkedin_jobs(
        keyword="Java Engineer",
        limit=5,
    )

    print_results(
        jobs
    )


if __name__ == "__main__":
    main()