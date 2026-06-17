"""
餐饮POI采集分析 — 主流水线

用法:
  python main.py                          # 默认：华工五山校区
  python main.py --force                  # 强制重新采集
  python main.py --center 113.322,23.128 --prefix sanxin  # 其他区域

流程:
  1. 高德API网格化采集(5x5网格,2000m半径) -> 原始数据 Excel
  2. DeepSeek API 批量分类(每10条一批,结果缓存) -> 最终数据 Excel
  3. 交互式地图(HTML) + 统计图表(PNG)
  4. 输出分析结论

API密钥: 在 .env 文件中填写 AMAP_KEY / DEEPSEEK_API_KEY
"""
import os
import sys
import pandas as pd
from config import (
    AMAP_KEY, DEEPSEEK_API_KEY, WUSHAN_CENTER, GRID_CENTERS,
    RAW_DATA_FILE, FINAL_DATA_FILE, MAP_FILE, BAR_CHART_FILE, PIE_CHART_FILE,
    CACHE_FILE, make_grid,
)
from poi_fetcher import fetch_pois, save_raw_data
from classifier import classify_all
from visualizer import create_map, create_charts, print_summary


def _parse_args():
    """Parse command-line args. Returns dict of overrides."""
    args = {"force": False, "center": None, "prefix": None}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--force":
            args["force"] = True
        elif sys.argv[i] == "--center" and i + 1 < len(sys.argv):
            parts = sys.argv[i + 1].split(",")
            args["center"] = (float(parts[0]), float(parts[1]))
            i += 1
        elif sys.argv[i] == "--prefix" and i + 1 < len(sys.argv):
            args["prefix"] = sys.argv[i + 1]
            i += 1
        i += 1
    return args


def _check_keys():
    """Check API keys configured in .env."""
    missing = []
    if not AMAP_KEY or AMAP_KEY == "your_amap_key_here":
        missing.append("AMAP_KEY")
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_key_here":
        missing.append("DEEPSEEK_API_KEY")
    if missing:
        print("=" * 50)
        print("[Error] Missing API keys: {}".format(", ".join(missing)))
        print("Fill them in .env and retry.")
        print("=" * 50)
        return False
    return True


def _collect_all_shops(center, grid):
    """Collect shops from all grid points, dedup by (name, address)."""
    import pandas as pd
    all_shops = []
    print("=" * 50)
    print("Step 1/3: Amap Grid POI Collection")
    print("  Center: ({}, {})".format(center[0], center[1]))
    print("  Grid cells: {}".format(len(grid)))
    print("=" * 50)
    for i, (lng, lat) in enumerate(grid, 1):
        print("  Cell {}/{}: ({:.4f}, {:.4f})".format(i, len(grid), lng, lat))
        shops = fetch_pois(lng, lat, radius=500, types="050000")
        print("    {} records".format(len(shops)))
        all_shops.extend(shops)
    if not all_shops:
        return pd.DataFrame()
    df = pd.DataFrame(all_shops)
    before = len(df)
    df = df.drop_duplicates(subset=["name", "address"], keep="first")
    print("  Total: {} ({} duplicates removed)".format(len(df), before - len(df)))
    return df


def main():
    """Main pipeline."""
    args = _parse_args()
    force = args["force"]

    # Set center and grid
    if args["center"]:
        center = args["center"]
        grid = make_grid(center[0], center[1])
    else:
        center = WUSHAN_CENTER
        grid = GRID_CENTERS

    # Set file prefix
    prefix = args.get("prefix") or "wushan"
    raw_file = "{}_food_2026_raw.xlsx".format(prefix)
    final_file = "{}_food_2026.xlsx".format(prefix)
    map_file = "{}_food_map.html".format(prefix)
    bar_file = "{}_category_bar.png".format(prefix)
    pie_file = "{}_category_pie.png".format(prefix)
    cache_file = "{}_classification_cache.json".format(prefix)

    print("\n" + "=" * 50)
    print("  Food POI Analysis")
    print("  Center: ({:.4f}, {:.4f})  Radius: ~2000m".format(center[0], center[1]))
    print("=" * 50)

    if not _check_keys():
        sys.exit(1)

    # Step 1: POI collection
    if os.path.exists(raw_file) and not force:
        print("\n[Step 1/3] Loading cached raw data: {}".format(raw_file))
        print("  (use --force to re-collect)")
        df = pd.read_excel(raw_file, engine="openpyxl")
        print("  Loaded {} records".format(len(df)))
    else:
        if force:
            print("\n[Step 1/3] Force re-collecting...")
        df = _collect_all_shops(center, grid)
        if df.empty:
            print("\n[Error] No data collected. Check AMAP_KEY and network.")
            sys.exit(1)
        save_raw_data(df, raw_file)

    # Step 2: Classification (with custom cache)
    print("\n[Step 2/3] Classifying with DeepSeek API...")
    import classifier
    classifier.CACHE_FILE = cache_file
    df = classify_all(df)
    df.to_excel(final_file, index=False, engine="openpyxl")
    print("  Saved: {}".format(final_file))

    # Step 3: Visualization
    print("\n[Step 3/3] Generating visualizations...")
    create_map(df, output_path=map_file, center=center)
    create_charts(df, output_paths=(bar_file, pie_file))

    total = len(df)
    print("  Map saved: {}".format(map_file))
    print("  {} shops across {} categories".format(total, df['category'].nunique()))

    print("\n" + "=" * 50)
    print("  Done. Open {} to view map.".format(map_file))
    print("=" * 50)


if __name__ == "__main__":
    main()
