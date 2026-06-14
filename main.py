"""
五山地铁站周边餐饮分析 — 主流水线

流程：
  1. 高德API网格化采集餐饮POI → 原始数据 Excel
  2. DeepSeek API 批量分类 → 带类别标签的最终数据 Excel
  3. 生成交互式地图（HTML）+ 统计图表（PNG）
  4. 输出简要分析结论

运行前请确保在 .env 文件中填写了 AMAP_KEY 和 DEEPSEEK_API_KEY。
"""
import sys
from config import (
    AMAP_KEY, DEEPSEEK_API_KEY, RAW_DATA_FILE, FINAL_DATA_FILE
)
from poi_fetcher import collect_all_shops, save_raw_data
from classifier import classify_all
from visualizer import create_map, create_charts, print_summary


def check_api_keys():
    """检查 API 密钥是否已配置"""
    missing = []
    if not AMAP_KEY or AMAP_KEY == "your_amap_key_here":
        missing.append("AMAP_KEY（高德地图）")
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "your_deepseek_key_here":
        missing.append("DEEPSEEK_API_KEY（DeepSeek）")

    if missing:
        print("=" * 50)
        print("[错误] 以下 API 密钥未配置：")
        for key in missing:
            print(f"  - {key}")
        print(f"\n请在项目根目录的 .env 文件中填入正确的 API 密钥后重试。")
        print("=" * 50)
        return False
    return True


def main():
    """主流水线"""
    print("\n" + "█" * 50)
    print("  五山地铁站周边餐饮分析")
    print("  高德POI采集 + DeepSeek分类 + 可视化")
    print("█" * 50)

    # 检查 API 密钥
    if not check_api_keys():
        sys.exit(1)

    # ---- 步骤 1：POI 采集 ----
    df = collect_all_shops()

    if df.empty:
        print("\n[错误] 未能采集到任何数据，流程终止。")
        print("请检查：")
        print("  1. 高德 API Key 是否正确")
        print("  2. 网络连接是否正常")
        sys.exit(1)

    save_raw_data(df, RAW_DATA_FILE)

    # ---- 步骤 2：DeepSeek 分类 ----
    df = classify_all(df)

    # 保存最终数据
    df.to_excel(FINAL_DATA_FILE, index=False, engine="openpyxl")
    print(f"\n最终数据已保存到: {FINAL_DATA_FILE}")

    # ---- 步骤 3：可视化 ----
    create_map(df)
    create_charts(df)

    # ---- 总结 ----
    print_summary(df)

    print("\n" + "█" * 50)
    print("  分析完成！请查看生成的输出文件。")
    print("█" * 50)


if __name__ == "__main__":
    main()
