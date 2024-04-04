#!/usr/bin/env python3
#
# (C) 2024 Jonathan Whitten
#
# Licensed under MIT License only.
# See LICENSE for more information.
#

import os
from tqdm import tqdm
import requests
import getpass

# Set up Environment Variables
CURRENT_USER = getpass.getuser()
BASE_PATH = f"C:/Users/{CURRENT_USER}/Downloads"

# Set up your repository here
OWNER="<OWNER_NAME>"
REPO="<REPO_NAME>"
BRANCH="<BRANCH_NAME>" # eg, master, main, etc.
WORKFLOW_NAME="<WORKFLOW_YML_FILE>"
WORKFLOW_EVENT="<WORKFLOW_EVENT_TYPE>" # eg, push, pull_request, etc.
ARTIFACT_FILE = f"{BASE_PATH}/<YOUR_ARTIFACT_NAME>"
FILE_TYPE = "zip"

# GitHub PAT
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
# If the GitHub token is not found, ask the user for it
if GITHUB_TOKEN is None:
    print("GitHub PAT (Personal Access Token) not found in environment variables.")
    GITHUB_TOKEN = input("*** THIS WILL NOT BE SAVED *** Enter your GitHub PAT: ")
    # Python cannot save Environment variables to Windows.  User must do it manually.
    print("Reminder: Enter your GitHub PAT as a Windows Environment variable named 'GITHUB_TOKEN' if you'd like to skip this step in the future.")

# Constants
API_URL="https://api.github.com"
HEADER = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
        }

def get_workflow_id(workflow_name):
    response = requests.get(f"{API_URL}/repos/{OWNER}/{REPO}/actions/workflows/{workflow_name}", headers=HEADER)
    response.raise_for_status()
    return response.json()['id']

def get_latest_workflow_run_id(workflow_id, workflow_event):
    response = requests.get(f"{API_URL}/repos/{OWNER}/{REPO}/actions/workflows/{workflow_id}/runs", headers=HEADER)
    json = response.json()
    for workflow_run in json['workflow_runs']:

        # Only consider completed runs
        if workflow_run['status'] != "completed":
            continue
        if workflow_run['conclusion'] != "success":
            continue

        # Match by BRANCH
        if workflow_run['head_branch'] != BRANCH:
            continue

        # Match by event
        if workflow_run['event'] != workflow_event:
            continue

        return workflow_run['id']

    return None #FIXME: Exception

def get_artifact_id(workflow_run_id, name):
    response = requests.get(f"{API_URL}/repos/{OWNER}/{REPO}/actions/runs/{workflow_run_id}/artifacts", headers=HEADER)
    json = response.json()

    for artifact in json['artifacts']:
        # Match by name
        if artifact['name'] == name:
            return artifact['id']

    return None #FIXME: Exception

def get_latest_artifact_url(workflow_name, worfklow_event, artifact_name):
    workflow_id = get_workflow_id(workflow_name)
    print(f"found workflow {workflow_id}")

    workflow_run_id = get_latest_workflow_run_id(workflow_id, worfklow_event)
    print(f"found workflow_run_id {workflow_run_id}")

    artifact_id = get_artifact_id(workflow_run_id, artifact_name)
    print(f"found artifact_id {workflow_run_id}")

    latest_artifact_url = f"{API_URL}/repos/{OWNER}/{REPO}/actions/artifacts/{artifact_id}/{FILE_TYPE}"
    print(latest_artifact_url)

    return latest_artifact_url

def download_with_progress_bar():
    # Initialize tqdm with the total file size
    with open(ARTIFACT_FILE, "wb") as file, tqdm(
        desc=ARTIFACT_FILE,
        total=int(response.headers.get("content-length", 0)),
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            # Write data to the file
            file.write(data)
            # Update the progress bar
            progress_bar.update(len(data))


if __name__ == "__main__":
    artifact_url = get_latest_artifact_url(WORKFLOW_NAME, WORKFLOW_EVENT, ARTIFACT_FILE)

    # Send a GET request to the URL with custom headers
    response = requests.get(artifact_url, headers=HEADER, stream=True)

    # Download the artifact file with a progress bar
    download_with_progress_bar()

    print("Artifact downloaded successfully.")
