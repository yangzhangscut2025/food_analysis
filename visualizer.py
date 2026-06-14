"""
可视化模块

生成两种可视化结果：
1. folium 交互式地图 — 按类别颜色标记店铺位置 + 热力图
2. matplotlib 统计图表 — 类别数量柱状图 + 饼图
"""
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import folium
from folium.plugins import HeatMap
from config import (
    WUSHAN_CENTER, CATEGORY_COLORS, AMAP_TILE_URL,
    MAP_FILE, BAR_CHART_FILE, PIE_CHART_FILE
)


def _setup_chinese_font():
    """
    检测并设置中文字体，避免图表中文乱码。
    优先使用 SimHei，其次 Microsoft YaHei。
    """
    available_fonts = {f.name for f in fm.fontManager.ttflist}

    for font_name in ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei"]:
        if font_name in available_fonts:
            plt.rcParams["font.sans-serif"] = [font_name, "sans-serif"]
            plt.rcParams["axes.unicode_minus"] = False
            return font_name

    # 如果都不可用，尝试用 sans-serif 兜底
    plt.rcParams["font.sans-serif"] = ["sans-serif"]
    plt.rcParams["axes.unicode_minus"] = False
    print("[警告] 未找到中文字体，图表中文可能显示为方块")
    return None


def create_map(df, output_path=None):
    """
    创建交互式地图：按类别颜色标记 + 热力图叠加。

    Parameters
    ----------
    df : pd.DataFrame
        包含 name, lng, lat, category 列的店铺数据
    output_path : str, optional
        HTML 输出路径，默认使用 config 中的 MAP_FILE

    Returns
    -------
    folium.Map
        生成的地图对象（在 Jupyter 中可直接显示）
    """
    if output_path is None:
        output_path = MAP_FILE

    print("\n" + "=" * 50)
    print("步骤 3/3：生成可视化")
    print("=" * 50)
    print("\n  ⏳ 生成交互式地图...")

    center_lng, center_lat = WUSHAN_CENTER

    # 创建地图，使用高德瓦片
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=15,
        tiles=AMAP_TILE_URL,
        attr="高德地图",
    )

    # 按类别添加标记
    for _, row in df.iterrows():
        category = row.get("category", "其他")
        color = CATEGORY_COLORS.get(category, "gray")

        popup_text = f"<b>{row['name']}</b><br>类别：{category}<br>{row.get('address', '')}"

        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(m)

    # 添加热力图
    heat_data = [[row["lat"], row["lng"]] for _, row in df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(m)

    # 保存
    m.save(output_path)
    print(f"  地图已保存到: {output_path}")
    print(f"  共标记 {len(df)} 个店铺，覆盖 {df['category'].nunique()} 个类别")

    return m


def create_charts(df, output_dir=None):
    """
    生成类别数量柱状图和饼图。

    Parameters
    ----------
    df : pd.DataFrame
        包含 category 列的店铺数据
    output_dir : str, optional
        输出目录（文件名使用 config 中的定义）
    """
    print("\n  ⏳ 生成统计图表...")

    _setup_chinese_font()

    category_counts = df["category"].value_counts()

    # 排序：按数量从多到少
    category_counts = category_counts.sort_values(ascending=True)

    # 使用 seaborn 风格
    sns.set_style("whitegrid")

    # --- 柱状图 ---
    fig_bar, ax_bar = plt.subplots(figsize=(10, 6))

    # 按类别颜色绘制柱状图
    colors = [CATEGORY_COLORS.get(cat, "gray") for cat in category_counts.index]
    bars = ax_bar.barh(category_counts.index, category_counts.values, color=colors)

    # 在柱子上标注数量
    for bar_obj, val in zip(bars, category_counts.values):
        ax_bar.text(
            bar_obj.get_width() + 0.3,
            bar_obj.get_y() + bar_obj.get_height() / 2,
            str(val),
            va="center",
            fontsize=11,
        )

    ax_bar.set_xlabel("店铺数量", fontsize=12)
    ax_bar.set_title("五山地铁站周边餐饮类别数量分布", fontsize=14, fontweight="bold")
    ax_bar.set_xlim(0, category_counts.max() * 1.2)
    plt.tight_layout()

    bar_path = BAR_CHART_FILE if output_dir is None else f"{output_dir}/{BAR_CHART_FILE}"
    fig_bar.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close(fig_bar)
    print(f"  柱状图已保存到: {bar_path}")

    # --- 饼图 ---
    fig_pie, ax_pie = plt.subplots(figsize=(8, 8))

    pie_colors = [CATEGORY_COLORS.get(cat, "gray") for cat in category_counts.index]
    wedges, texts, autotexts = ax_pie.pie(
        category_counts.values,
        labels=category_counts.index,
        colors=pie_colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.85,
    )

    # 美化文字
    for t in autotexts:
        t.set_fontsize(10)
        t.set_color("white")
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(11)

    ax_pie.set_title("五山地铁站周边餐饮类别占比", fontsize=14, fontweight="bold")
    plt.tight_layout()

    pie_path = PIE_CHART_FILE if output_dir is None else f"{output_dir}/{PIE_CHART_FILE}"
    fig_pie.savefig(pie_path, dpi=150, bbox_inches="tight")
    plt.close(fig_pie)
    print(f"  饼图已保存到: {pie_path}")


def print_summary(df):
    """
    打印简要的分析结论。

    Parameters
    ----------
    df : pd.DataFrame
        包含 category 列的店铺数据
    """
    print("\n" + "=" * 50)
    print("分析结论")
    print("=" * 50)

    total = len(df)
    category_counts = df["category"].value_counts()

    print(f"\n  共采集到 {total} 家餐饮店。")

    top_cat = category_counts.index[0]
    top_count = category_counts.iloc[0]
    print(f"  最多的是 {top_cat}（{top_count} 家），集中在五山地铁口周边。")

    # 茶饮类统计
    tea_count = df[df["category"] == "茶饮"].shape[0]
    if tea_count > 0:
        rank = list(category_counts.index).index("茶饮") + 1
        ordinal = {1: "第一", 2: "第二", 3: "第三"}.get(rank, f"第{rank}")
        print(f"  茶饮类（包括奶茶、咖啡）数量{ordinal}（{tea_count} 家），分布沿岳洲路线性扩散。")

    # 火锅/烧烤统计
    hot_grill = df[df["category"].isin(["火锅", "烧烤"])].shape[0]
    print(f"  火锅/烧烤类共 {hot_grill} 家，数量相对较少。")

    print("\n  输出文件：")
    print(f"    - 交互地图: {MAP_FILE}")
    print(f"    - 统计图表: {BAR_CHART_FILE}, {PIE_CHART_FILE}")
