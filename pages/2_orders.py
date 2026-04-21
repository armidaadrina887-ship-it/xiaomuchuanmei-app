"""
晓牧传媒 · 订单管理页（需登录）
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
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
[data-testid="stSidebarNav"]              { display: none !important; }
[data-testid="stAppViewContainer"] > .main { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── 登录拦截 ──────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("streamlit_app.py")
    st.stop()

# ── 已登录：显示内容 + 橙色主题 + 侧边栏 ────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { visibility: visible; }
[data-testid="stSidebarNav"] { display: none !important; }
button[kind="primary"] {
    background-color: #E65000 !important;
    border-color: #E65000 !important;
}
button[kind="primary"]:hover {
    background-color: #CC4800 !important;
    border-color: #CC4800 !important;
}
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
    pending = sum(1 for o in orders if o.get("status") == "待处理")
    st.metric("待处理", pending)

filtered = orders if status_filter == "全部" else [o for o in orders if o.get("status") == status_filter]
filtered = sorted(filtered, key=lambda o: o.get("submitted_at", ""), reverse=True)

# ── 批量操作栏（始终可见，紧贴列表顶部）─────────────
pending_orders = [o for o in orders if o.get("status") == "待处理"]
if pending_orders:
    st.markdown("""
<div style='background:#FFF4EE;border:1.5px solid #E65000;border-radius:10px;padding:12px 16px;margin-bottom:8px'>
<b style='color:#E65000'>📦 批量生成</b>
<span style='color:#555;font-size:13px;margin-left:8px'>勾选下方订单 → 点击「批量生成」→ 跳到文案页依次处理</span>
</div>
""", unsafe_allow_html=True)

    selected_ids = []
    sel_cols = st.columns([0.05, 0.95])
    for o in pending_orders:
        chk = st.checkbox(
            f"【{o.get('group_name','—')}】**{o.get('name','—')}** · {o.get('shop','—')} · {o.get('submitted_at','')}",
            key=f"batch_chk_{o['id']}",
        )
        if chk:
            selected_ids.append(o["id"])

    btn_label = f"🚀 批量生成选中订单（{len(selected_ids)}个）" if selected_ids else "请勾选订单"
    if st.button(btn_label, type="primary", disabled=not selected_ids, use_container_width=True):
        batch_queue = []
        for o in pending_orders:
            if o["id"] not in selected_ids:
                continue
            raw_text = f"""出镜称呼：{o.get('name', '')}
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
            batch_queue.append({"raw": raw_text, "order_id": o["id"], "name": o.get("name", "")})
        st.session_state["batch_queue"] = batch_queue
        st.switch_page("streamlit_app.py")

st.divider()

# ── 订单列表 ──────────────────────────────────────────
for idx, order in enumerate(filtered):
    status = order.get("status", "待处理")
    status_badge = "🟡 待处理" if status == "待处理" else "✅ 已生成"
    group_name = order.get("group_name", "未知群")
    name = order.get("name", "未知")
    submitted_at = order.get("submitted_at", "")

    with st.expander(f"{status_badge}  |  【{group_name}】{name} · {submitted_at}"):

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

        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])

        with btn_col1:
            if st.button("🚀 一键生成文案", key=f"gen_{order['id']}", type="primary"):
                raw_text = f"""出镜称呼：{order.get('name', '')}
性别：{order.get('gender', '')}
店铺信息名称：{order.get('shop', '')}
城市名字：{order.get('city', '')}
从业年限：{order.get('years', '')}
主营业务：{order.get('main_biz', '')}
主推产品：{order.get('product', '')}
产品特点：{order.get('feature', '')}
核心优势：{order.get('advantage', '')}
目标客群：{order.get('target', '')}
创业经历：{order.get('story', '')}
最难的时期：{order.get('hard_time', '')}
客户案例：{order.get('best_case', '')}
与同行差异：{order.get('differentiation', '')}
能解决的痛点：{order.get('pain', '')}
营业时间：{order.get('hours', '')}
补充信息：{order.get('extra', '')}"""
                st.session_state["prefill_order"] = raw_text
                st.session_state["prefill_order_id"] = order["id"]
                st.switch_page("streamlit_app.py")

        with btn_col2:
            if status == "待处理":
                if st.button("✅ 标记为已生成", key=f"done_{order['id']}"):
                    update_order(order["id"], {
                        "status":       "已生成",
                        "processed_by": st.session_state.get("username", ""),
                        "processed_at": now_beijing(),
                    })
                    st.rerun()

        with btn_col3:
            confirm_key = f"confirm_del_{order['id']}"
            if st.session_state.get(confirm_key):
                st.warning("确认删除？")
                c1, c2 = st.columns(2)
                if c1.button("确认", key=f"yes_{order['id']}", type="primary"):
                    delete_order(order["id"])
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
                if c2.button("取消", key=f"no_{order['id']}"):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
            else:
                if st.button("🗑️ 删除", key=f"del_{order['id']}"):
                    st.session_state[confirm_key] = True
                    st.rerun()
