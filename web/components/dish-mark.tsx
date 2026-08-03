// 菜谱印章：取菜名首字 + 按名字哈希取色，替代千篇一律的图标
type P = { title: string; size?: number; className?: string };

const TINTS = [
  { bg: "#e7c79a", fg: "#9c3421" },
  { bg: "#cfe0c8", fg: "#2f5f36" },
  { bg: "#ecd3b0", fg: "#8a5a10" },
  { bg: "#e3c9c2", fg: "#9c3421" },
  { bg: "#d8d3c2", fg: "#54422f" },
];

function hash(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

export default function DishMark({ title, size = 44, className }: P) {
  const ch = title.trim().charAt(0) || "食";
  const t = TINTS[hash(title) % TINTS.length];
  return (
    <span
      className={className}
      style={{
        width: size, height: size, borderRadius: 12, flexShrink: 0,
        background: t.bg, color: t.fg,
        display: "grid", placeItems: "center",
        fontFamily: '"Noto Serif SC", "Songti SC", "SimSun", serif',
        fontWeight: 900, fontSize: size * 0.52, lineHeight: 1,
        border: "1px solid rgba(43,33,24,.18)",
        boxShadow: "0 2px 0 rgba(43,33,24,.10)",
        userSelect: "none",
      }}
      aria-hidden="true"
    >
      {ch}
    </span>
  );
}
