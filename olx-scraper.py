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
    # Use the direct search URL format for OLX India
    search_url = f"https://www.olx.in/en-in/delhi_g4058659/cars_c84{search_query.replace(' ', '-')}"
    
    all_items = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.olx.in/',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    for page in range(1, num_pages + 1):
        try:
            # Add page parameter if not the first page
            url = search_url
            if page > 1:
                url = f"{search_url}?page={page}"
            
            print(f"Scraping page {page}: {url}")
            print("Downloading page content...")
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise exception for 4XX/5XX status codes
            
            # Save HTML to debug (optional)
            with open(f"olx_page_{page}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved HTML to olx_page_{page}.html for debugging")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try multiple potential selectors for item listings
            selectors = [
                'li.EIR5N',                           # Old selector
                'li[data-aut-id="itemBox"]',          # Alternative old selector
                'div[data-aut-id="itemCard"]',        # Possible new selector
                'div.ee2b0479',                       # Class-based selector
                'div.a0db33f2',                       # Another possible class
                'div._7e3920c1',                      # Another possible class
                'a._6d5b4928'                         # Product link wrapper
            ]
            
            item_listings = []
            for selector in selectors:
                item_listings = soup.select(selector)
                if item_listings:
                    print(f"Found {len(item_listings)} listings using selector: {selector}")
                    break
            
            if not item_listings:
                print("No listings found with any of the selectors. Trying general approach...")
                # Try a more general approach - find all product cards by looking for common patterns
                possible_listings = soup.find_all(['div', 'li', 'a'], class_=True)
                for element in possible_listings:
                    # Look for elements that might be product cards
                    if element.find('span', string=lambda text: text and "₹" in text):
                        item_listings.append(element)
                
            if not item_listings:
                print(f"Still no listings found. Stopping at page {page}.")
                break
                
            print(f"Found {len(item_listings)} listings on page {page}")
            
            for item in item_listings:
                try:
                    # Try multiple selectors for each field
                    
                    # Extract title with multiple potential selectors
                    title = "No title"
                    title_selectors = [
                        '[data-aut-id="itemTitle"]', 
                        'span._2tW1I', 
                        'span[title]',
                        '.a5112ca8',
                        '.ee6029c6'
                    ]
                    for selector in title_selectors:
                        title_element = item.select_one(selector)
                        if title_element:
                            title = title_element.text.strip()
                            break
                    
                    # If still no title, look for any heading element
                    if title == "No title":
                        heading_elements = item.find_all(['h2', 'h3', 'h4'])
                        if heading_elements:
                            title = heading_elements[0].text.strip()
                    
                    # Extract price with multiple potential selectors
                    price = "Price not specified"
                    price_selectors = [
                        '[data-aut-id="itemPrice"]',
                        'span._89yzn',
                        'span._2Ks63',
                        'span._1zgtX',
                        'span.f41f9a37',
                        'span[aria-label*="price"]'
                    ]
                    for selector in price_selectors:
                        price_element = item.select_one(selector)
                        if price_element:
                            price = price_element.text.strip()
                            break
                    
                    # If still no price, try to find any element with ₹ symbol
                    if price == "Price not specified":
                        price_matches = [e.text.strip() for e in item.find_all(string=lambda s: s and '₹' in s)]
                        if price_matches:
                            price = price_matches[0]
                    
                    # Extract location with multiple potential selectors
                    location = "Location not specified"
                    location_selectors = [
                        '[data-aut-id="item-location"]',
                        'span._2TVI3',
                        'span._1KOFM',
                        'span._2FRXm',
                        'span.fc2d3494',
                        '.f059bf95'
                    ]
                    for selector in location_selectors:
                        location_element = item.select_one(selector)
                        if location_element:
                            location = location_element.text.strip()
                            break
                    
                    # Extract posting date with multiple potential selectors
                    date = "Date not specified"
                    date_selectors = [
                        '[data-aut-id="item-date"]',
                        'span._2Kz3m',
                        'span._2DGqt',
                        'span.e9efc01a',
                        'span[aria-label*="post"]'
                    ]
                    for selector in date_selectors:
                        date_element = item.select_one(selector)
                        if date_element:
                            date = date_element.text.strip()
                            break
                    
                    # Extract link
                    link = "No link"
                    # If the item itself is an anchor tag
                    if item.name == 'a' and 'href' in item.attrs:
                        link = item['href']
                    else:
                        link_element = item.select_one('a')
                        if link_element and 'href' in link_element.attrs:
                            link = link_element['href']
                    
                    # Ensure the link is absolute
                    if link != "No link" and not link.startswith('http'):
                        link = "https://www.olx.in" + link
                    
                    # Extract image URL with multiple potential selectors
                    img_url = "No image"
                    img_selectors = ['img', '[data-aut-id="itemImage"]']
                    for selector in img_selectors:
                        img_element = item.select_one(selector)
                        if img_element:
                            for attr in ['src', 'data-src', 'srcset']:
                                if attr in img_element.attrs:
                                    img_url = img_element[attr]
                                    break
                            if img_url != "No image":
                                break
                    
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
        
        print("\nSUCCESS! Results saved to:")
        print(f"- {json_filename} (JSON format)")
        print(f"- {csv_filename} (CSV format)")
        print("\nYou can open the CSV file in Excel or any spreadsheet program.")
    else:
        print("No results found. Please check the HTML files saved to see what's on the actual page.")

if __name__ == "__main__":
    main()