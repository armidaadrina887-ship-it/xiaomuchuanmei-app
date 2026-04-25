"""
晓牧传媒 · 文案生成系统
"""
import streamlit as st
import os
import logging
import extra_streamlit_components as stx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
from core import (
    parse_form, build_client, generate_scripts,
    make_word_bytes, INDUSTRY_NAMES
)
from db import update_order, now_beijing
from version import VERSION
from styles import DARK_CSS, LOGIN_EXTRA_CSS, ACCENT, accent_badge, section_title, SIDEBAR_BRAND_HTML, render_topnav, get_theme_css, render_sidebar_brand

_COOKIE_NAME = "xm_auth_v1"

# ── 页面配置 ──────────────────────────────────────
st.set_page_config(
    page_title="晓牧传媒 · 文案生成",
    page_icon="🎬",
    layout="centered",
)

# ── Cookie 管理器（浏览器持久化登录状态）─────────────
_cookies = stx.CookieManager(key="xm_cookie_main")

# ── 退出处理（最优先，避免双重 rerun）────────────────
if st.session_state.get("_logout_pending"):
    st.session_state.clear()
    _cookies.delete(_COOKIE_NAME)
    st.rerun()

# 最早注入：隐藏导航 + 隐藏内容直到鉴权完成
_theme = st.session_state.get("theme", "dark")
st.markdown(DARK_CSS + get_theme_css(_theme) + """
<style>
[data-testid="stAppViewContainer"] > .main { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

def _check_login(username, password):
    try:
        return st.secrets["users"].get(username) == password
    except Exception:
        return False

def _user_exists(username):
    try:
        return username in st.secrets["users"]
    except Exception:
        return False

def _do_login(username: str):
    st.session_state["logged_in"] = True
    st.session_state["username"]  = username
    _cookies.set(_COOKIE_NAME, username)

def _do_logout():
    st.session_state["_logout_pending"] = True
    st.rerun()

# ── Cookie 自动登录（刷新页面保持登录）────────────────
if not st.session_state.get("logged_in"):
    saved = _cookies.get(_COOKIE_NAME)
    if saved and _user_exists(saved):
        st.session_state["logged_in"] = True
        st.session_state["username"]  = saved

# ── 登录页 ────────────────────────────────────────────
def login_page():
    st.markdown(LOGIN_EXTRA_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;margin-top:80px'>"
        f"<div style='font-size:13px;color:#FF7533;font-family:monospace;"
        f"letter-spacing:3px;margin-bottom:12px;text-align:center'>// XIAOMUCHUANMEI</div>"
        f"<h2 style='color:#F0F0F0;margin-bottom:4px;text-align:center'>晓牧传媒</h2>"
        f"<p style='color:#888;font-size:14px;margin-bottom:40px;text-align:center'>文案生成系统 · 内部专用</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        username = st.text_input("用户名", placeholder="请输入用户名")
        password = st.text_input("密码", type="password", placeholder="请输入密码")
        submitted = st.form_submit_button("登 录", use_container_width=True, type="primary")
        if submitted:
            if _check_login(username, password):
                _do_login(username)
            else:
                st.error("用户名或密码错误")

if not st.session_state.get("logged_in"):
    login_page()
    st.stop()

# ── 已登录：显示内容 ─────────────────────────────────
st.markdown("""
<style>[data-testid="stAppViewContainer"] > .main { visibility: visible; }</style>
""", unsafe_allow_html=True)

with st.sidebar:
    render_sidebar_brand(
        username=st.session_state.get("username", ""),
        theme=_theme,
    )

# ── 顶部标题 ──────────────────────────────────────
col_title, col_ver = st.columns([5, 1])
col_title.markdown(
    "<h2 style='color:#F0F0F0;margin-bottom:0'>"
    "<span style='color:rgba(255,117,51,0.5);font-family:monospace;font-size:20px'>// </span>"
    "晓牧传媒 · 文案生成系统</h2>",
    unsafe_allow_html=True,
)
col_ver.markdown(
    f"<br>{accent_badge('v' + VERSION)}",
    unsafe_allow_html=True,
)

st.caption("粘贴客户信息表 → 自动识别行业 → 10批×3条生成 → 行业违禁词扫描 → 下载Word")

render_topnav("generate", on_logout=_do_logout)

# ── API Key ───────────────────────────────────────
api_key = None
try:
    api_key = st.secrets["KIMI_API_KEY"]
except Exception:
    api_key = os.environ.get("KIMI_API_KEY", "")

if not api_key:
    st.error("未配置 API Key，请联系管理员")
    st.stop()

# ── 主界面 ────────────────────────────────────────
st.divider()

if "prefill_order" in st.session_state:
    st.session_state["_raw_input"] = st.session_state.pop("prefill_order")
    st.session_state["_from_order"] = True

if st.session_state.get("_from_order"):
    st.success("✅ 已从订单管理载入客户信息，确认后点击生成")

raw = st.text_area(
    "粘贴客户信息表",
    key="_raw_input",
    height=320,
    placeholder="""出镜称呼：小明
店铺信息名称：XX餐厅
城市名字：杭州
主营业务：牛排、意面
主推产品：澳洲M9和牛
产品特点：现切现烤，30秒出餐
...""",
)

generate_btn = st.button("开始生成 →", type="primary", use_container_width=True)

# ── 生成流程 ──────────────────────────────────────
if generate_btn:
    if not raw.strip():
        st.warning("请先粘贴客户信息表")
        st.stop()

    fields = parse_form(raw)
    try:
        client, prompt_file = build_client(fields)
    except Exception as e:
        st.error(f"信息解析失败：{e}")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("主理人", client['name'] or "未识别")
    col2.metric("品牌/店铺", client['company'][:10] if client['company'] else "未识别")
    col3.metric("识别行业", INDUSTRY_NAMES.get(prompt_file, '通用'))
    ikeys = client.get('industry_keys', [])
    if ikeys:
        st.info(f"🔍 检测到行业违禁词分类：{' / '.join(ikeys)}，已自动加载专项词库")

    if not client['name'] and not client['company']:
        st.error("未能识别出客户姓名或店铺，请检查信息表格式（需含\"出镜称呼：XXX\"等字段）")
        st.stop()

    progress_bar = st.progress(0.0)
    status_text  = st.empty()

    def on_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.info(f"⏳ {msg}")

    try:
        scripts = generate_scripts(client, api_key, progress_callback=on_progress)
    except Exception as e:
        st.error(f"生成失败：{e}")
        st.stop()

    if not scripts:
        st.error("API返回内容解析失败，请重试")
        st.stop()

    progress_bar.progress(1.0)
    status_text.success(f"生成完成！共 {len(scripts)} 条脚本")
    st.session_state.pop("_from_order", None)

    # ── 质量评分展示 ─────────────────────────────────
    score = client.get('score', {})
    if score:
        total = score.get('total', 0)
        if total >= 90:
            st.success(f"质量评分 **{total} 分** — 达标（≥90分）")
        elif total >= 80:
            st.warning(f"质量评分 **{total} 分** — 良好，可考虑重新生成")
        else:
            st.error(f"质量评分 **{total} 分** — 偏低，建议重新生成")
        bd = score.get('breakdown', {})
        cols = st.columns(5)
        for col, (k, v) in zip(cols, [
            ('钩子力',     bd.get('钩子力',     0)),
            ('自然感',     bd.get('内容自然感', 0)),
            ('多样性',     bd.get('内容多样性', 0)),
            ('可执行性',   bd.get('拍摄可执行性', 0)),
            ('结尾节奏',   bd.get('结尾节奏',   0)),
        ]):
            col.metric(k, f"{v}分")
        issues = score.get('issues', [])
        if issues:
            st.caption("失分项：" + "；".join(issues))

    failed_batches = client.get('failed_batches', [])
    if failed_batches:
        st.warning(f"以下批次解析失败，实际生成 {len(scripts)} 条（非30条）：第{'、'.join(failed_batches)}条批次，建议重新生成")

    violations = client.get('violations', [])
    if violations:
        vlist = "、".join(f"第{v['script']}条[{v['word']}]" for v in violations[:8])
        st.warning(f"违禁词（已重写后仍存在）：{vlist}，建议人工复查")

    opening_remaining = client.get('opening_violations_remaining', [])
    if opening_remaining:
        st.warning(f"以下条目开场仍有套话，请人工替换：第{'、'.join(str(n) for n in opening_remaining)}条")

    scene_violations = client.get('scene_violations', [])
    if scene_violations:
        sv_list = "、".join(f"第{v['script']}条镜头{v['shot']}[{v['keyword']}]" for v in scene_violations[:6])
        st.warning(f"场景描述出现禁止人物词：{sv_list}，需人工修改场景描述")

    zui_replacements = client.get('zui_replacements', [])
    if zui_replacements:
        zui_count = len([r for r in zui_replacements if r.get('type') == 'zui'])
        if zui_count:
            st.info(f"程序已自动替换「最」字 {zui_count} 处（涉及{len(set(r['script'] for r in zui_replacements if r.get('type') == 'zui'))}条脚本）")

    dedup_flags = [r for r in zui_replacements if r.get('field') == 'dedup_flag']
    if dedup_flags:
        dup_list = "、".join(f"第{r['script']}条（{r['type']}）" for r in dedup_flags[:6])
        st.warning(f"检测到疑似重复脚本：{dup_list}，建议人工检查替换")

    try:
        word_bytes = make_word_bytes(client, scripts)
    except Exception as e:
        st.error(f"Word生成失败：{e}")
        st.stop()

    filename = f"{client['name']}_{client['company'][:8]}_30条文案.docx"

    downloaded = st.download_button(
        label=f"下载 Word 文档（{len(scripts)}条）",
        data=word_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary",
    )
    if downloaded:
        order_id = st.session_state.pop("prefill_order_id", None)
        if order_id:
            update_order(order_id, {
                "status":       "已生成",
                "processed_by": st.session_state.get("username", ""),
                "processed_at": now_beijing(),
            })

    with st.expander("预览前3条脚本"):
        for s in scripts[:3]:
            st.markdown(f"**第{s.get('number')}条 · {s.get('title')}**")
            st.caption(f"{s.get('type')} · {s.get('duration')} · {len(s.get('shots',[]))}个镜头")
            for i, shot in enumerate(s.get('shots', [])[:3]):
                st.markdown(f"- 镜头{i+1}：{shot.get('scene','')}  \n  > {shot.get('dialogue','')[:60]}...")
            st.divider()
