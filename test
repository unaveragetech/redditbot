import os
import praw

def main():
    # Get the post URL from environment variable
    post_url = os.getenv("POST_URL")
    if not post_url:
        print("Error: POST_URL environment variable is not set.")
        return

    # Set up Reddit API credentials with stripped whitespace
    reddit = praw.Reddit(
        client_id=os.getenv("CLIENT_ID").strip(),
        client_secret=os.getenv("CLIENT_SECRET").strip(),
        username=os.getenv("USERNAME").strip(),
        password=os.getenv("PASSWORD").strip(),
        user_agent=os.getenv("USER_AGENT").strip()
    )

    try:
        # Retrieve the submission from the URL
        submission = reddit.submission(url=post_url)
        query_terms = ["dupe", "glitch"]

        # Check if any query term is in the title or body of the post
        if any(term in submission.title.lower() or term in submission.selftext.lower() for term in query_terms):
            print(f"Match found in post: {submission.title}")
        else:
            print("No match found in post content.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
