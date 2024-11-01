import os
import praw
import json
import argparse
import requests
from datetime import datetime

# Load responses from the combined bot_text JSON file
def load_bot_text():
    with open('bot_text.json', 'r') as bot_text_file:
        return json.load(bot_text_file)["triggers_and_responses"]

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
def scan_and_respond(reddit, bot_text, subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")
        update_log(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            response_text = None
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
                for item in bot_text:
                    trigger = item["trigger"]
                    if trigger.lower() in submission.title.lower() or trigger.lower() in submission.selftext.lower():
                        response_text = item["response"]
                        found_trigger = True
                        break

            if found_trigger and response_text and not submission.saved:
                submission.reply(response_text)
                submission.save()  # Mark as replied
                print(f"Replied to post: {submission.title}")
                update_log(f"Replied to post: {submission.title} with response: {response_text}")

# Reply to a specific post link from manual issue trigger
def reply_to_post(reddit, bot_text, post_url):
    submission = reddit.submission(url=post_url)
    
    response_text = "I'm sorry, I couldn't find a suitable response for your post."
    found_trigger = False

    # Detect relevant keywords and select the appropriate response
    for item in bot_text:
        trigger = item["trigger"]
        if trigger.lower() in submission.title.lower() or trigger.lower() in submission.selftext.lower():
            response_text = item["response"]
            found_trigger = True
            break

    if not found_trigger:
        print("No specific trigger found, using the default response.")
        
    submission.reply(response_text)
    print(f"Replied to specific post: {submission.title}")
    update_log(f"Replied to specific post: {submission.title} with response: {response_text}")

def main():
    bot_text = load_bot_text()
    reddit = authenticate()
    subreddits = ["TextRpgGame"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, bot_text, args.manual)
    else:
        scan_and_respond(reddit, bot_text, subreddits)

if __name__ == "__main__":
    main()
