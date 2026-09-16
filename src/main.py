"""Main entry point for OLX Indonesia scraper."""
import asyncio
from datetime import datetime
from typing import Optional
from apify import Actor
from .utils import _fetch
from .parser import parse_listing_page, parse_detail_page


async def main() -> None:
    """Main scraper function."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        search_query = actor_input.get('searchQuery', 'mobil')
        category = actor_input.get('category', 'all')
        location = actor_input.get('location', 'jakarta')
        price_min = actor_input.get('priceMin', 0)
        price_max = actor_input.get('priceMax', 100000000)
        sort_by = actor_input.get('sortBy', 'date')
        include_description = actor_input.get('includeDescription', True)
        max_results = actor_input.get('maxResults', 50)
        proxy_config = actor_input.get('proxyConfiguration', {})
        
        Actor.log.info(f'Starting OLX Indonesia scraper for query: {search_query}')
        Actor.log.info(f'Location: {location}, Category: {category}, Max results: {max_results}')
        
        # Get proxy URL
        proxy_url = None
        if proxy_config.get('useApifyProxy'):
            proxy_configuration = await Actor.create_proxy_configuration(
                groups=proxy_config.get('apifyProxyGroups', ['RESIDENTIAL'])
            )
            proxy_url = await proxy_configuration.new_url()
        
        # Build search URL
        base_url = 'https://www.olx.co.id'
        search_url = f'{base_url}/items/q-{search_query}'
        
        # Add location if specified
        if location and location != 'all':
            search_url = f'{base_url}/{location}/q-{search_query}'
        
        Actor.log.info(f'Search URL: {search_url}')
        
        # Track progress
        item_count = 0
        request_count = 0
        error_count = 0
        page = 1
        
        # Paginate through results
        while item_count < max_results:
            # Build page URL
            page_url = search_url
            if page > 1:
                page_url = f'{search_url}?page={page}'
            
            Actor.log.info(f'Fetching page {page}: {page_url}')
            
            # Fetch page with retries
            html = None
            for attempt in range(3):
                try:
                    html = await _fetch(page_url, proxy_url, wait_selector='li[data-aut-id]')
                    request_count += 1
                    if html:
                        break
                except Exception as e:
                    Actor.log.warning(f'Attempt {attempt + 1} failed: {e}')
                    error_count += 1
                    if attempt < 2:
                        await asyncio.sleep(5 * (attempt + 1))
            
            if not html:
                Actor.log.error(f'Failed to fetch page {page} after 3 attempts')
                break
            
            # Parse listings
            listings = parse_listing_page(html)
            Actor.log.info(f'Found {len(listings)} listings on page {page}')
            
            if not listings:
                Actor.log.info('No more listings found, stopping pagination')
                break
            
            # Process each listing
            for listing in listings:
                if item_count >= max_results:
                    break
                
                try:
                    # If include_description is True, fetch detail page
                    if include_description and listing.get('url'):
                        detail_url = listing['url']
                        Actor.log.info(f'Fetching detail page: {detail_url}')
                        
                        detail_html = None
                        for attempt in range(3):
                            try:
                                detail_html = await _fetch(detail_url, proxy_url)
                                request_count += 1
                                if detail_html:
                                    break
                            except Exception as e:
                                Actor.log.warning(f'Detail fetch attempt {attempt + 1} failed: {e}')
                                error_count += 1
                                if attempt < 2:
                                    await asyncio.sleep(2 * (attempt + 1))
                        
                        if detail_html:
                            # Parse detail page
                            full_listing = parse_detail_page(detail_html, detail_url)
                            listing.update(full_listing)
                    
                    # Ensure scrapedAt is set
                    if 'scrapedAt' not in listing:
                        listing['scrapedAt'] = datetime.utcnow().isoformat() + 'Z'
                    
                    # Fill in None for missing fields instead of crashing
                    listing.setdefault('url', None)
                    listing.setdefault('title', None)
                    listing.setdefault('price', None)
                    listing.setdefault('location', None)
                    listing.setdefault('category', None)
                    listing.setdefault('description', None)
                    listing.setdefault('seller', None)
                    listing.setdefault('postedDate', None)
                    listing.setdefault('imageUrl', None)
                    
                    # Push to dataset
                    await Actor.push_data(listing)
                    item_count += 1
                    
                    # Log progress every 10 items
                    if item_count % 10 == 0:
                        Actor.log.info(f'Progress: {item_count}/{max_results} items scraped')
                    
                except Exception as e:
                    Actor.log.error(f'Error processing listing: {e}')
                    error_count += 1
                    continue
            
            # Move to next page
            page += 1
            
            # Avoid rate limiting
            await asyncio.sleep(2)
        
        # Save task context
        await Actor.set_value('SAVED-TASK', {
            'actorId': Actor.config.actor_id,
            'actorRunId': Actor.config.actor_run_id,
            'defaultDatasetId': Actor.config.default_dataset_id,
            'startedAt': Actor.config.started_at.isoformat() if Actor.config.started_at else None,
            'input': actor_input,
            'stats': {
                'itemsScraped': item_count,
                'requestsMade': request_count,
                'errors': error_count,
            }
        })
        
        Actor.log.info('=== SCRAPING COMPLETE ===')
        Actor.log.info(f'Total items scraped: {item_count}')
        Actor.log.info(f'Total requests made: {request_count}')
        Actor.log.info(f'Total errors: {error_count}')


if __name__ == '__main__':
    asyncio.run(main())
