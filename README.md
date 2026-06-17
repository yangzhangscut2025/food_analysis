# 华南理工大学五山校区周边餐饮分析

高德POI采集 + DeepSeek自动分类 + Folium交互可视化

## 1. 项目背景

基于奶茶店爬取作业升级为完整数据流水线：

- **数据范围**：从单一奶茶品类 → 周边所有餐饮（正餐、快餐、茶饮、小吃等）
- **分类方式**：从手动打标签 → DeepSeek API 智能分类（8 个类别）
- **分析深度**：从简单统计 → 交互式地图 + 图层控制 + 聚合标记 + 热力图 + 统计图表

## 2. 数据来源

| 数据层   | 来源                        | 用途                             |
| :------- | :-------------------------- | :------------------------------- |
| 基础POI  | 高德地图 `/v3/place/around` | 店名、地址、经纬度、类型码       |
| 智能分类 | DeepSeek Chat API           | 8 类别自动归类（火锅/茶饮/粉面等）|
| 底图     | 高德瓦片（通过 folium）     | 替代 OSM，国内加载快             |

**采集范围**：华南理工大学五山校区（113.351, 23.155）为中心，5×5 网格（25个子区域），500m半径/子区，覆盖 ~2000m。

## 3. 技术栈

- Python 3.9+
- requests — 调用高德API与DeepSeek API
- pandas — 数据清洗、去重、存储
- folium + 插件（MarkerCluster, HeatMap, Fullscreen, LayerControl）— 交互式地图
- matplotlib / seaborn — 统计图表
- python-dotenv — 环境变量管理（API 密钥）

## 4. 项目流程

```text
高德API -> 5x5网格分页采集 -> 合并去重 -> 原始数据 Excel
                  ↓
        DeepSeek 批量分类（每10条一批，结果缓存JSON）
                  ↓
        带"类别"字段的最终数据表
                  ↓
   folium 地图（LayerControl + MarkerCluster + HeatMap + 图例面板）
                  ↓
   matplotlib 柱状图/饼图 + 分析结论
```

## 5. 项目结构

```
food/
├── .env                        # API密钥（自行填写，已 gitignore）
├── .gitignore
├── README.md                   # 项目文档
├── requirements.txt            # Python 依赖
├── config.py                   # 全局配置（网格坐标、类别、颜色、路径）
├── poi_fetcher.py              # 高德API网格采集（含限流重试）
├── classifier.py               # DeepSeek 批量分类（含缓存）
├── visualizer.py               # 地图 + 图例 + matplotlib 图表
├── main.py                     # 主流水线入口
├── project.html                # 项目展示页（个人主页用）
├── food_analysis.ipynb         # Jupyter Notebook 版本
├── classification_cache.json   # 分类缓存（自动生成）
├── wushan_food_2026_raw.xlsx   # 原始POI数据
├── wushan_food_2026.xlsx       # 带分类标签的最终数据
├── wushan_food_map.html        # 交互式地图（浏览器打开）
├── category_bar.png            # 类别柱状图
└── category_pie.png            # 类别饼图
```

## 6. 核心实现

### 6.1 高德网格采集

25 个网格点覆盖 2000m 范围。遇到 `CUQPS_HAS_EXCEEDED_THE_LIMIT` 自动重试（最多 3 次，指数退避 2s/4s/8s）。

```python
def fetch_pois(lng, lat, radius=500):
    # 高德 around 接口分页获取
    # 限流自动重试

for lng, lat in GRID_CENTERS:          # 5x5 共 25 个中心点
    shops = fetch_pois(lng, lat)
df.drop_duplicates(["name", "address"])  # 去重
```

### 6.2 DeepSeek 分类

10 个类别：火锅、烧烤、茶饮咖啡、粉面小吃、快餐简餐、中餐正餐、异国料理、面包甜点、早餐粥铺、其他。含 13 条边界案例 few-shot 示例，区分肠粉(早餐) vs 螺蛳粉(小吃) vs 饺子(快餐)。

- 批量调用：每 10 条合并一次请求
- 结果缓存：`classification_cache.json`，重复运行不重复扣费
- 低温度参数（temperature=0.1）保证输出稳定
- System prompt 含分类说明，要求 JSON 格式返回

### 6.3 地图功能

| 功能         | 实现方式                                    |
| :----------- | :------------------------------------------ |
| 图层切换     | `LayerControl` — 10 个类别 + 热力图，自由开关  |
| 标记聚合     | `MarkerCluster` — 邻近店铺聚合，显示数量，点击展开 |
| 标记样式     | `DivIcon` 20px 彩色圆点                      |
| 悬停提示     | `Tooltip` 显示店名                           |
| 点击弹窗     | 店名 + 类别 + 地址 + 高德导航链接按钮         |
| 热力图       | `HeatMap` 插件，通过图层控制器开关             |
| 图例面板     | 右上角：总数 + 各类别数量/占比 + 采集日期       |
| 全屏         | `Fullscreen` 插件（左上角）                   |

### 6.4 坐标系

高德返回 GCJ-02（火星坐标系），folium 使用相同坐标系，无需转换。

## 7. 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 在 .env 中填写 API 密钥
AMAP_KEY=你的高德key
DEEPSEEK_API_KEY=你的deepseek key

# 3. 运行（原始数据存在则跳过采集）
python main.py

# 强制重新采集
python main.py --force

# 或使用 Jupyter
jupyter notebook food_analysis.ipynb
```

> DeepSeek API 调用会产生少量费用。分类结果已缓存，重复运行不额外扣费。

## 8. 输出文件

| 文件                          | 说明                     |
| :---------------------------- | :----------------------- |
| `wushan_food_2026_raw.xlsx`   | 原始采集数据             |
| `wushan_food_2026.xlsx`       | 带类别标签的最终数据     |
| `wushan_food_map.html`        | 交互式地图（浏览器打开） |
| `category_bar.png`            | 类别柱状图               |
| `category_pie.png`            | 类别饼图                 |

## 9. 可扩展方向

- [ ] 接入大众点评评分与人均消费
- [ ] 时间段分析（早餐/夜宵分布）
- [ ] Streamlit / PyEcharts Dashboard
- [ ] 距离计算（店铺到校区各门距离）
- [ ] 同类竞品热力对比

## 10. 参考

- 高德开放平台：https://lbs.amap.com/
- DeepSeek API：https://platform.deepseek.com/
- Folium 文档：https://python-visualization.github.io/folium/

---

**Author**：张阳
**Date**：2026.06
