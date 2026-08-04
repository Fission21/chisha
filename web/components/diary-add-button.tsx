// 菜谱详情「记一笔」：选餐次即写入当天饮食记录
"use client";

import { useState } from "react";
import { addToDiary, dateKey, pushDiaryDateToServer, type DiaryItem } from "@/lib/diary";
import { IconCheck } from "@/components/icons";

type Nutrition = { energyKCal: number; protein: number; fat: number; CHO: number; dietaryFiber: number; sodium: number };

const MEALS: [string, string][] = [
  ["breakfast", "早餐"],
  ["lunch", "午餐"],
  ["dinner", "晚餐"],
  ["snack", "加餐"],
];

export default function DiaryAddButton({ recipeId, title, nutrition }: { recipeId: string; title: string; nutrition: Nutrition }) {
  const [open, setOpen] = useState(false);
  const [done, setDone] = useState("");

  const add = (meal: string, label: string) => {
    const date = dateKey(new Date());
    const item: DiaryItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: "recipe",
      refId: recipeId,
      name: title,
      meal,
      amount: 1,
      unit: "份",
      nutrition,
    };
    const map = addToDiary(date, item);
    pushDiaryDateToServer(date, map[date] || []);
    setDone(label);
    setOpen(false);
  };

  return (
    <span className="diary-add">
      {!done ? (
        <>
          {open ? (
            MEALS.map(([value, label]) => (
              <button type="button" className="btn ghost diary-add-meal" key={value} onClick={() => add(value, label)}>
                {label}
              </button>
            ))
          ) : (
            <button type="button" className="btn ghost diary-add-open" onClick={() => setOpen(true)}>记一笔</button>
          )}
        </>
      ) : (
        <span className="pill diary-add-done"><IconCheck size={14} /> 已记入{done}</span>
      )}
    </span>
  );
}
