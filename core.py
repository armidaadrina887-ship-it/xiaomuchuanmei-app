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

# ── 违禁词库（程序级扫描，不依赖AI）────────────────
FORBIDDEN_WORDS = {
    'all': [
        # 极限词
        "唯一", "绝对", "行业第一", "当地第一", "无与伦比", "史上最强",
        "行业领先", "绝对放心", "绝对保证", "最好", "最优质", "最专业",
        "最实惠", "最高端", "最权威", "最正确",
        # 套话
        "专业团队", "匠心", "初心", "情怀", "全程无忧",
        "超高性价比", "良心价格", "值得信赖",
    ],
    'jiazhuang': ["无甲醛", "零甲醛", "无毒", "环保认证"],
    'canyin':    ["纯天然", "无添加", "祖传秘方"],
    'meiiye':    ["根治", "治愈", "无副作用"],
    'jiudian':   [],
    'general':   [],
}

# 禁止开场词（程序级检测，触发自动重写）
FORBIDDEN_OPENING_PATTERNS = [
    "大家好", "你好，我是", "欢迎大家", "今天给大家",
    "欢迎来到", "我来给大家", "今天我来", "我在这里",
]

# 场景禁止出现的人物词（C2/C3规则）
SCENE_FORBIDDEN_PERSONS = [
    "团队成员", "设计师", "员工", "顾客", "客户", "年轻时", "同事",
    "助理", "工人", "师傅们", "我们团队",
]

def scan_forbidden_words(scripts, prompt_file):
    """返回违规列表 [{'script': 条号, 'word': 违禁词}]"""
    industry = prompt_file.replace('.md', '')
    words = FORBIDDEN_WORDS.get('all', []) + FORBIDDEN_WORDS.get(industry, [])
    violations = []
    for s in scripts:
        full_text = s.get('title', '') + s.get('tips', '') + ''.join(
            shot.get('dialogue', '') + shot.get('scene', '')
            for shot in s.get('shots', [])
        )
        for w in words:
            if w in full_text:
                violations.append({'script': s.get('number', '?'), 'word': w})
    return violations

def scan_forbidden_openings(scripts):
    """检测开场套话，返回违规条号列表"""
    violations = []
    for s in scripts:
        shots = s.get('shots', [])
        if not shots:
            continue
        first_line = shots[0].get('dialogue', '')
        first_12 = first_line[:12]
        hit = any(p in first_12 for p in FORBIDDEN_OPENING_PATTERNS)
        # 也检测 "我是老X / 我是小X" 格式
        if not hit and re.match(r'^我是[\u4e00-\u9fff]{1,4}', first_line):
            hit = True
        if hit:
            violations.append(s['number'])
    return violations

def scan_scene_persons(scripts):
    """检测场景描述中出现的禁止人物词，返回违规详情"""
    violations = []
    for s in scripts:
        for i, shot in enumerate(s.get('shots', [])):
            scene = shot.get('scene', '')
            for kw in SCENE_FORBIDDEN_PERSONS:
                if kw in scene:
                    violations.append({
                        'script': s.get('number', '?'),
                        'shot': i + 1,
                        'keyword': kw,
                    })
                    break
    return violations

def extract_city(location_text):
    """从完整地址中只提取城市/商圈名"""
    if not location_text:
        return location_text
    # 去掉路/号/大厦/楼层等详细信息
    clean = re.sub(r'(路|街|道|大道|大街)[\d零一二三四五六七八九十百\s]*号.*', '', location_text)
    clean = re.sub(r'(大厦|广场|中心|楼|层|室|号楼|栋|幢|单元).*', '', clean)
    clean = clean.strip()
    return clean if clean else location_text

# ── 规则包 v2.0（每批5条前重注入，防止规则衰减）───────
RULES_V2 = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【规则包 v2.0 — 本批生成前必须完整读取，每条脚本均适用】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ R1【开场钩子】
⚠️ 程序将在生成完毕后自动扫描所有开场。发现"大家好/我是XX/欢迎/我在这里"等套话，该条自动被退回重写。
第一句必须从以下6个模板选一，填入具体内容后使用：
  模板A【悬念型】：「[具体时间/情境]，有件事我从没在镜头前说过——」
  模板B【冲突型】：「[具体事件]，让我[情绪词]，差点[具体后果]——」
  模板C【数字型】：「[精确数字]+[反常识结论]——」
  模板D【提问型】：「[做某件具体事]之前，你知道[具体问题]吗？」
  模板E【身份型】：仅限第1、2条。「[一个具体经历]——我叫[称呼]，做[行业]X年了。」
  模板F【场景型】：「[具体可感知的场景细节]，我发现了一件事——」
  自检标准：①首句≤20字 ②读出来自然 ③听完想继续。不达标换模板。

■ R2【出镜限制】只有主理人一人出镜。场景描述禁止出现团队/设计师/员工/顾客出镜（程序会扫描场景描述关键词）。客户故事只在口播中说，镜头只拍主理人。

■ R3【场景可执行】限门店/工作室内部。一部手机可完成为标准。不得要求：无人机/轨道推车/多机位/专业打光/数控设备界面特写。

■ R4【回忆处理】涉及过去的场景只通过主理人口播讲述。不得要求镜头还原历史/回忆画面。正确写法：「主理人站在工作室，讲述过去的经历，镜头对着他」

■ R5【口语化】每句口播≤25字，超过必须拆成两句。禁止书面排比句。读出来超过3秒的单句必须断句。

■ R6【违禁词】全行业禁：无与伦比/史上最强/行业领先/行业第一/专业团队/匠心/初心。
  建材额外禁：无甲醛/零甲醛/无毒。食品额外禁：纯天然/无添加/祖传秘方。
  医疗额外禁：根治/治愈/无副作用。教育额外禁：保过/保分/承诺成绩。

■ R7【结尾引导】禁套话：等你/理想家园/一起打造/欢迎关注/我在这里等你。
  结尾必须是：①与本条内容强关联的互动问句 ②轻量行动引导（私信/评论） ③无引导自然收尾。

■ R8【地址】禁止完整街道/门牌号/楼层号。只允许城市名或知名商圈名。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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

# ── 自动重写：开场套话 + 违禁词（批量一次调用）────────
def rewrite_violations(scripts, violation_numbers, system_prompt, api_key, client_name):
    """对有开场套话或违禁词的脚本，批量重写违规部分"""
    if not violation_numbers:
        return scripts
    violating = [s for s in scripts if s.get('number') in violation_numbers]
    if not violating:
        return scripts

    api_client = openai.OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
    rewrite_msg = f"""以下脚本的第一句口播有套话，请根据脚本本身的内容重写第一句，使其有吸引力。

主理人称呼：{client_name}

需要修正的脚本：
{json.dumps(violating, ensure_ascii=False, indent=2)}

修正要求：
1. 只修改每条脚本 shots[0].dialogue（第一个镜头的口播）
2. 新的第一句必须根据该条脚本的具体内容来写，直接切入事件/数字/冲突/悬念
   - 禁止大家好/我是XX/欢迎/今天给大家等开头
   - 禁止使用"[填入]""[具体X]"这类占位符，必须写出实际内容
   - 字数控制在20字以内
   - 参考这条脚本的标题和其他镜头内容来创作开场句
3. 如有违禁词（唯一/绝对/匠心/行业第一等），替换为具体描述
4. 其他所有字段保持不变
5. 输出格式：JSON数组，包含所有修正后的脚本（字段与输入完全一致）
直接输出JSON数组，不要其他文字，不要markdown代码块。"""

    full_text = ""
    try:
        stream = api_client.chat.completions.create(
            model="moonshot-v1-128k",
            max_tokens=8000,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": rewrite_msg},
            ],
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_text += delta
    except Exception:
        return scripts  # 重写失败则保留原文

    rewritten = extract_json_list(full_text)
    if rewritten:
        rewritten_map = {s.get('number'): s for s in rewritten}
        return [rewritten_map.get(s['number'], s) for s in scripts]
    return scripts

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
    location = extract_city(get_field(fields, '城市名字', '地点', '城市'))
    shop_pos = extract_city(get_field(fields, '店铺位置', '位置'))
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
        msg += "内容角度覆盖：故事型（人设/创业故事）、产品型（核心产品卖点）、幕后型（制作/工艺/流程）、痛点型（行业痛点/避坑）、互动型（互动问答/投票）、氛围型（场景/日常/感受），30条角度完全不同。\n"
        msg += "分布：第1条和第2条必须是故事型（人设介绍），故事型≥6条，产品型≥5条，幕后型≥5条，痛点型≥5条，互动型≥5条，氛围型≥4条。\n"
        type_hint = "type只能是：故事型、产品型、幕后型、痛点型、互动型、氛围型"

    msg += "\n" + type_hint

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
    v2.0 三层防崩架构：大纲 → 6批×5条（每批重注入规则）→ 违禁词扫描
    progress_callback(pct, message) 用于向UI汇报进度，可选。
    """
    api_client = openai.OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
    system_prompt = load_prompt(client['prompt_file'])
    base_msg = client['user_message']

    def kimi_call(user_msg, max_tokens=8000):
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

    # ── 阶段一：生成30条选题大纲 ─────────────────────
    if progress_callback:
        progress_callback(0.05, "阶段一：正在生成30条选题大纲...")

    outline_msg = base_msg + """

生成30条选题大纲，严格遵守：
- 第1条和第2条必须是故事型（人设介绍，写清楚讲哪个具体经历）
- 分布：故事型≥6条、产品型≥5条、幕后型≥5条、痛点型≥5条、互动型≥5条、氛围型≥4条
- 30条核心角度完全不同，不得有两条讲同一件具体事件
- 标题要说清楚讲什么具体事件，不能是泛泛概念
输出格式（JSON数组，不要其他文字）：
[{"number":1,"type":"故事型","title":"说清楚讲哪个具体事件的标题"},...]"""

    raw_outline = kimi_call(outline_msg, max_tokens=3000)
    outline = extract_json_list(raw_outline)

    outline_text = ""
    if outline:
        outline_text = "\n\n【已确定30条选题大纲】\n" + "\n".join(
            f"{o.get('number', i+1):02d}. [{o.get('type','')}] {o.get('title','')}"
            for i, o in enumerate(outline)
        )

    # ── 阶段二：6批×5条，每批重注入规则包 ────────────
    all_scripts = []

    for batch_idx in range(6):
        batch_start = batch_idx * 5 + 1
        batch_end   = batch_start + 4
        progress    = 0.1 + batch_idx * 0.13

        if progress_callback:
            progress_callback(progress, f"阶段二：正在生成第{batch_start}–{batch_end}条（批次{batch_idx+1}/6）...")

        # 防重复摘要：把已生成条目的标题+开场第一句传给下一批
        anti_repeat = ""
        if all_scripts:
            anti_repeat = "\n\n【防重复 — 以下条目已生成，本批禁止重复其核心事件或开场句式】\n" + "\n".join(
                "第{}条: [{}] {} | 开场: {}".format(
                    s['number'], s.get('type', ''),
                    s.get('title', ''),
                    (s.get('shots') or [{}])[0].get('dialogue', '')[:20]
                )
                for s in all_scripts
            )

        # 本批大纲条目
        batch_outline = ""
        if outline:
            batch_items = outline[batch_idx * 5: (batch_idx + 1) * 5]
            batch_outline = "\n\n【本批大纲（第{}-{}条）】\n".format(batch_start, batch_end) + "\n".join(
                "{:02d}. [{}] {}".format(
                    o.get('number', batch_start + i), o.get('type', ''), o.get('title', '')
                )
                for i, o in enumerate(batch_items)
            )

        batch_msg = (
            base_msg
            + outline_text
            + anti_repeat
            + RULES_V2          # 每批重注入完整规则包
            + batch_outline
            + f"""

现在生成第{batch_start}条到第{batch_end}条完整分镜脚本（共5条）。
严格按大纲标题和类型，每条6-8个镜头，口播约1分钟。
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
    "tips": "拍摄建议（门店内/手机可拍）"
  }},
  ...共5条
]"""
        )

        raw = kimi_call(batch_msg, max_tokens=8000)
        parsed = extract_json_list(raw)
        if parsed:
            for i, s in enumerate(parsed):
                s['number'] = batch_start + i
                if 'difficulty' not in s:
                    s['difficulty'] = '深度版'
            all_scripts.extend(parsed)

    # ── 阶段三：程序级扫描 ─────────────────────────────
    opening_violations = scan_forbidden_openings(all_scripts)
    word_violations    = scan_forbidden_words(all_scripts, client['prompt_file'])
    scene_violations   = scan_scene_persons(all_scripts)

    # 合并需要重写的条号
    rewrite_numbers = set(opening_violations) | {v['script'] for v in word_violations}

    # 触发自动重写（开场套话 + 违禁词）
    if rewrite_numbers:
        if progress_callback:
            progress_callback(0.88, f"⚠️ 发现{len(rewrite_numbers)}条违规，正在自动重写...")
        all_scripts = rewrite_violations(
            all_scripts, rewrite_numbers,
            system_prompt, api_key, client['name']
        )
        # 重写后重新扫描一次
        opening_violations = scan_forbidden_openings(all_scripts)
        word_violations    = scan_forbidden_words(all_scripts, client['prompt_file'])

    if progress_callback:
        progress_callback(0.95, f"生成完成，共{len(all_scripts)}条，正在制作Word...")

    # 把违规信息附加到 client，供 streamlit 显示
    client['violations']       = word_violations
    client['scene_violations'] = scene_violations
    client['opening_violations_remaining'] = opening_violations
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
