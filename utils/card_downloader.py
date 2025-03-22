import os
import requests
import shutil
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def ensure_directory(directory):
    """Make sure the directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_card_images(target_dir='static/images/cards'):
    """Download card images from a public API"""
    # Define output directory
    output_dir = target_dir
    ensure_directory(output_dir)
    
    # Use the Deck of Cards API
    base_url = "https://deckofcardsapi.com/static/img"
    
    # We need cards 2-7, 9-A of all suits (no 8s)
    suits = {
        'hearts': 'H',
        'diamonds': 'D', 
        'clubs': 'C',
        'spades': 'S'
    }
    
    ranks = {
        '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7',
        '9': '9', '10': '0', 'jack': 'J', 'queen': 'Q', 'king': 'K', 'ace': 'A'
    }
    
    # Download each card
    cards_downloaded = 0
    for rank_name, rank_code in ranks.items():
        for suit_name, suit_code in suits.items():
            # Format for the API is like "2H.png" for 2 of Hearts
            # But their 10 is "0"
            filename = f"{rank_code}{suit_code}.png"
            target_filename = f"{rank_name}_of_{suit_name}.png" 
            url = f"{base_url}/{filename}"
            
            output_path = os.path.join(output_dir, target_filename)
            
            # Skip if already downloaded
            if os.path.exists(output_path):
                continue
                
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        shutil.copyfileobj(response.raw, f)
                    logger.info(f"Downloaded {target_filename}")
                    cards_downloaded += 1
                else:
                    logger.error(f"Failed to download {url}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")
    
    # Download card back
    back_url = f"{base_url}/back.png"
    back_path = os.path.join(output_dir, "card_back.png")
    
    if not os.path.exists(back_path):
        try:
            response = requests.get(back_url, stream=True)
            if response.status_code == 200:
                with open(back_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                logger.info("Downloaded card back")
                cards_downloaded += 1
            else:
                logger.error(f"Failed to download card back: {response.status_code}")
        except Exception as e:
            logger.error(f"Error downloading card back: {e}")
    
    logger.info(f"Downloaded {cards_downloaded} card images")
    return cards_downloaded

if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the download script
    download_card_images() 