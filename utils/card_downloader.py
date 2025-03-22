"""
Card Image Downloader
Downloads card images for the Literature Card Game
"""
import os
import requests
import logging
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

# Card suits and ranks
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['a', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']

# Base URL for downloading card images
BASE_URL = "https://deckofcardsapi.com/static/img"

def download_card_images():
    """Download card images from the Deck of Cards API"""
    output_dir = os.path.join('assets', 'cards')
    os.makedirs(output_dir, exist_ok=True)
    
    downloaded = 0
    failed = 0
    
    for suit in SUITS:
        for rank in RANKS:
            # Define the output filename
            output_file = os.path.join(output_dir, f"{suit}_{rank}.png")
            
            # Skip if the file already exists
            if os.path.exists(output_file):
                log.info(f"Image already exists: {output_file}")
                downloaded += 1
                continue
            
            # Format for the API: for example 'AS' for Ace of Spades, '10H' for 10 of Hearts
            suit_code = suit[0].upper()
            rank_code = rank.upper() if rank != '10' else '10'
            card_code = f"{rank_code}{suit_code}"
            
            # Download the image
            url = f"{BASE_URL}/{card_code}.png"
            log.info(f"Downloading {card_code} from {url}")
            
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(output_file, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    downloaded += 1
                    log.info(f"Downloaded {card_code} to {output_file}")
                else:
                    log.error(f"Failed to download {card_code}: {response.status_code}")
                    failed += 1
            except Exception as e:
                log.error(f"Error downloading {card_code}: {e}")
                failed += 1
    
    # Create a card back image
    create_card_back_image(os.path.join(output_dir, "card_back.png"))
    
    log.info(f"Downloaded {downloaded} card images, {failed} failed")
    return downloaded, failed

def create_card_back_image(output_file):
    """Create a simple card back image"""
    if os.path.exists(output_file):
        log.info(f"Card back image already exists: {output_file}")
        return
    
    try:
        # Create a simple blue card back
        img = Image.new('RGB', (140, 190), color=(30, 60, 180))
        d = ImageDraw.Draw(img)
        d.rectangle([(5, 5), (135, 185)], outline=(255, 255, 255), width=2)
        
        # Add some decoration
        for i in range(0, 120, 20):
            d.rectangle([(20 + i//4, 20 + i//4), (120 - i//4, 170 - i//4)], 
                        outline=(200, 200, 250), width=1)
        
        img.save(output_file)
        log.info(f"Created card back image: {output_file}")
    except Exception as e:
        log.error(f"Failed to create card back image: {e}")

if __name__ == "__main__":
    log.info("Starting card image download")
    download_card_images()
    log.info("Card image download complete") 