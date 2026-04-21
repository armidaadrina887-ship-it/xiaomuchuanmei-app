"""
晓牧传媒 · 订单管理页（需登录）
生成在后台线程运行，页面保持可交互，每 1.5s 自动刷新进度
"""
import os
import threading
import time
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import parse_form, build_client, generate_scripts, make_word_bytes, INDUSTRY_NAMES
from db import load_orders, update_order, delete_order, now_beijing
from version import VERSION

st.set_page_config(
    page_title="晓牧传媒 · 订单管理",
    page_icon="📋",
    layout="wide",
)

# 最早注入：隐藏原生英文导航 + 隐藏内容直到鉴权完成
st.markdown("""
<style>
[data-testid="stSidebarNav"]               { display: none !important; }
[data-testid="stAppViewContainer"] > .main { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("logged_in"):
    st.switch_page("streamlit_app.py")
    st.stop()

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { visibility: visible; }
[data-testid="stSidebarNav"] { display: none !important; }
button[kind="primary"] { background-color:#E65000 !important; border-color:#E65000 !important; }
button[kind="primary"]:hover { background-color:#CC4800 !important; border-color:#CC4800 !important; }
a { color: #E65000 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        "<div style='padding:12px 0 8px;font-size:15px;font-weight:600;color:#E65000'>🎬 晓牧传媒后台</div>",
        unsafe_allow_html=True,
    )
    st.page_link("streamlit_app.py",  label="✍️  生成文案")
    st.page_link("pages/2_orders.py", label="📋  订单管理")
    st.divider()
    st.markdown(
        f"<span style='font-size:12px;color:#999'>👤 {st.session_state.get('username','')}</span>",
        unsafe_allow_html=True,
    )
    if st.button("退出登录", use_container_width=True):
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

try:
    api_key = st.secrets["KIMI_API_KEY"]
except Exception:
    api_key = os.environ.get("KIMI_API_KEY", "")

if not api_key:
    st.error("未配置 API Key，请联系管理员")
    st.stop()

# ── 后台生成状态（模块级，跨 rerun 保持）────────────────
# key: (session_state_id, order_id) → {status, progress, msg, ...}
_GEN: dict = {}
_GEN_LOCK = threading.Lock()

def _skey(oid: str) -> tuple:
    return (id(st.session_state), oid)

def _get_gen(oid: str) -> dict:
    with _GEN_LOCK:
        return dict(_GEN.get(_skey(oid), {}))

def _order_to_raw(o: dict) -> str:
    return f"""出镜称呼：{o.get('name', '')}
性别：{o.get('gender', '')}
店铺信息名称：{o.get('shop', '')}
城市名字：{o.get('city', '')}
从业年限：{o.get('years', '')}
主营业务：{o.get('main_biz', '')}
主推产品：{o.get('product', '')}
产品特点：{o.get('feature', '')}
核心优势：{o.get('advantage', '')}
目标客群：{o.get('target', '')}
创业经历：{o.get('story', '')}
最难的时期：{o.get('hard_time', '')}
客户案例：{o.get('best_case', '')}
与同行差异：{o.get('differentiation', '')}
能解决的痛点：{o.get('pain', '')}
营业时间：{o.get('hours', '')}
补充信息：{o.get('extra', '')}"""

def _start_gen(order: dict, api_key: str):
    """启动后台线程生成该订单文案"""
    oid  = order["id"]
    skey = _skey(oid)
    with _GEN_LOCK:
        if _GEN.get(skey, {}).get("status") == "running":
            return  # 已在生成中，防止重复启动
        _GEN[skey] = {"status": "running", "progress": 0.0, "msg": "准备中..."}

    def run():
        try:
            raw    = _order_to_raw(order)
            fields = parse_form(raw)
            client, _ = build_client(fields)

            def on_progress(p, m):
                with _GEN_LOCK:
                    if skey in _GEN:
                        _GEN[skey].update({"progress": p, "msg": m})

            scripts    = generate_scripts(client, api_key, progress_callback=on_progress)
            word_bytes = make_word_bytes(client, scripts)

            with _GEN_LOCK:
                _GEN[skey] = {
                    "status":   "done",
                    "bytes":    word_bytes,
                    "filename": f"{client['name']}_{client.get('company','')[:8]}_30条文案.docx",
                    "count":    len(scripts),
                    "client":   client,
                }
        except Exception as e:
            with _GEN_LOCK:
                _GEN[skey] = {"status": "error", "error": str(e)}

    threading.Thread(target=run, daemon=True).start()

# ── 页面标题 ──────────────────────────────────────────
col_t, col_v = st.columns([6, 1])
col_t.title("📋 订单管理")
col_v.markdown(
    f"<br><span style='background:#E65000;color:white;padding:3px 10px;"
    f"border-radius:12px;font-size:13px'>v{VERSION}</span>",
    unsafe_allow_html=True,
)
st.caption(now_beijing())

orders = load_orders()

if not orders:
    st.info("暂无订单，等待客户填表提交")
    st.stop()

# ── 状态筛选 ──────────────────────────────────────────
col_filter, col_count = st.columns([3, 1])
with col_filter:
    status_filter = st.radio("筛选状态", ["全部", "待处理", "已生成"], horizontal=True)
with col_count:
    pending_cnt = sum(1 for o in orders if o.get("status") == "待处理")
    st.metric("待处理", pending_cnt)

filtered = orders if status_filter == "全部" else [o for o in orders if o.get("status") == status_filter]
filtered = sorted(filtered, key=lambda o: o.get("submitted_at", ""), reverse=True)

# ── 批量操作栏（仅待处理订单）────────────────────────
pending_orders = [o for o in orders if o.get("status") == "待处理"]
if pending_orders:
    st.markdown("""
<div style='background:#FFF4EE;border:1.5px solid #E65000;border-radius:10px;
            padding:12px 16px;margin-bottom:8px'>
<b style='color:#E65000'>📦 批量生成</b>
<span style='color:#555;font-size:13px;margin-left:8px'>
勾选待处理订单 → 批量生成（多个订单同时在后台运行，互不影响）
</span>
</div>
""", unsafe_allow_html=True)
    selected_ids = []
    for o in pending_orders:
        gen = _get_gen(o["id"])
        is_running = gen.get("status") == "running"
        label = (
            f"⏳ 生成中 {int(gen.get('progress',0)*100)}%  · "
            if is_running else ""
        ) + f"【{o.get('group_name','—')}】**{o.get('name','—')}** · {o.get('shop','—')} · {o.get('submitted_at','')}"
        if st.checkbox(label, key=f"batch_chk_{o['id']}", disabled=is_running):
            selected_ids.append(o["id"])

    btn_label = f"🚀 批量生成选中订单（{len(selected_ids)}个）" if selected_ids else "请先勾选订单"
    if st.button(btn_label, type="primary", disabled=not selected_ids, use_container_width=True):
        for oid in selected_ids:
            order = next((o for o in pending_orders if o["id"] == oid), None)
            if order:
                _start_gen(order, api_key)
        st.rerun()

st.divider()

# ── 订单列表 ──────────────────────────────────────────
any_running = False

for order in filtered:
    oid   = order["id"]
    gen   = _get_gen(oid)
    gst   = gen.get("status")          # "running" / "done" / "error" / None
    db_status = order.get("status", "待处理")

    # 已完成：把结果搬进 session_state，清理模块级 dict
    if gst == "done":
        st.session_state[f"_result_{oid}"] = gen
        with _GEN_LOCK:
            _GEN.pop(_skey(oid), None)
        update_order(oid, {
            "status":       "已生成",
            "processed_by": st.session_state.get("username", ""),
            "processed_at": now_beijing(),
        })
        gst = None

    is_running  = (gst == "running")
    is_error    = (gst == "error")
    has_result  = f"_result_{oid}" in st.session_state

    if is_running:
        any_running = True

    # 标签
    if is_running:
        pct   = int(gen.get("progress", 0) * 100)
        badge = f"⏳ 生成中 {pct}%"
    elif is_error:
        badge = "❌ 生成出错"
    elif has_result:
        badge = "🟢 待下载"
    elif db_status == "已生成":
        badge = "✅ 已生成"
    else:
        badge = "🟡 待处理"

    group_name   = order.get("group_name", "未知群")
    name         = order.get("name", "未知")
    submitted_at = order.get("submitted_at", "")

    with st.expander(
        f"{badge}  |  【{group_name}】{name} · {submitted_at}",
        expanded=is_running or has_result or is_error,
    ):
        # ── 生成中 ────────────────────────────────────
        if is_running:
            prog = gen.get("progress", 0.0)
            msg  = gen.get("msg", "")
            st.progress(prog)
            st.info(f"⏳ {msg}")
            st.caption("生成期间可继续操作其他订单")

        # ── 出错 ──────────────────────────────────────
        elif is_error:
            st.error(f"生成失败：{gen.get('error', '未知错误')}")
            if st.button("🔄 重试", key=f"retry_{oid}", type="primary"):
                _start_gen(order, api_key)
                st.rerun()

        # ── 待下载 ────────────────────────────────────
        elif has_result:
            result = st.session_state[f"_result_{oid}"]
            st.success(f"✅ 文案已生成完毕，共 {result['count']} 条")
            dl = st.download_button(
                label=f"⬇️ 下载 Word 文档（{result['count']}条）",
                data=result["bytes"],
                file_name=result["filename"],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                type="primary",
                key=f"dl_{oid}",
            )
            if dl:
                st.session_state.pop(f"_result_{oid}", None)
                st.rerun()
            if st.button("🔄 重新生成", key=f"regen_{oid}"):
                st.session_state.pop(f"_result_{oid}", None)
                _start_gen(order, api_key)
                st.rerun()

        # ── 普通：展示信息 + 操作按钮 ─────────────────
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**微信群：** {group_name}")
                st.markdown(f"**出镜称呼：** {name}")
                st.markdown(f"**店铺：** {order.get('shop', '')}")
                st.markdown(f"**城市：** {order.get('city', '')}")
                st.markdown(f"**从业年限：** {order.get('years', '—')}")
                st.markdown(f"**主营业务：** {order.get('main_biz', '—')}")
                st.markdown(f"**主推产品：** {order.get('product', '—')}")
            with col2:
                st.markdown(f"**产品特点：** {order.get('feature', '—')}")
                st.markdown(f"**核心优势：** {order.get('advantage', '—')}")
                st.markdown(f"**目标客群：** {order.get('target', '—')}")
                st.markdown(f"**营业时间：** {order.get('hours', '—')}")

            st.markdown("**创业故事：**")
            st.text(order.get("story", "—"))
            if order.get("hard_time"):
                st.markdown("**最难的时期：**")
                st.text(order.get("hard_time"))
            if order.get("best_case"):
                st.markdown("**印象最深的客户案例：**")
                st.text(order.get("best_case"))
            if order.get("differentiation"):
                st.markdown("**与同行的不同：**")
                st.text(order.get("differentiation"))

            st.divider()
            btn1, btn2, btn3 = st.columns([2, 2, 1])

            with btn1:
                if st.button("🚀 立即生成文案", key=f"gen_{oid}", type="primary"):
                    _start_gen(order, api_key)
                    st.rerun()

            with btn2:
                if db_status == "待处理":
                    if st.button("✅ 标记为已生成", key=f"done_{oid}"):
                        update_order(oid, {
                            "status":       "已生成",
                            "processed_by": st.session_state.get("username", ""),
                            "processed_at": now_beijing(),
                        })
                        st.rerun()

            with btn3:
                ckey = f"_confirm_del_{oid}"
                if st.session_state.get(ckey):
                    st.warning("确认删除？")
                    c1, c2 = st.columns(2)
                    if c1.button("确认", key=f"yes_{oid}", type="primary"):
                        delete_order(oid)
                        st.session_state.pop(ckey, None)
                        st.rerun()
                    if c2.button("取消", key=f"no_{oid}"):
                        st.session_state.pop(ckey, None)
                        st.rerun()
                else:
                    if st.button("🗑️ 删除", key=f"del_{oid}"):
                        st.session_state[ckey] = True
                        st.rerun()

# ── 有任务在后台跑时，每 1.5s 自动刷新进度 ──────────
if any_running:
    time.sleep(1.5)
    st.rerun()
