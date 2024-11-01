#nft.py

import random
import json
import os
from PIL import Image, ImageDraw, ImageFont

# Function to generate random colors
def random_color():
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

# Function to generate random NFT attributes
def generate_nft_attributes():
    attributes = {
        "name": f"NFT #{random.randint(1, 10000)}",
        "description": "A unique piece of digital art.",
        "creator": f"Creator {random.randint(1, 100)}",
        "color": random_color(),
        "size": f"{random.randint(100, 500)}x{random.randint(100, 500)}"
    }
    return attributes

# Function to create a simple NFT image
def create_nft_image(attributes, filename):
    width, height = map(int, attributes["size"].split('x'))
    image = Image.new("RGB", (width, height), attributes["color"])
    draw = ImageDraw.Draw(image)

    # Add text to the image
    font = ImageFont.load_default()
    draw.text((10, 10), attributes["name"], fill=(255, 255, 255), font=font)
    
    # Save the image
    image.save(filename)

# Main function to generate NFT and save details
def main():
    nft_attributes = generate_nft_attributes()
    
    # Create a filename based on the NFT name
    filename = f"{nft_attributes['name'].replace('#', '')}.json"
    
    # Create an NFT image
    image_filename = f"{nft_attributes['name'].replace('#', '')}.png"
    create_nft_image(nft_attributes, image_filename)

    # Save NFT attributes to a JSON file
    with open(filename, 'w') as json_file:
        json.dump(nft_attributes, json_file, indent=4)

    print(f"Generated NFT: {nft_attributes['name']}")
    print(f"NFT image saved as: {image_filename}")
    print(f"NFT details saved as: {filename}")

if __name__ == "__main__":
    main()
