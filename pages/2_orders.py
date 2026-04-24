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
import extra_streamlit_components as stx

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import parse_form, build_client, generate_scripts, make_word_bytes, INDUSTRY_NAMES
from db import load_orders, update_order, delete_order, now_beijing, _local_load
from version import VERSION
from styles import DARK_CSS, ACCENT, accent_badge, section_title, SIDEBAR_BRAND_HTML, render_topnav

_COOKIE_NAME = "xm_auth_v1"
_cookies = stx.CookieManager(key="xm_cookie_orders")

st.set_page_config(
    page_title="晓牧传媒 · 订单管理",
    page_icon="📋",
    layout="wide",
)

st.markdown(DARK_CSS + """
<style>
[data-testid="stAppViewContainer"] > .main { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# cookie → session restore，防止刷新后丢失登录状态
if not st.session_state.get("logged_in"):
    saved = _cookies.get(_COOKIE_NAME)
    if saved:
        st.session_state["logged_in"] = True
        st.session_state["username"]  = saved
    else:
        st.switch_page("streamlit_app.py")
        st.stop()

st.markdown("""
<style>[data-testid="stAppViewContainer"] > .main { visibility: visible; }</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(SIDEBAR_BRAND_HTML, unsafe_allow_html=True)
    st.divider()
    st.markdown(
        f"<span style='font-size:11px;color:#555;font-family:monospace'>"
        f"{st.session_state.get('username','')}</span>",
        unsafe_allow_html=True,
    )
    if st.button("退出登录", use_container_width=True):
        _cookies.delete(_COOKIE_NAME)
        st.session_state.clear()
        st.switch_page("streamlit_app.py")

try:
    api_key = st.secrets["KIMI_API_KEY"]
except Exception:
    api_key = os.environ.get("KIMI_API_KEY", "")

if not api_key:
    st.error("未配置 API Key，请联系管理员")
    st.stop()

# ── 后台生成状态（cache_resource 保证跨 rerun 不丢失）──
@st.cache_resource
def _gen_store():
    return {"data": {}, "lock": threading.Lock()}

def _skey(oid: str) -> tuple:
    return (id(st.session_state), oid)

def _get_gen(oid: str) -> dict:
    store = _gen_store()
    with store["lock"]:
        return dict(store["data"].get(_skey(oid), {}))

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
    store = _gen_store()
    oid   = order["id"]
    skey  = _skey(oid)
    with store["lock"]:
        if store["data"].get(skey, {}).get("status") == "running":
            return
        store["data"][skey] = {"status": "running", "progress": 0.0, "msg": "准备中..."}

    def run():
        try:
            raw    = _order_to_raw(order)
            fields = parse_form(raw)
            client, _ = build_client(fields)

            def on_progress(p, m):
                with store["lock"]:
                    if skey in store["data"]:
                        store["data"][skey].update({"progress": p, "msg": m})

            scripts    = generate_scripts(client, api_key, progress_callback=on_progress)
            word_bytes = make_word_bytes(client, scripts)

            with store["lock"]:
                store["data"][skey] = {
                    "status":   "done",
                    "bytes":    word_bytes,
                    "filename": f"{client['name']}_{client.get('company','')[:8]}_30条文案.docx",
                    "count":    len(scripts),
                    "client":   client,
                    "score":    client.get('score', {}),
                }
        except Exception as e:
            with store["lock"]:
                store["data"][skey] = {"status": "error", "error": str(e)}

    threading.Thread(target=run, daemon=True).start()

# ── 页面标题 ──────────────────────────────────────────
col_t, col_v = st.columns([6, 1])
col_t.markdown(
    "<h2 style='color:#F0F0F0;margin-bottom:0'>"
    "<span style='color:rgba(255,117,51,0.5);font-family:monospace;font-size:20px'>// </span>"
    "订单管理</h2>",
    unsafe_allow_html=True,
)
col_v.markdown(f"<br>{accent_badge('v' + VERSION)}", unsafe_allow_html=True)
st.caption(now_beijing())

render_topnav("orders")

orders = load_orders()

# ── 本地备份订单检测（Supabase 失败时的应急数据）────────
_local_orders = _local_load()
if _local_orders:
    st.warning(
        f"⚠️ 检测到 **{len(_local_orders)} 条本地备份订单**（Supabase 曾提交失败时自动存储）。\n\n"
        "这些订单**不在上方列表中**，服务器重启后将丢失。请尽快处理：\n\n"
        "展开查看 ↓",
        icon="🚨",
    )
    with st.expander(f"📂 本地备份订单（{len(_local_orders)}条）— 点击查看并手动处理"):
        for lo in _local_orders:
            st.json(lo)
        st.caption("处理方式：复制上方 JSON 数据，或联系技术人员手动写入 Supabase")

if not orders and not _local_orders:
    st.info("暂无订单，等待客户填表提交")
    st.stop()
elif not orders:
    st.stop()

# ── 状态筛选 ──────────────────────────────────────────
col_filter, col_count = st.columns([3, 1])
with col_filter:
    status_filter = st.radio("筛选状态", ["全部", "待处理", "已生成"], horizontal=True)
with col_count:
    st.metric("待处理", sum(1 for o in orders if o.get("status") == "待处理"))

filtered = orders if status_filter == "全部" else [o for o in orders if o.get("status") == status_filter]
filtered = sorted(filtered, key=lambda o: o.get("submitted_at", ""), reverse=True)

# ── 批量操作栏 ────────────────────────────────────────
pending_orders = [o for o in orders if o.get("status") == "待处理"]
if pending_orders:
    st.markdown("""
<div style='background:rgba(255,117,51,0.06);border:1px solid rgba(255,117,51,0.25);
            border-left:3px solid #FF7533;border-radius:6px;
            padding:12px 16px;margin-bottom:8px'>
<span style='color:#FF7533;font-family:monospace;font-weight:700'>// 批量生成</span>
<span style='color:#888;font-size:13px;margin-left:8px'>
勾选待处理订单 → 批量生成（多个订单同时在后台运行，页面不冻结）
</span>
</div>
""", unsafe_allow_html=True)
    selected_ids = []
    for o in pending_orders:
        gen = _get_gen(o["id"])
        is_running = gen.get("status") == "running"
        label = (f"[{int(gen.get('progress',0)*100)}%]  · " if is_running else "") + \
                f"【{o.get('group_name','—')}】**{o.get('name','—')}** · {o.get('shop','—')} · {o.get('submitted_at','')}"
        if st.checkbox(label, key=f"batch_chk_{o['id']}", disabled=is_running):
            selected_ids.append(o["id"])

    btn_label = f"批量生成选中订单（{len(selected_ids)}个）" if selected_ids else "请先勾选订单"
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
    oid       = order["id"]
    gen       = _get_gen(oid)
    gst       = gen.get("status")
    db_status = order.get("status", "待处理")
    is_editing = st.session_state.get(f"_editing_{oid}", False)

    # 完成：搬进 session_state，更新数据库
    if gst == "done":
        st.session_state[f"_result_{oid}"] = gen
        store = _gen_store()
        with store["lock"]:
            store["data"].pop(_skey(oid), None)
        update_order(oid, {
            "status":       "已生成",
            "processed_by": st.session_state.get("username", ""),
            "processed_at": now_beijing(),
        })
        gst = None

    is_running = (gst == "running")
    is_error   = (gst == "error")
    has_result = f"_result_{oid}" in st.session_state

    if is_running:
        any_running = True

    if is_running:
        badge = f"[生成中 {int(gen.get('progress', 0)*100)}%]"
    elif is_error:
        badge = "[出错]"
    elif has_result:
        badge = "[待下载]"
    elif is_editing:
        badge = "[编辑中]"
    elif db_status == "已生成":
        badge = "[已生成]"
    else:
        badge = "[待处理]"

    group_name   = order.get("group_name", "未知群")
    name         = order.get("name", "未知")
    submitted_at = order.get("submitted_at", "")

    with st.expander(
        f"{badge}  |  【{group_name}】{name} · {submitted_at}",
        expanded=is_running or has_result or is_error or is_editing,
    ):

        # ── 生成中 ────────────────────────────────────
        if is_running:
            st.progress(gen.get("progress", 0.0))
            st.info(gen.get('msg', ''))
            st.caption("生成期间可继续操作其他订单")

        # ── 出错 ──────────────────────────────────────
        elif is_error:
            st.error(f"生成失败：{gen.get('error', '未知错误')}")
            if st.button("重试", key=f"retry_{oid}", type="primary"):
                _start_gen(order, api_key)
                st.rerun()

        # ── 待下载 ────────────────────────────────────
        elif has_result:
            result = st.session_state[f"_result_{oid}"]
            score  = result.get('score', {})
            total  = score.get('total', 0)
            score_tag = f"  |  {total}分" if total else ""
            st.success(f"文案已生成完毕，共 {result['count']} 条{score_tag}")
            if score:
                bd = score.get('breakdown', {})
                c1, c2, c3, c4, c5 = st.columns(5)
                for col, (k, v) in zip([c1,c2,c3,c4,c5], [
                    ('钩子力', bd.get('钩子力', 0)),
                    ('自然感', bd.get('内容自然感', 0)),
                    ('多样性', bd.get('内容多样性', 0)),
                    ('可执行性', bd.get('拍摄可执行性', 0)),
                    ('结尾节奏', bd.get('结尾节奏', 0)),
                ]):
                    col.metric(k, f"{v}分")
                if score.get('issues'):
                    st.caption("失分项：" + "；".join(score['issues']))
            dl = st.download_button(
                label=f"下载 Word 文档（{result['count']}条）",
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
                _start_gen(order, api_key)
                st.rerun()

        # ── 编辑资料 ──────────────────────────────────
        elif is_editing:
            st.markdown("**编辑客户资料**")
            with st.form(key=f"edit_form_{oid}"):
                c1, c2 = st.columns(2)
                with c1:
                    e_group  = st.text_input("微信群",     value=order.get("group_name", ""))
                    e_name   = st.text_input("出镜称呼",   value=order.get("name", ""))
                    e_gender = st.selectbox("性别", ["男", "女", "未填写"],
                                            index=["男","女","未填写"].index(order.get("gender","未填写"))
                                            if order.get("gender","未填写") in ["男","女","未填写"] else 2)
                    e_shop   = st.text_input("店铺名称",   value=order.get("shop", ""))
                    e_city   = st.text_input("城市",       value=order.get("city", ""))
                    e_years  = st.text_input("从业年限",   value=order.get("years", ""))
                    e_hours  = st.text_input("营业时间",   value=order.get("hours", ""))
                with c2:
                    e_biz    = st.text_input("主营业务",   value=order.get("main_biz", ""))
                    e_prod   = st.text_input("主推产品",   value=order.get("product", ""))
                    e_feat   = st.text_area("产品特点/卖点", value=order.get("feature", ""),  height=80)
                    e_adv    = st.text_area("核心优势",    value=order.get("advantage", ""), height=80)
                    e_target = st.text_input("目标客群",   value=order.get("target", ""))
                    e_pain   = st.text_input("能解决的痛点", value=order.get("pain", ""))

                e_story = st.text_area("创业经历/故事",        value=order.get("story", ""),         height=100)
                e_hard  = st.text_area("最难熬的一段时期",     value=order.get("hard_time", ""),     height=80)
                e_case  = st.text_area("印象最深的客户案例",   value=order.get("best_case", ""),     height=80)
                e_diff  = st.text_area("你和同行最大的不同",   value=order.get("differentiation",""), height=80)
                e_extra = st.text_area("补充信息",             value=order.get("extra", ""),         height=60)

                save_col, cancel_col = st.columns(2)
                saved    = save_col.form_submit_button("💾 保存", type="primary", use_container_width=True)
                cancelled = cancel_col.form_submit_button("取消", use_container_width=True)

            if saved:
                update_order(oid, {
                    "group_name":      e_group.strip(),
                    "name":            e_name.strip(),
                    "gender":          e_gender,
                    "shop":            e_shop.strip(),
                    "city":            e_city.strip(),
                    "years":           e_years.strip(),
                    "hours":           e_hours.strip(),
                    "main_biz":        e_biz.strip(),
                    "product":         e_prod.strip(),
                    "feature":         e_feat.strip(),
                    "advantage":       e_adv.strip(),
                    "target":          e_target.strip(),
                    "pain":            e_pain.strip(),
                    "story":           e_story.strip(),
                    "hard_time":       e_hard.strip(),
                    "best_case":       e_case.strip(),
                    "differentiation": e_diff.strip(),
                    "extra":           e_extra.strip(),
                })
                st.session_state.pop(f"_editing_{oid}", None)
                st.success("已保存")
                st.rerun()
            elif cancelled:
                st.session_state.pop(f"_editing_{oid}", None)
                st.rerun()

        # ── 普通展示 + 操作按钮 ───────────────────────
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
            st.markdown("**创业故事：**"); st.text(order.get("story", "—"))
            if order.get("hard_time"):
                st.markdown("**最难的时期：**"); st.text(order.get("hard_time"))
            if order.get("best_case"):
                st.markdown("**印象最深的客户案例：**"); st.text(order.get("best_case"))
            if order.get("differentiation"):
                st.markdown("**与同行的不同：**"); st.text(order.get("differentiation"))

            st.divider()
            btn1, btn2, btn3, btn4 = st.columns([2, 2, 1, 1])

            with btn1:
                if st.button("立即生成文案", key=f"gen_{oid}", type="primary"):
                    _start_gen(order, api_key)
                    st.rerun()

            with btn2:
                if st.button("编辑资料", key=f"edit_{oid}"):
                    st.session_state[f"_editing_{oid}"] = True
                    st.rerun()

            with btn3:
                if db_status == "待处理":
                    if st.button("标记已生成", key=f"done_{oid}"):
                        update_order(oid, {
                            "status":       "已生成",
                            "processed_by": st.session_state.get("username", ""),
                            "processed_at": now_beijing(),
                        })
                        st.rerun()

            with btn4:
                ckey = f"_confirm_del_{oid}"
                if st.session_state.get(ckey):
                    st.warning("确认？")
                    c1, c2 = st.columns(2)
                    if c1.button("是", key=f"yes_{oid}", type="primary"):
                        delete_order(oid)
                        st.session_state.pop(ckey, None)
                        st.rerun()
                    if c2.button("否", key=f"no_{oid}"):
                        st.session_state.pop(ckey, None)
                        st.rerun()
                else:
                    if st.button("删除", key=f"del_{oid}"):
                        st.session_state[ckey] = True
                        st.rerun()

# ── 有任务在后台跑时，每 1.5s 自动刷新进度 ──────────
if any_running:
    time.sleep(1.5)
    st.rerun()
