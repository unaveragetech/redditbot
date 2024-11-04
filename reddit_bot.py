import os
import praw
import json
import argparse
import requests
from datetime import datetime
from random import choice

# Load responses
def load_responses():
    with open('responses.json', 'r') as responses_file:
        return json.load(responses_file)

# Load triggers
def load_triggers():
    with open('triggers.json', 'r') as triggers_file:
        return json.load(triggers_file)["keywords"]

# Load user character traits
def load_user_profile():
    with open('user.json', 'r') as user_file:
        return json.load(user_file)

# Load inspirations for dynamic responses
def load_inspirations():
    with open('inspirations.txt', 'r') as inspirations_file:
        return inspirations_file.readlines()

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

# Construct a dynamic response based on user profile and inspirations
def construct_response(base_response, user_profile, inspirations):
    response = base_response
    # Add mannerisms or quirks from the user profile
    if "mannerisms" in user_profile:
        response = f"{choice(user_profile['mannerisms'])} {response}"
    # Add a random inspiration quote if relevant
    if inspirations:
        response += f"\n\nInspiration: {choice(inspirations).strip()}"
    return response

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits, responded_posts, user_profile, inspirations):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            if submission.id in responded_posts:
                print(f"Already responded to post: {submission.title}. Skipping.")
                continue

            response_text = responses["bug_reply"]["default"]  # Default response
            found_trigger = False

            # Detect relevant keywords and prepare a response
            for keyword in triggers:
                if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
                    response_key = "bug_reply" if keyword in responses["bug_reply"] else "dupe_reply"
                    base_response = responses[response_key].get(keyword, responses[response_key]["default"])
                    response_text = construct_response(base_response, user_profile, inspirations)
                    found_trigger = True
                    break

            if found_trigger and not submission.saved:
                submission.reply(response_text)
                submission.save()  # Mark as replied
                responded_posts.add(submission.id)  # Add to responded posts
                print(f"Replied to post: {submission.title}")
                update_log(f"Replied to post: {submission.title} with response: {response_text}")

def main():
    responses = load_responses()
    triggers = load_triggers()
    user_profile = load_user_profile()
    inspirations = load_inspirations()
    reddit = authenticate()
    subreddits = ["TextRpgGame"]
    
    # Load previously responded posts
    responded_posts = set()
    if os.path.exists("responded_posts.json"):
        with open("responded_posts.json", "r") as f:
            responded_posts = set(json.load(f))

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, responses, triggers, args.manual, responded_posts)
    else:
        scan_and_respond(reddit, responses, triggers, subreddits, responded_posts, user_profile, inspirations)

    # Save the responded posts
    with open("responded_posts.json", "w") as f:
        json.dump(list(responded_posts), f)

if __name__ == "__main__":
    main()
