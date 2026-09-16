"""Parser functions for extracting data from OLX Indonesia pages."""
import re
import json
from typing import List, Dict, Optional
from datetime import datetime


def _extract_next_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ JSON from HTML."""
    try:
        match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return data
    except Exception as e:
        print(f"Failed to extract __NEXT_DATA__: {e}")
    return None


def parse_listing_page(html: str) -> List[Dict[str, str]]:
    """Parse listings from OLX search results page.
    
    Args:
        html: HTML content of search results page
        
    Returns:
        List of listing dictionaries with basic info
    """
    # Try __NEXT_DATA__ first
    next_data = _extract_next_data(html)
    if next_data:
        try:
            # Navigate the Next.js data structure
            props = next_data.get('props', {})
            page_props = props.get('pageProps', {})
            data = page_props.get('data', {})
            
            # Look for listings in various possible locations
            listings = data.get('results', []) or data.get('items', []) or []
            
            results = []
            for item in listings:
                listing = {
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'price': item.get('price', {}).get('value', {}).get('display', '') if isinstance(item.get('price'), dict) else str(item.get('price', '')),
                    'location': item.get('location', {}).get('name', '') if isinstance(item.get('location'), dict) else str(item.get('location', '')),
                    'category': item.get('category', {}).get('name', '') if isinstance(item.get('category'), dict) else str(item.get('category', '')),
                    'imageUrl': item.get('images', [{}])[0].get('url', '') if item.get('images') else '',
                }
                
                # Ensure URL is absolute
                if listing['url'] and not listing['url'].startswith('http'):
                    listing['url'] = f"https://www.olx.co.id{listing['url']}"
                
                results.append(listing)
            
            if results:
                return results
                
        except Exception as e:
            print(f"Failed to parse __NEXT_DATA__ listings: {e}")
    
    # Fallback: Parse HTML directly
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    results = []
    
    # Try to find listing containers
    # OLX uses data-aut-id attributes
    containers = soup.find_all('li', {'data-aut-id': True})
    
    for container in containers:
        try:
            # Extract title and URL
            title_elem = container.find('a', href=lambda x: x and '/item/' in x)
            if not title_elem:
                continue
            
            url = title_elem.get('href', '')
            if url and not url.startswith('http'):
                url = f"https://www.olx.co.id{url}"
            
            title_text = title_elem.get_text(strip=True)
            
            # Extract price
            price_elem = container.find(string=lambda x: x and 'Rp' in str(x))
            price = price_elem.strip() if price_elem else None
            
            # Extract location
            location_elem = container.find(['span', 'div'], string=lambda x: x and any(city in str(x).lower() for city in ['jakarta', 'bandung', 'surabaya', 'kota', 'kabupaten']))
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Extract image
            img_elem = container.find('img')
            image_url = img_elem.get('src', '') if img_elem else None
            
            listing = {
                'url': url,
                'title': title_text,
                'price': price,
                'location': location,
                'category': None,
                'imageUrl': image_url,
            }
            
            results.append(listing)
            
        except Exception as e:
            print(f"Failed to parse listing container: {e}")
            continue
    
    return results


def parse_detail_page(html: str, base_url: str) -> Dict[str, Optional[str]]:
    """Parse detail page to extract full listing information.
    
    Args:
        html: HTML content of detail page
        base_url: URL of the detail page
        
    Returns:
        Dictionary with all listing fields
    """
    # Try __NEXT_DATA__ first
    next_data = _extract_next_data(html)
    if next_data:
        try:
            props = next_data.get('props', {})
            page_props = props.get('pageProps', {})
            data = page_props.get('data', {})
            
            return {
                'url': base_url,
                'title': data.get('title', ''),
                'price': data.get('price', {}).get('value', {}).get('display', '') if isinstance(data.get('price'), dict) else str(data.get('price', '')),
                'location': data.get('location', {}).get('name', '') if isinstance(data.get('location'), dict) else '',
                'category': data.get('category', {}).get('name', '') if isinstance(data.get('category'), dict) else '',
                'description': data.get('description', ''),
                'seller': data.get('user', {}).get('name', '') if isinstance(data.get('user'), dict) else '',
                'postedDate': data.get('created_at', ''),
                'imageUrl': data.get('images', [{}])[0].get('url', '') if data.get('images') else '',
                'scrapedAt': datetime.utcnow().isoformat() + 'Z',
            }
        except Exception as e:
            print(f"Failed to parse __NEXT_DATA__ detail: {e}")
    
    # Fallback: Parse HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract fields with fallbacks
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else None
    
    price_elem = soup.find(string=lambda x: x and 'Rp' in str(x))
    price = price_elem.strip() if price_elem else None
    
    # Description
    desc_elem = soup.find(['div', 'p'], class_=lambda x: x and 'description' in str(x).lower())
    description = desc_elem.get_text(strip=True) if desc_elem else None
    
    # Seller
    seller_elem = soup.find(['span', 'div'], class_=lambda x: x and 'seller' in str(x).lower())
    seller = seller_elem.get_text(strip=True) if seller_elem else None
    
    # Location
    location_elem = soup.find(string=lambda x: x and any(city in str(x).lower() for city in ['jakarta', 'bandung', 'surabaya', 'kota']))
    location = location_elem.strip() if location_elem else None
    
    # Image
    img_elem = soup.find('img', src=lambda x: x and 'olx' in str(x).lower())
    image_url = img_elem.get('src', '') if img_elem else None
    
    return {
        'url': base_url,
        'title': title,
        'price': price,
        'location': location,
        'category': None,
        'description': description,
        'seller': seller,
        'postedDate': None,
        'imageUrl': image_url,
        'scrapedAt': datetime.utcnow().isoformat() + 'Z',
    }
