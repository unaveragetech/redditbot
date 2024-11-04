import os
import praw
import json
import argparse
import requests
import subprocess
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

# Load the character state
def load_character_state():
    try:
        with open("character_state.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # Create a default character state if the file doesn't exist
        return {"name": "RedditBot", "history": [], "traits": ["curious", "helpful"]}

# Save the character state
def save_character_state(state):
    with open("character_state.json", "w") as file:
        json.dump(state, file, indent=4)

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

# Run the LLM model using Ollama with a constructed prompt
def run_llm_query(model_name, post_title, post_body, user_profile):
    # Construct the prompt for the LLM
    prompt = (
        f"You are a Reddit bot with the following traits: {', '.join(user_profile['traits'])}.\n"
        f"Your user profile mentions these mannerisms: {', '.join(user_profile.get('mannerisms', []))}.\n\n"
        f"Here is the Reddit post you need to respond to:\n"
        f"Title: {post_title}\n"
        f"Body: {post_body}\n\n"
        f"Please generate a helpful and relevant response considering your traits and the post's content."
    )

    model_commands = {
        "Llama 3": "ollama run llama3",
        "Llama 3 (70B)": "ollama run llama3:70b",
    }
    command = model_commands.get(model_name)
    if not command:
        print(f"Model '{model_name}' not found.")
        return None

    command_parts = command.split()
    command_parts.append(prompt)
    process = subprocess.Popen(command_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Error running model: {error}")
        return None

    return output.strip()

# Construct a dynamic response
def construct_response(base_response, user_profile, inspirations):
    response = base_response
    # Add mannerisms or quirks from the user profile
    if "mannerisms" in user_profile:
        response = f"{choice(user_profile['mannerisms'])} {response}"
    # Add a random inspiration quote if relevant
    if inspirations:
        response += f"\n\nInspiration: {choice(inspirations).strip()}"
    return response

# Update character state with the LLM response
def update_character_state(llm_response):
    character_state = load_character_state()
    character_state["history"].append({
        "timestamp": datetime.now().isoformat(),
        "interaction": llm_response
    })
    save_character_state(character_state)

# Search for relevant posts and respond
def scan_and_respond(reddit, responses, triggers, subreddits, responded_posts, user_profile, inspirations):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"Scanning subreddit: {subreddit_name}")

        for submission in subreddit.new(limit=10):  # Check the 10 most recent posts
            if submission.id in responded_posts:
                print(f"Already responded to post: {submission.title}. Skipping.")
                continue

            # Use the LLM to generate a response
            llm_response = run_llm_query(
                model_name="Llama 3",  # You can adjust the model name as needed
                post_title=submission.title,
                post_body=submission.selftext,
                user_profile=user_profile
            )

            if llm_response and not submission.saved:
                submission.reply(llm_response)
                submission.save()  # Mark as replied
                responded_posts.add(submission.id)  # Add to responded posts
                print(f"Replied to post: {submission.title}")
                update_log(f"Replied to post: {submission.title} with response: {llm_response}")
                update_character_state(llm_response)  # Update character state

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
