# SCUT Wushan Food Analysis

Amap POI + DeepSeek auto-classify + Folium visualization.

## 1. Overview

Expanded from a milk-tea-shop scraping assignment to a full pipeline:

- **Range**: all food POIs within 2000m of SCUT Wushan Campus
- **Classification**: DeepSeek API auto-labels 8 categories
- **Visualization**: interactive map (LayerControl + marker cluster + heatmap + legend) + charts

## 2. Data Sources

| Layer     | Source                        | Purpose                                |
| :-------- | :---------------------------- | :------------------------------------- |
| POI       | Amap `/v3/place/around` API   | name, address, lng/lat, typecode       |
| Classify  | DeepSeek Chat API             | auto-tag into 8 food categories        |
| Basemap   | Amap tiles (via folium)       | map display (replaces OSM for speed)   |

**Scope**: 25-point (5x5) grid, 500m per cell, centered on SCUT (113.351, 23.155), covering ~2000m radius. Amap `types=050000`.

## 3. Tech Stack

- Python 3.9+
- requests — Amap & DeepSeek API
- pandas — data cleaning, dedup, storage
- folium + plugins (MarkerCluster, HeatMap, Fullscreen, LayerControl) — interactive map
- matplotlib / seaborn — bar + pie charts
- python-dotenv — API key management

## 4. Pipeline

```
Amap API -> 5x5 grid fetch -> merge & dedup -> raw Excel
                    |
            DeepSeek batch classify (10/batch, cached)
                    |
            add "category" column -> final Excel
                    |
        folium map (LayerControl toggle + MarkerCluster + HeatMap + legend)
                    |
        matplotlib bar/pie charts
                    |
              summary report
```

## 5. Project Structure

```
food/
├── .env                        # API keys (fill in yourself)
├── .gitignore
├── README.md
├── requirements.txt
├── config.py                   # constants: grid, categories, colors, URLs
├── poi_fetcher.py              # Amap grid collection + retry logic
├── classifier.py               # DeepSeek batch classify + cache
├── visualizer.py               # folium map + legend + matplotlib charts
├── main.py                     # pipeline entry point
├── food_analysis.ipynb         # Jupyter notebook version
├── classification_cache.json   # auto-generated cache
├── wushan_food_2026_raw.xlsx   # raw POI data
├── wushan_food_2026.xlsx       # classified data
├── wushan_food_map.html        # interactive map
├── category_bar.png            # bar chart
└── category_pie.png            # pie chart
```

## 6. Key Implementation

### 6.1 Amap Grid Collection

25-grid coverage with retry on rate-limit (QPS), exponential backoff.

```python
def fetch_pois(lng, lat, radius=500):
    # paginated Amap around API
    # auto-retry on CUQPS_EXCEEDED (up to 3x, 2s/4s/8s backoff)

# 5x5 grid covering 2000m from SCUT center
for lng, lat in GRID_CENTERS:
    shops = fetch_pois(lng, lat)
# dedup by (name, address)
```

### 6.2 DeepSeek Classification

8 categories: hotpot, grill, tea, fast-food, noodles, regional-cuisine, bakery, other.

- Batch: 10 shops per API call
- Cache: `classification_cache.json` prevents re-calling for known shops
- Prompt: system-level few-shot with JSON output format

### 6.3 Map (Interactive)

| Feature       | Implementation                         |
| :------------ | :------------------------------------- |
| Layer toggle  | `folium.LayerControl` (8 cats + heatmap)|
| Clustering    | `MarkerCluster` — shows count, click to expand |
| Markers       | `DivIcon` 20px colored circles         |
| Tooltip       | shop name on hover                     |
| Popup         | name + category + address + Amap nav link |
| Heatmap       | `HeatMap` plugin, toggle via layer control |
| Legend        | top-right panel: total count + per-category stats + collection date |
| Fullscreen    | `Fullscreen` plugin (top-left)         |
| Coords        | `MousePosition` (bottom-right)         |

### 6.4 Coordinates

Amap returns GCJ-02 (Mars coordinates). Folium uses same — no conversion needed.

## 7. Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Fill in API keys in .env
AMAP_KEY=your_amap_key
DEEPSEEK_API_KEY=your_deepseek_key

# 3. Run (skips collection if raw data exists)
python main.py

# Force re-collect
python main.py --force

# Or use Jupyter
jupyter notebook food_analysis.ipynb
```

> DeepSeek API incurs small cost. Classification results are cached; re-runs skip API calls for cached items.

## 8. Outputs

| File                        | Description                       |
| :-------------------------- | :-------------------------------- |
| `wushan_food_2026_raw.xlsx` | raw POI data from Amap            |
| `wushan_food_2026.xlsx`     | final data with category labels   |
| `wushan_food_map.html`      | interactive map (open in browser) |
| `category_bar.png`          | category count bar chart          |
| `category_pie.png`          | category share pie chart          |

## 9. Future

- [ ] Dianping ratings & avg-spend integration
- [ ] Time-segment analysis (breakfast / late-night)
- [ ] Streamlit / PyEcharts dashboard
- [ ] Distance calculation to campus gates
- [ ] Competitive analysis (same-category heatmaps)

## 10. References

- Amap: https://lbs.amap.com/
- DeepSeek: https://platform.deepseek.com/
- Folium: https://python-visualization.github.io/folium/

---

**Author**: Yang Zhang
**Date**: 2026.06
