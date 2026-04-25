# 🧴 Indian Perfume Pricing Intelligence Pipeline

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-SQLite-lightgrey?logo=sqlite)
![Looker Studio](https://img.shields.io/badge/Dashboard-Looker%20Studio-4285F4?logo=googleanalytics)
![SerpApi](https://img.shields.io/badge/Data-SerpApi-green)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)

An end-to-end pricing intelligence pipeline that scrapes perfume listings across **Amazon.in, Flipkart, and Nykaa** — cleans, analyses, and visualises cross-platform pricing strategy using SQL, Python, and Looker Studio.

> **This is not a dashboard exercise.** This project answers real business questions a brand manager or e-commerce analyst would ask before making a pricing or channel decision.

---

## 🔗 Live Dashboard

👉 [View Interactive Looker Studio Dashboard](https://datastudio.google.com/reporting/45d52495-9ce0-4e54-9451-da9c9bb45b5a)

![Dashboard Preview](https://github.com/Mudit-Thakur/perfume-pricing-analytics/blob/main/Indian_Perfume_Pricing_Intelligence_Dashboard.png)

---

## ❓ Business Questions Answered

| # | Business Question | Finding |
|---|---|---|
| 1 | Which platform positions itself as premium vs budget? | Nykaa avg ₹1,969 vs Flipkart avg ₹759 — 2.6x gap reveals distinct positioning |
| 2 | Where do luxury brands list their products? | Amazon.in carries the widest price range (₹149 → ₹26,999) — true marketplace strategy |
| 3 | Which platform dominates the budget segment (<₹500)? | Flipkart — 53% of its listings are budget tier, zero luxury products |
| 4 | How many unique brands are active across platforms? | 133 unique brands identified, only 1 selling on 2+ platforms simultaneously |
| 5 | What does cross-platform brand pricing look like? | Window function analysis reveals platform-level price rank per brand |

---

## 🏗️ Pipeline Architecture

```
ScraperAPI (rotating proxies, 3 platforms)
            ↓
  perfume_scraper_v2.py  ←  Python 3.11
            ↓
  perfume_prices_raw.csv  (5,254 raw rows)
            ↓
  perfume_prices_clean.csv  (2,067 unique products)
            ↓
  Colab Notebook  ←  Pandas + SQLite + Plotly + RapidFuzz
            ↓
  Google Sheets  →  Looker Studio Dashboard
```

---

## 📁 Repository Structure

```
perfume-pricing-analytics/
│
├── perfume_scraper_v2.py                    # ScraperAPI multi-platform scraper
├── Perfume_Pricing_Analytics_India.ipynb    # Full analysis + matching + recommendations
├── perfume_prices_clean.csv                 # Clean dataset (2,067 products)
├── perfume_arbitrage.csv                    # Cross-platform arbitrage opportunities
├── perfume_recommendations.csv              # Price recommendation engine output
├── .gitignore
└── README.md
```

---

## 🔍 Data Collection

**Platforms scraped:** Amazon.in · Flipkart · Nykaa

**Search terms:** perfume · eau de parfum · attar · fragrance

**Fields collected per product:**

| Field | Description |
|---|---|
| `platform` | Source platform |
| `product_name` | Full product title |
| `price_inr` | Listed selling price (₹) |
| `mrp_inr` | Maximum retail price where available |
| `discount_pct` | Calculated discount percentage |
| `rating` | Product rating |
| `review_count` | Number of reviews |
| `search_term` | Keyword that returned this product |
| `scraped_at` | UTC timestamp of scrape |

**Why SerpApi over direct scraping:**
Amazon.in uses a 6-layer anti-bot defense (TLS fingerprinting, IP reputation, CAPTCHA). Nykaa and Flipkart use Cloudflare enterprise protection. Routing through SerpApi was the deliberate engineering decision — fighting bot detection was not the problem being solved.

---

## 🧹 Data Cleaning Decisions

| Issue | Decision | Reason |
|---|---|---|
| Nykaa category pages scraped as products | Filtered using keyword mask (`buy`, `online`, `at best price`) | These were navigation pages, not product listings |
| Missing prices on Flipkart/Nykaa organic results | Retained rows, flagged as `Unknown` tier | Product name + platform data still valuable for listing analysis |
| Duplicate listings | Dropped on `platform + product_name + price_inr` | Same product appearing across multiple search terms |

---

## 📊 Analysis Summary (SQL + Python)

All analysis runs in SQLite inside the Colab notebook — no cloud warehouse required.

### 1. Platform Price Comparison
```sql
SELECT platform,
       COUNT(*)                     AS total_products,
       ROUND(AVG(price_inr), 0)     AS avg_price,
       ROUND(MIN(price_inr), 0)     AS min_price,
       ROUND(MAX(price_inr), 0)     AS max_price
FROM perfume_prices
WHERE price_inr IS NOT NULL
GROUP BY platform
ORDER BY avg_price DESC;
```

### 2. Brand Platform Price Ranking (Window Function)
```sql
SELECT brand_clean,
       platform,
       ROUND(AVG(price_inr), 0)                        AS avg_price,
       RANK() OVER (
           PARTITION BY brand_clean
           ORDER BY AVG(price_inr) DESC
       )                                                AS price_rank
FROM perfume_prices
WHERE price_inr IS NOT NULL
GROUP BY brand_clean, platform
HAVING COUNT(*) >= 2
ORDER BY brand_clean, price_rank;
```

> Window functions partition the ranking per brand — so each brand's platforms are ranked independently. This is the kind of SQL that separates junior from mid-level analysts.

---

## 📈 Key Findings

- **Nykaa is premium-first** — avg ₹1,996, highest among all platforms
- **Flipkart owns budget** — avg ₹633, 53% listings under ₹500
- **Amazon plays all segments** — widest range ₹57 → ₹48,496
- **784 underpriced products** identified → avg revenue uplift ₹4,961 per SKU
- **583 overpriced products** flagged at risk of conversion loss
- **13 cross-platform arbitrage opportunities** detected → max gap ₹7,001
- **Most expensive listing:** Parfums De Marly Delina on Amazon.in at ₹27,000
- 
---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Scraping, cleaning, orchestration |
| SerpApi | Anti-bot-safe data collection |
| Pandas | Data cleaning and transformation |
| SQLite | In-notebook SQL warehouse |
| Plotly | Interactive charts in notebook |
| Google Colab | Cloud notebook environment |
| Google Sheets | Dashboard data source |
| Looker Studio | Interactive business dashboard |
| Git + GitHub | Version control |
| ScraperAPI | Anti-bot rotating proxy scraping |
| RapidFuzz  | Fuzzy product matching across platforms |

---

## ⚠️ Limitations & Next Steps

**Current limitations:**
- ScraperAPI free tier = 1,000 calls/month
- Nykaa JS rendering occasionally returns 500 errors — handled with retry logic
- Product matching limited to 500 products per platform for runtime efficiency
- Single scrape snapshot — no time-series pricing trends yet

**Planned improvements:**
- [ ] Schedule daily scrapes via GitHub Actions
- [ ] Migrate warehouse to Supabase (free Postgres)
- [ ] Add price tracking over time (detect price drops/hikes)
- [ ] Expand to Myntra and Meesho
- [ ] Streamlit app for live price lookup

---

**Search terms:** perfume · eau de parfum · attar · fragrance · cologne · body mist · luxury perfume · budget perfume · Indian perfume · deodorant perfume

---

## 👤 Author

**Mudit Thakur** · Data Analyst
[GitHub](https://github.com/Mudit-Thakur) · [LinkedIn](https://www.linkedin.com/in/mudit-thakur1/)
