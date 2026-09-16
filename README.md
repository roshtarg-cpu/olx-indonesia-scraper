# OLX Indonesia Scraper

Extract classified listings from OLX Indonesia (olx.co.id) - the leading classifieds platform in Indonesia.

## Features

- **Comprehensive Data**: Extract vehicles, property, electronics, jobs, and services
- **Rich Details**: Titles, prices, locations, descriptions, seller info, images
- **Flexible Filtering**: Search by keywords, category, location, price range
- **AI-Ready Output**: Clean structured data for analysis and automation
- **Residential Proxies**: Built-in Apify proxy support for reliability

## Use Cases

- Market research and price analysis
- Competitor monitoring
- Lead generation
- Data aggregation platforms
- Price comparison tools

## Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `searchQuery` | String | No | Search keywords (e.g., 'mobil', 'laptop') |
| `category` | String | No | Filter by category (vehicles, property, electronics, jobs, services) |
| `location` | String | No | City or region (e.g., 'jakarta', 'bandung') |
| `priceMin` | Integer | No | Minimum price in Rupiah |
| `priceMax` | Integer | No | Maximum price in Rupiah |
| `sortBy` | String | No | Sort order (relevance, date, price_asc, price_desc) |
| `includeDescription` | Boolean | No | Extract full descriptions (slower) |
| `maxResults` | Integer | Yes | Maximum items to scrape (1-500) |

## Output Schema

Each listing includes:

- `url` - Link to the listing
- `title` - Item title
- `price` - Price in Rupiah
- `location` - City/region
- `category` - Item category
- `description` - Full description
- `seller` - Seller name
- `postedDate` - When listed
- `imageUrl` - Main image
- `scrapedAt` - Extraction timestamp

## Example Use

```json
{
  "searchQuery": "mobil",
  "location": "jakarta",
  "category": "vehicles",
  "priceMax": 200000000,
  "maxResults": 50
}
```

## Technical Details

- **Runtime**: Python 3.11 with Camoufox browser automation
- **Proxy**: Residential proxy recommended
- **Speed**: ~3-5 seconds per item with descriptions
- **Memory**: 1024 MB recommended

## Geographic Scope

Indonesia only (Jakarta, Bandung, Surabaya, Bali, and all major cities)

## SEO Keywords

olx indonesia, olx scraper, indonesia classifieds, olx data extraction, mobil, motor, property indonesia, jual beli indonesia, marketplace scraper, olx api alternative
