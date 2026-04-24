"""
晓牧传媒 · 全局 UI 主题（暗黑 + 品红）
"""

ACCENT      = "#FF2D78"
ACCENT_GLOW = "rgba(255,45,120,0.35)"
ACCENT_DIM  = "rgba(255,45,120,0.12)"
BG          = "#0D0D0D"
BG_CARD     = "#161616"
BG_INPUT    = "#1C1C1C"

DARK_CSS = """
<style>
/* ─── 全局变量 ─────────────────────────────────────── */
:root {
  --accent:      #FF2D78;
  --accent-glow: rgba(255,45,120,0.35);
  --accent-dim:  rgba(255,45,120,0.12);
  --bg:          #0D0D0D;
  --bg-card:     #161616;
  --bg-input:    #1C1C1C;
  --border:      rgba(255,45,120,0.20);
  --border-hi:   rgba(255,45,120,0.55);
  --txt:         #E8E8E8;
  --txt-muted:   #666;
}

/* ─── 主背景 ────────────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
[data-testid="block-container"] {
  background-color: var(--bg) !important;
}

/* ─── 侧边栏 ────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #070707 !important;
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
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

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
/* placeholder */
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
  transition: border-color .15s, box-shadow .15s;
}
.stButton > button:hover {
  border-color: var(--border-hi) !important;
  box-shadow: 0 0 10px var(--accent-glow) !important;
  color: #fff !important;
}
/* Primary 按钮 */
button[kind="primary"],
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"],
.stFormSubmitButton > button {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 0 14px var(--accent-glow) !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
  background-color: #e0235e !important;
  box-shadow: 0 0 22px var(--accent-glow) !important;
}
/* 下载按钮 */
.stDownloadButton > button {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 0 14px var(--accent-glow) !important;
  border-radius: 6px !important;
}
.stDownloadButton > button:hover {
  background-color: #e0235e !important;
  box-shadow: 0 0 22px var(--accent-glow) !important;
}

/* ─── 进度条 ─────────────────────────────────────────── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), #cc00ff) !important;
  border-radius: 4px !important;
}
.stProgress > div > div {
  background-color: #222 !important;
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
[data-testid="stExpander"] summary:hover {
  color: var(--accent) !important;
}
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
.stTabs [data-baseweb="tab-panel"] {
  background-color: transparent !important;
}

/* ─── 通知横幅 ───────────────────────────────────────── */
[data-testid="stAlert"] {
  border-radius: 6px !important;
  border-left-width: 3px !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="positive"] {
  background-color: rgba(0,200,100,0.08) !important;
  border-color: rgba(0,200,100,0.35) !important;
  border-left-color: #00C864 !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
  background-color: rgba(255,180,0,0.08) !important;
  border-color: rgba(255,180,0,0.35) !important;
  border-left-color: #FFB400 !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
  background-color: var(--accent-dim) !important;
  border-color: var(--border-hi) !important;
  border-left-color: var(--accent) !important;
}
[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
  background-color: rgba(80,80,255,0.08) !important;
  border-color: rgba(80,80,255,0.35) !important;
  border-left-color: #6464FF !important;
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
[data-testid="stCheckbox"] span[aria-checked="true"],
[data-testid="stCheckbox"] input:checked + span {
  background-color: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* ─── Divider ────────────────────────────────────────── */
hr { border-color: var(--border) !important; opacity: 1 !important; }

/* ─── Scrollbar ──────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; background: var(--bg); }
::-webkit-scrollbar-thumb {
  background: rgba(255,45,120,0.25);
  border-radius: 2px;
}
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ─── Links ──────────────────────────────────────────── */
a { color: var(--accent) !important; }
a:hover { color: #ff6096 !important; text-decoration: none !important; }

/* ─── 顶部 header 区域 ───────────────────────────────── */
header[data-testid="stHeader"] {
  background-color: var(--bg) !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ─── 表格（Word 预览等）────────────────────────────── */
.stDataFrame, [data-testid="stTable"] {
  background-color: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
</style>
"""

# 登录页额外补丁：隐藏侧边栏 + 居中卡片
LOGIN_EXTRA_CSS = """
<style>
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stAppViewContainer"] > .main { visibility: visible !important; }
</style>
"""


def accent_badge(text: str) -> str:
    """生成品红色徽章 HTML"""
    return (
        f"<span style='background:var(--accent);color:#fff;"
        f"padding:2px 10px;border-radius:12px;font-size:13px'>{text}</span>"
    )


def section_title(text: str, prefix: bool = True) -> str:
    """生成带 // 前缀的 section 标题 HTML"""
    pre = "<span style='color:rgba(255,45,120,0.5);font-family:monospace'>// </span>" if prefix else ""
    return (
        f"<h3 style='color:#FF2D78;font-family:monospace;"
        f"margin:20px 0 8px;letter-spacing:1px'>{pre}{text}</h3>"
    )
