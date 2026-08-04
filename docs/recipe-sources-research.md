# 开源菜谱数据源调研（2026-08-04）

> 目的：把「吃啥」的菜谱库从 77 道扩充到规模化，同时保持"食材→营养库→按克数推导营养"的现有管道成立。

## 一、国际菜谱（英语/全球）

### 1. TheMealDB —— 首选，已实测可用
- 官网：https://www.themealdb.com （免费 REST API，key 用默认 1 即可）
- 规模：669 道全球菜谱，14 个分类：Beef / Chicken / Dessert / Pasta / Seafood / Vegetarian / Breakfast / Lamb / Goat / Pork / Starter / Side / Miscellaneous / Vegan
- 每道菜包含：菜名、地区（British / Chinese / Italian / Mexican...）、食材+用量、分步做法、封面图、分类标签
- 实测：/api/json/v1/1/search.php?s=chicken 返回 200 OK（59KB）；分类拉取正常
- 优点：免费、JSON 直接拿、字段结构与现有菜谱格式高度吻合、正好补"全球菜谱"空缺
- 缺点：英文；中餐只有少量（宫保鸡丁等）；食材是英文明称，需要映射到营养库

### 2. hhursev/recipe-scrapers —— 抓取工具（GitHub 2208 星）
- https://github.com/hhursev/recipe-scrapers
- Python 包，支持解析 300+ 菜谱网站（AllRecipes / BBC Good Food / 下厨房等）
- 不直接给数据，是"批量抓取器"：指定 URL/站点即可抓结构化菜谱
- 用途：按需补充特定品类（健身友好：鸡胸、牛肉、虾仁、减脂餐）

### 3. openrecipes（fictive-kin）—— 下载源疑似失效
- https://github.com/fictive-kin/openrecipes
- 曾提供 10 万+ 菜谱 MongoDB dump
- 实测官方 S3 链接只返回 20 字节，已失效；需找镜像

### 4. Recipe1M —— 学术数据集（英文，100 万道）
- 需注册申请，1.3GB，pickle / layer1.json 格式
- 含步骤/食材/图片，但无营养数据，清洗成本高

### 5. Kaggle 数据集
- Food.com：18 万菜谱含营养信息 + 70 万条评分
- Epicurious：2 万菜谱含营养
- 均为 CSV，需 Kaggle 账号下载

## 二、中文菜谱（最贴合产品定位）

### 1. 下厨房语料库 —— 152 万条（含 3 万道菜）非 GitHub
- OpenBayes：openbayes.com/console/hyperai-tutorials/datasets/FiI7ADwGuzB/1/overview
- 含菜名/食材/步骤，学术用途；需要清洗 + 食材名映射营养库
- 最大，但落地成本最高

### 2. 美食天下爬虫仓库 —— 大多只有代码没有数据
- copyWith/meishiChina 等 5+ 个仓库都是静态站爬虫代码，无数据，不值得用

### 3. JoeanAmier/Kitchen_Helper —— 下厨房爬虫
- https://github.com/JoeanAmier/Kitchen_Helper
- 可自己跑，抓取下厨房菜谱入库（含食材、步骤、营养标签）

## 三、营养数据策略（关键约束）
- 现有营养库：1657 条中国食物成分表 + 84 条全球食材 = 1741 条
- 新菜谱的食材尽量映射到现有营养库，按克数推导营养，推荐/热量计算依然成立
- 映射不上的：按份估算并标注"参考值"，或跳过该道菜

## 四、推荐落地路线
1. 第一步（立刻做）：导入 TheMealDB 669 道，菜谱库 77 -> 700+，全球菜系全覆盖，英文菜名配中文译名+emoji
2. 第二步（补充中文）：用 recipe-scrapers 从下厨房/美食天下抓"健身友好品类"（鸡胸/牛肉/虾/减脂餐），先小批量（几百道）
3. 第三步（规模化）：下厨房 152 万语料库做清洗管线，长期扩充