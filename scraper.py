import requests
from bs4 import BeautifulSoup
import json
import time
import re
import codegen

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def scrape_property(url):
    try:
        print(f"Catenary Systems Scraper v{codegen.ver()}")
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        codelist = url.split("/")
        code = codelist[6]

        # Extract price
        price_tag = soup.find("div", class_="price")
        price = price_tag.get_text(strip=True) if price_tag else "N/A"

        desc_tag = soup.find("p", class_="description")
        desc = desc_tag.get_text(strip=True) if desc_tag else "N/A"

        # Search all spans and look for one containing 'Υπνοδωμάτια:'
        bed_tag = None
        for span in soup.find_all('span'):
            full_text = span.get_text(strip=False)
            if "Υπνοδωμάτια:" in full_text:
                bed_tag = span
                break
        bedtext = bed_tag.find_next_sibling("span")
        beds = bedtext.get_text(strip=True)
        print(bedtext)
        
        bath_tag = None
        for span in soup.find_all('span'):
            full_text = span.get_text(strip=False)
            if "Μπάνια:" in full_text:
                bath_tag = span
                break
        bathtext = bath_tag.find_next_sibling("span")
        baths = bathtext.get_text(strip=True)
        print(bathtext)

        floor_tag = None
        for span in soup.find_all('span'):
            full_text = span.get_text(strip=False)
            if "Όροφος:" in full_text:
                floor_tag = span
                break
        floortext = floor_tag.find_next_sibling("span")
        floors = floortext.get_text(strip=True)
        print(floortext)



        # Extract all image URLs
        image_tags = soup.select('div.image-gallery img') or soup.select('img[src]')
        images = []

        for img in image_tags:
            src = img.get("data-src") or img.get("src")
            if src and src.startswith("http"):
                images.append(src)

        return {
            "url": "https://xe.gr/p/"+code,
            "code": code,
            "price": price,
            "description": desc,
            "bedrooms": beds,
            "bathrooms": baths,
            "floor": floors,
            "images": images
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {
            "url": url,
            "error": str(e)
        }

def main(infile):
    with open(infile, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    for i, url in enumerate(urls, 1):
        print(f"Scraping ({i}/{len(urls)}): NO1")
        data = scrape_property(url)
        results.append(data)
        time.sleep(1)  # Be polite to the server

    # Save to out.json
    with open("out.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print("✅ Done. Data saved to out.json")

if __name__ == "__main__":
    main()
