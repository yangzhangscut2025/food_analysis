"""
高德API网格化采集模块

通过高德地图 v3/place/around 接口，对五山地铁站周边进行网格化POI采集，
将多个子区域的搜索结果合并去重，获取完整的餐饮店铺列表。
"""
import time
import requests
import pandas as pd
from config import (
    AMAP_KEY, AMAP_AROUND_URL, AMAP_PAGE_SIZE, REQUEST_DELAY,
    GRID_CENTERS, RAW_DATA_FILE
)


def fetch_pois(lng, lat, radius=500, types="050000"):
    """
    调用高德 around 接口，分页获取指定中心点周边的所有POI数据。

    Parameters
    ----------
    lng : float
        中心点经度
    lat : float
        中心点纬度
    radius : int
        搜索半径（米），默认500
    types : str
        高德POI类型码，050000=餐饮

    Returns
    -------
    list[dict]
        店铺列表，每条包含 name, address, lng, lat, typecode, adname
    """
    shops = []
    page = 1

    while True:
        params = {
            "key": AMAP_KEY,
            "location": f"{lng},{lat}",
            "radius": radius,
            "types": types,
            "offset": AMAP_PAGE_SIZE,
            "page": page,
            "extensions": "base",
        }

        try:
            resp = requests.get(AMAP_AROUND_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [警告] 请求失败 (page={page}): {e}")
            break
        except ValueError as e:
            print(f"  [警告] JSON 解析失败 (page={page}): {e}")
            break

        if data.get("status") != "1":
            print(f"  [警告] API 返回异常状态: {data.get('info', '未知错误')}")
            break

        pois = data.get("pois", [])
        if not pois:
            break

        for poi in pois:
            location = poi.get("location", "0,0")
            try:
                poi_lng, poi_lat = location.split(",")
                poi_lng = float(poi_lng)
                poi_lat = float(poi_lat)
            except (ValueError, AttributeError):
                poi_lng, poi_lat = 0.0, 0.0

            shops.append({
                "name": poi.get("name", ""),
                "address": poi.get("address", ""),
                "lng": poi_lng,
                "lat": poi_lat,
                "typecode": poi.get("typecode", ""),
                "adname": poi.get("adname", ""),
            })

        total = int(data.get("count", 0))
        fetched = page * AMAP_PAGE_SIZE
        if fetched >= total:
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    return shops


def collect_all_shops():
    """
    遍历所有网格中心点，采集POI数据，按 (店名, 地址) 去重。

    Returns
    -------
    pd.DataFrame
        去重后的店铺数据，包含 name, address, lng, lat, typecode, adname 列
    """
    all_shops = []

    print("=" * 50)
    print("步骤 1/3：高德API网格化采集餐饮POI")
    print("=" * 50)

    for i, (lng, lat) in enumerate(GRID_CENTERS, 1):
        print(f"\n采集网格 {i}/{len(GRID_CENTERS)}：中心=({lng}, {lat})")
        shops = fetch_pois(lng, lat, radius=500, types="050000")
        print(f"  获取到 {len(shops)} 条记录")
        all_shops.extend(shops)

    print(f"\n网格采集完成，共获取 {len(all_shops)} 条记录（含重复）")

    # 转为 DataFrame 并按 (name, address) 去重
    df = pd.DataFrame(all_shops)
    if df.empty:
        print("[警告] 未采集到任何数据，请检查 API Key 或网络连接")
        return df

    before = len(df)
    df = df.drop_duplicates(subset=["name", "address"], keep="first")
    after = len(df)
    print(f"去重后保留 {after} 条记录（移除 {before - after} 条重复）")

    return df


def save_raw_data(df, path=None):
    """
    保存原始数据到 Excel 文件。

    Parameters
    ----------
    df : pd.DataFrame
        原始店铺数据
    path : str, optional
        输出路径，默认使用 config 中的 RAW_DATA_FILE
    """
    if path is None:
        path = RAW_DATA_FILE
    df.to_excel(path, index=False, engine="openpyxl")
    print(f"\n原始数据已保存到: {path}")
