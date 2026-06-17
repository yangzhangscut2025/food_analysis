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
MAX_RETRIES = 3       # 限流/网络错误时最大重试次数
RETRY_BACKOFF = 2     # 重试等待基础秒数（指数增长：2s, 4s, 8s）

# --- 网格采集中心点 ---
# 华南理工大学五山校区坐标：113.351, 23.155
# 半径 2000 米范围，用 5×5 网格的 500m 半径子区域覆盖
# 500m ≈ 0.0045° lat, ≈ 0.0049° lng（广州纬度 cos(23.15°)≈0.919）
WUSHAN_CENTER = (113.351, 23.155)  # (lng, lat) — 华工五山校区（默认）
GRID_CENTERS = [
    # 5×5 网格，步长 ~500m，覆盖 2000m 半径
    (113.3412, 23.1640), (113.3461, 23.1640), (113.3510, 23.1640), (113.3559, 23.1640), (113.3608, 23.1640),
    (113.3412, 23.1595), (113.3461, 23.1595), (113.3510, 23.1595), (113.3559, 23.1595), (113.3608, 23.1595),
    (113.3412, 23.1550), (113.3461, 23.1550), (113.3510, 23.1550), (113.3559, 23.1550), (113.3608, 23.1550),
    (113.3412, 23.1505), (113.3461, 23.1505), (113.3510, 23.1505), (113.3559, 23.1505), (113.3608, 23.1505),
    (113.3412, 23.1460), (113.3461, 23.1460), (113.3510, 23.1460), (113.3559, 23.1460), (113.3608, 23.1460),
]


def make_grid(center_lng, center_lat, span=2000, cell=500):
    """Generate a 5x5 grid centered on (lng, lat), covering ~span meters."""
    import math
    step_lng = cell / (111000 * math.cos(math.radians(center_lat)))
    step_lat = cell / 111000
    grid = []
    for i in range(-2, 3):
        for j in range(-2, 3):
            grid.append((center_lng + j * step_lng, center_lat + i * step_lat))
    return grid

# --- DeepSeek API 配置 ---
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
CLASSIFICATION_BATCH_SIZE = 10  # 每批处理的店铺数
CACHE_FILE = "classification_cache.json"

# --- 餐饮类别（10 类）---
CATEGORIES = [
    "火锅", "烧烤", "茶饮咖啡", "粉面小吃", "快餐简餐",
    "中餐正餐", "异国料理", "面包甜点", "早餐粥铺", "其他"
]

# --- 类别颜色映射（folium marker 颜色）---
CATEGORY_COLORS = {
    "火锅":     "red",
    "烧烤":     "orange",
    "茶饮咖啡": "green",
    "粉面小吃": "purple",
    "快餐简餐": "blue",
    "中餐正餐": "darkred",
    "异国料理": "cadetblue",
    "面包甜点": "pink",
    "早餐粥铺": "beige",
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
