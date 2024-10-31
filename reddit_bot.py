# reddit_bot.py
import os
import praw
import json
import argparse

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
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        username=os.getenv("REDDIT_USERNAME"),
        password=os.getenv("PASSWORD"),
        user_agent="python:com.reddit.minecraftbot:v1.0.0"
    )

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
                    response_key = "dupe_reply" if "dupe" in keyword else "bug_reply"
                    response_text = responses.get(response_key, response_text)
                    found_trigger = True
                    break
            
            if found_trigger and not submission.saved:
                submission.reply(response_text)
                submission.save()  # Mark as replied
                print(f"Replied to post: {submission.title}")

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

def main():
    responses = load_responses()
    triggers = load_triggers()
    reddit = authenticate()
    subreddits = ["Minecraft", "technicalminecraft", "minecraftsuggestions"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, responses, triggers, args.manual)
    else:
        scan_and_respond(reddit, responses, triggers, subreddits)

if __name__ == "__main__":
    main()
