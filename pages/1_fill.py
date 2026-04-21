"""
晓牧传媒 · 客户信息填写页（公开，无需登录）
"""
import streamlit as st
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import parse_form, get_field
from db import insert_order, now_beijing

st.set_page_config(
    page_title="晓牧传媒 · 客户填表",
    page_icon="📝",
    layout="centered",
)

# 客户填表页：始终隐藏侧边栏，避免客户误点导航导致数据丢失
st.markdown("""
<style>
[data-testid="stSidebarNav"]     { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
#MainMenu                        { display: none !important; }
header[data-testid="stHeader"]   { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── 提交锁：防止重复提交 ──────────────────────────────
# 表单数据已存入 session_state，正在调用 Supabase 写入
if st.session_state.get("_submitting") and "_pending_order" in st.session_state:
    st.markdown(
        "<div style='text-align:center;padding:60px 20px'>"
        "<div style='font-size:48px'>⏳</div>"
        "<h3>正在提交，请稍候…</h3>"
        "<p style='color:#888'>请勿关闭页面或重复点击</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    order = st.session_state.pop("_pending_order")
    try:
        insert_order(order)
        for k in list(st.session_state.keys()):
            if k.startswith("pf_") or k in ("step1_done", "missing_fields", "_submitting"):
                st.session_state.pop(k, None)
        st.session_state["form_submitted"] = True
        st.session_state["submitted_name"] = order["name"]
    except Exception as e:
        st.session_state.pop("_submitting", None)
        st.error(f"提交失败，请截图联系工作人员：{e}")
        st.stop()
    st.rerun()
    st.stop()

# ── 提交成功页 ────────────────────────────────────────
if st.session_state.get("form_submitted"):
    submitted_name = st.session_state.get("submitted_name", "您")
    st.markdown(
        f"<div style='text-align:center;padding:60px 20px'>"
        f"<div style='font-size:64px'>✅</div>"
        f"<h2>{submitted_name} 的资料已提交成功！</h2>"
        f"<p style='color:#666;font-size:16px'>我们的文案老师会在 1-2 个工作日内完成制作<br>"
        f"完成后通过微信发送给您，请注意查收</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── 页面标题 ──────────────────────────────────────────
st.markdown(
    "<h2 style='text-align:center;margin-top:16px'>📝 客户资料填写</h2>"
    "<p style='text-align:center;color:#888'>晓牧传媒 · 专业短视频文案定制</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── 第一步：群名称 + 称呼（门控）────────────────────────
# 未完成第一步时，只显示入口字段，不展示完整表单
if not st.session_state.get("step1_done"):
    st.markdown("### 请先填写以下信息")
    st.caption("填写完成后点击「开始填写资料」进入详细表单")

    with st.form("step1_form"):
        s1_group = st.text_input(
            "微信群名称 *",
            placeholder="请复制您所在的晓牧传媒服务群名称粘贴到此处",
        )
        s1_name = st.text_input(
            "您的称呼 *",
            placeholder="如：老苏、川哥、小美（视频里怎么称呼就怎么填）",
        )
        go = st.form_submit_button("开始填写资料 →", type="primary", use_container_width=True)

    if go:
        if not s1_group.strip() or not s1_name.strip():
            st.error("两项都必须填写才能继续")
        else:
            st.session_state["pf_group"] = s1_group.strip()
            st.session_state["pf_name"]  = s1_name.strip()
            st.session_state["step1_done"] = True
            st.rerun()
    st.stop()

# ── 一键解析区（放在表单外，解析后写入 session_state）───
with st.expander("📋 已有资料？一键粘贴自动填写", expanded=False):
    st.caption("把之前填写的客户信息表（任意格式）粘贴进来，系统自动识别并填入下方表单")
    quick_raw = st.text_area(
        "粘贴客户资料",
        key="quick_raw",
        height=180,
        placeholder="""出镜称呼：老苏
店铺信息名称：入木三分木作工作室
城市名字：邢台
主营业务：全屋定制木作
主推产品：极简系列橱柜
产品特点：全实木框架，榫卯工艺
...""",
    )
    if st.button("🔍 解析并自动填写 →", type="primary", use_container_width=True):
        if not quick_raw.strip():
            st.error("请粘贴客户资料")
        else:
            fields = parse_form(quick_raw)
            # 群名称已在第一步填好，保持不变
            # 写入 session_state，表单字段会自动读取
            st.session_state["pf_name"]    = get_field(fields, '出镜称呼', '主理人姓名', '姓名')
            st.session_state["pf_shop"]    = get_field(fields, '店铺信息名称', '店名', '品牌名称', '公司名')
            st.session_state["pf_city"]    = get_field(fields, '城市名字', '城市', '地点')
            st.session_state["pf_years"]   = get_field(fields, '从业年限', '年限')
            st.session_state["pf_biz"]     = get_field(fields, '主营业务', '主营')
            st.session_state["pf_product"] = get_field(fields, '主推产品', '主推', '招牌产品')
            st.session_state["pf_feature"] = get_field(fields, '产品特点', '卖点', '特点')
            st.session_state["pf_adv"]     = get_field(fields, '核心优势', '优势')
            st.session_state["pf_target"]  = get_field(fields, '受众人群', '目标客户', '客户群体')
            st.session_state["pf_story"]   = get_field(fields, '创业经历', '入行故事', '故事')
            st.session_state["pf_hard"]    = get_field(fields, '最难', '困难', '低谷')
            st.session_state["pf_case"]    = get_field(fields, '客户案例', '印象', '客户故事')
            st.session_state["pf_diff"]    = get_field(fields, '与同行', '差异', '不同')
            st.session_state["pf_pain"]    = get_field(fields, '痛点', '解决客户')
            st.session_state["pf_hours"]   = get_field(fields, '营业时间')
            st.session_state["pf_extra"]   = get_field(fields, '补充', '其他')

            parsed_count = sum(1 for k in [
                'pf_name','pf_shop','pf_city','pf_biz','pf_product'
            ] if st.session_state.get(k))
            st.success(f"✅ 已解析 {parsed_count}/5 个核心字段，请检查下方表单后提交")
            st.rerun()

st.divider()
st.info(
    "💡 **填写建议**：内容较多，手机用户可使用语音输入\n\n"
    "iOS：长按键盘左下角 🎤  |  Android：长按键盘麦克风键"
)

# ── 辅助：读取预填值 ──────────────────────────────────
def _v(key, default=""):
    return st.session_state.get(key, default)

# 高亮样式：未填字段下方显示红色提示
_ERR_HTML = (
    "<div style='background:#fff0f0;border-left:3px solid #ff4444;"
    "padding:4px 10px;margin:-6px 0 10px;border-radius:0 4px 4px 0;"
    "font-size:13px;color:#cc0000'>⚠️ 此项必填，请填写后再提交</div>"
)
_missing_set: set = set(st.session_state.get("missing_fields", []))

def _err(field_id):
    if field_id in _missing_set:
        st.markdown(_ERR_HTML, unsafe_allow_html=True)

# ── 表单 ──────────────────────────────────────────────
with st.form("client_form"):

    st.markdown("### 验证信息")
    group_name = st.text_input(
        "微信群名称 *",
        value=_v("pf_group"),
        placeholder="请复制您所在的晓牧传媒服务群名称，粘贴到此处",
    )
    _err("微信群名称")

    st.divider()
    st.markdown("### 第一部分：基本信息")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("出镜称呼 *", value=_v("pf_name"), placeholder="如：老苏、川哥、小美")
        _err("出镜称呼")
    with col2:
        gender = st.selectbox("性别", ["女", "男", "不限"])

    shop = st.text_input("店铺 / 品牌名称 *", value=_v("pf_shop"), placeholder="如：入木三分木作工作室")
    _err("店铺/品牌名称")

    col3, col4 = st.columns(2)
    with col3:
        city = st.text_input("城市 *", value=_v("pf_city"), placeholder="如：杭州、重庆石桥铺")
        _err("城市")
    with col4:
        years = st.text_input("从业年限", value=_v("pf_years"), placeholder="如：8年")

    main_biz = st.text_input("主营业务 *", value=_v("pf_biz"), placeholder="如：全屋定制木作、川菜餐厅")
    _err("主营业务")

    st.divider()
    st.markdown("### 第二部分：产品与优势")

    product = st.text_input("主推产品 / 服务 *", value=_v("pf_product"), placeholder="如：极简系列橱柜、麻辣龙虾")
    _err("主推产品/服务")
    feature = st.text_area("产品特点 / 卖点 *", value=_v("pf_feature"), height=80,
                           placeholder="如：全实木框架、现捞现炒、进口玻尿酸")
    _err("产品特点/卖点")
    advantage = st.text_area("核心优势（与同类的不同之处）*", value=_v("pf_adv"), height=80,
                              placeholder="如：自己工厂直供无中间商、只做本地食材")
    _err("核心优势")
    target = st.text_input("目标客群 *", value=_v("pf_target"), placeholder="如：25-40岁有装修需求的业主")
    _err("目标客群")

    st.divider()
    st.markdown("### 第三部分：你的故事")
    st.warning("🎤 **这部分最适合语音输入** — 说大白话就行，越真实越好")

    story = st.text_area("创业经历 / 入行故事 *", value=_v("pf_story"), height=120,
                         placeholder="怎么入行的？当时为什么做这个？有什么转折点？")
    _err("创业经历/入行故事")
    hard_time = st.text_area("最难熬的一段时期 *", value=_v("pf_hard"), height=100,
                             placeholder="做这行最难的时候是什么？差点放弃吗？怎么撑过来的？")
    _err("最难熬的一段时期")
    best_case = st.text_area("印象最深的客户案例 *", value=_v("pf_case"), height=100,
                             placeholder="有没有特别让你印象深刻的客户或订单？发生了什么？")
    _err("印象最深的客户案例")
    differentiation = st.text_area("你和同行最大的不同 *", value=_v("pf_diff"), height=80,
                                   placeholder="如果客户问你「为什么选你不选别人」，你会怎么回答？")
    _err("你和同行最大的不同")

    st.divider()
    st.markdown("### 补充信息（选填）")
    pain  = st.text_area("能帮客户解决什么痛点", value=_v("pf_pain"), height=80)
    hours = st.text_input("营业时间", value=_v("pf_hours"), placeholder="如：每天10:00-21:00")
    extra = st.text_area("其他补充", value=_v("pf_extra"), height=80)

    st.divider()
    submitted = st.form_submit_button("✅ 提交资料", use_container_width=True, type="primary")

# ── 提交处理 ──────────────────────────────────────────
if submitted:
    # 已有提交在进行中，忽略重复点击
    if st.session_state.get("_submitting"):
        st.stop()

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
        st.session_state["missing_fields"] = missing
        st.error(f"⚠️ 还有 {len(missing)} 项未填写，已在下方标红提示，请补充后再提交")
    else:
        # 保存订单数据，设提交锁，立即 rerun 显示 loading 页
        st.session_state["_pending_order"] = {
            "id":              uuid.uuid4().hex[:12] + now_beijing().replace("-","").replace(":","").replace(" ",""),
            "submitted_at":    now_beijing(),
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
        st.session_state["_submitting"] = True
        st.rerun()  # 立即跳到 loading 页，Supabase 写入在下一帧执行
