// 购物清单按类目分组：按名称关键词归类，方便按摊位采买
export type ShoppingItem = { name: string; amount: number; unit: string; note: string };

export type ShoppingGroup = { key: string; label: string; items: ShoppingItem[] };

export const SHOP_GROUPS: { key: string; label: string; keywords: string[] }[] = [
  { key: "meat", label: "肉蛋水产", keywords: ["鸡", "牛柳", "牛腱", "牛肉", "牛排", "猪", "羊", "鸭", "鹅", "鱼", "虾", "蟹", "贝", "三文鱼", "金枪鱼", "蛋", "火腿", "培根"] },
  { key: "veggie", label: "蔬菜菌菇", keywords: ["菜", "瓜", "椒", "茄", "萝卜", "菇", "菌", "葱", "姜", "蒜", "豆芽", "笋", "芹", "芦笋", "洋葱", "番茄", "黄瓜", "紫菜", "海带", "南瓜", "藕", "山药", "土豆", "红薯", "芋"] },
  { key: "fruit", label: "水果", keywords: ["果", "蕉", "莓", "柠檬", "青柠", "橙", "柚", "桃", "梨", "苹果", "葡萄"] },
  { key: "grain", label: "主食谷物", keywords: ["米", "饭", "面", "包", "麦", "藜", "玉米", "卷饼", "皮塔", "汉堡", "馒头", "粥", "粉"] },
  { key: "dairy", label: "奶制品", keywords: ["奶", "酸奶", "芝士", "奶酪", "黄油", "奶油"] },
  { key: "seasoning", label: "调料干货", keywords: ["油", "盐", "糖", "醋", "酱", "料酒", "胡椒", "椒粉", "咖喱", "味噌", "鱼露", "蚝油", "淀粉", "蜂蜜", "香茅", "罗勒", "迷迭香", "孜然", "姜黄", "辣椒", "八", "桂皮", "花椒", "香油", "蒜末", "花生", "核桃", "杏仁", "芝麻", "奇亚籽", "蛋白粉", "海苔"] },
];

export function groupShoppingItems(items: ShoppingItem[]): ShoppingGroup[] {
  const grouped = SHOP_GROUPS.map((group) => ({ key: group.key, label: group.label, items: [] as ShoppingItem[] }));
  const other: ShoppingItem[] = [];
  for (const item of items) {
    const hit = grouped.find((group) => SHOP_GROUPS.find((g) => g.key === group.key)!.keywords.some((kw) => item.name.includes(kw)));
    if (hit) hit.items.push(item);
    else other.push(item);
  }
  const list = grouped.filter((group) => group.items.length > 0);
  if (other.length > 0) list.push({ key: "other", label: "其他", items: other });
  return list;
}
