"""
Card Image Downloader
Downloads card images for the Literature Card Game
"""
import os
import requests
import logging
from PIL import Image, ImageDraw
import urllib.request

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

# Card suits and ranks
SUITS = ['hearts', 'diamonds', 'clubs', 'spades']
RANKS = ['a', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k']

# Base URL for downloading card images
BASE_URL = "https://deckofcardsapi.com/static/img"

def download_card_images():
    """Download card images if they don't exist"""
    # Define the URL pattern for the card images
    base_url = "https://deckofcardsapi.com/static/img/"
    
    # Map our suit and rank names to the ones used in the API
    suit_map = {'Hearts': 'H', 'Diamonds': 'D', 'Clubs': 'C', 'Spades': 'S'}
    rank_map = {'A': 'A', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', 
                '7': '7', '8': '8', '9': '9', '10': '0', 'J': 'J', 'Q': 'Q', 'K': 'K'}
    
    # Download each card image
    for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
        for rank in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']:
            # The API uses a different naming convention than our game
            api_code = f"{rank_map[rank]}{suit_map[suit]}"
            api_url = f"{base_url}{api_code}.png"
            
            # Define our filename (e.g., hearts_a.png)
            filename = f"{suit.lower()}_{rank.lower()}.png"
            output_path = os.path.join('assets', 'cards', filename)
            
            # Skip if file already exists
            if os.path.exists(output_path):
                continue
                
            try:
                # Print debug info for 10 cards specifically
                if rank == '10':
                    print(f"Downloading 10 card: {api_url} -> {output_path}")
                
                # Download the image
                urllib.request.urlretrieve(api_url, output_path)
                print(f"Downloaded: {filename}")
            except Exception as e:
                print(f"Error downloading {filename}: {str(e)}")

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