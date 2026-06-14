"""
项目配置文件
从 .env 文件加载 API 密钥，提供全局配置常量。
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# --- API 密钥 ---
AMAP_KEY = os.getenv("AMAP_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# --- 高德 API 配置 ---
AMAP_AROUND_URL = "https://restapi.amap.com/v3/place/around"
AMAP_PAGE_SIZE = 25  # 每页最多返回条数
REQUEST_DELAY = 0.5   # 请求间隔（秒），避免限流

# --- 网格采集中心点 ---
# 五山地铁站坐标：113.347, 23.150
# 半径 1000 米范围，用 4 个 500m 半径子区域覆盖
WUSHAN_CENTER = (113.347, 23.150)  # (lng, lat)
GRID_CENTERS = [
    (113.347, 23.150),   # 中心点（地铁站）
    (113.344, 23.154),   # 西北偏移 ~500m
    (113.350, 23.154),   # 东北偏移 ~500m
    (113.344, 23.146),   # 西南偏移 ~500m
    (113.350, 23.146),   # 东南偏移 ~500m
]

# --- DeepSeek API 配置 ---
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
CLASSIFICATION_BATCH_SIZE = 10  # 每批处理的店铺数
CACHE_FILE = "classification_cache.json"

# --- 餐饮类别 ---
CATEGORIES = [
    "火锅", "烧烤", "茶饮", "快餐简餐",
    "粉面馆", "地方菜系", "面包甜点", "其他"
]

# --- 类别颜色映射（folium marker 颜色）---
CATEGORY_COLORS = {
    "火锅":     "red",
    "烧烤":     "orange",
    "茶饮":     "green",
    "快餐简餐": "blue",
    "粉面馆":   "purple",
    "地方菜系": "darkred",
    "面包甜点": "pink",
    "其他":     "gray",
}

# --- 高德地图瓦片 URL（用于 folium 底图）---
# 使用高德卫星图/街道图瓦片，解决 OpenStreetMap 国内加载慢的问题
AMAP_TILE_URL = (
    "https://webrd01.is.autonavi.com/appmaptile"
    "?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
)

# --- 输出文件路径 ---
RAW_DATA_FILE = "wushan_food_2026_raw.xlsx"
FINAL_DATA_FILE = "wushan_food_2026.xlsx"
MAP_FILE = "wushan_food_map.html"
BAR_CHART_FILE = "category_bar.png"
PIE_CHART_FILE = "category_pie.png"
