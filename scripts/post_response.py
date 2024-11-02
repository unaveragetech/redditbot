import praw
import sys
import os

def main(response, post_url):
    # Create a Reddit instance using environment variables for credentials
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        username=os.getenv('REDDIT_USERNAME'),
        password=os.getenv('REDDIT_PASSWORD'),
        user_agent=os.getenv('USER_AGENT')
    )

    # Extract the post ID from the URL
    post_id = post_url.split('/')[-3]  # Extract the post ID from the URL
    submission = reddit.submission(id=post_id)

    # Post the response as a comment
    submission.reply(response)
    print(f"Posted response to: {post_url}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python post_response.py '<response>' '<post_url>'")
        sys.exit(1)

    response = sys.argv[1]
    post_url = sys.argv[2]
    main(response, post_url)
