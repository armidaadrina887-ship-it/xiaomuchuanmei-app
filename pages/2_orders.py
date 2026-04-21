"""
晓牧传媒 · 订单管理页（需登录）
生成在本页内联完成，无需跳转主页
"""
import os
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

# ── 登录拦截 ──────────────────────────────────────────
if not st.session_state.get("logged_in"):
    st.switch_page("streamlit_app.py")
    st.stop()

# ── 已登录：显示内容 + 主题 ───────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { visibility: visible; }
[data-testid="stSidebarNav"] { display: none !important; }
button[kind="primary"] { background-color:#E65000 !important; border-color:#E65000 !important; }
button[kind="primary"]:hover { background-color:#CC4800 !important; border-color:#CC4800 !important; }
a { color: #E65000 !important; }
</style>
""", unsafe_allow_html=True)

# ── 侧边栏 ────────────────────────────────────────────
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

# ── API Key ───────────────────────────────────────────
try:
    api_key = st.secrets["KIMI_API_KEY"]
except Exception:
    api_key = os.environ.get("KIMI_API_KEY", "")

if not api_key:
    st.error("未配置 API Key，请联系管理员")
    st.stop()

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

# ── 批量操作栏 ────────────────────────────────────────
pending_orders = [o for o in orders if o.get("status") == "待处理"]
if pending_orders:
    st.markdown("""
<div style='background:#FFF4EE;border:1.5px solid #E65000;border-radius:10px;
            padding:12px 16px;margin-bottom:8px'>
<b style='color:#E65000'>📦 批量生成</b>
<span style='color:#555;font-size:13px;margin-left:8px'>
勾选下方待处理订单 → 点击「批量生成」→ 在本页依次生成，完成后逐个下载
</span>
</div>
""", unsafe_allow_html=True)

    selected_ids = []
    for o in pending_orders:
        if st.checkbox(
            f"【{o.get('group_name','—')}】**{o.get('name','—')}** · "
            f"{o.get('shop','—')} · {o.get('submitted_at','')}",
            key=f"batch_chk_{o['id']}",
        ):
            selected_ids.append(o["id"])

    btn_label = f"🚀 批量生成选中订单（{len(selected_ids)}个）" if selected_ids else "请先勾选订单"
    if st.button(btn_label, type="primary", disabled=not selected_ids, use_container_width=True):
        st.session_state["_batch_ids"] = selected_ids[:]
        st.session_state.pop("_current_gen_id", None)
        st.rerun()

st.divider()

# ── 批量队列自动推进 ──────────────────────────────────
# 如果有待处理批量队列且当前没有正在生成的任务，取出下一个开始生成
batch_ids = st.session_state.get("_batch_ids", [])
current_gen_id = st.session_state.get("_current_gen_id")

if batch_ids and not current_gen_id:
    st.session_state["_current_gen_id"] = batch_ids[0]
    st.session_state["_batch_ids"] = batch_ids[1:]
    st.rerun()

# ── 辅助：订单转文本 ──────────────────────────────────
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

# ── 批量进度提示 ──────────────────────────────────────
remaining = len(st.session_state.get("_batch_ids", []))
if current_gen_id or remaining > 0:
    total_done = sum(
        1 for o in pending_orders
        if f"_result_{o['id']}" in st.session_state
    )
    batch_total = total_done + (1 if current_gen_id else 0) + remaining
    st.info(f"📦 批量进行中：已完成 {total_done} 个 / 共 {batch_total} 个"
            + (f"，还有 {remaining} 个排队中" if remaining > 0 else ""))

# ── 订单列表 ──────────────────────────────────────────
for order in filtered:
    oid        = order["id"]
    status     = order.get("status", "待处理")
    is_gen     = (current_gen_id == oid)
    has_result = f"_result_{oid}" in st.session_state

    status_badge = {
        "待处理": "🟡 待处理",
        "已生成": "✅ 已生成",
    }.get(status, f"🔵 {status}")
    if is_gen:
        status_badge = "⏳ 生成中..."
    elif has_result:
        status_badge = "🟢 待下载"

    group_name   = order.get("group_name", "未知群")
    name         = order.get("name", "未知")
    submitted_at = order.get("submitted_at", "")

    with st.expander(
        f"{status_badge}  |  【{group_name}】{name} · {submitted_at}",
        expanded=is_gen or has_result,
    ):

        # ── 生成中：运行生成逻辑 ──────────────────────
        if is_gen:
            st.markdown(f"**正在为 {name} 生成文案，请稍候（约 2-3 分钟）…**")
            pb   = st.progress(0.0)
            stxt = st.empty()

            raw = _order_to_raw(order)
            fields = parse_form(raw)
            try:
                client, prompt_file = build_client(fields)
            except Exception as e:
                stxt.error(f"信息解析失败：{e}")
                st.session_state.pop("_current_gen_id", None)
                st.rerun()
                st.stop()

            stxt.info("⏳ 正在生成第 1 批...")
            try:
                scripts = generate_scripts(
                    client, api_key,
                    progress_callback=lambda p, m, _pb=pb, _s=stxt: (
                        _pb.progress(p), _s.info(f"⏳ {m}")
                    ),
                )
            except Exception as e:
                stxt.error(f"生成失败：{e}")
                st.session_state.pop("_current_gen_id", None)
                st.rerun()
                st.stop()

            pb.progress(1.0)
            stxt.success(f"✅ 生成完成！共 {len(scripts)} 条")

            try:
                word_bytes = make_word_bytes(client, scripts)
            except Exception as e:
                stxt.error(f"Word 生成失败：{e}")
                st.session_state.pop("_current_gen_id", None)
                st.rerun()
                st.stop()

            # 存结果，清当前任务，触发下一个（如有）
            st.session_state[f"_result_{oid}"] = {
                "bytes":    word_bytes,
                "filename": f"{client['name']}_{client.get('company','')[:8]}_30条文案.docx",
                "count":    len(scripts),
                "client":   client,
            }
            st.session_state.pop("_current_gen_id", None)
            update_order(oid, {
                "status":       "已生成",
                "processed_by": st.session_state.get("username", ""),
                "processed_at": now_beijing(),
            })
            st.rerun()

        # ── 待下载：展示下载按钮 ──────────────────────
        elif has_result:
            result = st.session_state[f"_result_{oid}"]
            st.success(f"✅ 文案已生成完毕，共 {result['count']} 条，请点击下载")
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
            if st.button("重新生成", key=f"regen_{oid}"):
                st.session_state.pop(f"_result_{oid}", None)
                st.session_state["_current_gen_id"] = oid
                st.rerun()

        # ── 普通状态：信息展示 + 操作按钮 ──────────────
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
            btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])

            with btn_col1:
                if st.button("🚀 立即生成文案", key=f"gen_{oid}", type="primary"):
                    st.session_state["_current_gen_id"] = oid
                    st.rerun()

            with btn_col2:
                if status == "待处理":
                    if st.button("✅ 标记为已生成", key=f"done_{oid}"):
                        update_order(oid, {
                            "status":       "已生成",
                            "processed_by": st.session_state.get("username", ""),
                            "processed_at": now_beijing(),
                        })
                        st.rerun()

            with btn_col3:
                confirm_key = f"_confirm_del_{oid}"
                if st.session_state.get(confirm_key):
                    st.warning("确认删除？")
                    c1, c2 = st.columns(2)
                    if c1.button("确认", key=f"yes_{oid}", type="primary"):
                        delete_order(oid)
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                    if c2.button("取消", key=f"no_{oid}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
                else:
                    if st.button("🗑️ 删除", key=f"del_{oid}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
