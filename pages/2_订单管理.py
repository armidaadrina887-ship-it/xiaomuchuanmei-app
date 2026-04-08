"""
晓牧传媒 · 订单管理页（需登录）
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="晓牧传媒 · 订单管理",
    page_icon="📋",
    layout="wide",
)

# ── 登录拦截 ──────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.warning("请先登录")
    st.page_link("streamlit_app.py", label="去登录 →")
    st.stop()

# ── 数据读取 ──────────────────────────────────────────
DATA_FILE = Path(__file__).parent.parent / "data" / "orders.json"

def load_orders():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_orders(orders):
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 页面标题 ──────────────────────────────────────────
st.title("📋 订单管理")
st.caption(f"当前用户：{st.session_state.get('username', '')}  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")

orders = load_orders()

if not orders:
    st.info("暂无订单，等待客户填表提交")
    st.stop()

# ── 状态筛选 ──────────────────────────────────────────
col_filter, col_count = st.columns([3, 1])
with col_filter:
    status_filter = st.radio(
        "筛选状态",
        ["全部", "待处理", "已生成"],
        horizontal=True,
    )
with col_count:
    pending = sum(1 for o in orders if o.get("status") == "待处理")
    st.metric("待处理", pending)

filtered = orders if status_filter == "全部" else [o for o in orders if o.get("status") == status_filter]
# 最新的排前面
filtered = sorted(filtered, key=lambda o: o.get("submitted_at", ""), reverse=True)

st.divider()

# ── 订单列表 ──────────────────────────────────────────
for idx, order in enumerate(filtered):
    status = order.get("status", "待处理")
    status_badge = "🟡 待处理" if status == "待处理" else "✅ 已生成"
    name = order.get("name", "未知")
    shop = order.get("shop", "")
    city = order.get("city", "")
    submitted_at = order.get("submitted_at", "")

    with st.expander(f"{status_badge}  |  {name}（{shop}）· {city}  |  {submitted_at}"):

        # 信息预览
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**出镜称呼：** {name}")
            st.markdown(f"**店铺：** {shop}")
            st.markdown(f"**城市：** {city}")
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

        # 操作按钮
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])

        with btn_col1:
            # 一键把该客户信息转成填表格式，跳转到生成页
            if st.button("🚀 一键生成文案", key=f"gen_{order['id']}", type="primary"):
                # 把订单数据转换成填表格式，存入 session_state
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
                    for o in orders:
                        if o["id"] == order["id"]:
                            o["status"] = "已生成"
                            o["processed_by"] = st.session_state.get("username", "")
                            o["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_orders(orders)
                    st.rerun()

        with btn_col3:
            if st.button("🗑️ 删除", key=f"del_{order['id']}"):
                orders = [o for o in orders if o["id"] != order["id"]]
                save_orders(orders)
                st.rerun()
