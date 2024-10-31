# reddit_bot.py
import praw
import json
import argparse

# Load configuration
def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

# Load responses
def load_responses():
    with open('responses.json', 'r') as responses_file:
        return json.load(responses_file)

# Load triggers
def load_triggers():
    with open('triggers.json', 'r') as triggers_file:
        return json.load(triggers_file)["keywords"]

# Authenticate Reddit client
def authenticate(config):
    return praw.Reddit(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        username=config["username"],
        password=config["password"],
        user_agent=config["user_agent"]
    )

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            response_text = "Thanks for sharing!"  # Default response
            found_trigger = False  # To check if a trigger is found

            # Detect relevant keywords in the title or body and select the appropriate response
            for keyword in triggers:
                if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
                    response_key = "dupe_reply" if "dupe" in keyword else "bug_reply"
                    response_text = responses.get(response_key, response_text)
                    found_trigger = True
                    break  # Stop at the first match to prevent multiple responses
            
            if found_trigger and not submission.saved:
                submission.reply(response_text)
                submission.save()  # Mark as replied
                print(f"Replied to post: {submission.title}")

# Reply to a specific post link from manual issue trigger
def reply_to_post(reddit, responses, triggers, post_url):
    submission = reddit.submission(url=post_url)
    
    response_text = responses["bug_reply"]["default"]  # Default response
    found_trigger = False

    for keyword in triggers:
        if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
            # Use the specific response based on the keyword
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
    config = load_config()
    responses = load_responses()
    triggers = load_triggers()
    reddit = authenticate(config)
    subreddits = config.get("subreddits", ["Minecraft"])

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, responses, triggers, args.manual)
    else:
        scan_and_respond(reddit, responses, triggers, subreddits)

if __name__ == "__main__":
    main()
