import json
import re
import subprocess
import time


SEARCH_URL = (
    "https://www.linkedin.com/jobs/search-results/"
    "?keywords=Java%20Engineer"
)


def run_agent_browser(*args):
    command = ["npx", "agent-browser", *args]

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


def get_snapshot_json(retries=5, delay=2):
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
    if " (Verified job)" in name:
        return name.split(" (Verified job)")[0].strip()

    match = re.search(
        r"Dismiss (.+?) job",
        name,
    )

    if match:
        return match.group(1).strip()

    return name.strip()


def find_first_five_titles(snapshot):
    refs = snapshot["data"]["refs"]

    titles = []

    for _, info in refs.items():
        if info.get("role") != "button":
            continue

        name = info.get("name", "")

        if not name:
            continue

        if "Dismiss " not in name:
            continue

        if name.startswith("Dismiss "):
            continue

        if " job" not in name:
            continue

        title = extract_title_from_button_name(name)

        if title not in titles:
            titles.append(title)

        if len(titles) == 5:
            break

    return titles


def find_current_ref_for_title(snapshot, title):
    refs = snapshot["data"]["refs"]

    for ref, info in refs.items():
        if info.get("role") != "button":
            continue

        name = info.get("name", "")

        if not name:
            continue

        if name.startswith("Dismiss "):
            continue

        current_title = extract_title_from_button_name(
            name
        )

        if current_title == title:
            return ref

    return None


def extract_selected_job(snapshot, expected_title):
    snapshot_text = snapshot["data"]["snapshot"]

    pattern = re.compile(
        r'link "([^"]+)" '
        r'\[ref=e\d+, '
        r'url=(https://www\.linkedin\.com/jobs/view/\d+/[^]]*)\]'
    )

    matches = pattern.findall(snapshot_text)

    for title, url in matches:
        clean_match = re.match(
            r"(https://www\.linkedin\.com/jobs/view/\d+/)",
            url,
        )

        if clean_match:
            url = clean_match.group(1)

        if title == expected_title:
            return title, url

    return None


def click_job_safely(ref):
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


def main():
    print("=" * 60)
    print("LinkedIn Java Engineer Job Search")
    print("=" * 60)

    print("\nOpening LinkedIn job search...")

    run_agent_browser(
        "open",
        SEARCH_URL,
        "--headed",
    )

    run_agent_browser(
        "wait",
        "--load",
        "domcontentloaded",
    )

    time.sleep(2)

    print("Reading job results...")

    initial_snapshot = get_snapshot_json()

    titles = find_first_five_titles(
        initial_snapshot
    )

    if not titles:
        print("No job results found.")
        return

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
            # Fresh snapshot every time.
            snapshot = get_snapshot_json()

            ref = find_current_ref_for_title(
                snapshot,
                title,
            )

            if not ref:
                print(
                    "Could not find current ref."
                )
                continue

            success = click_job_safely(ref)

            if not success:
                # Re-snapshot once and retry.
                snapshot = get_snapshot_json()

                ref = find_current_ref_for_title(
                    snapshot,
                    title,
                )

                if not ref:
                    print(
                        "Could not find ref after retry."
                    )
                    continue

                run_agent_browser(
                    "scrollintoview",
                    f"@{ref}",
                )

                time.sleep(1)

                run_agent_browser(
                    "click",
                    f"@{ref}",
                )

            # Give LinkedIn time to update right panel.
            time.sleep(2)

            selected_job = None

            # Retry detail extraction a few times.
            for _ in range(4):
                detail_snapshot = get_snapshot_json()

                selected_job = extract_selected_job(
                    detail_snapshot,
                    title,
                )

                if selected_job:
                    break

                time.sleep(1)

            if not selected_job:
                print(
                    "Could not find job detail link."
                )
                continue

            results.append(selected_job)

        except Exception as error:
            print(
                f"Could not read job {index}: {error}"
            )

    print("\n" + "=" * 60)
    print("Top Java Engineer Jobs")
    print("=" * 60)

    if not results:
        print(
            "No job links could be extracted."
        )
        return

    for index, (title, url) in enumerate(
        results,
        start=1,
    ):
        print(f"\n{index}. {title}")
        print(f"   {url}")


if __name__ == "__main__":
    main()