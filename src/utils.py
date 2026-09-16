"""Utility functions for OLX Indonesia scraper."""
import re
from typing import Optional
from camoufox.async_api import AsyncCamoufox


def _parse_proxy(proxy_url: str) -> dict:
    """Parse Apify proxy URL into Camoufox proxy dict."""
    if not proxy_url:
        return {}
    
    # Extract components from proxy URL
    # Format: http://username:password@proxy.apify.com:8000
    match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
    if not match:
        return {}
    
    username, password, server, port = match.groups()
    
    return {
        'server': f'http://{server}:{port}',
        'username': username,
        'password': password,
    }


async def _fetch(url: str, proxy_url: Optional[str] = None, wait_selector: Optional[str] = None) -> Optional[str]:
    """Fetch a URL using Camoufox browser automation.
    
    Args:
        url: URL to fetch
        proxy_url: Optional Apify proxy URL
        wait_selector: Optional CSS selector to wait for
        
    Returns:
        HTML content or None if failed
    """
    proxy_config = _parse_proxy(proxy_url) if proxy_url else None
    
    try:
        async with AsyncCamoufox(
            headless=True,
            geoip=True,
            proxy=proxy_config,
        ) as browser:
            page = await browser.new_page()
            
            # Navigate to URL
            await page.goto(url, wait_until='networkidle', timeout=90000)
            
            # Wait for selector if provided
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:
                    pass  # Continue even if selector not found
            
            # Extra wait for dynamic content
            await page.wait_for_timeout(3000)
            
            # Get HTML
            html = await page.content()
            
            # Debug logging
            print(f"Fetched URL: {url}")
            print(f"HTML length: {len(html)}")
            print(f"First 500 chars: {html[:500]}")
            
            await page.close()
            
            # Verify we got meaningful content
            if len(html) < 500:
                return None
            
            return html
            
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
