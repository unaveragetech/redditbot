# reddit_bot.py
import os
import praw
import json
import argparse
import subprocess
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

# Execute script and return output
def execute_script(script_path):
    try:
        result = subprocess.run(["bash", script_path], capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error executing script: {str(e)}"

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            response_text = responses["bug_reply"]["default"]  # Default response
            found_trigger = False  # To check if a trigger is found

            # Detect relevant keywords in the title or body and select the appropriate response
            for keyword in triggers:
                if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
                    if keyword in responses["dupe_reply"]:
                        response_key = "dupe_reply"
                    elif keyword in responses["misc_commands"]:
                        response_key = "misc_commands"
                        # Handle misc commands
                        if "run script" in submission.selftext.lower():
                            script_name = submission.selftext.lower().split("run script(")[-1].split(")")[0].strip()
                            script_path = f"./scripts/{script_name}.sh"
                            if os.path.isfile(script_path):
                                response_text = f"Running `{script_name}`:\n\n```\n{execute_script(script_path)}\n```"
                            else:
                                response_text = f"Script `{script_name}` not found in the `scripts` directory."
                        elif "get logs" in submission.selftext.lower():
                            with open("bot_log.log", "r") as log_file:
                                response_text = "Here are the recent logs:\n\n" + log_file.read()
                        elif "list files" in submission.selftext.lower():
                            files = os.listdir(".")
                            response_text = "Files in the current directory:\n\n" + "\n".join(files)
                        else:
                            response_text = responses[response_key]["default"]
                        found_trigger = True
                        break
                    else:
                        response_key = "bug_reply"

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
    
    response_text = responses["bug_reply"]["default"]  # Default response
    found_trigger = False

    # Detect relevant keywords and select the appropriate response
    for keyword in triggers:
        if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
            if keyword in responses["bug_reply"]:
                response_text = responses["bug_reply"][keyword]
            elif keyword in responses["dupe_reply"]:
                response_text = responses["dupe_reply"][keyword]
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
