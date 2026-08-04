// 购物清单：按类目分组，可勾选「家里已有」，勾选状态按天保存在本地
import { useEffect, useState } from "react";
import { IconCheck } from "@/components/icons";
import { groupShoppingItems, type ShoppingItem } from "@/lib/shopping";

const STORAGE_KEY = "chisha-shopping-checked-v1";

function loadChecked(): Record<string, string[]> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const data = raw ? JSON.parse(raw) : {};
    return typeof data === "object" && data !== null ? data : {};
  } catch {
    return {};
  }
}

export default function ShoppingList({ items, storageKey }: { items: ShoppingItem[]; storageKey: string }) {
  const [checked, setChecked] = useState<Set<string>>(new Set());

  useEffect(() => {
    setChecked(new Set(loadChecked()[storageKey] || []));
  }, [storageKey]);

  const itemKey = (item: ShoppingItem) => `${item.name}|${item.unit}|${item.note}`;

  const toggle = (item: ShoppingItem) => {
    setChecked((prev) => {
      const next = new Set(prev);
      const key = itemKey(item);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      const all = loadChecked();
      all[storageKey] = [...next];
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
      } catch { /* ignore */ }
      return next;
    });
  };

  const clear = () => {
    const all = loadChecked();
    delete all[storageKey];
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(all));
    } catch { /* ignore */ }
    setChecked(new Set());
  };

  if (items.length === 0) return null;

  const groups = groupShoppingItems(items);
  const doneCount = groups.reduce((sum, group) => sum + group.items.filter((item) => checked.has(itemKey(item))).length, 0);

  return (
    <div>
      {groups.map((group) => (
        <div className="shop-group" key={group.key}>
          <div className="shop-group-title">{group.label}</div>
          <ul className="shop-list shop-checkable">
            {group.items.map((item) => {
              const key = itemKey(item);
              const done = checked.has(key);
              return (
                <li key={key} className={done ? "done" : ""} onClick={() => toggle(item)}>
                  <span className="shop-box" aria-hidden="true">{done ? <IconCheck size={11} /> : null}</span>
                  <span>
                    {item.name}
                    {item.note ? <span className="note">（{item.note}）</span> : null}
                  </span>
                  <span className="amt">{item.amount}{item.unit}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
      {doneCount > 0 && (
        <div className="btn-row" style={{ marginTop: 10 }}>
          <button type="button" className="btn ghost" onClick={clear}>清空勾选（已勾 {doneCount} 项）</button>
        </div>
      )}
    </div>
  );
}
