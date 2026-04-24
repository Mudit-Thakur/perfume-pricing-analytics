# ============================================================
# PERFUME PRICING SCRAPER — Final Version
# Amazon.in  : google_shopping engine (working ✅)
# Flipkart   : google engine with site: filter
# Nykaa      : google engine with site: filter
# Output     : perfume_prices_YYYYMMDD_HHMM.csv
# ============================================================

import requests
import pandas as pd
import time
import random
import re
from datetime import datetime, timezone

# ============================================================
# CONFIGURATION — only edit these
# ============================================================

SERPAPI_KEY = "YOUR_SERPAPI_KEY_HERE"

SEARCH_TERMS = ["perfume", "eau de parfum", "attar", "fragrance"]

PAGES_PER_TERM = 2     # 2 pages × 4 terms × 3 platforms = 24 API calls total

# ============================================================
# HELPERS
# ============================================================

def parse_price(text):
    """Pulls the first number out of a string like '₹1,299' → 1299.0"""
    if not text:
        return None
    digits = re.sub(r"[^\d.]", "", str(text))   # keep only digits and dot
    try:
        return float(digits)
    except ValueError:
        return None

def random_delay():
    time.sleep(random.uniform(1.5, 3.5))

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def call_serpapi(params):
    """
    Central function for all SerpApi calls.
    Adds the API key, makes the request, returns JSON or None.
    """
    params["api_key"] = SERPAPI_KEY
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=20)
        print(f"    [SerpApi] engine={params.get('engine')} status={r.status_code}")
        if r.status_code != 200:
            return None
        return r.json()
    except Exception as e:
        print(f"    [SerpApi] error: {e}")
        return None

# ============================================================
# PRICE EXTRACTOR from Google organic snippet
# Google sometimes puts prices in snippets like "₹1,299 - In stock"
# ============================================================

def extract_price_from_snippet(snippet):
    """
    Looks for ₹ followed by digits in an organic search snippet.
    Example: 'Buy Dior Sauvage ₹7,500 on Flipkart' → 7500.0
    """
    match = re.search(r"₹[\s]*([\d,]+)", str(snippet))
    if match:
        return parse_price(match.group(1))
    return None

# ============================================================
# SCRAPER 1: AMAZON.IN — google_shopping (already working ✅)
# ============================================================

def scrape_amazon(search_term, page=1):
    results = []
    data = call_serpapi({
        "engine": "google_shopping",
        "q":      f"{search_term} perfume",
        "gl":     "in",
        "hl":     "en",
        "start":  (page - 1) * 10
    })
    if not data:
        return results

    for item in data.get("shopping_results", []):
        if "amazon" not in str(item.get("source", "")).lower():
            continue
        results.append({
            "platform":     "Amazon.in",
            "search_term":  search_term,
            "product_name": item.get("title", "N/A"),
            "brand":        item.get("source", "N/A"),
            "price_inr":    parse_price(item.get("price")),
            "mrp_inr":      None,
            "discount_pct": None,
            "rating":       item.get("rating", "N/A"),
            "review_count": item.get("reviews", "N/A"),
            "scraped_at":   now_utc()
        })
    return results

# ============================================================
# SCRAPER 2: FLIPKART — google organic search
# ============================================================

def scrape_flipkart(search_term, page=1):
    results = []
    data = call_serpapi({
        "engine":        "google",
        "q":             f"{search_term} perfume site:flipkart.com",
        "gl":            "in",
        "hl":            "en",
        "google_domain": "google.co.in",     # use Indian Google for relevant results
        "num":           10,                  # 10 results per page
        "start":         (page - 1) * 10
    })
    if not data:
        return results

    organic = data.get("organic_results", [])
    print(f"    [Flipkart] organic results found: {len(organic)}")

    for item in organic:
        title   = item.get("title", "N/A")
        snippet = item.get("snippet", "")
        link    = item.get("link", "")

        # Only keep actual product pages, skip category/search pages
        if "flipkart.com" not in link:
            continue
        if "/search?" in link or "/p/" not in link:
            continue

        price = extract_price_from_snippet(snippet)

        # Try rich snippet for price if available
        rich = item.get("rich_snippet", {})
        if not price and rich:
            price = parse_price(
                rich.get("top", {}).get("detected_extensions", {}).get("price", None)
            )

        results.append({
            "platform":     "Flipkart",
            "search_term":  search_term,
            "product_name": title,
            "brand":        "N/A",
            "price_inr":    price,
            "mrp_inr":      None,
            "discount_pct": None,
            "rating":       rich.get("top", {}).get("detected_extensions", {}).get("rating", "N/A"),
            "review_count": rich.get("top", {}).get("detected_extensions", {}).get("reviews", "N/A"),
            "scraped_at":   now_utc()
        })
    return results

# ============================================================
# SCRAPER 3: NYKAA — google organic search
# ============================================================

def scrape_nykaa(search_term, page=1):
    results = []
    data = call_serpapi({
        "engine":        "google",
        "q":             f"{search_term} perfume site:nykaa.com",
        "gl":            "in",
        "hl":            "en",
        "google_domain": "google.co.in",
        "num":           10,
        "start":         (page - 1) * 10
    })
    if not data:
        return results

    organic = data.get("organic_results", [])
    print(f"    [Nykaa] organic results found: {len(organic)}")

    for item in organic:
        title   = item.get("title", "N/A")
        snippet = item.get("snippet", "")
        link    = item.get("link", "")

        # Skip category/search/blog pages — only product pages
        if "nykaa.com" not in link:
            continue
        if any(x in link for x in ["/search", "/collections", "/blog", "/sp/"]):
            continue

        price = extract_price_from_snippet(snippet)

        rich = item.get("rich_snippet", {})
        if not price and rich:
            price = parse_price(
                rich.get("top", {}).get("detected_extensions", {}).get("price", None)
            )

        results.append({
            "platform":     "Nykaa",
            "search_term":  search_term,
            "product_name": title,
            "brand":        "N/A",
            "price_inr":    price,
            "mrp_inr":      None,
            "discount_pct": None,
            "rating":       rich.get("top", {}).get("detected_extensions", {}).get("rating", "N/A"),
            "review_count": rich.get("top", {}).get("detected_extensions", {}).get("reviews", "N/A"),
            "scraped_at":   now_utc()
        })
    return results

# ============================================================
# MAIN RUNNER
# ============================================================

def run_all_scrapers():
    all_results = []

    for term in SEARCH_TERMS:
        print(f"\n🔍 Searching: '{term}'")

        for page in range(1, PAGES_PER_TERM + 1):
            print(f"  Page {page}...")

            amazon_data   = scrape_amazon(term, page)
            all_results.extend(amazon_data)
            print(f"    Amazon.in : {len(amazon_data)} products")
            random_delay()

            flipkart_data = scrape_flipkart(term, page)
            all_results.extend(flipkart_data)
            print(f"    Flipkart  : {len(flipkart_data)} products")
            random_delay()

            nykaa_data    = scrape_nykaa(term, page)
            all_results.extend(nykaa_data)
            print(f"    Nykaa     : {len(nykaa_data)} products")
            random_delay()

    if not all_results:
        print("\n⚠️  No data collected. Check your SerpApi key.")
        return None

    df = pd.DataFrame(all_results)
    df.drop_duplicates(subset=["platform", "product_name", "price_inr"], inplace=True)

    output_file = f"perfume_prices_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"\n✅ Done! {len(df)} products saved to: {output_file}")
    print(df[["platform", "product_name", "price_inr"]].head(15).to_string())
    return df

if __name__ == "__main__":
    run_all_scrapers()