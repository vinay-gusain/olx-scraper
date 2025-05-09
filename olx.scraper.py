import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
from datetime import datetime

def scrape_olx_search_results(search_query, num_pages=3):
    """
    Scrape OLX search results for the given query.
    
    Args:
        search_query (str): The search query term
        num_pages (int): Number of pages to scrape
        
    Returns:
        list: List of dictionaries containing product information
    """
    base_url = "https://www.olx.in/en-in/delhi_g4058659/cars_c84"
    search_url = base_url + search_query.replace(" ", "-")
    
    all_items = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    for page in range(1, num_pages + 1):
        try:
            # Add page parameter if not the first page
            url = search_url
            if page > 1:
                url = f"{search_url}?page={page}"
            
            print(f"Scraping page {page}: {url}")
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all item listings
            # Note: The exact CSS selector may need adjustment based on OLX's current HTML structure
            item_listings = soup.select('li.EIR5N')
            
            if not item_listings:
                print(f"No listings found on page {page}. The selector might need updating.")
                # Try an alternative selector
                item_listings = soup.select('li[data-aut-id="itemBox"]')
            
            if not item_listings:
                print(f"Still no listings found. Stopping at page {page}.")
                break
                
            print(f"Found {len(item_listings)} listings on page {page}")
            
            for item in item_listings:
                try:
                    # Extract title
                    title_element = item.select_one('[data-aut-id="itemTitle"]')
                    title = title_element.text.strip() if title_element else "No title"
                    
                    # Extract price
                    price_element = item.select_one('[data-aut-id="itemPrice"]')
                    price = price_element.text.strip() if price_element else "Price not specified"
                    
                    # Extract location
                    location_element = item.select_one('[data-aut-id="item-location"]')
                    location = location_element.text.strip() if location_element else "Location not specified"
                    
                    # Extract posting date
                    date_element = item.select_one('[data-aut-id="item-date"]')
                    date = date_element.text.strip() if date_element else "Date not specified"
                    
                    # Extract link
                    link_element = item.select_one('a')
                    link = "https://www.olx.in" + link_element['href'] if link_element and 'href' in link_element.attrs else "No link"
                    
                    # Extract image URL if available
                    img_element = item.select_one('img')
                    img_url = img_element['src'] if img_element and 'src' in img_element.attrs else "No image"
                    
                    item_data = {
                        'title': title,
                        'price': price,
                        'location': location,
                        'date': date,
                        'link': link,
                        'image_url': img_url
                    }
                    
                    all_items.append(item_data)
                    
                except Exception as e:
                    print(f"Error extracting item data: {e}")
            
            # Add a small delay to avoid hitting the server too hard
            time.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
    
    return all_items

def save_to_json(data, filename):
    """Save data to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")

def save_to_csv(data, filename):
    """Save data to a CSV file"""
    if not data:
        print("No data to save to CSV")
        return
        
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Data saved to {filename}")

def main():
    search_query = "car cover"
    num_pages = 3  # Adjust based on how many pages you want to scrape
    
    print(f"Starting to scrape OLX for '{search_query}'...")
    results = scrape_olx_search_results(search_query, num_pages)
    
    if results:
        print(f"Found {len(results)} listings")
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save data in both JSON and CSV formats
        json_filename = f"olx_{search_query.replace(' ', '_')}_{timestamp}.json"
        csv_filename = f"olx_{search_query.replace(' ', '_')}_{timestamp}.csv"
        
        save_to_json(results, json_filename)
        save_to_csv(results, csv_filename)
    else:
        print("No results found")

if __name__ == "__main__":
    main()