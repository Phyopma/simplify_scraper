import requests
import json
import time
import math
import argparse
import os

# Base URL
base_url = "https://api.simplify.jobs/v2/candidate/me/tracker/"

# Non-sensitive headers (kept in script)
headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "origin": "https://simplify.jobs"
}

# Load sensitive headers from config.json
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    # Add sensitive headers
    headers["cookie"] = config.get("cookie", "")
    headers["x-csrf-token"] = config.get("x-csrf-token", "")
except FileNotFoundError:
    print("Error: config.json not found. Please create it using config.json.sample and fill in your credentials.")
    # Generate sample config file if it doesn't exist
    sample_config = {
        "cookie": "YOUR_AUTHORIZATION_AND_CSRF_TOKEN_HERE",
        "x-csrf-token": "YOUR_X_CSRF_TOKEN_HERE"
    }

    if not os.path.exists('config.json.sample'):
        with open('config.json.sample', 'w') as sample_file:
            json.dump(sample_config, sample_file, indent=2)
        print("Generated config.json.sample. Please fill it with your credentials and save as config.json.")

    exit(1)
except json.JSONDecodeError:
    print("Error: config.json is invalid JSON. Please check the file format.")
    exit(1)

# Mapping of job types to their API values
JOB_TYPE_MAP = {
    "internship": 1,  # Internship = 1
    "part-time": 3,   # Part-time = 3
    "full-time": 2    # Full-time = 2 (assumed)
}

# Mapping of status to their API values
STATUS_MAP = {
    "applied": 2,     # Status = 2
    "saved": 1,       # Status = 1
    "screen": 11,     # Status = 11
    "interview": 12,  # Status = 12
    "offer": 13,      # Status = 13
    "withdrawn": 21,  # Status = 21
    "ghosted": 22,    # Status = 22
    "rejected": 23,   # Status = 23
    "accepted": 24    # Status = 24
}


def fetch_data(params):
    """Fetch data from the API with dynamic pagination."""
    all_items = []

    # Fetch first page to determine total pages
    params["page"] = 0
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code != 200:
        print(
            f"Failed to fetch first page: {response.status_code} - {response.text}")
        return None

    first_page_data = response.json()
    total_items = first_page_data["total"]
    items_per_page = params["size"]
    total_pages = math.ceil(total_items / items_per_page)
    all_items.extend(first_page_data["items"])

    print(
        f"Total items (filtered): {total_items}, Items per page: {items_per_page}, Total pages: {total_pages}")

    # Fetch remaining pages
    for page in range(1, total_pages):
        print(f"Fetching page {page} of {total_pages - 1}...")
        params["page"] = page
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            all_items.extend(data["items"])
        else:
            print(
                f"Error on page {page}: {response.status_code} - {response.text}")
            break

        time.sleep(1)  # Avoid rate limiting

    return {"total": total_items, "items": all_items}


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Fetch job tracker data from Simplify Jobs API.")
    parser.add_argument("--all", action="store_true",
                        help="Fetch all data without filters.")
    parser.add_argument(
        "--after", type=str, help="Start date (e.g., 2025-03-01) for date_applied_after.")
    parser.add_argument(
        "--before", type=str, help="End date (e.g., 2025-03-07) for date_applied_before.")
    parser.add_argument(
        "--job-type",
        type=str,
        choices=["internship", "part-time", "full-time"],
        help="Job type filter: internship (1), part-time (3), full-time (2)."
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["applied", "saved", "screen", "interview", "offer",
                 "withdrawn", "ghosted", "rejected", "accepted"],
        help="Status filter: applied (2), saved (1), screen (11), interview (12), offer (13), withdrawn (21), ghosted (22), rejected (23), accepted (24)."
    )
    args = parser.parse_args()

    # Base parameters
    params = {
        "size": 25,
        "value": "",
        "archived": "false"
    }

    # Apply filters based on arguments (case-insensitive)
    if not args.all:
        if args.after:
            params["date_applied_after"] = f"{args.after}T00:00:00.000Z"
        if args.before:
            params["date_applied_before"] = f"{args.before}T23:59:59.999Z"
        if args.job_type:
            job_type = args.job_type.lower()  # Case-insensitive
            params["job_type"] = JOB_TYPE_MAP[job_type]
            print(
                f"Filtering by job_type: {job_type} (job_type={params['job_type']})")
        if args.status:
            status = args.status.lower()  # Case-insensitive
            params["status"] = STATUS_MAP[status]
            print(f"Filtering by status: {status} (status={params['status']})")
    else:
        print("Fetching all data without filters...")

    # Fetch data
    data = fetch_data(params)
    if data:
        with open("tracker_data.json", "w") as f:
            json.dump(data, f, indent=2)
        print(
            f"Done! Retrieved {len(data['items'])} items. Data saved to tracker_data.json")
    else:
        print("Failed to retrieve data.")


if __name__ == "__main__":
    main()
