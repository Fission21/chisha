// 全局错误兜底：避免白屏/裸错误，给出可操作的中文提示
"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="zh-CN">
      <body>
        <div className="container" style={{ textAlign: "center", paddingTop: 80 }}>
          <span className="brand-mark" style={{ margin: "0 auto 18px" }}>吃</span>
          <h1 style={{ fontFamily: "var(--serif)", fontSize: 26, margin: "0 0 8px" }}>出错了</h1>
          <p className="muted">页面出了点问题，刷新一下或回首页重试。</p>
          <div className="btn-row" style={{ justifyContent: "center" }}>
            <button className="btn" onClick={reset}>重试</button>
            <a className="btn ghost" href="/">回首页</a>
          </div>
        </div>
      </body>
    </html>
  );
}
