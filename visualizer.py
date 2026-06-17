"""
Visualization module.

Outputs:
  1. folium interactive map (marker clusters + heatmap + layer control + legend)
  2. matplotlib charts (bar + pie of category counts)
"""
import os
from datetime import date
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen
from config import (
    WUSHAN_CENTER, CATEGORIES, CATEGORY_COLORS, AMAP_TILE_URL,
    MAP_FILE, BAR_CHART_FILE, PIE_CHART_FILE
)


def _setup_chinese_font():
    """检测并设置中文字体，避免图表中文乱码。"""
    windows_font_dir = os.environ.get("WINDIR", r"C:\Windows") + r"\Fonts"
    CJK_FONT_FILES = [
        ("simhei.ttf", "SimHei"),
        ("msyh.ttc", "Microsoft YaHei"),
        ("simsun.ttc", "SimSun"),
    ]
    for font_file, fallback_name in CJK_FONT_FILES:
        font_path = os.path.join(windows_font_dir, font_file)
        if not os.path.exists(font_path):
            continue
        try:
            fm.fontManager.addfont(font_path)
            prop = fm.FontProperties(fname=font_path)
            real_name = prop.get_name()
            plt.rcParams["font.sans-serif"] = [real_name, fallback_name, "sans-serif"]
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["axes.unicode_minus"] = False
            print(f"  [font] loaded: {font_file} -> family='{real_name}'")
            return real_name
        except Exception:
            plt.rcParams["font.sans-serif"] = [fallback_name, "sans-serif"]
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["axes.unicode_minus"] = False
            return fallback_name
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "sans-serif"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
    return None

def _collection_date():
    """Get collection date from raw data file mtime, or today."""
    from config import RAW_DATA_FILE
    try:
        ts = os.path.getmtime(RAW_DATA_FILE)
        return date.fromtimestamp(ts).strftime("%Y-%m-%d")
    except OSError:
        return date.today().strftime("%Y-%m-%d")


def _inject_legend(html_path, categories, colors, counts, total):
    """Post-process: inject a simple stats legend panel before </body>."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    rows = ""
    for cat in sorted(categories, key=lambda c: counts.get(c, 0), reverse=True):
        c = counts.get(cat, 0)
        pct = c / total * 100
        color = colors.get(cat, "gray")
        rows += (
            '<div style="display:flex;align-items:center;padding:3px 0;font-size:12px;">'
            '<span style="width:10px;height:10px;background:{};border-radius:2px;'
            'margin-right:8px;flex-shrink:0;"></span>'
            '<span style="flex:1;color:#444;">{}</span>'
            '<span style="font-weight:600;color:#333;margin-right:2px;">{}</span>'
            '<span style="color:#aaa;font-size:10px;">{:.0f}%</span>'
            '</div>'
        ).format(color, cat, c, pct)

    legend = (
        '<div style="position:fixed;top:50px;left:12px;z-index:9998;'
        'background:rgba(255,255,255,0.88);border:1px solid rgba(0,0,0,0.08);'
        'border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,0.06);'
        'padding:10px 12px;min-width:100px;'
        'font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;">'
        '<div style="font-size:20px;font-weight:700;color:#1a1a1a;margin-bottom:2px;">{}'
        '<span style="font-size:11px;font-weight:400;color:#aaa;"> shops</span></div>'
        '<div style="font-size:10px;color:#bbb;margin-bottom:8px;padding-bottom:6px;'
        'border-bottom:1px solid rgba(0,0,0,0.06);">Wushan SCUT Food Map</div>'
        '{}'
        '<div style="font-size:10px;color:#ccc;margin-top:6px;padding-top:6px;'
        'border-top:1px solid rgba(0,0,0,0.06);text-align:right;">'
        'Collected {}</div>'
        '</div>'
    ).format(total, rows, _collection_date())

    hide_attr = '<style>.leaflet-control-attribution{display:none!important}</style>'
    html = html.replace('</body>', legend + hide_attr + '</body>')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


def create_map(df, output_path=None):
    """Create interactive folium map with marker clusters, heatmap, and custom UI."""
    if output_path is None:
        output_path = MAP_FILE

    print("\n" + "=" * 50)
    print("Step 3/3: Generating visualizations")
    print("=" * 50)
    print("\n  Generating interactive map...")

    center_lng, center_lat = WUSHAN_CENTER

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=15,
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer(tiles=AMAP_TILE_URL, name="高德地图", attr=" ").add_to(m)

    Fullscreen(position="topleft").add_to(m)

    groups = {}

    for cat in CATEGORIES:
        fg = folium.FeatureGroup(name=cat, show=True)
        mc = MarkerCluster().add_to(fg)
        groups[cat] = {"fg": fg, "mc": mc}

    fg_all = folium.FeatureGroup(name="All", show=True)
    mc_all = MarkerCluster().add_to(fg_all)

    fg_heat = folium.FeatureGroup(name="Heatmap", show=False)

    def _popup_html(name, category, address, lat, lng):
        from urllib.parse import quote
        amap_url = "https://uri.amap.com/marker?position={},{}&name={}".format(lng, lat, quote(name))
        return (
            '<div style="font-family:-apple-system,BlinkMacSystemFont,'
            "'Segoe UI','Microsoft YaHei',sans-serif;min-width:200px;padding:2px 0;\">"
            '<div style="font-size:15px;font-weight:600;color:#1a1a1a;margin-bottom:8px;">{name}</div>'
            '<div style="font-size:12px;color:#888;margin-bottom:3px;">'
            '<span style="display:inline-block;width:8px;height:8px;background:#999;'
            'border-radius:2px;margin-right:6px;"></span>{cat}</div>'
            '<div style="font-size:12px;color:#888;margin-bottom:12px;">{addr}</div>'
            '<a href="{url}" target="_blank" style="display:inline-block;padding:5px 16px;'
            'background:#1677ff;color:#fff;text-decoration:none;border-radius:6px;font-size:12px;'
            'font-weight:500;">Navigate</a>'
            '</div>'
        ).format(name=name, cat=category, addr=address, url=amap_url)

    def _marker(lat, lng, color, name, category, address):
        icon_html = (
            '<div style="width:20px;height:20px;background:{c};border:3px solid #fff;'
            'border-radius:50%;box-shadow:0 1px 4px rgba(0,0,0,0.4);cursor:pointer;"></div>'
        ).format(c=color)
        return folium.Marker(
            location=[lat, lng],
            icon=folium.DivIcon(html=icon_html),
            tooltip=folium.Tooltip("<b>{}</b>".format(name), sticky=False),
            popup=folium.Popup(_popup_html(name, category, address, lat, lng), max_width=320),
        )

    for _, row in df.iterrows():
        category = row.get("category", "")
        color = CATEGORY_COLORS.get(category, "gray")
        lat, lng = row["lat"], row["lng"]
        if pd.isna(lat) or pd.isna(lng):
            continue
        address = row.get("address", "")
        name = row["name"]
        _marker(lat, lng, color, name, category, address).add_to(mc_all)
        target = groups.get(category) or groups.get("其他")
        if target:
            _marker(lat, lng, color, name, category, address).add_to(target["mc"])

    heat_data = [[row["lat"], row["lng"]] for _, row in df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(fg_heat)

    fg_all.add_to(m)
    fg_heat.add_to(m)
    for cat in CATEGORIES:
        groups[cat]["fg"].add_to(m)

    folium.plugins.MousePosition(position="bottomright").add_to(m)

    # 原生图层控制 — 免注入，直接可用
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(output_path)

    # Inject legend panel (pure HTML, no JS)
    category_counts = df["category"].value_counts()
    total = len(df)
    _inject_legend(output_path, CATEGORIES, CATEGORY_COLORS, category_counts, total)

    print("  Map saved to: {}".format(output_path))
    print("  {} shops across {} categories".format(total, df['category'].nunique()))
    print("  LayerControl + legend panel in top-right")

    return m


def create_charts(df, output_dir=None):
    """Generate bar chart and pie chart of category counts."""
    print("\n  Generating charts...")

    category_counts = df["category"].value_counts()
    category_counts = category_counts.sort_values(ascending=True)

    sns.set_style("whitegrid")
    _setup_chinese_font()

    # Bar chart
    fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
    colors = [CATEGORY_COLORS.get(cat, "gray") for cat in category_counts.index]
    bars = ax_bar.barh(category_counts.index, category_counts.values, color=colors)
    for bar_obj, val in zip(bars, category_counts.values):
        ax_bar.text(bar_obj.get_width() + 0.3, bar_obj.get_y() + bar_obj.get_height() / 2,
                    str(val), va="center", fontsize=11)
    ax_bar.set_xlabel("count", fontsize=12)
    ax_bar.set_title("SCUT Wushan Food Category Distribution", fontsize=14, fontweight="bold")
    ax_bar.set_xlim(0, category_counts.max() * 1.2)
    plt.tight_layout()
    bar_path = BAR_CHART_FILE if output_dir is None else "{}/{}".format(output_dir, BAR_CHART_FILE)
    fig_bar.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close(fig_bar)
    print("  Bar chart saved: {}".format(bar_path))

    # Pie chart
    fig_pie, ax_pie = plt.subplots(figsize=(8, 8))
    pie_colors = [CATEGORY_COLORS.get(cat, "gray") for cat in category_counts.index]
    wedges, texts, autotexts = ax_pie.pie(
        category_counts.values, labels=category_counts.index,
        colors=pie_colors, autopct="%1.1f%%", startangle=90, pctdistance=0.85)
    for t in autotexts:
        t.set_fontsize(10)
        t.set_color("white")
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(11)
    ax_pie.set_title("SCUT Wushan Food Category Share", fontsize=14, fontweight="bold")
    plt.tight_layout()
    pie_path = PIE_CHART_FILE if output_dir is None else "{}/{}".format(output_dir, PIE_CHART_FILE)
    fig_pie.savefig(pie_path, dpi=150, bbox_inches="tight")
    plt.close(fig_pie)
    print("  Pie chart saved: {}".format(pie_path))


def print_summary(df):
    """Print analysis summary to console."""
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    total = len(df)
    category_counts = df["category"].value_counts()
    print("\n  Total: {} food shops.".format(total))
    print("  Categories breakdown:")
    for cat, cnt in category_counts.items():
        print("    {}: {}".format(cat, cnt))
    top_cat = category_counts.index[0]
    top_count = category_counts.iloc[0]
    print("\n  Top: {} ({} shops)".format(top_cat, top_count))
    print("\n  Output files:")
    print("    - Map: {}".format(MAP_FILE))
    print("    - Charts: {}, {}".format(BAR_CHART_FILE, PIE_CHART_FILE))
