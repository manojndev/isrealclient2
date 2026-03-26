# gemini_webapi based image generation script for KDP automation
# This script replicates the functionality of finalscript.py using gemini_webapi

# RESUME FROM PAGE: Set this to the page number you want to start from (1-based)
# If the script fails at page 10, set this to 10 to resume from that page
START_PAGE = 1

import asyncio
import os
import json
import random
from pathlib import Path
from gemini_webapi import GeminiClient, set_log_level
from gemini_webapi.constants import Model
import numpy as np
from PIL import Image


# Set log level for debugging (can be: DEBUG, INFO, WARNING, ERROR, CRITICAL)
set_log_level("INFO")

# Cookie values for authentication
Secure_1PSID = "g.a0005wgv-g3nRet3H8KDMjbBdMoLt5OMGkUOuR6zL7WtHfrrXA6YjvdBbXTiuE2Qr-C26QLKCQACgYKAT4SARISFQHGX2MizrTJzmaXbs8tMH1w6mHKXBoVAUF8yKrqDVELh01BdXPYaIZQZskQ0076"
Secure_1PSIDTS = "sidts-CjEB7I_69PF8fsvWv9zdrhRWMtKMvayDeB2GfaZa1crIlizLbTG0QzNv0KKmhrewE9poEAA"

# Human-like delay settings (in seconds)
MIN_DELAY_BETWEEN_PAGES = 15  # Minimum delay between pages
MAX_DELAY_BETWEEN_PAGES = 35  # Maximum delay between pages
MIN_DELAY_ON_RETRY = 8       # Minimum delay before retry
MAX_DELAY_ON_RETRY = 15      # Maximum delay before retry


def get_human_delay(min_delay: float, max_delay: float) -> float:
    """Generate a random human-like delay between min and max seconds."""
    return random.uniform(min_delay, max_delay)

# Watermark Removal Logic
def calculate_alpha_map(bg_image):
    """
    Calculates the alpha map from the background image.
    Alpha extraction logic: alpha = max(R, G, B) / 255.0
    Returns a numpy array of shape (H, W) with float values 0-1.
    """
    bg_data = np.array(bg_image.convert('RGB')).astype(np.float32)
    alpha_map = np.max(bg_data, axis=2) / 255.0
    return alpha_map

def remove_watermark(image_path, output_path, assets_dir):
    if not os.path.exists(image_path):
        print(f"Error: {image_path} not found for watermark removal.")
        return

    try:
        img = Image.open(image_path).convert('RGBA')
    except Exception as e:
        print(f"Error loading image for watermark removal: {e}")
        return

    width, height = img.size
    
    # Logic from engine.js: getWatermarkInfo
    is_large = width > 1024 and height > 1024
    size = 96 if is_large else 48
    margin = 64 if is_large else 32
    
    x = width - margin - size
    y = height - margin - size
    
    # Load reference background image
    bg_filename = f"bg_{size}.png"
    bg_path = os.path.join(assets_dir, bg_filename)
    
    if not os.path.exists(bg_path):
        print(f"Warning: Asset {bg_filename} not found at {bg_path}. Skipping watermark removal.")
        return

    try:
        bg_img = Image.open(bg_path)
    except Exception as e:
        print(f"Error loading asset {bg_path}: {e}")
        return

    if bg_img.size != (size, size):
        bg_img = bg_img.resize((size, size))
        
    alpha_map = calculate_alpha_map(bg_img)
    img_data = np.array(img).astype(np.float32)
    
    ALPHA_THRESHOLD = 0.002
    MAX_ALPHA = 0.99
    LOGO_VALUE = 255.0

    roi = img_data[y:y+size, x:x+size]
    alpha_expanded = alpha_map[:, :, np.newaxis] 
    active_mask = alpha_expanded > ALPHA_THRESHOLD
    alpha_clamped = np.minimum(alpha_expanded, MAX_ALPHA)
    roi_cleaned = roi.copy()
    
    for c in range(3): # R, G, B
        channel = roi[:, :, c]
        restored = (channel - alpha_clamped[:, :, 0] * LOGO_VALUE) / (1.0 - alpha_clamped[:, :, 0])
        np.putmask(roi_cleaned[:, :, c], active_mask[:, :, 0], restored)
        
    roi_cleaned = np.clip(roi_cleaned, 0, 255)
    img_data[y:y+size, x:x+size] = roi_cleaned
    
    result_img = Image.fromarray(img_data.astype(np.uint8))
    result_img.save(output_path)
    print(f"Watermark removed and saved to {output_path}")


# Dimension prompt to append to every scene - strongly emphasizes the exact ratio and quality
DIMENSION_PROMPT = """
 CRITICAL IMAGE REQUIREMENTS (MUST FOLLOW):


ART STYLE DEFINITION:

- Medium: Digital imitation of chalk pastel, dry brush gouache, and soft textured acrylics.

- Texture: Heavy usage of grain, noise, stippling, and paper texture. No smooth/plastic surfaces.

- Visuals: Lineless art (no harsh black outlines), soft edges, volumetric shapes, glowing ambient lighting .

- Atmosphere: Nighttime cozy, magical, dimly lit room with glowing magical elements.

- Font Style: Casual, hand-lettered sans-serif, slightly organic/wobbly (like a crayon or marker).


FORMATTING RULES (Strict Adherence):

- Aspect Ratio: Wide Panoramic Spread (17" x 8.5" equivalent) --ar 2:1.

- Composition: Seamless double-page spread. Do NOT place main characters in the exact center (gutter).

- Text Placement: Text must be distinct and legible. Place text in "Negative Space" on the far LEFT or far RIGHT to prevent spine splitting.

- Framing: FULL BLEED. Fill the canvas completely.


RESOLUTION & QUALITY:

- Generate the image in the HIGHEST RESOLUTION possible (4K quality preferred)

- Use maximum detail and sharpness

- Professional print-quality output

- Ultra high definition with crisp details


PROHIBITED:

- Do NOT write measurement numbers (like "17 inches") on the image

- Do NOT add white borders

- Do NOT use speech bubbles (blend text into the environment)

- DO NOT generate square images

- DO NOT generate portrait/vertical images


"""


async def generate_book_images():
    """Main function to generate book images using gemini_webapi."""
    
    # Read output.json
    try:
        with open('output.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: output.json not found.")
        return

    system_prompt = data.get('systemprompt', '')
    pages = data.get('pages', [])

    if not pages:
        print("Error: No pages found in output.json")
        return

    # Ensure input directory exists
    os.makedirs('input', exist_ok=True)

    # Initialize the Gemini client
    print("Initializing Gemini client...")
    client = GeminiClient(Secure_1PSID, Secure_1PSIDTS, proxy=None)
    await client.init(timeout=350, auto_close=False, close_delay=300, auto_refresh=True)
    print("Client initialized successfully!")

    # Chat session metadata file for resuming
    chat_metadata_file = "chat_session.json"
    chat = None
    
    if os.path.exists(chat_metadata_file) and START_PAGE > 1:
        # Only reuse existing chat if we're resuming from a later page
        try:
            with open(chat_metadata_file, 'r') as f:
                saved_metadata = json.load(f)
            print(f"Loading existing chat session from {chat_metadata_file}...")
            chat = client.start_chat(metadata=saved_metadata, model=Model.G_3_0_PRO)
            print("Existing chat session loaded successfully!")
        except Exception as e:
            print(f"Could not load existing chat session: {e}")
            chat = None
    
    if chat is None:
        # Start a fresh new chat session with Gemini 2.5 Pro model
        print("Starting new chat session with Gemini 2.5 Pro...")
        chat = client.start_chat(model=Model.G_3_0_PRO)
        print("New chat session created with Gemini 2.5 Pro!")

    print(f"\nStarting image generation for {len(pages)} pages...")
    print(f"Starting from page {START_PAGE}\n")

    for i, page_prompt in enumerate(pages):
        page_num = i + 1
        
        # Skip pages before START_PAGE
        if page_num < START_PAGE:
            print(f"Skipping page {page_num}/{len(pages)} (already processed)...")
            continue

        print(f"\n{'='*50}")
        print(f"Processing page {page_num}/{len(pages)}...")
        print(f"{'='*50}")

        # Build the prompt
        if page_num == 1 or (START_PAGE > 1 and page_num == START_PAGE):
            # First prompt: include system prompt + scene + dimension prompt
            full_prompt = f"""You are a children's book illustrator. Please follow these guidelines for ALL illustrations in this conversation:

{system_prompt}

Now generate an illustration for this scene:

{page_prompt}

{DIMENSION_PROMPT}
"""
            print("Sending system prompt + first scene...")
        else:
            # Following prompts: just the scene
            full_prompt = f"""{page_prompt}

{DIMENSION_PROMPT}
"""

        try:
            print(f"Generating image...")
            
            response = await chat.send_message(full_prompt)
                
            print(f"Thoughts: {response.thoughts[:200] if response.thoughts else 'None'}...")
            print(f"Text: {response.text[:200] if response.text else 'None'}...")

            # Save generated images directly (no PIL processing)
            image_saved = False
            
            # Check for images in the response
            if response.images:
                print(f"Images count: {len(response.images)}")
                for j, image in enumerate(response.images):
                    # Use page number as filename
                    if j == 0:
                        filename = f"{page_num}.png"
                    else:
                        filename = f"{page_num}_{j}.png"
                    
                    await image.save(path="input/", filename=filename, verbose=True)
                    image_saved = True
                    print(f"Saved image: input/{filename}")
                    
                    # Remove watermark
                    full_image_path = os.path.join("input", filename)
                    assets_dir = os.path.dirname(os.path.abspath(__file__))
                    print(f"Removing watermark from {full_image_path}...")
                    remove_watermark(full_image_path, full_image_path, assets_dir)


            if image_saved:
                # Save chat session metadata after each successful page
                try:
                    with open(chat_metadata_file, 'w') as f:
                        json.dump(chat.metadata, f)
                    print(f"Chat session saved to {chat_metadata_file}")
                except Exception as e:
                    print(f"Warning: Could not save chat session: {e}")
            else:
                print(f"Warning: No image generated for page {page_num}, moving to next page...")

        except Exception as e:
            print(f"Error generating page {page_num}: {e}")
            print("Moving to next page...")
        
        # Wait 40 seconds before next page
        if page_num < len(pages):
            print(f"Waiting 40 seconds before next page...")
            await asyncio.sleep(10)

    print(f"\n{'='*50}")
    print("Image generation complete!")
    print(f"{'='*50}")


async def main():
    """Entry point."""
    await generate_book_images()


if __name__ == "__main__":
    asyncio.run(main())