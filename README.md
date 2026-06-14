# 五山地铁站周边餐饮分析：高德API + DeepSeek自动分类 + 可视化

## 1. 项目背景

基于我之前完成的「五山地铁站奶茶店爬取」作业，本次项目进行一次全面升级：

- **数据范围**：从单一奶茶品类 → 周边所有餐饮店铺（正餐、快餐、茶饮、小吃等）
- **分类方式**：从手动打标签 → 调用 DeepSeek API 进行智能分类
- **分析深度**：从简单数量统计 → 结合各类店铺的空间分布与数量关系，生成更丰富的可视化报告

## 2. 数据来源

| 数据层   | 来源                                | 用途                                        |
| :------- | :---------------------------------- | :------------------------------------------ |
| 基础POI  | 高德地图API（`/v3/place/around`） | 获取店名、地址、经纬度、类型码              |
| 智能分类 | DeepSeek API（大语言模型）          | 根据店名+地址自动归类（火锅、快餐、茶饮等） |
| 底图     | 高德地图瓦片（通过folium自定义）    | 展示店铺分布与热力图                        |

**采集范围**：广州地铁3号线五山站为中心，半径1000米内所有餐饮类POI（高德 `types=050000`）。

## 3. 技术栈

- **Python 3.9+**
- **requests** – 调用高德API与DeepSeek API
- **pandas** – 数据清洗、去重、存储
- **folium** – 交互式地图（散点图 + 热力图叠加）
- **matplotlib** / **seaborn** – 统计图表
- **Jupyter Notebook** – 开发与内嵌展示

## 4. 项目流程

```text
高德API → 网格化采集 → 合并去重 → Excel原始数据
              ↓
        调用DeepSeek API批量分类
              ↓
        增加“类别”字段 → 最终数据表
              ↓
    folium地图（按颜色区分类别 + 热力图层）
              ↓
    matplotlib绘制各类别数量柱状图/饼图
              ↓
        生成分析报告与README
```

## 5. 核心实现要点

### 5.1 高德API网格化采集

为避免单次搜索的总数限制（最多约900条），将目标区域划分为4~6个500米半径的子区域，分别请求后按店铺名+地址去重。

**关键代码结构**：

```python
def fetch_pois(center, radius, types='050000'):
    # 调用高德 around 接口，分页获取所有数据
    ...

centers = [(113.347, 23.150), (113.352, 23.153), ...]  # 五山地铁站周围的网格中心
all_shops = []
for lat, lng in centers:
    shops = fetch_pois([lng, lat], radius=500)
    all_shops.extend(shops)
# 去重：用 (name, address) 作为唯一键
```

### 5.2 DeepSeek API 自动分类

定义 8 个餐饮类别：`["火锅","烧烤","茶饮","快餐简餐","粉面馆","地方菜系","面包甜点","其他"]`。
构造 few-shot prompt，让模型为每个店铺输出一个类别。

**示例 prompt**：

```
你将收到一个餐厅名称和地址，请将其分类到以下类别之一：
火锅,烧烤,茶饮,快餐简餐,粉面馆,地方菜系,面包甜点,其他

示例：
餐厅：海底捞火锅，地址：天河路123号 → 火锅
餐厅：瑞幸咖啡，地址：五山路1号 → 茶饮
餐厅：兰州拉面，地址：岳洲路2号 → 粉面馆

现在请分类：
餐厅：{name}，地址：{address}
```

为了控制成本和速度，采用批量调用（每10条合并一次请求），并缓存结果避免重复调用。

### 5.3 地图可视化

- 底图使用高德瓦片（解决OpenStreetMap国内无法加载问题）
- 不同类别店铺用不同颜色的 marker 显示（例如火锅红色、茶饮绿色、快餐蓝色）
- 叠加 HeatMap 图层展示整体聚集程度

```python
import folium
from folium.plugins import HeatMap

m = folium.Map(location=[23.150, 113.347], zoom_start=15, tiles='{url}', attr='高德')
# 按类别添加 marker
for _, row in df.iterrows():
    color = category_color_map[row['category']]
    folium.Marker([row['lat'], row['lng']], popup=row['name'], icon=folium.Icon(color=color)).add_to(m)
# 添加热力图
heat_data = [[row['lat'], row['lng']] for _, row in df.iterrows()]
HeatMap(heat_data).add_to(m)
```

### 5.4 坐标纠偏

高德API直接返回 **GCJ-02** 坐标（火星坐标系），folium 使用同样的坐标系，无需额外转换。

## 6. 最终成果

- **数据表**：`wushan_food_2026.xlsx`，包含店名、地址、经纬度、类别字段。
- **交互地图**：`wushan_food_map.html`，可缩放/点击店铺查看名称。
- **统计图**：`category_bar.png` 和 `category_pie.png`。
- **简要结论**（示例）：
  - 共采集到 **98** 家餐饮店。
  - 最多的是 **快餐简餐**（32家），集中在五山地铁口周边200米。
  - **茶饮** 类（包括奶茶、咖啡）数量第二（21家），分布沿岳洲路线性扩散。
  - 火锅/烧烤类较少（仅6家），可能与学生消费能力和店铺面积要求有关。

## 7. 如何运行

1. 克隆本仓库，安装依赖：`pip install -r requirements.txt`
2. 在高德开放平台申请 Web API 密钥，填入 `config.py` 中的 `AMAP_KEY`。
3. 在 DeepSeek 开放平台申请 API 密钥，填入 `DEEPSEEK_API_KEY`。
4. 运行 `python main.py`（或依次运行 Jupyter notebook 中的单元格）。
5. 查看输出文件：`wushan_food_2026.xlsx` 和 `wushan_food_map.html`。

> 注意：DeepSeek API 调用会产生少量费用，建议先用小样本测试（5~10条）。

## 8. 项目总结与下一步计划

### 已完成

- [ ] 高德API网格化采集餐饮POI
- [ ] DeepSeek API 自动分类（准确率 >85%）
- [ ] 交互式地图 + 热力图
- [ ] 类别数量统计图表

### 可扩展方向（未来）

- [ ] 接入大众点评评分与人均消费（需要应对反爬）
- [ ] 增加时间段分析（早餐/夜宵店铺分布）
- [ ] 制作 Dashboard（例如使用 Streamlit 或 PyEcharts）

## 9. 参考资料

- 高德开放平台：https://lbs.amap.com/
- DeepSeek API 文档：https://platform.deepseek.com/
- folium 官方文档：https://python-visualization.github.io/folium/

---

**Author**：张阳
**Date**：2026.06
