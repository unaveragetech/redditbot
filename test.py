#test.py

import os
import praw

def test_login():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    user_agent = os.getenv("USER_AGENT")

    # Create Reddit instance
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        password=password,
        user_agent=user_agent
    )

    try:
        # Attempt to fetch the logged-in user's profile
        user = reddit.user.me()
        print(f"Logged in as: {user.name}")
    except Exception as e:
        print(f"Login failed: {e}")

if __name__ == "__main__":
    test_login()
