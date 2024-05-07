import datetime
import os
import boto3
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Personal variables
GITLAB_BASE_URL = os.getenv("GITLAB_BASE_URL")
STALE_DAYS_THRESHOLD = int(os.getenv("STALE_DAYS_THRESHOLD"))
FALLBACK_CHANNEL_ID = os.getenv("FALLBACK_CHANNEL_ID")
INTERNAL_EMAIL_DOMAINS = (
    os.getenv("INTERNAL_EMAIL_DOMAINS").split(", ")
    if os.getenv("INTERNAL_EMAIL_DOMAINS")
    else []
)
EXCLUDE_GROUPS = (
    os.getenv("EXCLUDE_GROUPS").split(", ") if os.getenv("EXCLUDE_GROUPS") else []
)

# GitLab provided descriptive status of merge request
DETAILED_MERGE_STATUS_MAP = {
    "blocked_status": "🚫 Blocked by another merge request.",
    "broken_status": "⚔️ Can’t merge into the target branch due to a potential conflict.",
    "checking": "🧐 Git is testing if a valid merge is possible.",
    "unchecked": "❓ Git has not yet tested if a valid merge is possible.",
    "ci_must_pass": "⛔ A CI/CD pipeline must succeed before merge.",
    "ci_still_running": "🏃‍♂️ A CI/CD pipeline is still running.",
    "discussions_not_resolved": "💬 All discussions must be resolved before merge.",
    "draft_status": "📝 Can’t merge because the merge request is a draft.",
    "external_status_checks": "🔄 All status checks must pass before merge.",
    "mergeable": "✅ The branch can merge cleanly into the target branch.",
    "not_approved": "🔎 Approval is required before merge.",
    "not_open": "🔒 The merge request must be open before merge.",
    "policies_denied": "🚷 The merge request contains denied policies.",
}


def get_parameter_store_value(parameter_name):
    """Retrieve parameter values."""
    try:
        client = boto3.client("ssm")
        print(f"Getting parameter: {parameter_name}...")
        response = client.get_parameter(Name=parameter_name, WithDecryption=True)
        value = response["Parameter"]["Value"]
        print(f"Parameter {parameter_name} fetched successfully.")
        return value
    except Exception as e:
        print(f"Error getting parameter {parameter_name}: {e}")
        return None


# Retrieve API token values from Parameter Store
SLACK_TOKEN = get_parameter_store_value(os.getenv("PARAMETER_NAME_SLACK"))
GITLAB_TOKEN = get_parameter_store_value(os.getenv("PARAMETER_NAME_GITLAB"))


def get_all_groups():
    """Get all GitLab groups."""
    headers = {"Private-Token": GITLAB_TOKEN}
    all_groups = []
    page = 1

    print("Getting all GitLab Groups and storing in list 'all_groups'...")

    try:
        while True:
            print(f"Getting GitLab Groups - page {page}...")
            response = requests.get(
                f"{GITLAB_BASE_URL}/api/v4/groups?page={page}&per_page=100",
                headers=headers,
                timeout=180,
            )

            # Check for successful response
            response.raise_for_status()

            # Extend all_groups with response data
            all_groups.extend(response.json())

            # Use the 'X-Next-Page' header for the next page number
            next_page = response.headers.get("X-Next-Page")
            if not next_page:
                break
            page = int(next_page)

    except requests.RequestException as e:
        # Handle request exceptions
        print(f"Error getting GitLab groups: {e}")
        return None

    # Exclude groups containing the specified keywords
    removed_groups = []
    if EXCLUDE_GROUPS:
        removed_groups = [
            group
            for group in all_groups
            if any(keyword in group["name"] for keyword in EXCLUDE_GROUPS)
        ]
        all_groups = [group for group in all_groups if group not in removed_groups]

    # Print removed groups
    if removed_groups:
        print(
            "The following groups have been removed from 'all_groups' based on the 'exclude groups' variable:"
        )
        for group in removed_groups:
            print(group["name"])

    print("List of relevant GitLab groups has been generated.")
    return all_groups


def get_stale_merge_requests(updated_before, all_groups):
    """Get all stale merge requests using a single loop for pagination in each group."""
    headers = {"Private-Token": GITLAB_TOKEN}
    stale_merge_requests = []
    print(
        f"Getting open merge requests not updated in the last {STALE_DAYS_THRESHOLD} days (last updated before {updated_before}) in non-archived projects..."
    )
    for group in all_groups:
        page = 1
        while True:
            print(
                f"Getting stale merge requests for group {group['name']}"
                + (f" - page {page}" if page > 1 else "")
                + "..."
            )
            try:
                response = requests.get(
                    f"{GITLAB_BASE_URL}/api/v4/groups/{group['id']}/merge_requests?non_archived=true&state=opened&scope=all&updated_before={updated_before}&page={page}&per_page=100",
                    headers=headers,
                    timeout=180,
                )

                # Check for successful response
                response.raise_for_status()

                # Break the loop if no merge requests are returned
                if not response.json():
                    break

                # Assign merge request if unassigned
                for mr in response.json():
                    # Check if merge request is unassigned and update it
                    if not mr["assignee"]:
                        response_assign_mr = requests.put(
                            f"{GITLAB_BASE_URL}/api/v4/projects/{mr['project_id']}/merge_requests/{mr['iid']}?assignee_id={mr['author']['id']}",
                            headers=headers,
                        )

                        # Check if the update was successful
                        if response_assign_mr.ok:
                            print(
                                f"Successfully assigned author {mr['author']['username']}, to merge request {mr['references']['full']}, because there was no assignee. GitLab API response: {response_assign_mr.status_code} - {response_assign_mr.text}"
                            )
                        else:
                            print(
                                f"Failed to assign author to {mr['references']['full']}. GitLab API response: {response_assign_mr.status_code} - {response_assign_mr.text}"
                            )

                    stale_merge_requests.append(mr)

                # Use the 'X-Next-Page' header for the next page number
                next_page = response.headers.get("X-Next-Page")
                if not next_page:
                    break
                page = int(next_page)

            except requests.RequestException as e:
                # Handle request exceptions
                print(f"Error getting merge requests for group '{group['name']}': {e}")
    print("Finished getting stale merge requests successfully.")
    return stale_merge_requests


def get_gitlab_user_email(user_id):
    """Get email address of a GitLab user by their ID."""
    try:
        response = requests.get(
            f"{GITLAB_BASE_URL}/api/v4/users/{user_id}",
            headers={"Private-Token": GITLAB_TOKEN},
            timeout=180,
        )

        # Check for successful response
        response.raise_for_status()

        if response.status_code == 200:
            return response.json()["email"]
    except requests.RequestException as e:
        # Handle request exceptions
        print(f"Error getting GitLab user email: {e}")

    return None


def send_slack_summary(stale_merge_requests, slack_client):
    """Send summary of stale merge requests to fallback Slack channel."""
    summary_message = f"""Total of *{len(stale_merge_requests)}* open merge requests not updated in the last {STALE_DAYS_THRESHOLD} days, in non-archived projects. \n
_Note: If the numbers below do not match the merge requests in GitLab, you may not have permission to view them._\n\n"""

    # Create a dictionary to store unique merge requests per assignee
    merge_requests_by_assignee = {}
    for mr in stale_merge_requests:
        assignee_id = mr.get("assignee", {}).get("id", "Unassigned")
        if assignee_id not in merge_requests_by_assignee:
            merge_requests_by_assignee[assignee_id] = set()
        merge_requests_by_assignee[assignee_id].add(mr["id"])

    summary = {}
    for assignee_id, merge_request_ids in merge_requests_by_assignee.items():
        if assignee_id == "Unassigned":
            assignee_username = "Unassigned"
            assignee_email = None
            assignee_state = None
        else:
            assignee_info = next(
                (
                    mr
                    for mr in stale_merge_requests
                    if mr["assignee"]["id"] == assignee_id
                ),
                None,
            )
            if assignee_info:
                assignee_username = assignee_info["assignee"]["username"]
                assignee_email = get_gitlab_user_email(assignee_id)
                assignee_state = assignee_info["assignee"].get("state", None)
            else:
                assignee_username = "Unknown"
                assignee_email = None
                assignee_state = None

        summary[assignee_id] = {
            "count": len(merge_request_ids),
            "username": assignee_username,
            "email": assignee_email,
            "state": assignee_state,
        }

    # Sort summary assignees by count, descending
    sorted_summary = sorted(
        summary.items(), key=lambda item: item[1]["count"], reverse=True
    )

    # Create summary message
    for assignee_id, data in sorted_summary:
        # Check if there is an assignee
        assignee_param = (
            f"assignee_username={data['username']}"
            if data["username"] != "Unassigned"
            else "assignee_id=None"
        )

        # Construct assignee merge URL
        assignee_merge_url = f"{GITLAB_BASE_URL}/dashboard/merge_requests?scope=all&state=opened&{assignee_param}"

        # Find Slack user ID to be able to mention them
        slack_user_tag = data["email"] if data["email"] else data["username"]

        if data["email"]:
            try:
                if INTERNAL_EMAIL_DOMAINS and any(
                    domain in data["email"] for domain in INTERNAL_EMAIL_DOMAINS
                ):
                    slack_user = slack_client.users_lookupByEmail(email=data["email"])
                    user_id = slack_user["user"]["id"]
                    slack_user_tag = f"<@{user_id}>"
            except SlackApiError as e:
                print(
                    f"Error creating Slack user tag for {data['email']}: {e.response['error']}"
                )

        if data["state"] == "blocked":
            summary_message += f"- {slack_user_tag} has a count of <{assignee_merge_url}|{data['count']}> - user is BLOCKED :x: please re-assign their merge requests\n"
        else:
            summary_message += f"- {slack_user_tag} has a count of <{assignee_merge_url}|{data['count']}>\n"

    # Send summary message
    try:
        slack_client.chat_postMessage(
            channel=FALLBACK_CHANNEL_ID, text=summary_message, unfurl_links=False
        )
        print(
            f"Successfully sent Slack summary message to channel: {FALLBACK_CHANNEL_ID}."
        )
    except SlackApiError as e:
        print(f"Error sending message to {FALLBACK_CHANNEL_ID}: {e}")


def send_slack_individual_mr(stale_merge_requests, slack_client):
    """Send Slack individual message for stale merge requests."""

    messages_by_recipient = {}

    # Process each stale merge request
    for mr in stale_merge_requests:
        # Determine where to send Slack message
        assignee_email = get_gitlab_user_email(mr["assignee"]["id"])
        if (
            not assignee_email
            or assignee_email.split("@")[-1] not in INTERNAL_EMAIL_DOMAINS
        ):
            if not assignee_email:
                print(f"Couldn't get email for assignee {mr['assignee']['id']}")
            else:
                print(f"Email domain of {assignee_email} not in allowed list.")
            user_id = FALLBACK_CHANNEL_ID
        else:
            try:
                slack_user = slack_client.users_lookupByEmail(email=assignee_email)
                user_id = slack_user["user"]["id"]
            except SlackApiError as e:
                print(
                    f"Error finding Slack user with email {assignee_email} for direct message: {e}"
                )
                user_id = FALLBACK_CHANNEL_ID

        # Dissect merge request URL
        url_parts = mr["web_url"].split("/")
        project_url = "/".join(url_parts[:-3])
        group = url_parts[-5]
        project_name = url_parts[-4]

        # Build 'Last Updated'
        last_updated_date = datetime.datetime.fromisoformat(
            mr["updated_at"].replace("Z", "+00:00")
        )
        days_since_update = (
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            - last_updated_date
        ).days

        # Slack message to send to user
        message_list = [
            f"\n\n`Merge Request:` <{mr['web_url']}|{mr['title']}>",
            f"`Project:` <{project_url}|{group}/{project_name}>",
            f"`Last Updated:` {last_updated_date.strftime('%d-%m-%Y')} ({days_since_update} days ago)",
            f"`Status:` {DETAILED_MERGE_STATUS_MAP.get(mr['detailed_merge_status'], '')}",
            "---",
        ]

        # Add 'Assignee' when sent to fallback channel
        if user_id == FALLBACK_CHANNEL_ID:
            assignee_info = (
                f"`Assignee:` {mr.get('assignee', {}).get('name')} / {assignee_email}"
            )
            message_list.insert(3, assignee_info)

        # Convert Slack message from list to string
        message = "\n".join(message_list)

        # Gather all merge requests for recipient, using a set to ensure uniqueness
        if user_id in messages_by_recipient:
            messages_by_recipient[user_id].add(message)
        else:
            messages_by_recipient[user_id] = {message}

    # Send Slack message
    for recipient, messages in messages_by_recipient.items():
        # Change Slack message intro depending on recipient
        if recipient == FALLBACK_CHANNEL_ID:
            intro = "The assignee(s) of the merge requests below either could not be found in Slack, or are external users."
            print(
                f"Sending Slack message containing summary to fallback channel {recipient}..."
            )
        else:
            intro = f"You have open merge requests that haven't been updated in the last {STALE_DAYS_THRESHOLD} days. Please review and take appropriate action."
            print(f"Sending Slack direct message to user {recipient}...")

        message = intro + "\n".join(messages)

        # Send Slack individual message
        try:
            slack_client.chat_postMessage(
                channel=recipient, text=message, unfurl_links=False
            )
            if recipient == FALLBACK_CHANNEL_ID:
                print(
                    f"Successfully sent Slack message to fallback channel {recipient}."
                )
            else:
                print(f"Successfully sent Slack direct message to {recipient}.")
        except SlackApiError as e:
            print(f"Error sending Slack direct message to {recipient}: {e}")


def check_and_notify_stale_merge_requests(event, context):
    """Bring multiple functions together to send Slack message."""
    # Create variable to use as search for stale merge requests
    updated_before = (
        datetime.datetime.utcnow()
        - datetime.timedelta(days=STALE_DAYS_THRESHOLD)
        + datetime.timedelta(minutes=5)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_groups = get_all_groups()
    if not all_groups:
        print("No groups retrieved. Exiting function.")
        return

    stale_merge_requests = get_stale_merge_requests(updated_before, all_groups)

    if not stale_merge_requests:
        print("No stale merge requests found.")
        return

    print(
        f"Open merge requests not updated in the last {STALE_DAYS_THRESHOLD} days, in non-archived projects: {len(stale_merge_requests)}"
    )

    slack_client = WebClient(token=SLACK_TOKEN)
    send_slack_summary(stale_merge_requests, slack_client)
    send_slack_individual_mr(stale_merge_requests, slack_client)

    print("Stale merge request check completed successfully.")


if __name__ == "__main__":
    check_and_notify_stale_merge_requests()
