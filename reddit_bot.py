import os
import sys
import json
import requests
import praw
import subprocess

# Model command mapping (same as previously)
model_commands = {
    "Llama 3": "ollama run llama3",
    "Llama 3 (70B)": "ollama run llama3:70b",
    "Phi 3 Mini": "ollama run phi3",
    "Phi 3 Medium": "ollama run phi3:medium",
    "Gemma (2B)": "ollama run gemma:2b",
    "Gemma (7B)": "ollama run gemma:7b",
    "Mistral": "ollama run mistral",
    "Moondream 2": "ollama run moondream",
    "Neural Chat": "ollama run neural-chat",
    "Starling": "ollama run starling-lm",
    "Code Llama": "ollama run codellama",
    "Llama 2 Uncensored": "ollama run llama2-uncensored",
    "LLaVA": "ollama run llava",
    "Solar": "ollama run solar",
}

def load_user_data():
    """Load the user data from user.json."""
    try:
        with open("user.json", "r") as file:
            user_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        raise Exception("Failed to load user.json. Make sure the file exists and is valid JSON.")
    
    return user_data

def fetch_reddit_post_data(url):
    """Fetch the Reddit post's title and body using PRAW."""
    reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"),
                         client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                         user_agent="your_bot_user_agent",
                         username=os.getenv("REDDIT_USERNAME"),
                         password=os.getenv("REDDIT_PASSWORD"))
    
    post = reddit.submission(url=url)
    
    title = post.title
    body = post.selftext
    
    return title, body

def run_ollama_model(model_name, query):
    """Run the Ollama model with the given model name and query."""
    normalized_model_name = model_name.lower()
    command = next((cmd for name, cmd in model_commands.items() if name.lower() == normalized_model_name), None)
    
    if command is None:
        print(f"Model '{model_name}' not found. Please specify a valid model.")
        return None

    command_parts = command.split()  # Split the command into parts
    command_parts.append(query)      # Append the query to the command

    # Start the Ollama model and get the response
    process = subprocess.Popen(command_parts, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Error running model: {error}")
        return None

    # Write the output to response.txt
    with open("response.txt", "w") as response_file:
        response_file.write(output.strip())
    
    print("Response written to response.txt.")
    return output.strip()

def post_to_reddit(url, response):
    """Post the model's response as a comment on Reddit."""
    reddit = praw.Reddit(client_id=os.getenv("REDDIT_CLIENT_ID"),
                         client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                         user_agent="your_bot_user_agent",
                         username=os.getenv("REDDIT_USERNAME"),
                         password=os.getenv("REDDIT_PASSWORD"))
    
    post = reddit.submission(url=url)
    post.reply(response)  # Reply to the post with the model's response
    print(f"Posted response to Reddit: {response}")

def generate_prompt(title, body, user_data):
    """Generate a prompt using the post title, body, and user data."""
    prompt = f"Post Title: {title}\nPost Body: {body}\n\n"
    prompt += f"User Style: {user_data['writing_conventions']['style']}\n"
    prompt += f"User Mannerisms: {', '.join(user_data['mannerisms'])}\n"
    prompt += f"Writing conventions: {'Use emojis' if user_data['writing_conventions']['use_emojis'] else 'Do not use emojis'}\n"
    prompt += "\nGenerate a response based on the above information."

    return prompt

def main(url):
    """Main function to run the Reddit bot."""
    # Load user data
    user_data = load_user_data()

    # Fetch Reddit post data
    title, body = fetch_reddit_post_data(url)
    
    # Generate the prompt using post data and user data
    prompt = generate_prompt(title, body, user_data)
    
    # Use a predefined model, you can modify this as needed
    model_name = "Llama 3"  # Choose a predefined model
    response = run_ollama_model(model_name, prompt)
    
    if response:
        post_to_reddit(url, response)  # Post the response to Reddit
    else:
        print("Failed to generate a response.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reddit_bot.py <reddit_post_url>")
        sys.exit(1)

    reddit_post_url = sys.argv[1]
    main(reddit_post_url)
