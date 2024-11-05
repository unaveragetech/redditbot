import os
import praw
import json
import argparse
import requests
from datetime import datetime

# Load responses from the JSON file
def load_responses():
    try:
        with open('responses.json', 'r') as responses_file:
            return json.load(responses_file)
    except FileNotFoundError:
        print("Error: responses.json file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error: responses.json file is not a valid JSON.")
        return {}

# Load user profile from the JSON file
def load_user_profile():
    with open('user.json', 'r') as user_file:
        return json.load(user_file)

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

# Generate a prompt for the LLM
def generate_llm_prompt(post_title, post_body, user_profile):
    prompt = f"""
    You are a friendly, empathetic, and optimistic assistant with the following personality traits:
    - Name: {user_profile['name']}
    - Age: {user_profile['age']}
    - Birthplace: {user_profile['birthplace']}
    - Traits: {', '.join(user_profile['traits'])}
    - Mannerisms: {', '.join(user_profile['mannerisms'])}
    - Interests: {', '.join(user_profile['interests'])}
    - Hobbies: {', '.join(user_profile['hobbies'])}
    
    Your writing conventions are:
    - Style: {user_profile['writing_conventions']['style']}
    - Use of emojis: {'Yes' if user_profile['writing_conventions']['use_emojis'] else 'No'}
    - Tone: {user_profile['writing_conventions']['tone']}
    - Avoid: {', '.join(user_profile['writing_conventions']['avoid'])}

    Communication preferences:
    - Formality: {user_profile['communication_preferences']['formality']}
    - Emoji usage: {user_profile['communication_preferences']['emoji_usage']}
    - Pacing: {user_profile['communication_preferences']['pacing']}
    - Humor: {user_profile['communication_preferences']['humor']}

    You should respond to the following Reddit post in a way that is consistent with your personality:
    - **Title**: {post_title}
    - **Body**: {post_body}

    Please provide helpful advice or commentary, keeping in mind the user's preferences and your own personality.
    """
    return prompt

# Call the LLM to generate a response
def call_llm(prompt):
    # Use the Ollama API to generate a response (change this if you're using a different LLM)
    response = requests.post("http://localhost:11434/generate", json={"prompt": prompt})
    return response.json().get('text', "I'm sorry, I couldn't generate a response.")

# Reply to a specific Reddit post
def reply_to_post(reddit, post_url, responded_posts):
    try:
        # Extract the submission ID from the URL
        submission_id = post_url.split('/')[-3]
        submission = reddit.submission(id=submission_id)

        # Check if the bot has already responded to this post
        if submission.id in responded_posts:
            print(f"Already responded to post: {submission.title}. Skipping.")
            return

        user_profile = load_user_profile()

        # Generate a prompt for the LLM based on the post
        llm_prompt = generate_llm_prompt(submission.title, submission.selftext, user_profile)

        # Call the LLM to get the response
        llm_response = call_llm(llm_prompt)

        # Reply to the post with the LLM's response
        submission.reply(llm_response)
        submission.save()  # Mark as replied
        responded_posts.add(submission.id)  # Add to responded posts
        print(f"Replied to post: {submission.title}")
        update_log(f"Replied to post: {submission.title} with response: {llm_response}")

    except Exception as e:
        print(f"Error replying to post: {e}")
        update_log(f"Error replying to post: {e}")

# Scan and respond to relevant posts in multiple subreddits
def scan_and_respond(reddit, subreddits, responded_posts):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            if submission.id in responded_posts:
                print(f"Already responded to post: {submission.title}. Skipping.")
                continue

            # Generate a prompt for the LLM based on the post
            user_profile = load_user_profile()
            llm_prompt = generate_llm_prompt(submission.title, submission.selftext, user_profile)

            # Call the LLM and get the response
            llm_response = call_llm(llm_prompt)

            # Reply to the post with the LLM's response
            submission.reply(llm_response)
            submission.save()  # Mark as replied
            responded_posts.add(submission.id)  # Add to responded posts
            print(f"Replied to post: {submission.title}")
            update_log(f"Replied to post: {submission.title} with response: {llm_response}")

def main():
    reddit = authenticate()
    subreddits = ["TextRpgGame"]  # Subreddit list to scan

    # Load previously responded posts
    responded_posts = set()
    if os.path.exists("responded_posts.json"):
        with open("responded_posts.json", "r") as f:
            responded_posts = set(json.load(f))

    parser = argparse.ArgumentParser()
    parser.add_argument("--manual", help="URL of specific Reddit post to reply to")
    args = parser.parse_args()

    if args.manual:
        reply_to_post(reddit, args.manual, responded_posts)
    else:
        scan_and_respond(reddit, subreddits, responded_posts)

    # Save the responded posts
    with open("responded_posts.json", "w") as f:
        json.dump(list(responded_posts), f)

if __name__ == "__main__":
    main()
