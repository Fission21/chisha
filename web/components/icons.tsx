// 手绘风线性图标集：统一 1.8 描边、currentColor，不用 emoji 当图标
import type { CSSProperties } from "react";

type P = { size?: number; className?: string; style?: CSSProperties };

const S = ({ size = 20, className, style, children }: P & { children: React.ReactNode }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    className={className} style={style} aria-hidden="true">
    {children}
  </svg>
);

export const IconBowl = (p: P) => (
  <S {...p}><path d="M4 11h16a8 8 0 0 1-16 0Z" /><path d="M12 3v3M8 3v2M16 3v2" /></S>
);
export const IconFlame = (p: P) => (
  <S {...p}><path d="M12 3c1 3-4 5-4 9a4 4 0 0 0 8 0c0-2-1-3-2-4-.3 1-1 2-2 2 1-3 0-5 0-7Z" /></S>
);
export const IconProtein = (p: P) => (
  <S {...p}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5v9M8.5 10.5h7" /></S>
);
export const IconCarbs = (p: P) => (
  <S {...p}><path d="M4 10.5h16v6a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5v-6Z" /><path d="M7.5 10.5V8a4.5 4.5 0 0 1 9 0v2.5" /></S>
);
export const IconFat = (p: P) => (
  <S {...p}><path d="M12 3.5s6 6.2 6 10.2a6 6 0 0 1-12 0C6 9.7 12 3.5 12 3.5Z" /><path d="M9.5 15a2.5 2.5 0 0 0 2.5 2.5" /></S>
);
export const IconClock = (p: P) => (
  <S {...p}><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></S>
);
export const IconChef = (p: P) => (
  <S {...p}><path d="M7 10h10a4 4 0 0 0-3.2-3.9A3.5 3.5 0 0 0 10.2 6 4 4 0 0 0 7 10Z" /><path d="M7 10v9h10v-9" /><path d="M9.5 13.5h5" /></S>
);
export const IconBasket = (p: P) => (
  <S {...p}><path d="M4 10h16l-1.5 9h-13L4 10Z" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></S>
);
export const IconScale = (p: P) => (
  <S {...p}><path d="M12 3v3M5 8l-2 5h6L7 8H5Z" /><path d="M19 8l-2 5h6L21 8h-2Z" /><path d="M5 13h14" /><path d="M12 13v6M9 19h6" /></S>
);
export const IconLeaf = (p: P) => (
  <S {...p}><path d="M5 19C5 9 11 4 20 4c0 9-5 15-15 15Z" /><path d="M5 19c3-4 6-7 10-9" /></S>
);
export const IconArrow = (p: P) => (
  <S {...p}><path d="M5 12h14M13 6l6 6-6 6" /></S>
);
export const IconCheck = (p: P) => (
  <S {...p}><path d="M4.5 12.5l5 5L19.5 6.5" /></S>
);
export const IconAlert = (p: P) => (
  <S {...p}><path d="M12 3.5 21 20H3L12 3.5Z" /><path d="M12 10v4.5M12 17.5v.5" /></S>
);
export const IconStar = ({ size = 20, className, style, filled = false }: P & { filled?: boolean }) => (
  <svg width={size} height={size} viewBox="0 0 24 24"
    fill={filled ? "currentColor" : "none"}
    stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"
    className={className} style={style} aria-hidden="true">
    <path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 17l-5.2 2.6 1-5.8-4.3-4.1 5.9-.9L12 3.5Z" />
  </svg>
);
