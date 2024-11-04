#reddit_bot.py
import os
import praw
import json
import argparse
import requests
from datetime import datetime
from random import choice

# Load responses from the JSON file
def load_responses():
    with open('responses.json', 'r') as responses_file:
        return json.load(responses_file)

# Load triggers from the JSON file
def load_triggers():
    with open('triggers.json', 'r') as triggers_file:
        return json.load(triggers_file)["keywords"]

# Load user profile from the JSON file
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

# Generate a prompt for the LLM
def generate_llm_prompt(post_title, post_body, user_profile):
    prompt = f"""
    You are a helpful and friendly assistant. Here is some context about your personality:
    - Mannerisms: {', '.join(user_profile.get('mannerisms', []))}
    - Traits: {', '.join(user_profile.get('traits', []))}

    Your task is to generate a helpful and insightful response to the following Reddit post:
    - **Title**: {post_title}
    - **Body**: {post_body}

    Please respond in a manner consistent with your personality and provide relevant information, advice, or support based on the post content.
    """
    return prompt

# Call the LLM to generate a response
def call_llm(prompt):
    # Use the Ollama API to generate a response
    response = requests.post("http://localhost:11434/generate", json={"prompt": prompt})
    return response.json().get('text', "I'm sorry, I couldn't generate a response.")

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

# Reply to a specific Reddit post
def reply_to_post(reddit, responses, triggers, post_url, responded_posts):
    try:
        # Extract the submission ID from the URL
        submission_id = post_url.split('/')[-3]
        submission = reddit.submission(id=submission_id)

        # Check if the bot has already responded to this post
        if submission.id in responded_posts:
            print(f"Already responded to post: {submission.title}. Skipping.")
            return

        user_profile = load_user_profile()
        inspirations = load_inspirations()
        
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

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits, responded_posts):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            if submission.id in responded_posts:
                print(f"Already responded to post: {submission.title}. Skipping.")
                continue

            found_trigger = False

            # Detect relevant keywords and prepare a response
            for keyword in triggers:
                if keyword.lower() in submission.title.lower() or keyword.lower() in submission.selftext.lower():
                    # Use the LLM for generating a response
                    user_profile = load_user_profile()
                    inspirations = load_inspirations()
                    llm_prompt = generate_llm_prompt(submission.title, submission.selftext, user_profile)
                    
                    # Call the LLM and get the response
                    llm_response = call_llm(llm_prompt)

                    # Reply to the post
                    submission.reply(llm_response)
                    submission.save()  # Mark as replied
                    responded_posts.add(submission.id)  # Add to responded posts
                    print(f"Replied to post: {submission.title}")
                    update_log(f"Replied to post: {submission.title} with response: {llm_response}")
                    found_trigger = True
                    break

            if found_trigger:
                continue

def main():
    responses = load_responses()
    triggers = load_triggers()
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
        scan_and_respond(reddit, responses, triggers, subreddits, responded_posts)

    # Save the responded posts
    with open("responded_posts.json", "w") as f:
        json.dump(list(responded_posts), f)

if __name__ == "__main__":
    main()
