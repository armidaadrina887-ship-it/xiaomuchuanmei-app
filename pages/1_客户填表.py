"""
晓牧传媒 · 客户信息填写页（公开，无需登录）
"""
import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="晓牧传媒 · 客户填表",
    page_icon="📝",
    layout="centered",
)

# ── 隐藏侧边栏导航（客户不需要看到其他页面）────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"]  { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── 数据存储 ──────────────────────────────────────────
DATA_FILE = Path(__file__).parent.parent / "data" / "orders.json"

def save_order(data: dict):
    DATA_FILE.parent.mkdir(exist_ok=True)
    orders = []
    if DATA_FILE.exists():
        try:
            orders = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            orders = []
    orders.append(data)
    DATA_FILE.write_text(json.dumps(orders, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 提交成功页 ────────────────────────────────────────
if st.session_state.get("form_submitted"):
    submitted_name = st.session_state.get("submitted_name", "您")
    st.markdown(
        f"<div style='text-align:center;padding:60px 20px'>"
        f"<div style='font-size:64px'>✅</div>"
        f"<h2>{submitted_name} 的资料已提交成功！</h2>"
        f"<p style='color:#666;font-size:16px'>我们的文案老师会在 1-2 个工作日内完成制作<br>完成后通过微信发送给您，请注意查收</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── 页面标题 ──────────────────────────────────────────
st.markdown(
    "<h2 style='text-align:center;margin-top:16px'>📝 客户资料填写</h2>"
    "<p style='text-align:center;color:#888'>晓牧传媒 · AI短视频文案定制</p>",
    unsafe_allow_html=True,
)
st.divider()

st.info(
    "💡 **填写建议**：内容较多，手机用户可使用语音输入\n\n"
    "iOS：长按键盘左下角 🎤  |  Android：长按键盘麦克风键"
)

# ── 表单 ──────────────────────────────────────────────
with st.form("client_form"):

    # ── 群名字（必填，防止随意填写）──────────────────
    st.markdown("### 验证信息")
    group_name = st.text_input(
        "微信群名称 *",
        placeholder="请复制您所在的晓牧传媒服务群名称，粘贴到此处",
        help="请从微信群聊界面复制群名称后粘贴，确保信息与我们匹配"
    )

    st.divider()

    # ── 第一部分：基本信息 ────────────────────────────
    st.markdown("### 第一部分：基本信息")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("出镜称呼 *", placeholder="如：老苏、川哥、小美")
    with col2:
        gender = st.selectbox("性别", ["女", "男", "不限"])

    shop = st.text_input("店铺 / 品牌名称 *", placeholder="如：入木三分木作工作室")

    col3, col4 = st.columns(2)
    with col3:
        city = st.text_input("城市 *", placeholder="如：杭州、重庆石桥铺")
    with col4:
        years = st.text_input("从业年限", placeholder="如：8年")

    main_biz = st.text_input("主营业务 *", placeholder="如：全屋定制木作、川菜餐厅、皮肤管理")

    st.divider()

    # ── 第二部分：产品与优势 ──────────────────────────
    st.markdown("### 第二部分：产品与优势")

    product = st.text_input("主推产品 / 服务 *", placeholder="如：极简系列橱柜、麻辣龙虾、水光针")
    feature = st.text_area("产品特点 / 卖点 *", height=80,
                           placeholder="如：全实木框架、现捞现炒、进口玻尿酸")
    advantage = st.text_area("核心优势（与同类的不同之处）*", height=80,
                              placeholder="如：自己工厂直供无中间商、只做本地食材、15年只做一个项目")
    target = st.text_input("目标客群 *", placeholder="如：25-40岁有装修需求的业主、本地上班族")

    st.divider()

    # ── 第三部分：你的故事 ────────────────────────────
    st.markdown("### 第三部分：你的故事")
    st.warning("🎤 **这部分最适合语音输入** — 说大白话就行，越真实越好")

    story = st.text_area(
        "创业经历 / 入行故事 *",
        height=120,
        placeholder="怎么入行的？当时为什么做这个？有什么转折点？\n例：2009年从装修工地打工开始，做了5年师傅后自己出来单干……",
    )
    hard_time = st.text_area(
        "最难熬的一段时期 *",
        height=100,
        placeholder="做这行最难的时候是什么？差点放弃吗？怎么撑过来的？",
    )
    best_case = st.text_area(
        "印象最深的客户案例 *",
        height=100,
        placeholder="有没有特别让你印象深刻的客户或订单？发生了什么？",
    )
    differentiation = st.text_area(
        "你和同行最大的不同 *",
        height=80,
        placeholder="如果客户问你「为什么选你不选别人」，你会怎么回答？",
    )

    st.divider()

    # ── 补充信息（选填）──────────────────────────────
    st.markdown("### 补充信息（选填）")
    pain = st.text_area("能帮客户解决什么痛点", height=80,
                        placeholder="你的客户最常遇到什么问题？你怎么解决的？")
    hours = st.text_input("营业时间", placeholder="如：每天10:00-21:00")
    extra = st.text_area("其他补充（产品特殊卖点、想重点展示的内容等）", height=80)

    st.divider()
    submitted = st.form_submit_button("✅ 提交资料", use_container_width=True, type="primary")

# ── 提交处理 ──────────────────────────────────────────
if submitted:
    # 必填校验
    required_fields = {
        "微信群名称": group_name,
        "出镜称呼": name,
        "店铺/品牌名称": shop,
        "城市": city,
        "主营业务": main_biz,
        "主推产品/服务": product,
        "产品特点/卖点": feature,
        "核心优势": advantage,
        "目标客群": target,
        "创业经历/入行故事": story,
        "最难熬的一段时期": hard_time,
        "印象最深的客户案例": best_case,
        "你和同行最大的不同": differentiation,
    }
    missing = [k for k, v in required_fields.items() if not v.strip()]

    if missing:
        st.error(f"⚠️ 以下必填项未填写，请补充后再提交：\n\n**{'、'.join(missing)}**")
    else:
        order = {
            "id":              datetime.now().strftime("%Y%m%d%H%M%S"),
            "submitted_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status":          "待处理",
            "group_name":      group_name.strip(),
            "name":            name.strip(),
            "gender":          gender,
            "shop":            shop.strip(),
            "city":            city.strip(),
            "years":           years.strip(),
            "main_biz":        main_biz.strip(),
            "product":         product.strip(),
            "feature":         feature.strip(),
            "advantage":       advantage.strip(),
            "target":          target.strip(),
            "story":           story.strip(),
            "hard_time":       hard_time.strip(),
            "best_case":       best_case.strip(),
            "differentiation": differentiation.strip(),
            "pain":            pain.strip(),
            "hours":           hours.strip(),
            "extra":           extra.strip(),
        }
        try:
            save_order(order)
            st.session_state["form_submitted"] = True
            st.session_state["submitted_name"] = name.strip()
            st.rerun()
        except Exception as e:
            st.error(f"提交失败，请截图联系工作人员：{e}")
