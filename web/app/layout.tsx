import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "吃啥 · 健身吃什么",
  description: "输入身体信息与目标，推荐吃什么、怎么做——专业健身菜谱平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
