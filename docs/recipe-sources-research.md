# 开源菜谱与营养数据源调研（2026-08-05）

目标是补齐日式、西式菜谱，同时保持“每份营养 = 已知食材 × 明确克数”的计算链路。评估标准依次是：许可证和权利链、食材/步骤可结构化程度、营养可验证性、维护性，以及是否适合静态构建期导入。

## 已采纳：HowToCook 作为做法来源

[Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook) 的根 [LICENSE](https://github.com/Anduin2017/HowToCook/blob/master/LICENSE) 为 Unlicense，允许复制、修改、商用和再分发。它是 Markdown 菜谱库，模板与实际菜谱有标题、工具、食材、计算和步骤，但没有统一、可验证的蛋白质/脂肪/碳水数据。

本项目采用以下受控方式，而不是全量自动抓取：

- 固定到提交 `c05758fa661ac4efa0361a987b700a351a22159b`；每道菜保存原始 URL、许可证和版本。
- 首批导入 4 道已人工映射到本地食材表的菜谱：日式肥牛丼饭、日式咖喱鸡肉饭、意式肉酱面、黄油香煎牛排配蔬菜。
- 不复制图片；不把上游“预估卡路里”当作产品营养数据；统一以 `ingredients[].ref` 与 g/ml 重算。
- 以后每批导入仍须检查可食部、生熟重量、范围值、可选食材和过敏原；不能因上游是 Unlicense 就跳过营养审校。

这让 HowToCook 成为中文做法的可追溯来源，但它不是西餐/日餐营养数据库的替代品。

## 营养事实源

| 来源 | 许可证/权利 | 适合用途 | 结论 |
|---|---|---|---|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) | CC0 / 公共领域；建议标明来源 | 西式常见食材、家庭份量、每 100g 营养 | 推荐作为全球食材和份量规则的构建期参考，不在运行期依赖 API |
| [日本食品标准成分表 / MEXT 食品成分数据库](https://fooddb.mext.go.jp/) | 官方明确可二次利用，须注明出典 | 日式食材、米饭、纳豆、豆腐、调味品 | 推荐作为下一批日餐食材补充；导入前保存版本和来源字段 |
| 《中国食物成分表（第 6 版）》 | 出版社版权，商用需单独授权 | 当前中文食材主库 | 继续沿用现有学习/研究边界；商业化时优先替换或取得授权 |

FoodData Central 的份量文档明确以“可食部分克数”配合每 100g 营养计算每份，正好对应本项目的计算方式。因此“大苹果”“中等香蕉”“一杯牛奶”被实现为带来源的估算词典，而不是把自然语言直接当成精确重量。

## GitHub 候选与处理结论

| 候选 | 覆盖 | 许可证/数据质量 | 结论 |
|---|---|---|---|
| [Anduin2017/HowToCook](https://github.com/Anduin2017/HowToCook) | 中文家庭菜、部分日式/意式/西式 | Unlicense；步骤可用，营养不完整 | 已采用为做法来源，人工映射后导入 |
| [mrslbt/tabedata-mcp](https://github.com/mrslbt/tabedata-mcp) | 日本连锁、便利店、日系快餐 | MIT；README 数据说明称约 10% 为估算/AI 编译 | 不作为核心营养真值；未来可人工复核后用于“品牌食品”补充 |
| [openfoodfacts/openfoodfacts-server](https://github.com/openfoodfacts/openfoodfacts-server) | 全球包装食品、条码、过敏原 | 服务器 AGPL-3.0，数据库 ODbL | 不合并进本地食品库；若将来做条码即时查询，需先接受署名/ShareAlike 数据义务 |
| [google-research-datasets/Nutrition5k](https://github.com/google-research-datasets/Nutrition5k) | 5,006 份餐食的营养聚合 | CC BY 4.0；没有可展示的完整菜谱，仓库已归档 | 仅可作聚合计算测试/研究数据，不导入产品菜谱 |
| [josephrmartinez/recipe-dataset](https://github.com/josephrmartinez/recipe-dataset) | 英文菜谱样本 | 标注 CC BY-SA，但正文来自 Epicurious | 上游权利链不清，不导入 |

未采用“网页爬虫 + 大规模抓取菜谱”路线：即使脚本仓库是开源，抓到的菜谱正文、图片和品牌数据仍未自动获得再分发权。

## 扩充流程

1. 选择有明确许可证的单道菜谱，固定上游提交或发布版本。
2. 在 `data/recipes/*.json` 写入 `source.name/url/license/revision`，并将所有食材改成可计算的 g/ml。
3. 让每个 `ref` 匹配 `data/processed/foods.json`；不匹配时先补充带来源的食材数据，不用“适量”绕过构建。
4. 运行 `python scripts/build_data.py`，检查营养和 `source` 是否进入 `data/processed/recipes.json`。
5. 执行后端测试、前端构建和实际页面检查；详情页必须显示来源，热量查询必须显示“估算”。

详见 [ADR-0005](../decisions/adr/2026-08/2026-08-05-0005-external-recipe-provenance-and-portion-estimation.md)。
