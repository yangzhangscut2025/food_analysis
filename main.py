"""
华南理工大学五山校区周边餐饮分析 — 主流水线

流程:
  1. 高德API网格化采集(5x5网格,2000m半径) -> 原始数据 Excel
  2. DeepSeek API 批量分类(每10条一批,结果缓存) -> 最终数据 Excel
  3. 交互式地图(HTML) + 统计图表(PNG)
  4. 输出分析结论

API密钥: 在 .env 文件中填写 AMAP_KEY / DEEPSEEK_API_KEY
断点续传: raw data 已存在时跳过采集; 用 --force 强制重新采集
"""
import os
import sys
import pandas as pd
from config import (
    AMAP_KEY, DEEPSEEK_API_KEY, RAW_DATA_FILE, FINAL_DATA_FILE
)
from poi_fetcher import collect_all_shops, save_raw_data
from classifier import classify_all
from visualizer import create_map, create_charts, print_summary


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


def main():
    """Main pipeline."""
    force = "--force" in sys.argv
    print("\n" + "=" * 50)
    print("  SCUT Wushan Food Analysis")
    print("  Amap POI + DeepSeek Classify + Folium Viz")
    print("=" * 50)

    if not _check_keys():
        sys.exit(1)

    # Step 1: POI collection
    if os.path.exists(RAW_DATA_FILE) and not force:
        print("\n[Step 1/3] Loading cached raw data: {}".format(RAW_DATA_FILE))
        print("  (use --force to re-collect)")
        df = pd.read_excel(RAW_DATA_FILE, engine="openpyxl")
        print("  Loaded {} records".format(len(df)))
    else:
        if force:
            print("\n[Step 1/3] Force re-collecting...")
        else:
            print("\n[Step 1/3] Collecting POIs from Amap API...")
        df = collect_all_shops()
        if df.empty:
            print("\n[Error] No data collected. Check AMAP_KEY and network.")
            sys.exit(1)
        save_raw_data(df, RAW_DATA_FILE)

    # Step 2: Classification
    print("\n[Step 2/3] Classifying with DeepSeek API...")
    df = classify_all(df)
    df.to_excel(FINAL_DATA_FILE, index=False, engine="openpyxl")
    print("  Saved: {}".format(FINAL_DATA_FILE))

    # Step 3: Visualization
    print("\n[Step 3/3] Generating visualizations...")
    create_map(df)
    create_charts(df)
    print_summary(df)

    print("\n" + "=" * 50)
    print("  Done. Check output files.")
    print("=" * 50)


if __name__ == "__main__":
    main()
