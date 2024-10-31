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
def scan_and_respond(reddit, responses, triggers):
    subreddit = reddit.subreddit("Minecraft")  # Adjust subreddit as needed

    for submission in subreddit.new(limit=10):  # Checks the 10 most recent posts
        if any(trigger.lower() in submission.title.lower() for trigger in triggers):
            print(f"Found relevant post: {submission.title}")

            # Check if already replied
            if not submission.saved:
                response_text = responses["bug_reply"]  # Use a relevant response
                submission.reply(response_text)
                submission.save()
                print(f"Replied to post: {submission.title}")

# Reply to a specific post link from manual issue trigger
def reply_to_post(reddit, responses, post_url):
    submission = reddit.submission(url=post_url)
    response_text = responses["bug_reply"]
    submission.reply(response_text)
    print(f"Replied to specific post: {submission.title}")

def main():
    config = load_config()
    responses = load_responses()
    triggers = load_triggers()
    reddit = authenticate(config)

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, responses, args.manual)
    else:
        scan_and_respond(reddit, responses, triggers)

if __name__ == "__main__":
    main()
