import os
import praw
import argparse

def create_reddit_instance():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    user_agent = os.getenv("USER_AGENT")

    # Initialize Reddit instance
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent
    )
    return reddit

def check_keywords_in_post(reddit, post_url):
    submission = reddit.submission(url=post_url)
    submission_text = submission.title.lower() + " " + submission.selftext.lower()

    # Check for keywords
    if "dupe" in submission_text and "glitch" in submission_text:
        print("Keywords 'dupe' and 'glitch' found in the post.")
    else:
        print("Keywords not found in the post.")

def main():
    parser = argparse.ArgumentParser(description="Check Reddit post for keywords.")
    parser.add_argument('--post_url', required=True, help='The Reddit post URL to check')
    args = parser.parse_args()

    reddit = create_reddit_instance()
    check_keywords_in_post(reddit, args.post_url)

if __name__ == "__main__":
    main()
