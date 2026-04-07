"""
晓牧传媒 · AI文案生成系统
"""
import streamlit as st
import os
from core import (
    parse_form, build_client, generate_scripts,
    make_word_bytes, INDUSTRY_NAMES
)

# ── 页面配置 ──────────────────────────────────────
st.set_page_config(
    page_title="晓牧传媒 · AI文案生成",
    page_icon="🎬",
    layout="centered",
)

col_title, col_ver = st.columns([5, 1])
col_title.title("🎬 晓牧传媒 · AI文案生成系统")
col_ver.markdown("<br><span style='background:#1a73e8;color:white;padding:3px 10px;border-radius:12px;font-size:13px'>v2.4</span>", unsafe_allow_html=True)
st.caption("粘贴客户信息表 → 自动识别行业 → 6批×5条生成 → 行业违禁词扫描 → 下载Word")

# ── API Key ───────────────────────────────────────
# 优先从 Streamlit secrets 读取，其次从环境变量
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

raw = st.text_area(
    "粘贴客户信息表",
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

    # 解析
    fields = parse_form(raw)
    try:
        client, prompt_file = build_client(fields)
    except Exception as e:
        st.error(f"信息解析失败：{e}")
        st.stop()

    # 显示识别结果
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

    # 生成
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
    status_text.success(f"✅ 生成完成！共 {len(scripts)} 条脚本")

    # 违禁词警告
    violations = client.get('violations', [])
    if violations:
        vlist = "、".join(f"第{v['script']}条[{v['word']}]" for v in violations[:8])
        st.warning(f"⚠️ 违禁词（已重写后仍存在）：{vlist}，建议人工复查")

    # 开场套话残留警告
    opening_remaining = client.get('opening_violations_remaining', [])
    if opening_remaining:
        st.warning(f"⚠️ 以下条目开场仍有套话，请人工替换：第{'、'.join(str(n) for n in opening_remaining)}条")

    # 场景人物警告（Patch 3）
    scene_violations = client.get('scene_violations', [])
    if scene_violations:
        sv_list = "、".join(f"第{v['script']}条镜头{v['shot']}[{v['keyword']}]" for v in scene_violations[:6])
        st.warning(f"⚠️ 场景描述出现禁止人物词：{sv_list}，需人工修改场景描述")

    # 生成 Word 字节流
    try:
        word_bytes = make_word_bytes(client, scripts)
    except Exception as e:
        st.error(f"Word生成失败：{e}")
        st.stop()

    filename = f"{client['name']}_{client['company'][:8]}_30条文案.docx"

    st.download_button(
        label=f"⬇️ 下载 Word 文档（{len(scripts)}条）",
        data=word_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
        type="primary",
    )

    # 预览前3条
    with st.expander("预览前3条脚本"):
        for s in scripts[:3]:
            st.markdown(f"**第{s.get('number')}条 · {s.get('title')}**")
            st.caption(f"{s.get('type')} · {s.get('duration')} · {len(s.get('shots',[]))}个镜头")
            for i, shot in enumerate(s.get('shots', [])[:3]):
                st.markdown(f"- 镜头{i+1}：{shot.get('scene','')}  \n  > {shot.get('dialogue','')[:60]}...")
            st.divider()
