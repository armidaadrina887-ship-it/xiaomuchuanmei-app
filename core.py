"""
晓牧传媒 · 核心生成逻辑
路径全部相对于本文件，可部署到任何环境
"""
import openai, json, re, os, datetime, io
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

PROMPTS_DIR = Path(__file__).parent / 'prompts'

# ── 工具函数 ──────────────────────────────────────

def load_prompt(filename):
    return (PROMPTS_DIR / filename).read_text(encoding='utf-8')

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def difficulty_style(d):
    if d == '简单版': return (46,125,50),  'E8F5E9'
    if d == '标准版': return (230,81,0),   'FFF3E0'
    return                  (106,27,154),  'EDE7F6'

# ── 口吻规范 ─────────────────────────────────────

STYLE_GUIDE = """
【口吻规范 - 必须遵守】
- 每条口播台词像在和朋友说话，不像广告
- 必须有具体细节：数字、时间、对话、事件，不说泛泛评价
- 有停顿、有克制，不急着说结论，让细节说话
- 每条结尾必须有明确行动指令（来店/评论/私信等）
- 禁止词：专业团队/匠心/用心/初心/情怀/顶级/高端/奢华/超高性价比/良心价格/全程无忧/让您满意/不踩雷
- 30条中任意两条相同短语（3字以上连续）不超过5%，同类意思必须换不同表达

【内容质量标准】
- 每条前两句有钩子，让人想继续看
- 30条角度完全不同，覆盖所有内容维度
- 口播每条不少于150字
- 每条6-8个镜头，时长约1分钟
"""

JSON_FORMAT = """
请输出JSON格式（直接输出JSON数组，不要其他文字，不要markdown代码块）：
[
  {
    "number": 1,
    "type": "类型",
    "duration": "约1分钟",
    "title": "标题",
    "shots": [
      {"scene": "场景描述", "dialogue": "口播台词"},
      {"scene": "场景描述", "dialogue": "口播台词"}
    ],
    "tips": "拍摄建议"
  }
]
每条6-8个镜头，口播约1分钟，30条角度全部不同。
"""

# ── 行业识别 ─────────────────────────────────────

EXTRA_KEYWORDS = {
    '牛排': 'canyin.md', '意面': 'canyin.md', '汉堡': 'canyin.md',
    '炸鸡': 'canyin.md', '披萨': 'canyin.md', '寿司': 'canyin.md',
    '甜品': 'canyin.md', '蛋糕': 'canyin.md', '炒饭': 'canyin.md',
    '剪发': 'meiiye.md', '发廊': 'meiiye.md', '护肤': 'meiiye.md',
    '装修': 'jiazhuang.md', '设计': 'jiazhuang.md',
}

INDUSTRY_NAMES = {
    'jiazhuang.md': '家装',
    'canyin.md':    '餐饮',
    'meiiye.md':    '美业',
    'jiudian.md':   '酒店/宴席',
    'general.md':   '通用',
}

def detect_industry(text):
    router = json.loads((PROMPTS_DIR / 'industry_router.json').read_text())
    all_rules = {**EXTRA_KEYWORDS, **router['routing_rules']}
    for keyword, prompt_file in all_rules.items():
        if keyword != 'default' and keyword in text:
            return prompt_file
    return router['routing_rules']['default']

# ── 表单解析 ─────────────────────────────────────

def parse_form(raw):
    fields = {}
    current_key = None
    current_val = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^[【⭐\*]*([^：:\n【】⭐\*]{2,20})[】]?[：:]\s*(.*)', line)
        if m:
            if current_key:
                fields[current_key] = '\n'.join(current_val).strip()
            current_key = m.group(1).strip()
            current_val = [m.group(2).strip()] if m.group(2).strip() else []
        elif current_key:
            current_val.append(line)
    if current_key:
        fields[current_key] = '\n'.join(current_val).strip()
    return fields

def get_field(fields, *keys, default=''):
    for k in keys:
        for fk, fv in fields.items():
            if k in fk and fv:
                return fv
    return default

def build_client(fields):
    name     = get_field(fields, '出镜称呼', '主理人姓名', '姓名')
    age      = get_field(fields, '年龄')
    gender   = get_field(fields, '性别')
    location = get_field(fields, '城市名字', '地点', '城市')
    shop_pos = get_field(fields, '店铺位置', '位置')
    shop     = get_field(fields, '店铺信息名称', '店名', '品牌名称', '公司名')
    hours    = get_field(fields, '营业时间')
    story    = get_field(fields, '创业经历', '入行故事', '故事')
    main_biz = get_field(fields, '主营业务', '主营')
    product  = get_field(fields, '主推产品', '主推', '主营产品', '招牌产品')
    feature  = get_field(fields, '产品特点', '卖点', '特点')
    target   = get_field(fields, '受众人群', '目标客户', '客户群体')
    advantage= get_field(fields, '核心优势', '优势')
    pain     = get_field(fields, '痛点', '解决客户')
    best     = get_field(fields, '客户喜好', '卖得多', '爆款')
    scale    = get_field(fields, '公司规模', '规模')
    b_or_c   = get_field(fields, 'B端', '对接')
    identity = get_field(fields, '身份', '想体现')

    is_b2b = 'B' in b_or_c.upper() and 'C' not in b_or_c.upper()

    detect_text = f"{shop} {main_biz} {product}"
    prompt_file = detect_industry(detect_text)

    msg = f"""以下是客户信息，请生成30条短视频分镜脚本。

【出镜称呼】：{name}
【性别】：{gender}  【年龄】：{age}
【店铺/品牌】：{shop}
【地点】：{location} {shop_pos}
【营业时间】：{hours}
【规模】：{scale}
【主营业务】：{main_biz}
【主推产品】：{product}
【产品特点/卖点】：{feature}
【创业经历/故事】：{story}
【核心优势】：{advantage}
【目标受众】：{target}
【能解决的痛点】：{pain}
【热销产品】：{best}
【人设定位】：{identity}
【内容定位】：{"B端（招募合伙人/加盟商）" if is_b2b else "C端（面向消费者）"}

"""
    if is_b2b:
        msg += "内容角度覆盖：创始人故事、商业模式/加盟、行业分析、门店展示、痛点避坑、招募互动（30条不重复）\n"
        type_hint = "type只能是：创始人/故事类、商业模式/加盟类、行业分析类、门店展示类、痛点/避坑类、招募/互动类"
    else:
        msg += "内容角度覆盖：主理人故事、招牌产品、幕后制作、场景氛围、痛点选择、口碑互动（30条不重复）\n"
        type_hint = "type只能是：主理人/故事类、招牌菜/食物类、幕后/制作类、场景/氛围类、痛点/选择类、口碑/互动类"

    msg += STYLE_GUIDE + "\n" + type_hint + "\n" + JSON_FORMAT

    company = shop or main_biz or name

    client = {
        'id':           re.sub(r'\W', '', name)[:8],
        'name':         name,
        'company':      company,
        'location':     f"{location} {shop_pos}".strip(),
        'prompt_file':  prompt_file,
        'user_message': msg,
    }
    return client, prompt_file

# ── API 调用 ──────────────────────────────────────

def extract_json_list(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', text)
    if not match:
        match = re.search(r'\[[\s\S]+\]', text)
    if not match:
        return []
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return []

def generate_scripts(client, api_key, progress_callback=None):
    """
    生成30条脚本。
    progress_callback(step, message) 用于向UI汇报进度，可选。
    """
    api_client = openai.OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
    system_prompt = load_prompt(client['prompt_file'])
    base_msg = client['user_message']

    def kimi_call(user_msg, label, max_tokens=16000):
        full_text = ""
        stream = api_client.chat.completions.create(
            model="moonshot-v1-128k",
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_text += delta
        return full_text

    # 第一步：生成大纲
    if progress_callback:
        progress_callback(0.1, "正在生成30条标题大纲...")
    outline_msg = base_msg + """

第一步：先列出30条的【标题】和【类型】，确保30条角度完全不同，覆盖所有内容维度。
输出格式（JSON数组）：
[{"number":1,"type":"类型","title":"标题"},...]
不要输出其他内容。"""
    raw_outline = kimi_call(outline_msg, "大纲", max_tokens=3000)
    outline = extract_json_list(raw_outline)
    outline_text = ""
    if outline:
        outline_text = "\n\n【已确定的30条标题大纲】\n" + "\n".join(
            f"{o.get('number',i+1)}. [{o.get('type','')}] {o.get('title','')}"
            for i, o in enumerate(outline)
        )

    # 第二步：分两批生成完整脚本
    all_scripts = []
    for idx, (batch_start, batch_end) in enumerate([(1, 15), (16, 30)]):
        progress = 0.3 + idx * 0.35
        if progress_callback:
            progress_callback(progress, f"正在生成第{batch_start}-{batch_end}条脚本...")
        batch_msg = base_msg + outline_text + f"""

第二步：请生成第{batch_start}条到第{batch_end}条的完整分镜脚本（共{batch_end-batch_start+1}条）。
严格按照大纲中对应编号的标题和类型来写，每条6-8个镜头，口播约1分钟。
直接输出JSON数组，不要其他文字，不要markdown代码块：
[
  {{
    "number": {batch_start},
    "type": "类型",
    "duration": "约1分钟",
    "title": "标题",
    "shots": [
      {{"scene": "场景描述", "dialogue": "口播台词"}},
      {{"scene": "场景描述", "dialogue": "口播台词"}}
    ],
    "tips": "拍摄建议"
  }},
  ...
]"""
        raw = kimi_call(batch_msg, f"第{batch_start}-{batch_end}条", max_tokens=16000)
        parsed = extract_json_list(raw)
        if parsed:
            for i, s in enumerate(parsed):
                s['number'] = batch_start + i
                if 'difficulty' not in s:
                    s['difficulty'] = '深度版'
            all_scripts.extend(parsed)

    if progress_callback:
        progress_callback(0.9, f"生成完成，共{len(all_scripts)}条，正在制作Word...")
    return all_scripts

# ── Word 生成（返回字节流，适配Web下载）────────────

def make_word_bytes(client, scripts):
    doc = Document()

    for sec in doc.sections:
        sec.page_width  = Cm(21)
        sec.page_height = Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.2)
        sec.top_margin  = sec.bottom_margin = Cm(2.2)

    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    # 封面
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(60)
    r = p.add_run(client['company'])
    r.font.size = Pt(26); r.font.bold = True
    r.font.color.rgb = RGBColor(0xCC, 0x33, 0x00)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run('30条短视频分镜脚本')
    r2.font.size = Pt(18); r2.font.bold = True

    doc.add_paragraph()
    for line in [
        f'主理人：{client["name"]}',
        f'地点：{client["location"]}',
        f'制作日期：{datetime.date.today().strftime("%Y年%m月%d日")}',
        '晓牧传媒 出品',
    ]:
        pi = doc.add_paragraph()
        pi.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ri = pi.add_run(line)
        ri.font.size = Pt(11)
        ri.font.color.rgb = RGBColor(0x66,0x66,0x66)
        pi.paragraph_format.space_after = Pt(4)

    doc.add_paragraph()
    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = 'Table Grid'
    easy_n = sum(1 for s in scripts if s.get('difficulty')=='简单版')
    std_n  = sum(1 for s in scripts if s.get('difficulty')=='标准版')
    deep_n = sum(1 for s in scripts if s.get('difficulty')=='深度版')
    for i, (label, bg, desc) in enumerate([
        (f'🟢 简单版 {easy_n}条', 'E8F5E9', '3-4镜头 · 20-30秒'),
        (f'🟠 标准版 {std_n}条',  'FFF3E0', '5镜头 · 30-60秒'),
        (f'🟣 深度版 {deep_n}条', 'EDE7F6', '6-8镜头 · 约1分钟'),
    ]):
        cell = tbl.rows[0].cells[i]
        set_cell_bg(cell, bg)
        pp = cell.paragraphs[0]
        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rl = pp.add_run(f'{label}\n'); rl.font.bold = True; rl.font.size = Pt(10)
        rd = pp.add_run(desc); rd.font.size = Pt(9)
        rd.font.color.rgb = RGBColor(0x55,0x55,0x55)

    doc.add_page_break()

    # 按类型分组
    all_types = []
    seen = set()
    for s in scripts:
        t = s.get('type','其他')
        if t not in seen:
            all_types.append(t)
            seen.add(t)

    for cat in all_types:
        group = [s for s in scripts if s.get('type') == cat]
        if not group:
            continue
        p_cat = doc.add_paragraph()
        p_cat.paragraph_format.space_before = Pt(4)
        p_cat.paragraph_format.space_after  = Pt(10)
        r_cat = p_cat.add_run(f'▌ {cat}（{len(group)}条）')
        r_cat.font.size = Pt(15); r_cat.font.bold = True
        r_cat.font.color.rgb = RGBColor(0xCC,0x33,0x00)
        for s in group:
            _add_script_block(doc, s)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def _add_script_block(doc, s):
    fg_t, bg_hex = difficulty_style(s.get('difficulty','深度版'))
    fg_color = RGBColor(*fg_t)
    shots = s.get('shots', [])

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(4)
    r_n = p.add_run(f'第{s.get("number","")}条  ')
    r_n.font.size = Pt(13); r_n.font.bold = True
    r_n.font.color.rgb = RGBColor(0xCC,0x33,0x00)
    r_t = p.add_run(s.get('title',''))
    r_t.font.size = Pt(13); r_t.font.bold = True

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(5)
    for tag, color in [
        (f'  {s.get("type","")}  ',       RGBColor(0x55,0x55,0x55)),
        (f'  {s.get("difficulty","")}  ',  fg_color),
        (f'  ⏱ {s.get("duration","")}  ', RGBColor(0x77,0x77,0x77)),
        (f'  📷 {len(shots)}个镜头  ',     RGBColor(0x77,0x77,0x77)),
    ]:
        r = p2.add_run(tag); r.font.size = Pt(9); r.font.color.rgb = color

    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdrs = table.rows[0].cells
    for cell, txt in zip(hdrs, ['镜头', '场景描述', '口播内容']):
        set_cell_bg(cell, '1A1A2E')
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = para.add_run(txt)
        r.font.bold = True; r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF,0xFF,0xFF)

    for i, shot in enumerate(shots):
        row = table.add_row()
        c0 = row.cells[0]
        c0.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r0 = c0.paragraphs[0].add_run(f'镜头{i+1}')
        r0.font.size = Pt(10); r0.font.bold = True
        c1 = row.cells[1]
        r1 = c1.paragraphs[0].add_run(shot.get('scene',''))
        r1.font.size = Pt(10); r1.font.italic = True
        r1.font.color.rgb = RGBColor(0x44,0x44,0x44)
        c2 = row.cells[2]
        r2 = c2.paragraphs[0].add_run(shot.get('dialogue',''))
        r2.font.size = Pt(10.5)
        if i % 2 == 1:
            for c in [c0, c1, c2]:
                set_cell_bg(c, 'F9F9F9')

    for row in table.rows:
        row.cells[0].width = Cm(2)
        row.cells[1].width = Cm(6.5)
        row.cells[2].width = Cm(7.5)

    p_tip = doc.add_paragraph()
    p_tip.paragraph_format.space_before = Pt(5)
    p_tip.paragraph_format.space_after  = Pt(12)
    rl = p_tip.add_run('📌 拍摄建议  ')
    rl.font.size = Pt(10); rl.font.bold = True
    rl.font.color.rgb = RGBColor(0xC0,0x5A,0x00)
    rt = p_tip.add_run(s.get('tips',''))
    rt.font.size = Pt(10)
    rt.font.color.rgb = RGBColor(0x44,0x44,0x44)

    pd = doc.add_paragraph()
    pd.add_run('─' * 58).font.size = Pt(7)
    pd.runs[0].font.color.rgb = RGBColor(0xCC,0xCC,0xCC)
    pd.paragraph_format.space_after = Pt(2)
