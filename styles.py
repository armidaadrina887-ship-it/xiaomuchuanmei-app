"""
晓牧传媒 · 全局 UI 主题（暗黑 + 橙色）
"""

ACCENT      = "#FF7533"
ACCENT_GLOW = "rgba(255,117,51,0.35)"
ACCENT_DIM  = "rgba(255,117,51,0.12)"
BG          = "#0D0D0D"
BG_CARD     = "#161616"
BG_INPUT    = "#1C1C1C"

DARK_CSS = """
<style>
/* ─── 全局变量 ─────────────────────────────────────── */
:root {
  --accent:           #FF7533;
  --accent-glow:      rgba(255,117,51,0.35);
  --accent-dim:       rgba(255,117,51,0.12);
  --bg:               #0D0D0D;
  --bg-card:          #161616;
  --bg-input:         #1C1C1C;
  --border:           rgba(255,117,51,0.20);
  --border-hi:        rgba(255,117,51,0.50);
  --txt:              #E8E8E8;
  --txt-muted:        #888;
  --login-right-bg:   #0E0E0E;
  --login-divider:    rgba(255,117,51,0.38);
}

/* ─── 主背景 ────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
[data-testid="block-container"] {
  background-color: var(--bg) !important;
}

/* ─── 顶部装饰条彻底隐藏 ────────────────────────────── */
[data-testid="stDecoration"],
[data-testid="stToolbar"],
.stDeployButton { display: none !important; }

header[data-testid="stHeader"] {
  background-color: var(--bg) !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ─── 侧边栏 ────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #080808 !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p {
  color: var(--txt) !important;
}
[data-testid="stSidebar"] hr {
  border-color: var(--border) !important;
  opacity: 1 !important;
}

/* ─── 输入框 hint 隐藏（密码框"Press Enter"乱入）──────── */
[data-testid="InputInstructions"] { display: none !important; }

/* ─── 文字 ──────────────────────────────────────────── */
p, span, div, label, caption, li,
h1, h2, h3, h4, h5, h6 {
  color: var(--txt);
}
.stCaption, [data-testid="stCaptionContainer"] * {
  color: var(--txt-muted) !important;
}

/* ─── 输入框 ─────────────────────────────────────────── */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  background-color: var(--bg-input) !important;
  color: var(--txt) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  caret-color: var(--accent);
}
.stTextInput input:focus,
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-glow) !important;
  outline: none !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
  color: var(--txt-muted) !important;
}

/* ─── Selectbox ─────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] > div:first-child {
  background-color: var(--bg-input) !important;
  border-color: var(--border) !important;
  color: var(--txt) !important;
  border-radius: 6px !important;
}
[data-baseweb="popover"] ul {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
}
[role="option"] {
  background-color: var(--bg-card) !important;
  color: var(--txt) !important;
}
[role="option"]:hover,
[aria-selected="true"][role="option"] {
  background-color: var(--accent-dim) !important;
}

/* ─── 按钮 ──────────────────────────────────────────── */
.stButton > button {
  background-color: transparent !important;
  color: var(--txt) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  transition: border-color .15s, box-shadow .15s, color .15s;
}
.stButton > button:hover {
  border-color: var(--border-hi) !important;
  box-shadow: 0 0 8px var(--accent-glow) !important;
  color: #fff !important;
}
button[kind="primary"],
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stFormSubmitButton > button {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 0 12px var(--accent-glow) !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background-color: #E65F1A !important;
  box-shadow: 0 0 20px var(--accent-glow) !important;
}
.stDownloadButton > button {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 0 12px var(--accent-glow) !important;
  border-radius: 6px !important;
}
.stDownloadButton > button:hover {
  background-color: #E65F1A !important;
  box-shadow: 0 0 20px var(--accent-glow) !important;
}

/* ─── 进度条 ─────────────────────────────────────────── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), #FFAA33) !important;
  border-radius: 4px !important;
}
.stProgress > div > div {
  background-color: #1E1E1E !important;
  border-radius: 4px !important;
}

/* ─── Metric ─────────────────────────────────────────── */
[data-testid="metric-container"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-left: 3px solid var(--accent) !important;
  border-radius: 6px !important;
  padding: 12px 16px !important;
}
[data-testid="stMetricValue"] { color: var(--txt) !important; }
[data-testid="stMetricLabel"] { color: var(--txt-muted) !important; }

/* ─── Expander ───────────────────────────────────────── */
[data-testid="stExpander"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
[data-testid="stExpander"] summary {
  color: var(--txt) !important;
  background-color: var(--bg-card) !important;
}
[data-testid="stExpander"] summary:hover { color: var(--accent) !important; }
[data-testid="stExpander"] > div:last-child {
  background-color: var(--bg-card) !important;
}

/* ─── Tabs ──────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background-color: transparent !important;
  border-bottom: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--txt-muted) !important;
  background-color: transparent !important;
  border: none !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
  background-color: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { background-color: transparent !important; }

/* ─── 通知横幅 ───────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: 6px !important;
  border-left-width: 3px !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="positive"] {
  background-color: rgba(0,200,100,0.08) !important;
  border-left-color: #00C864 !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
  background-color: rgba(255,180,0,0.08) !important;
  border-left-color: #FFB400 !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
  background-color: var(--accent-dim) !important;
  border-left-color: var(--accent) !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
  background-color: rgba(80,120,255,0.08) !important;
  border-left-color: #7090FF !important;
}

/* ─── 表单容器 ───────────────────────────────────────── */
[data-testid="stForm"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 16px 20px !important;
}

/* ─── Checkbox / Radio ───────────────────────────────── */
[data-testid="stCheckbox"] label,
.stRadio label { color: var(--txt) !important; }

/* ─── Divider ────────────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 1 !important; }

/* ─── Scrollbar ──────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; background: var(--bg); }
::-webkit-scrollbar-thumb {
  background: rgba(255,117,51,0.22);
  border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ─── Links ──────────────────────────────────────────── */
a { color: var(--accent) !important; }
a:hover { color: #FFB07A !important; text-decoration: none !important; }

/* ─── 表格 ───────────────────────────────────────────── */
.stDataFrame, [data-testid="stTable"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
</style>
"""

# 登录页 / 填表页补丁：完全隐藏侧边栏和折叠按钮
HIDE_SIDEBAR_CSS = """
<style>
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
#MainMenu { display: none !important; }
</style>
"""

# 登录页额外：让内容可见
LOGIN_EXTRA_CSS = HIDE_SIDEBAR_CSS + """
<style>
[data-testid="stAppViewContainer"] > .main { visibility: visible !important; }
</style>
"""

# 登录页分屏布局 CSS（响应式：桌面分屏全屏 / 手机单列）
LOGIN_SPLIT_CSS = HIDE_SIDEBAR_CSS + """
<style>
[data-testid="stAppViewContainer"] > .main { visibility: visible !important; }
header[data-testid="stHeader"] { display: none !important; }

/* ── 全宽：清除所有容器 padding / max-width ── */
section.main, [data-testid="stMain"] {
    padding: 0 !important;
    overflow-x: hidden !important;
}
.block-container, [data-testid="block-container"] {
    max-width: 100% !important;
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* ── 仅顶层列容器撑满全屏高度（:not 排除嵌套列）── */
[data-testid="stHorizontalBlock"]:not([data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"]) {
    gap: 0 !important;
    align-items: stretch !important;
    min-height: 100vh !important;
    overflow: hidden !important;
    flex-wrap: nowrap !important;
}

/* ── 嵌套列容器重置，避免撑高 ── */
[data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"] {
    min-height: unset !important;
    overflow: visible !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
}

/* ── 所有列：去 padding，flex 撑满 ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"],
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div > div,
[data-testid="stHorizontalBlock"] > [data-testid="column"] > div > div > div {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 !important;
    min-height: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
}

/* ── 左列：始终保持深色品牌风格 ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
    background-color: #080808 !important;
    background-image:
        linear-gradient(rgba(255,117,51,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,117,51,0.05) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    overflow: hidden !important;
}

/* ── 右列：跟随主题（CSS 变量由 DARK/LIGHT CSS 控制）── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    background-color: var(--login-right-bg) !important;
    border-left: 1px solid var(--login-divider) !important;
}

/* ── 欢迎文字区域 padding-top 实现视觉居中 ── */
.xm-right-wrap {
    padding: max(32px, calc(50vh - 220px)) 52px 0 !important;
}

/* ── 主题图标按钮：固定右上角 ── */
/* The theme button is rendered BEFORE st.columns(), so it is NOT inside
   stHorizontalBlock. The :not() selector uniquely targets it without
   affecting any button inside the column layout. */
[data-testid="stButton"]:not([data-testid="stHorizontalBlock"] [data-testid="stButton"]) {
    position: fixed !important;
    top: 14px !important;
    right: 16px !important;
    z-index: 9999 !important;
    width: auto !important;
}
[data-testid="stButton"]:not([data-testid="stHorizontalBlock"] [data-testid="stButton"]) > button {
    width: 38px !important;
    height: 38px !important;
    border-radius: 50% !important;
    padding: 0 !important;
    min-width: unset !important;
    font-size: 18px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,117,51,0.28) !important;
    transition: all 0.2s !important;
    line-height: 1 !important;
    color: inherit !important;
}
[data-testid="stButton"]:not([data-testid="stHorizontalBlock"] [data-testid="stButton"]) > button:hover {
    background: rgba(255,117,51,0.14) !important;
    border-color: rgba(255,117,51,0.55) !important;
    box-shadow: 0 0 10px rgba(255,117,51,0.20) !important;
}

/* ── Form 去除卡片外框 + 水平 padding ── */
[data-testid="stHorizontalBlock"] [data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 52px !important;
}

/* ── 桌面（≥769px）── */
@media (min-width: 769px) {
    .xm-mobile-brand { display: none !important; }
}

/* ── 手机（≤768px）：隐藏左列，右列全宽 ── */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {
        display: none !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
        flex: 1 1 100% !important;
        min-width: 100% !important;
        border-left: none !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stForm"] {
        padding: 0 24px !important;
    }
    .xm-right-wrap { padding: 40px 24px 0 !important; }
    .xm-mobile-brand { display: block !important; }
}
</style>
"""

# 登录左侧品牌面板 HTML
LOGIN_LEFT_PANEL_HTML = """
<div style="
    height:100%;
    min-height:100vh;
    padding:52px 60px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    position:relative;
    overflow:hidden;
    box-sizing:border-box;
">
  <div style="position:absolute;top:-80px;right:-60px;width:300px;height:300px;
      background:radial-gradient(circle,rgba(255,117,51,0.10),transparent 65%);
      pointer-events:none;z-index:0"></div>
  <div style="position:absolute;bottom:100px;left:-50px;width:220px;height:220px;
      background:radial-gradient(circle,rgba(255,117,51,0.06),transparent 65%);
      pointer-events:none;z-index:0"></div>

  <!-- 品牌 -->
  <div style="position:relative;z-index:1">
    <div style="font-family:monospace;font-size:10px;color:rgba(255,117,51,0.45);
                letter-spacing:4px;margin-bottom:5px">// XIAOMUCHUANMEI</div>
    <div style="font-size:20px;font-weight:800;color:#FF7533;letter-spacing:1px">晓牧传媒</div>
    <div style="font-size:11px;color:#242424;font-family:monospace;margin-top:3px">
      内容创作系统 · 内部专用</div>
  </div>

  <!-- 主文案 -->
  <div style="position:relative;z-index:1;flex:1;display:flex;flex-direction:column;
              justify-content:center;padding:44px 0 28px">
    <div style="font-family:monospace;font-size:56px;font-weight:900;
                color:rgba(255,117,51,0.08);line-height:0.9;margin-bottom:22px;
                letter-spacing:-2px;user-select:none">//</div>
    <div style="font-size:46px;font-weight:900;color:#F0F0F0;
                line-height:1.2;margin-bottom:16px;letter-spacing:-0.5px">
      专注短视频<br><span style="color:#FF7533">文案内容</span>创作
    </div>
    <div style="font-size:12px;color:#666;line-height:2.0;
                font-family:monospace;letter-spacing:0.3px">
      AI 驱动生成 &nbsp;·&nbsp; 行业违禁词精准扫描<br>
      10批次 × 3条 &nbsp;·&nbsp; 30个脚本一键导出 Word
    </div>
    <div style="width:36px;height:2px;background:#FF7533;
                margin:26px 0 20px;opacity:0.55"></div>
    <div style="display:flex;gap:32px;align-items:center">
      <div>
        <div style="font-size:24px;font-weight:700;color:#FF7533;
                    font-family:monospace;line-height:1">30+</div>
        <div style="font-size:10px;color:#666;margin-top:3px;letter-spacing:0.3px">脚本/次生成</div>
      </div>
      <div style="width:1px;height:32px;background:rgba(255,117,51,0.15)"></div>
      <div>
        <div style="font-size:24px;font-weight:700;color:#FF7533;
                    font-family:monospace;line-height:1">10+</div>
        <div style="font-size:10px;color:#666;margin-top:3px;letter-spacing:0.3px">行业分类适配</div>
      </div>
      <div style="width:1px;height:32px;background:rgba(255,117,51,0.15)"></div>
      <div>
        <div style="font-size:24px;font-weight:700;color:#FF7533;
                    font-family:monospace;line-height:1">AI</div>
        <div style="font-size:10px;color:#666;margin-top:3px;letter-spacing:0.3px">智能质量评分</div>
      </div>
    </div>
  </div>

  <!-- 标签 -->
  <div style="position:relative;z-index:1;display:flex;gap:8px;flex-wrap:wrap">
    <span style="border:1px solid rgba(255,117,51,0.30);color:#777;font-size:11px;
                 padding:5px 13px;border-radius:2px;font-family:monospace">AI 文案生成</span>
    <span style="border:1px solid rgba(255,117,51,0.30);color:#777;font-size:11px;
                 padding:5px 13px;border-radius:2px;font-family:monospace">违禁词扫描</span>
    <span style="border:1px solid rgba(255,117,51,0.30);color:#777;font-size:11px;
                 padding:5px 13px;border-radius:2px;font-family:monospace">Word 导出</span>
    <span style="border:1px solid rgba(255,117,51,0.30);color:#777;font-size:11px;
                 padding:5px 13px;border-radius:2px;font-family:monospace">订单管理</span>
  </div>
</div>
"""

# 侧边栏品牌头部 HTML
SIDEBAR_BRAND_HTML = (
    "<div style='padding:16px 0 4px;font-family:monospace'>"
    "<span style='color:rgba(255,117,51,0.5);font-size:11px'>// </span>"
    "<span style='color:#FF7533;font-size:14px;font-weight:700;letter-spacing:1px'>XIAOMUCHUANMEI</span>"
    "</div>"
    "<div style='color:#555;font-size:11px;padding-bottom:8px;font-family:monospace'>"
    "内容创作系统</div>"
)


LIGHT_CSS = """
<style>
:root {
  --bg:               #F7F5F0;
  --bg-card:          #FFFFFF;
  --bg-input:         #EEECE7;
  --txt:              #1A1A1A;
  --txt-muted:        #888;
  --border:           rgba(180,110,50,0.22);
  --border-hi:        rgba(180,110,50,0.50);
  --login-right-bg:   #F5F3EE;
  --login-divider:    rgba(180,110,50,0.28);
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
[data-testid="block-container"] {
  background-color: #F7F5F0 !important;
}
header[data-testid="stHeader"] {
  background-color: #F7F5F0 !important;
  border-bottom: 1px solid rgba(180,110,50,0.18) !important;
}
[data-testid="stSidebar"] {
  background-color: #ECEAE4 !important;
  border-right: 1px solid rgba(180,110,50,0.18) !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p {
  color: #1A1A1A !important;
}
p, span, div, label, caption, li,
h1, h2, h3, h4, h5, h6 { color: #1A1A1A; }
.stCaption, [data-testid="stCaptionContainer"] * { color: #888 !important; }
.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  background-color: #EEECE7 !important;
  color: #1A1A1A !important;
  border: 1px solid rgba(180,110,50,0.22) !important;
}
.stSelectbox [data-baseweb="select"] > div:first-child {
  background-color: #EEECE7 !important;
  color: #1A1A1A !important;
}
[data-baseweb="popover"] ul {
  background-color: #FFFFFF !important;
  border: 1px solid rgba(180,110,50,0.22) !important;
}
[role="option"] {
  background-color: #FFFFFF !important;
  color: #1A1A1A !important;
}
[data-testid="metric-container"] {
  background-color: #FFFFFF !important;
  border: 1px solid rgba(180,110,50,0.22) !important;
  border-left: 3px solid #FF7533 !important;
}
[data-testid="stMetricValue"] { color: #1A1A1A !important; }
[data-testid="stMetricLabel"] { color: #888 !important; }
[data-testid="stExpander"] {
  background-color: #FFFFFF !important;
  border: 1px solid rgba(180,110,50,0.22) !important;
}
[data-testid="stExpander"] summary {
  color: #1A1A1A !important;
  background-color: #FFFFFF !important;
}
[data-testid="stExpander"] > div:last-child {
  background-color: #FFFFFF !important;
}
[data-testid="stForm"] {
  background-color: #FFFFFF !important;
  border: 1px solid rgba(180,110,50,0.22) !important;
}
[data-testid="stCheckbox"] label,
.stRadio label { color: #1A1A1A !important; }
.stButton > button {
  color: #1A1A1A !important;
  border: 1px solid rgba(180,110,50,0.28) !important;
}
.stButton > button:hover { color: #1A1A1A !important; }
.stTabs [data-baseweb="tab"] { color: #888 !important; }
.stTabs [data-baseweb="tab-list"] {
  border-bottom: 1px solid rgba(180,110,50,0.22) !important;
}
hr { border-color: rgba(180,110,50,0.18) !important; }
.stProgress > div > div { background-color: #DDD9D0 !important; }
[data-testid="stAlert"][data-baseweb="notification"][kind="positive"] {
  background-color: rgba(0,180,90,0.07) !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
  background-color: rgba(200,140,0,0.07) !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
  background-color: rgba(220,60,40,0.07) !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
  background-color: rgba(60,100,220,0.06) !important;
}
::-webkit-scrollbar { background: #F7F5F0; }
::-webkit-scrollbar-thumb { background: rgba(180,110,50,0.20); }
</style>
"""


def get_theme_css(theme: str = "dark") -> str:
    return LIGHT_CSS if theme == "light" else ""


def render_sidebar_brand(username: str = "", theme: str = "dark"):
    import streamlit as st
    st.markdown(SIDEBAR_BRAND_HTML, unsafe_allow_html=True)
    st.markdown(
        f"<div style='font-size:11px;color:#444;font-family:monospace;"
        f"padding:4px 0'>{username}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='margin:8px 0'>", unsafe_allow_html=True)
    label = "日 白天模式" if theme == "dark" else "夜 夜间模式"
    if st.button(label, key="theme_toggle_btn", use_container_width=True):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()


def render_topnav(active: str = "generate", on_logout=None):
    """Top nav bar.  active: 'generate' | 'orders'
    on_logout: callable — called when user clicks 退出.
    """
    import streamlit as st
    c1, c2, _, c3 = st.columns([1, 1, 5, 1])
    if c1.button(
        "生成",
        key="topnav_gen",
        use_container_width=True,
        type="primary" if active == "generate" else "secondary",
    ):
        st.switch_page("streamlit_app.py")
    if c2.button(
        "订单",
        key="topnav_ord",
        use_container_width=True,
        type="primary" if active == "orders" else "secondary",
    ):
        st.switch_page("pages/2_orders.py")
    if c3.button("退出", key="topnav_logout", use_container_width=True):
        if on_logout:
            on_logout()


def accent_badge(text: str) -> str:
    return (
        f"<span style='background:#FF7533;color:#fff;"
        f"padding:2px 10px;border-radius:12px;font-size:13px'>{text}</span>"
    )


def section_title(text: str, prefix: bool = True) -> str:
    pre = "<span style='color:rgba(255,117,51,0.5);font-family:monospace'>// </span>" if prefix else ""
    return (
        f"<h3 style='color:#FF7533;font-family:monospace;"
        f"margin:20px 0 8px;letter-spacing:1px'>{pre}{text}</h3>"
    )
