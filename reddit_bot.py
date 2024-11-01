import os
import praw
import json
import argparse
import requests
from datetime import datetime

# Load responses
def load_responses():
    with open('responses.json', 'r') as responses_file:
        return json.load(responses_file)

# Load triggers
def load_triggers():
    with open('triggers.json', 'r') as triggers_file:
        return json.load(triggers_file)["keywords"]

# Authenticate Reddit client using environment variables
def authenticate():
    return praw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        username=os.getenv("USERNAME"),
        password=os.getenv("PASSWORD"),
        user_agent=os.getenv("USER_AGENT", "your_bot_user_agent")
    )

# Create or update log file
def update_log(entry):
    log_entry = f"{datetime.now()}: {entry}\n"
    with open("bot_log.log", "a") as log_file:
        log_file.write(log_entry)

# Trigger GitHub Actions workflow for the script and get the output URL
def trigger_github_action(script_name, arguments):
    try:
        github_api_url = "https://api.github.com/repos/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/actions/workflows/run_script.yml/dispatches"
        headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "ref": "main",  # Branch to run the workflow on
            "inputs": {
                "script_name": script_name,
                "arguments": arguments
            }
        }
        response = requests.post(github_api_url, headers=headers, json=payload)
        
        if response.status_code == 204:
            return "Script execution triggered successfully. Please wait for the output."
        else:
            return f"Failed to trigger GitHub Actions. Status code: {response.status_code}, Response: {response.text}"
    except Exception as e:
        return f"An error occurred while triggering the GitHub Action: {str(e)}"

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            response_text = responses["bug_reply"]["default"]  # Default response
            found_trigger = False

            # Detect command for script execution
            if "!botrun(" in submission.selftext:
                start = submission.selftext.find("!botrun(") + len("!botrun(")
                end = submission.selftext.find(")", start)
                command = submission.selftext[start:end].strip()

                if "-" in command:
                    script_name, arguments = command.split("-", 1)
                else:
                    script_name, arguments = command, ""

                # Trigger GitHub Actions for the script
                response_text = trigger_github_action(script_name, arguments)
                found_trigger = True

            # Detect relevant keywords and prepare a response
            if not found_trigger:
                for keyword in triggers:
                    if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
                        response_key = "bug_reply" if keyword in responses["bug_reply"] else "dupe_reply"
                        response_text = responses[response_key].get(keyword, responses[response_key]["default"])
                        found_trigger = True
                        break

            if found_trigger and not submission.saved:
                submission.reply(response_text)
                submission.save()  # Mark as replied
                print(f"Replied to post: {submission.title}")
                update_log(f"Replied to post: {submission.title} with response: {response_text}")

# Reply to a specific post link from manual issue trigger
def reply_to_post(reddit, responses, triggers, post_url):
    submission = reddit.submission(url=post_url)
    
    response_text = responses["bug_reply"]["default"]
    found_trigger = False

    # Detect relevant keywords and select the appropriate response
    for keyword in triggers:
        if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
            response_key = "bug_reply" if keyword in responses["bug_reply"] else "dupe_reply"
            response_text = responses[response_key].get(keyword, responses[response_key]["default"])
            found_trigger = True
            break

    if not found_trigger:
        print("No specific trigger found, using the default response.")
        
    submission.reply(response_text)
    print(f"Replied to specific post: {submission.title}")
    update_log(f"Replied to specific post: {submission.title} with response: {response_text}")

def main():
    responses = load_responses()
    triggers = load_triggers()
    reddit = authenticate()
    subreddits = ["TextRpgGame"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, responses, triggers, args.manual)
    else:
        scan_and_respond(reddit, responses, triggers, subreddits)

if __name__ == "__main__":
    main()
