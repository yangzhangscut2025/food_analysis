"""
DeepSeek API 批量分类模块

根据店铺名称和地址，调用 DeepSeek Chat API 进行智能分类。
支持批量调用（合并多条为一次请求）和结果缓存，减少API费用。
"""
import json
import time
import requests
import pandas as pd
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_URL, DEEPSEEK_MODEL,
    CATEGORIES, CLASSIFICATION_BATCH_SIZE, CACHE_FILE
)

# --- 分类 Prompt 模板 ---
SYSTEM_PROMPT = """你是一个餐饮店铺分类助手。你将收到一批餐厅数据，每条包含"店名"和"地址"。
请根据店名和地址，将每条餐厅分类到以下 10 个类别之一：

火锅, 烧烤, 茶饮咖啡, 粉面小吃, 快餐简餐, 中餐正餐, 异国料理, 面包甜点, 早餐粥铺, 其他

== 类别定义 ==

1. 火锅：以火锅为主的餐厅。包括麻辣火锅、潮汕牛肉火锅、椰子鸡火锅、串串香、麻辣烫等。
   - 典型: 海底捞火锅、八合里牛肉火锅、大龙燚、杨国福麻辣烫

2. 烧烤：以烧烤、烤肉为主的餐厅。注意：韩式烤肉属于烧烤，不是异国料理。
   - 典型: 木屋烧烤、东北烤肉、韩式烤肉、九田家

3. 茶饮咖啡：奶茶店、咖啡店、茶饮店、果汁店等饮品店。
   - 典型: 瑞幸咖啡、星巴克、喜茶、蜜雪冰城、茶颜悦色、邻里手打柠檬茶

4. 粉面小吃：以粉、面、米线、螺蛳粉、酸辣粉为主的小吃店，以及炸串、卤味、鸭脖、臭豆腐等零食小吃店。
   - 典型: 兰州拉面、螺蛳粉、桂林米粉、绝味鸭脖、周黑鸭、炸串铺、煎饼果子
   - 注意: 肠粉店归于"早餐粥铺"；饺子馆归于"快餐简餐"

5. 快餐简餐：快餐、简餐、食堂、自选快餐、盒饭、沙县小吃、隆江猪脚饭、黄焖鸡米饭、饺子馆等快速解决一顿饭的店铺。
   - 典型: 麦当劳、肯德基、沙县小吃、自选快餐、隆江猪脚饭、黄焖鸡米饭、东北饺子馆

6. 中餐正餐：有明确中国菜系归属的正餐餐厅。包括川菜、粤菜、湘菜、客家菜、东北菜、酸菜鱼专门店等。
   - 典型: 太二酸菜鱼、点都德、湘菜馆、客家王、东北人家

7. 异国料理：外国菜系餐厅。包括日料寿司、韩式炸鸡、泰国菜、越南河粉、西餐牛排、披萨等。
   - 典型: 元气寿司、韩式炸鸡、泰国餐厅、萨莉亚、必胜客
   - 注意: 韩式烤肉属于"烧烤"不是异国料理

8. 面包甜点：面包店、蛋糕店、甜品店、糕点店。
   - 典型: 面包新语、85度C、好利来、满记甜品

9. 早餐粥铺：主营早餐的肠粉店、包子铺、粥店、豆浆油条、蒸饺店等。
   - 典型: 银记肠粉、包子铺、粥店、豆浆油条、天津灌汤包

10. 其他：农庄、食堂、中央厨房、食品加工坊等无法归入以上类别的店铺。

== 常见边界案例 ==
- 椰子鸡 → 火锅
- 麻辣烫 → 火锅
- 韩式烤肉 → 烧烤
- 肠粉店 → 早餐粥铺
- 螺蛳粉/酸辣粉 → 粉面小吃
- 沙县小吃 → 快餐简餐
- 隆江猪脚饭 → 快餐简餐
- 饺子馆 → 快餐简餐
- 绝味鸭脖/周黑鸭 → 粉面小吃
- 日料寿司 → 异国料理
- 萨莉亚/必胜客 → 异国料理

请严格按照以下 JSON 数组格式返回结果，不要添加任何其他文字：
[{"index": 0, "category": "火锅"}, {"index": 1, "category": "茶饮咖啡"}, ...]"""


def load_cache():
    """加载分类缓存"""
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    """保存分类缓存"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def build_batch_prompt(shops_batch):
    """
    构建单批次的 user prompt。

    Parameters
    ----------
    shops_batch : list[dict]
        待分类的店铺列表，每项含 name, address

    Returns
    -------
    str
        用户消息文本
    """
    lines = ["请对以下餐厅进行分类：\n"]
    for i, shop in enumerate(shops_batch):
        lines.append(f"{i}. 店名：{shop['name']}，地址：{shop['address']}")
    return "\n".join(lines)


def call_deepseek_classify(shops_batch):
    """
    调用 DeepSeek API 对一批店铺进行分类。

    Parameters
    ----------
    shops_batch : list[dict]
        待分类的店铺列表

    Returns
    -------
    list[str]
        分类结果列表，顺序与输入一致
    """
    user_prompt = build_batch_prompt(shops_batch)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,  # 低温度，保证输出稳定
        "max_tokens": 2048,
    }

    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()
    except requests.RequestException as e:
        print(f"  [错误] DeepSeek API 请求失败: {e}")
        return ["其他"] * len(shops_batch)

    # 解析返回内容
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    content = content.strip()

    # 去除可能的 markdown 代码块标记
    if content.startswith("```"):
        lines = content.split("\n")
        # 去掉首尾的 ``` 行
        content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        parsed = json.loads(content)
        # 按 index 排序，提取 category
        parsed.sort(key=lambda x: x.get("index", 0))
        categories = [item.get("category", "其他") for item in parsed]
        # 确保长度匹配
        while len(categories) < len(shops_batch):
            categories.append("其他")
        return categories[: len(shops_batch)]
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"  [警告] 分类结果解析失败: {e}")
        print(f"  原始返回: {content[:200]}...")
        return ["其他"] * len(shops_batch)


def classify_all(df):
    """
    对 DataFrame 中所有店铺进行批量分类。

    先查缓存，缓存未命中的再分批调用 DeepSeek API。
    结果以 "category" 列的形式添加到原 DataFrame。

    Parameters
    ----------
    df : pd.DataFrame
        包含 name, address 列的店铺数据

    Returns
    -------
    pd.DataFrame
        添加了 category 列的 DataFrame
    """
    print("\n" + "=" * 50)
    print("步骤 2/3：DeepSeek API 批量分类")
    print("=" * 50)

    # 重置索引为连续的 0, 1, 2, ...，避免去重后跳号导致越界
    df = df.reset_index(drop=True)

    if df.empty:
        print("[警告] 数据为空，跳过分类")
        df["category"] = "其他"
        return df

    cache = load_cache()
    print(f"已加载缓存，包含 {len(cache)} 条历史记录")

    # 构建缓存键： (name, address)
    def make_key(row):
        return f"{row['name']}|{row['address']}"

    categories = [None] * len(df)
    uncached_indices = []

    for idx, row in df.iterrows():
        key = make_key(row)
        if key in cache:
            categories[idx] = cache[key]
        else:
            uncached_indices.append(idx)

    cached_count = len(df) - len(uncached_indices)
    if cached_count > 0:
        print(f"缓存命中 {cached_count} 条，需调用 API 分类 {len(uncached_indices)} 条")

    if not uncached_indices:
        df["category"] = categories
        return df

    # 分批调用 API
    batch_size = CLASSIFICATION_BATCH_SIZE
    total_batches = (len(uncached_indices) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start = batch_num * batch_size
        end = min(start + batch_size, len(uncached_indices))
        batch_indices = uncached_indices[start:end]
        batch_shops = [
            {"name": df.at[idx, "name"], "address": df.at[idx, "address"]}
            for idx in batch_indices
        ]

        print(f"\n处理批次 {batch_num + 1}/{total_batches}（{len(batch_shops)} 条）...")
        batch_categories = call_deepseek_classify(batch_shops)

        for i, idx in enumerate(batch_indices):
            if i < len(batch_categories):
                cat = batch_categories[i]
                # 验证类别是否在预定义列表中
                if cat not in CATEGORIES:
                    cat = "其他"
                categories[idx] = cat
                # 写入缓存
                key = make_key(df.loc[idx])
                cache[key] = cat

        # 每批结束后保存缓存
        save_cache(cache)
        print(f"  已分类: {[c for c in batch_categories]}")

        # 批次间延时，避免触发频率限制
        if batch_num < total_batches - 1:
            time.sleep(0.5)

    df["category"] = categories

    # 统计分类结果
    print("\n分类完成！各类别数量：")
    for cat, count in df["category"].value_counts().items():
        print(f"  {cat}: {count} 家")

    return df
