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

        for submission in subreddit.new(limit=10):  # Checks the 10 most recent posts
            if any(trigger.lower() in submission.title.lower() for trigger in triggers):
                print(f"Found relevant post: {submission.title}")

                # Check if already replied
                if not submission.saved:
                    # Use the appropriate response based on trigger keyword
                    response_text = responses.get("bug_reply", "Thanks for sharing!")
                    submission.reply(response_text)
                    submission.save()
                    print(f"Replied to post: {submission.title}")

# Reply to a specific post link from manual issue trigger
def reply_to_post(reddit, responses, triggers, post_url):
    submission = reddit.submission(url=post_url)
    
    # Detect relevant keyword in the title or body and select the corresponding response
    response_text = "Thanks for sharing!"  # Default response
    found_trigger = False  # To check if a trigger is found

    for keyword in triggers:
        if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
            # Check if there’s a specific response for the keyword type
            response_key = "dupe_reply" if "dupe" in keyword else "bug_reply"
            response_text = responses.get(response_key, response_text)
            found_trigger = True
            break  # Stop at the first match to prevent multiple responses

    if not found_trigger:
        print("No specific trigger found, using the default response.")
        
    submission.reply(response_text)
    print(f"Replied to post: {submission.title}")

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
