#!/usr/bin/env python3
"""Build the Class-section route UI structure workbook for design handoff."""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.page import PageMargins

OUT = "/workspace/docs/ui/设计结构呈现.xlsx"

# --- palette ---
NAVY = "1B2A4A"
NAVY2 = "243A6B"
WHITE = "FFFFFF"
INK = "1F2937"
MUTED = "5B6475"
LINE = "D9DEE8"
ORANGE = "E8791A"
ORANGE_SOFT = "FFF1E4"
BLUE = "2878D0"
BLUE_SOFT = "E8F2FC"
GREEN = "0E9F6E"
GREEN_SOFT = "E6F7F0"
GOLD = "C9A227"
GOLD_SOFT = "FFF6D6"
PURPLE = "5B5BD6"
PURPLE_SOFT = "EEEDFB"
PINK = "C2417D"
VIOLET = "7C3AED"
GREY = "F4F6FA"
GREY2 = "E5E9F0"
LOCK = "9AA3B2"

LEVEL_FILL = {
    "Level 1": "5B5BD6",
    "Level 2": "2878D0",
    "Level 3": "0E9F6E",
    "Level 4": "E8791A",
    "Level 5": "C9A227",
    "Level 6": "7C3AED",
}

thin = Border(
    left=Side(style="thin", color=LINE),
    right=Side(style="thin", color=LINE),
    top=Side(style="thin", color=LINE),
    bottom=Side(style="thin", color=LINE),
)


def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)


def font(size=11, bold=False, color=INK, name="Calibri"):
    return Font(name=name, size=size, bold=bold, color=color)


def align(h="left", v="center", wrap=True):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)


def header_cell(ws, row, col, text, bg=NAVY, fg=WHITE, size=11):
    c = ws.cell(row, col, text)
    c.fill = fill(bg)
    c.font = font(size, True, fg)
    c.alignment = align("center", "center", True)
    c.border = thin
    return c


def text_cell(ws, row, col, text, bg=None, fg=INK, bold=False, h="left", size=11):
    c = ws.cell(row, col, text)
    c.font = font(size, bold, fg)
    c.alignment = align(h, "center", True)
    c.border = thin
    if bg:
        c.fill = fill(bg)
    return c


def set_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def paint_header_row(ws, row, headers, bg=NAVY):
    for i, h in enumerate(headers, 1):
        header_cell(ws, row, i, h, bg=bg)
    ws.row_dimensions[row].height = 32


def title_block(ws, title_en, title_zh, subtitle, cols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=cols)
    c = ws.cell(1, 1, f"{title_en}  ·  {title_zh}")
    c.fill = fill(NAVY)
    c.font = font(18, True, WHITE)
    c.alignment = align("left", "center", True)
    ws.row_dimensions[1].height = 28
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=cols)
    c2 = ws.cell(2, 1, subtitle)
    c2.fill = fill(NAVY2)
    c2.font = font(11, False, "D6DEEE")
    c2.alignment = align("left", "center", True)
    ws.row_dimensions[2].height = 36
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins = PageMargins(0.4, 0.4, 0.5, 0.5)
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:3"
    ws.sheet_view.zoomScale = 110


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

LESSON_TYPES = [
    # zh, en, kid_tag_zh, kid_tag_en, color_hex, design_note
    ("词汇课", "Vocabulary Lesson", "单词", "Words", "5B5BD6", "Word teaching + practice. Hero art should show the unit topic, not a generic classroom."),
    ("句型课", "Sentence Pattern Lesson", "句子", "Sentences", "2878D0", "Pattern frames (This is… / I can…). Keep sentence preview on the lesson card."),
    ("主题阅读课", "Themed Reading Lesson", "阅读", "Reading", "0E9F6E", "Story/theme reading. Route is the same 9 steps; Teaching node may open a story video."),
    ("字母课", "Alphabet Lesson", "字母", "ABC", "E8791A", "Letter recognition. Preview can be a letter hunt."),
    ("拼读阅读课", "Phonics Reading Lesson", "拼读", "Phonics", "C9A227", "Decode + read. Listening node is extra important after class."),
    ("自拼课", "Independent Phonics Lesson", "自拼", "Blend", "C9A227", "Level 2 independent blending. Same 9-step route."),
    ("语法阅读课", "Grammar Reading Lesson", "语法阅读", "Grammar Read", "0E9F6E", "Grammar inside a reading. Summary node recaps the rule in kid language."),
    ("词句听说课", "Words & Sentences (Listen & Speak)", "听说", "Hear & Speak", "E8791A", "Current screenshot tag 'Hear of' is incorrect English. Use Hear & Speak / 听说."),
    ("阅读基础课", "Reading Foundations Lesson", "阅读基础", "Read Basics", "0E9F6E", "Foundational reading skills. Keep icons simple."),
    ("语法课", "Grammar Lesson", "语法", "Grammar", "2878D0", "Explicit grammar. Teaching node is the class; Practice is drills."),
    ("篇章阅读课", "Passage Reading Lesson", "篇章", "Passage", "0E9F6E", "Longer text. After-class Listening can replay the passage audio."),
    ("写作课", "Writing Lesson", "写作", "Writing", "C2417D", "Writing output. Award can celebrate the written piece."),
    ("语言筑基课", "Language Foundations Lesson", "筑基", "Foundations", "7C3AED", "Level 5–6 foundation block. Same 9-step route."),
    ("复习测评课", "Review & Assessment Lesson", "测评", "Review Quiz", "1B2A4A", "Still uses the same 9 steps. Teaching may be a recap video; Practice is the quiz; Report is the test report."),
]

CATALOG = [
    ("Level 1", "Lesson 1", "L1", "词汇课"),
    ("Level 1", "Lesson 2", "L2", "句型课"),
    ("Level 1", "Lesson 3", "L3", "主题阅读课"),
    ("Level 1", "Lesson 4", "L4", "字母课"),
    ("Level 1", "Lesson 5", "L5", "拼读阅读课"),
    ("Level 1", "Lesson 6", "L6", "复习测评课"),
    ("Level 2", "Lesson 1", "L1", "词汇课"),
    ("Level 2", "Lesson 2", "L2", "句型课"),
    ("Level 2", "Lesson 3", "L3", "自拼课"),
    ("Level 2", "Lesson 4", "L4", "拼读阅读课"),
    ("Level 2", "Lesson 5", "L5", "语法阅读课"),
    ("Level 2", "Lesson 6", "L6", "复习测评课"),
    ("Level 3", "Lesson 1", "L1", "词句听说课"),
    ("Level 3", "Lesson 2", "L2", "词句听说课"),
    ("Level 3", "Lesson 3", "L3", "词句听说课"),
    ("Level 3", "Lesson 4", "L4", "阅读基础课"),
    ("Level 3", "Lesson 5", "L5", "语法课"),
    ("Level 3", "Lesson 6", "L6", "复习测评课"),
    ("Level 4", "Lesson 1", "L1", "词句听说课"),
    ("Level 4", "Lesson 2", "L2", "篇章阅读课"),
    ("Level 4", "Lesson 3", "L3", "词句听说课"),
    ("Level 4", "Lesson 4", "L4", "篇章阅读课"),
    ("Level 4", "Lesson 5", "L5", "阅读基础课"),
    ("Level 4", "Lesson 6", "L6", "复习测评课"),
    ("Level 4", "Lesson 7", "L7", "词句听说课"),
    ("Level 4", "Lesson 8", "L8", "篇章阅读课"),
    ("Level 4", "Lesson 9", "L9", "词句听说课"),
    ("Level 4", "Lesson 10", "L10", "篇章阅读课"),
    ("Level 4", "Lesson 11", "L11", "写作课"),
    ("Level 4", "Lesson 12", "L12", "复习测评课"),
    ("Level 5", "U1L1", "U1L1", "词句听说课"),
    ("Level 5", "U1L2", "U1L2", "篇章阅读课"),
    ("Level 5", "U1L3", "U1L3", "词句听说课"),
    ("Level 5", "U1L4", "U1L4", "篇章阅读课"),
    ("Level 5", "U1L5", "U1L5", "语言筑基课"),
    ("Level 5", "U1L6", "U1L6", "复习测评课"),
    ("Level 5", "U1L7", "U1L7", "词句听说课"),
    ("Level 5", "U1L8", "U1L8", "篇章阅读课"),
    ("Level 5", "U1L9", "U1L9", "词句听说课"),
    ("Level 5", "U1L10", "U1L10", "篇章阅读课"),
    ("Level 5", "U1L11", "U1L11", "写作课"),
    ("Level 5", "U1L12", "U1L12", "复习测评课"),
    ("Level 6", "U1L1", "U1L1", "词句听说课"),
    ("Level 6", "U1L2", "U1L2", "篇章阅读课"),
    ("Level 6", "U1L3", "U1L3", "词句听说课"),
    ("Level 6", "U1L4", "U1L4", "篇章阅读课"),
    ("Level 6", "U1L5", "U1L5", "语言筑基课"),
    ("Level 6", "U1L6", "U1L6", "复习测评课"),
    ("Level 6", "U1L7", "U1L7", "词句听说课"),
    ("Level 6", "U1L8", "U1L8", "篇章阅读课"),
    ("Level 6", "U1L9", "U1L9", "词句听说课"),
    ("Level 6", "U1L10", "U1L10", "篇章阅读课"),
    ("Level 6", "U1L11", "U1L11", "写作课"),
    ("Level 6", "U1L12", "U1L12", "复习测评课"),
]

TYPE_EN = {r[0]: r[1] for r in LESSON_TYPES}
TYPE_TAG_ZH = {r[0]: r[2] for r in LESSON_TYPES}
TYPE_TAG_EN = {r[0]: r[3] for r in LESSON_TYPES}

ROUTE_STEPS = [
    # id, phase, order, zh, en, kid_zh, kid_en, icon, cta_zh, cta_en, meaning_zh, meaning_en, design
    (
        "S1",
        "in_class",
        1,
        "预习",
        "Preview",
        "先看看",
        "Peek first",
        "Binoculars / sparkle-book / eye",
        "去预习",
        "Start Preview",
        "课前热身：看图、听一听、猜一猜本课会遇见谁。降低上课焦虑。",
        "Pre-class warm look: pictures, a tiny listen, guess who we will meet. Lowers anxiety before class.",
        "First node on the in-class path. Feels like opening a gate. Small, inviting, not a test.",
    ),
    (
        "S2",
        "in_class",
        2,
        "教学",
        "Teaching",
        "上课",
        "Class time",
        "Teacher character / blackboard / play-video",
        "去上课",
        "Go to Class",
        "正式上课：AI 老师带着孩子学单词/句型/阅读。这是主课入口。",
        "Live class with the AI teacher. Main lesson entry. This is today's 'go to class' moment.",
        "Hero node. Slightly larger than others even when not current. Matches original orange 去上课 CTA.",
    ),
    (
        "S3",
        "in_class",
        3,
        "练习",
        "Practice",
        "练一练",
        "Try it",
        "Target / bullseye (keep from current UI)",
        "去练习",
        "Practice Now",
        "当堂操练刚学的词句。可反复进入直到过关。",
        "In-class drills on the new words/sentences. Replayable until passed.",
        "This is the ONLY in-class step shown in the old chip bar. Do not let it steal the whole route.",
    ),
    (
        "S4",
        "in_class",
        4,
        "总结",
        "Summary",
        "回顾",
        "Wrap up",
        "Star notebook / checklist / sparkle recap",
        "看总结",
        "See Summary",
        "用孩子能懂的方式回顾本课学会了什么。短、暖、有画面。",
        "Kid-friendly recap of what we learned. Short, warm, visual.",
        "Bridge into the award. Should feel like closing the story, not a report card.",
    ),
    (
        "S5",
        "in_class",
        5,
        "领奖",
        "Award",
        "领奖",
        "Prize",
        "Treasure chest / medal / gift / stars bursting",
        "领奖",
        "Claim Prize",
        "课中终点仪式：星星、贴纸、胸章。让孩子感到这条路走完了一段。",
        "In-class finish ritual: stars, sticker, badge. The path must celebrate before after-class work starts.",
        "Landmark / chest on the path. Bounce if unclaimed. Separates in-class from after-class.",
    ),
    (
        "S6",
        "after_class",
        6,
        "复习",
        "Review",
        "再练练",
        "Replay",
        "Replay arrows / flashcards / memory cards",
        "去复习",
        "Review Now",
        "课后巩固：隔一段时间再碰本课内容，抗遗忘。",
        "Spaced recap after class so the lesson sticks.",
        "First node of the after-class path. Visually a new 'chapter' after the award chest.",
    ),
    (
        "S7",
        "after_class",
        7,
        "口语",
        "Speaking",
        "开口说",
        "Say it",
        "Microphone (keep from current UI)",
        "去开口",
        "Start Speaking",
        "开口输出：跟读、回答、角色扮演。需要麦克风权限提示。",
        "Oral output: repeat, answer, role-play. Needs mic permission UX.",
        "Keep the mic icon. Current UI already uses this.",
    ),
    (
        "S8",
        "after_class",
        8,
        "听力",
        "Listening",
        "听一听",
        "Listen",
        "Headphones (keep from current UI)",
        "去听",
        "Start Listening",
        "听力输入：听课文/对话/题。可配进度条。",
        "Listening input: passage, dialogue, or quiz audio.",
        "Keep the headphone icon. Current UI already uses this.",
    ),
    (
        "S9",
        "after_class",
        9,
        "报告",
        "Report",
        "小报告",
        "My report",
        "Bar chart / report card / star sheet (keep from current UI)",
        "看报告",
        "View Report",
        "本课终点：给孩子和家长看本课星星、开口次数、掌握词句。",
        "Lesson destination: stars, speaking count, words/sentences mastered. Kid view first, parent detail second.",
        "End landmark of the lesson path. After this, the week path can walk to the next lesson station.",
    ),
]


def build_readme(wb):
    ws = wb.active
    ws.title = "00_ReadMe"
    cols = 4
    title_block(
        ws,
        "Class Route — Design Structure",
        "上课路线 · 设计结构呈现",
        "Hand-off for design. Every essential element on the kids' learning path, bilingual, layered. 给设计同学的图层与必出元素清单（中英）。",
        cols,
    )
    set_widths(ws, [28, 52, 52, 36])

    headers = ["Topic 主题", "English", "中文", "For designers 设计怎么用"]
    paint_header_row(ws, 3, headers)

    rows = [
        (
            "What this file is",
            "The Class tab must feel like a clear journey kids can walk with us — not a cramped toolbar of 4 chips. This workbook lists every layer and every element that must appear on that route, plus copy in English and Chinese.",
            "上课 Tab 要有「一条能跟着走的路」，而不是底部挤着 4 个小标签。本表列出路线上每一层、每一个必出元素，以及中英对照文案，方便设计出图。",
            "Start with 01_Screen_Layers, then 02_Route_Must_Have. Do not invent extra steps.",
        ),
        (
            "Why we are changing it",
            "Current Weekly Study Plan card (original screenshot) only shows Practice / Speaking / Listening / Report in a horizontal pill. Kids cannot see where they came from or where they go next. Preview, Teaching, Summary, Award, Review are missing.",
            "现有「本周学习计划」卡片底部只有 练习-口语-听力-报告 四个横条。孩子看不到从哪来、到哪去。预习、教学、总结、领奖、复习都没有出现在路线上。",
            "Keep the 3D art, teacher, lesson card, profile switcher, and tab bar. Rebuild the route.",
        ),
        (
            "Reference video",
            "Target feeling: a followable path / map journey (Lark clip Lark20260825-162130.mp4). Winding road, stations, character walks with the kid, current node is obvious, next node is visible. Not a chip bar.",
            "目标感觉：可跟随的路线/地图（飞书视频 Lark20260825-162130.mp4）。弯道、站点、角色陪孩子走、当前点足够大、下一步看得见。不要做成标签条。",
            "Match motion + path metaphor from the video. Match our existing 3D characters and warm farm/ocean art from the screenshot.",
        ),
        (
            "Route law (do not break)",
            "INSIDE every lesson: Preview → Teaching → Practice → Summary → Award. AFTER every lesson: Review → Speaking → Listening → Report. Same 9 steps for every lesson type in the catalog (vocab, phonics, reading, writing, assessment…).",
            "每节课课中固定：预习 → 教学 → 练习 → 总结 → 领奖。每节课课后固定：复习 → 口语 → 听力 → 报告。课表里所有课型都走同一条 9 步路线。",
            "You may restyle nodes by lesson type color, but never drop, reorder, or rename the 9 steps.",
        ),
        (
            "Two scales of route",
            "MACRO = the week: Lesson 1 station → Lesson 2 → … MICRO = inside the current lesson: the 9 steps. Kids always know (1) which lesson they are on this week, (2) which step they are on in that lesson.",
            "大路线 = 本周：第1课站点 → 第2课 → … 小路线 = 当前课内部的 9 步。孩子随时知道（1）这周上到哪一课，（2）这一课走到哪一步。",
            "Only the CURRENT lesson expands the 9-step path. Other lessons stay as stations on the week map.",
        ),
        (
            "How to read the sheets",
            "00 ReadMe · 01 z-order layers · 02 must-have elements on the route · 03 the 9 steps · 04 node states · 05 full Class page inventory · 06 original lesson catalog + EN · 07 lesson-type dictionary · 08 all UI copy EN/ZH · 09 current vs target.",
            "00 说明 · 01 图层顺序 · 02 路线必出元素 · 03 九步定义 · 04 节点状态 · 05 上课页全量元件 · 06 原课表+英文 · 07 课型词典 · 08 全部文案中英 · 09 现状对照目标。",
            "Required = Must draw. Recommended = should draw if it helps the path feel. Never hide Required behind a hover on a kids app.",
        ),
        (
            "Audience",
            "Kids 4–12 walk the path. Parents may glance at Weekly Study Plan. Design for the child's finger and eyes first. Labels stay visible; do not rely on color-only or icon-only.",
            "4–12 岁孩子走这条路。家长会扫一眼「本周学习计划」。先为孩子的手指和眼睛设计。标签要常驻，不能只靠颜色或只靠图标。",
            "Min tap 44×44 pt. Current node larger. Traveler character stands on the current node.",
        ),
        (
            "i18n rule",
            "Every kid-facing string has English + 中文. Default ship language can stay Chinese; layout must not break when English is longer. Keep kid labels to 1–2 words.",
            "所有孩子能看见的字都要有英文+中文。默认可先中文上线，但英文变长时版式不能挤爆。孩子标签控制在 1–2 个词。",
            "Use the Copy_i18n sheet as source of truth. Do not invent extra marketing words on nodes.",
        ),
        (
            "Out of scope",
            "This file does not specify Chat / Explore / Play interiors, lesson engine prompts, or backend APIs. It specifies what must appear on Class so the route is readable.",
            "本文件不规定 Chat / Explore / Play 内页、上课引擎 prompt、或后端接口。只规定 Class 上必须出现什么，好让路线可读。",
            "If a new element fights the path (banners, coupons, extra badges), park it off the route.",
        ),
    ]
    for i, row in enumerate(rows):
        r = 4 + i
        bg = WHITE if i % 2 == 0 else GREY
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.row_dimensions[r].height = 78
        ws.cell(r, 1).font = font(12, True, NAVY)

    # legend
    r = 14
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    header_cell(ws, r, 1, "Color legend used across this file  ·  本文件配色图例", bg=NAVY2)
    legends = [
        (ORANGE, ORANGE_SOFT, "In-class path 课中路线  预习-教学-练习-总结-领奖"),
        (BLUE, BLUE_SOFT, "After-class path 课后路线  复习-口语-听力-报告"),
        (GOLD, GOLD_SOFT, "Award / destination landmarks 领奖与终点"),
        (GREEN, GREEN_SOFT, "Completed / required 已完成 / 必出"),
        (LOCK, GREY2, "Locked / upcoming 未解锁 / 未到达"),
        (PINK, "FCE8F2", "Writing lesson type 写作课"),
        (PURPLE, PURPLE_SOFT, "Level 1 / Hear & Speak accents"),
    ]
    for i, (fg, bg, label) in enumerate(legends):
        rr = 15 + i
        text_cell(ws, rr, 1, "", bg=fg)
        ws.merge_cells(start_row=rr, start_column=2, end_row=rr, end_column=4)
        text_cell(ws, rr, 2, label, bg=bg, bold=True)
        ws.row_dimensions[rr].height = 22

    ws.auto_filter.ref = "A3:D12"
    ws.freeze_panes = "A4"


def build_layers(wb):
    ws = wb.create_sheet("01_Screen_Layers")
    cols = 8
    title_block(
        ws,
        "Screen layers (back → front)",
        "页面图层（从底到顶）",
        "Figma / PS layer order for Class → Weekly Study Plan. Designers should build the file in this stack. 上课-本周学习计划的图层顺序，请按此叠文件。",
        cols,
    )
    headers = [
        "Layer # 图层",
        "Layer name EN",
        "图层名 中文",
        "Z-order 叠放",
        "Contains 包含什么",
        "Motion / behavior 动效",
        "Must keep from current UI? 现有界面要保留吗",
        "Design notes 设计备注",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [16, 28, 22, 14, 48, 36, 28, 42])

    layers = [
        (
            "L00",
            "Scene background",
            "场景底图",
            "Back",
            "Full-bleed 3D environment matching the current lesson theme (farm, ocean, city…). Soft sky + ground so the path can sit on it.",
            "Slow parallax / idle breeze. Does not steal taps.",
            "Yes — keep the 3D world quality from the screenshot.",
            "The path must read on top of busy art. Add a slight ground shadow under the road.",
        ),
        (
            "L01",
            "Ambient props",
            "氛围小物件",
            "Back+",
            "Non-interactive friends: animals, trees, clouds, bubbles. They decorate the journey.",
            "Tiny idle loops (chick peck, cloud drift). Never cover a node.",
            "Yes — farm animals in the Farm Animals example.",
            "Props stay OFF the tappable path. Safe margin 8–12 pt around every node.",
        ),
        (
            "L02",
            "Week map road (macro path)",
            "本周大路线（课与课之间）",
            "Mid-back",
            "The road / trail that connects this week's lesson stations: L1 → L2 → L3… Solid behind, dashed or dim ahead.",
            "Fill animates when a lesson is cleared. Camera can ease to the current station.",
            "New — old UI had no week path, only one card.",
            "This is the 'follow us' feeling at week scale. One visible road, not a list of cards only.",
        ),
        (
            "L03",
            "Lesson stations",
            "课程站点",
            "Mid",
            "One station per lesson this week. Completed = stamp/star. Current = expanded. Locked = grey + lock. Shows lesson type color chip.",
            "Current station gently breathes. Locked stations do not bounce.",
            "Partial — we had one big card, not a chain of stations.",
            "Station must show: type tag, lesson number, title. Tapping a completed station can replay; tapping locked shows 'finish the one before'.",
        ),
        (
            "L04",
            "In-lesson micro path",
            "课内小路线（9 步）",
            "Mid",
            "The 9-step trail attached to the CURRENT lesson only: 5 in-class + 4 after-class. Connecting line + nodes.",
            "Line draws from last completed to current. Character walks along it.",
            "Replace the old 4-chip bar.",
            "Must group visually: 课中 cluster vs 课后 cluster, with Award as the gate between them.",
        ),
        (
            "L05",
            "Path connectors & progress fill",
            "路线连接线与进度填充",
            "Mid",
            "Segment between each pair of nodes. Done = bright/solid. Current = glowing. Locked = dotted/grey.",
            "A short 'paint the road' tween when a step completes (like the reference video).",
            "New.",
            "Kids read the LINE as much as the ICONS. Make completed vs remaining obvious in greyscale too.",
        ),
        (
            "L06",
            "Step nodes",
            "步骤节点",
            "Mid-front",
            "The 9 circular (or stamp-like) stations: icon + bilingual label + state badge.",
            "Current node scales up ~1.15–1.3×. Claimable Award / Report may bounce.",
            "Improve — old nodes had no Preview/Teaching/Summary/Award/Review.",
            "Always show the label. Icon-only fails for young kids and for i18n.",
        ),
        (
            "L07",
            "State badges on nodes",
            "节点状态角标",
            "Front-",
            "Checkmark, lock, star, 'new', progress pie, chest-closed / chest-open.",
            "Check pops in. Lock shakes once if tapped early.",
            "New (old UI only highlighted Practice).",
            "Do not cover the icon. Badge sits at 4–5 o'clock of the node.",
        ),
        (
            "L08",
            "Traveler / You-are-here",
            "旅人 / 你在这里",
            "Front",
            "The child's avatar (or teacher + child) standing on the current node. This is how kids 'follow the path with us'.",
            "Idle bounce. Walk-tween to the next node on complete. Faces the next step.",
            "Partial — teacher stood LEFT of the card, not ON the route.",
            "Use the current-profile avatar from the header so the kid recognizes themselves. Teacher can stand beside, pointing forward.",
        ),
        (
            "L09",
            "Current-step CTA",
            "当前步主按钮",
            "Front",
            "One primary pill attached to the current node (not a floating bar that fights the path). Icon + verb + lesson nickname.",
            "Pulse on first land. Sticky if the path scrolls.",
            "Yes — keep 去上课 energy, but glue it to the Teaching (or current) node.",
            "Never truncate the lesson name into 'Farm Anim…' if we can use two lines. CTA copy comes from the current step (see 03_Route_Steps).",
        ),
        (
            "L10",
            "Lesson hero info",
            "课程主卡片信息",
            "Front",
            "Type tag, Lesson n, Level · Unit, title, duration, status, Words, Sentences. Sits above or as the current station's 'signboard'.",
            "Status chip can shimmer when In progress.",
            "Yes — keep all of these from the screenshot.",
            "Fix 'Hear of' → Hear & Speak / 听说. Keep Words + Sentences so parents and kids know the destination of this path.",
        ),
        (
            "L11",
            "Header HUD",
            "顶部信息条",
            "Front+",
            "Child avatar, sibling switcher (multi-profile), screen title Weekly Study Plan, More lessons entry (submarine thumb in current UI).",
            "Switcher opens a kid-safe picker.",
            "Yes — keep.",
            "Title bilingual. More lessons must not jump kids off the path without a back affordance.",
        ),
        (
            "L12",
            "Bottom tab bar",
            "底部导航",
            "Front+",
            "Chat · Class (selected) · Explore · Play. Class has the yellow glow + book/star from current UI.",
            "Selection glow only. Do not animate every tab.",
            "Yes — keep icons and selected treatment.",
            "The route lives IN Class. Tabs are not part of the lesson path.",
        ),
        (
            "L13",
            "Overlays & celebrations",
            "弹层与庆祝",
            "Top",
            "Lock toast, mic permission, reward chest open, report sheet, parent report peek, error/offline.",
            "Chest-open is the biggest celebration. Do not block the path for more than a beat after claim.",
            "New / expand.",
            "After Award claim, auto-pan to the after-class path so kids see Review is next — that is the 'route is clear' moment.",
        ),
    ]
    for i, row in enumerate(layers):
        r = 4 + i
        bg = GREY if i % 2 else WHITE
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.row_dimensions[r].height = 64
        ws.cell(r, 1).font = font(12, True, WHITE)
        ws.cell(r, 1).fill = fill(NAVY)
        ws.cell(r, 1).alignment = align("center", "center")
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:H{3+len(layers)}"


def build_must_have(wb):
    ws = wb.create_sheet("02_Route_Must_Have")
    cols = 12
    title_block(
        ws,
        "Essential elements ON the route",
        "路线上必须出现的元素",
        "If an element is Required, it must exist in the design. This is the checklist to send designers. 标了 Required 的必须画出来。本表就是给设计的清单。",
        cols,
    )
    headers = [
        "ID",
        "Layer 图层",
        "Module EN",
        "模块 中文",
        "Element EN",
        "元素 中文",
        "Kid copy EN",
        "孩子文案 中文",
        "Icon / visual",
        "Priority 优先级",
        "When it appears 何时出现",
        "Design notes 设计说明",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [10, 14, 22, 18, 28, 22, 20, 16, 28, 14, 32, 44])

    items = [
        # PATH CORE
        ("R01", "L02", "Week path", "本周大路线", "Week road / trail", "本周道路", "This week's path", "本周路线", "Winding ground trail, 3D, readable on busy art", "Required 必出", "Always on Class weekly plan", "One continuous road connecting this week's lessons. Filled behind the current lesson, dim ahead. This is the 'follow us' metaphor at week scale."),
        ("R02", "L03", "Week path", "本周大路线", "Lesson station (one per lesson)", "课程站点（每课一个）", "Lesson 3", "第 3 课", "Colored pad / island with type chip", "Required 必出", "One for every lesson in the current week", "Station shows type tag + lesson number + short title. Current station is expanded and hosts the 9-step micro path."),
        ("R03", "L03", "Week path", "本周大路线", "Week progress marker", "本周进度", "3 / 6 lessons", "3 / 6 课", "Tiny dots or flag at the end of the week", "Required 必出", "Always", "Kids and parents must see how far the week has been walked. Place near title or at the end of the week road."),
        ("R04", "L03", "Week path", "本周大路线", "Next-lesson lock gate", "下一课关卡", "Finish this lesson first", "先走完这一课", "Lock + dim station", "Required 必出", "On future lessons", "Do not hide future lessons. Show them locked so the path has a destination."),
        # MICRO PATH
        ("R05", "L04", "Lesson path", "课内小路线", "In-class section header", "课中分段标题", "In class", "课中", "Small flag / signboard on the road", "Required 必出", "On the current lesson's micro path", "Groups S1–S5. Without this, 9 nodes become a flat necklace and kids get lost."),
        ("R06", "L04", "Lesson path", "课内小路线", "After-class section header", "课后分段标题", "After class", "课后", "Small flag / signboard after the award", "Required 必出", "On the current lesson's micro path", "Groups S6–S9. Visually a new chapter after Award."),
        ("R07", "L05", "Lesson path", "课内小路线", "Node connector line", "节点连接线", "—", "—", "Solid glow vs dotted grey", "Required 必出", "Between every consecutive pair of the 9 steps", "The line IS the route. Completed segments filled; remaining empty. Must still read in greyscale."),
        ("R08", "L05", "Lesson path", "课内小路线", "Path progress fill", "路线进度填充", "—", "—", "Painted road from start → current", "Required 必出", "Always on micro path", "When a step completes, the segment paints forward (reference video energy)."),
        # 9 NODES — listed also in sheet 03, but they MUST appear on the route
        ("R09", "L06", "In-class nodes", "课中节点", "Node: Preview", "节点：预习", "Peek first", "预习", "Binoculars / sparkle book", "Required 必出", "Step 1 of every lesson", "MISSING in current screenshot. First gate of the lesson."),
        ("R10", "L06", "In-class nodes", "课中节点", "Node: Teaching", "节点：教学", "Class time", "教学", "Teacher / play class", "Required 必出", "Step 2 of every lesson", "MISSING as a node today (only a 去上课 button). Must live ON the path."),
        ("R11", "L06", "In-class nodes", "课中节点", "Node: Practice", "节点：练习", "Try it", "练习", "Target / bullseye — keep", "Required 必出", "Step 3 of every lesson", "Present in current UI. Keep icon. Do not make it the only highlighted chip."),
        ("R12", "L06", "In-class nodes", "课中节点", "Node: Summary", "节点：总结", "Wrap up", "总结", "Star notebook / recap cards", "Required 必出", "Step 4 of every lesson", "MISSING in current screenshot. Short, warm, visual recap."),
        ("R13", "L06", "In-class nodes", "课中节点", "Node: Award (landmark)", "节点：领奖（地标）", "Prize", "领奖", "Chest / medal / gift — bigger than normal nodes", "Required 必出", "Step 5, end of in-class", "MISSING. This is the celebration gate before after-class work. Must feel like a landmark, not a 5th identical dot."),
        ("R14", "L06", "After-class nodes", "课后节点", "Node: Review", "节点：复习", "Replay", "复习", "Replay / flashcards", "Required 必出", "Step 6, start of after-class", "MISSING in current screenshot. First after-class step."),
        ("R15", "L06", "After-class nodes", "课后节点", "Node: Speaking", "节点：口语", "Say it", "口语", "Microphone — keep", "Required 必出", "Step 7", "Present in current UI. Keep mic icon."),
        ("R16", "L06", "After-class nodes", "课后节点", "Node: Listening", "节点：听力", "Listen", "听力", "Headphones — keep", "Required 必出", "Step 8", "Present in current UI. Keep headphone icon."),
        ("R17", "L06", "After-class nodes", "课后节点", "Node: Report (destination)", "节点：报告（终点）", "My report", "报告", "Chart / report card — landmark", "Required 必出", "Step 9, end of the lesson path", "Present in current UI as a chip. Promote to destination landmark of this lesson, then the week road continues to the next lesson."),
        # NODE ANATOMY (each node needs these sub-elements)
        ("R18", "L06", "Node anatomy", "节点构造", "Step icon", "步骤图标", "—", "—", "Simple, 1 concept, readable at 32–40 pt", "Required 必出", "Every node", "Different silhouette per step so color-blind / grey mode still works."),
        ("R19", "L06", "Node anatomy", "节点构造", "Step label ZH", "步骤中文名", "预习 / 教学 / …", "预习 / 教学 / …", "Under the icon, always visible", "Required 必出", "Every node", "Never hide Chinese labels. 2 characters preferred."),
        ("R20", "L06", "Node anatomy", "节点构造", "Step label EN", "步骤英文名", "Preview / Teaching / …", "Preview / Teaching / …", "Second line or locale swap", "Required 必出", "When language = EN; reserve space even in ZH build", "Layout must survive longer English words (Listening, Practice)."),
        ("R21", "L07", "Node anatomy", "节点构造", "State badge", "状态角标", "✓  lock  star", "✓  锁  星", "Check / lock / star / pie", "Required 必出", "Every node except maybe current (glow instead)", "4–5 o'clock of the node. Do not cover the icon."),
        ("R22", "L06", "Node anatomy", "节点构造", "Tap target", "点击热区", "—", "—", "Min 44×44 pt invisible hit area", "Required 必出", "Every node", "Kids miss small chips. The old pill row is too tight."),
        # YOU ARE HERE
        ("R23", "L08", "You-are-here", "你在这里", "Traveler character", "旅人角色", "—", "—", "Current child avatar on the current node; teacher may point forward", "Required 必出", "Always on the current step", "This is the 'kids can follow the path with us' element. Old UI put the teacher beside the card, not on the route."),
        ("R24", "L08", "You-are-here", "你在这里", "Current-node glow / scale", "当前节点高亮放大", "You are here", "你在这里", "Glow ring + 1.15–1.3× scale", "Required 必出", "Current step", "Old UI used a pale orange plate behind Practice only. New: the whole node + traveler + CTA."),
        ("R25", "L08", "You-are-here", "你在这里", "Next-step peek", "下一步预告", "Next: Practice", "下一步：练习", "The next node is fully visible, slightly smaller", "Required 必出", "Always (unless on Report of last lesson)", "Never crop the next node off-screen without a peek. Camera frames current + next."),
        # CTA
        ("R26", "L09", "CTA", "主按钮", "Primary action on current node", "当前步主按钮", "(see step CTA)", "（见各步 CTA）", "Orange pill + icon, glued to current node", "Required 必出", "Whenever the current step is playable", "Replace the left-side 去上课 that sits beside a 4-chip bar. One verb, no truncation like 'Farm Anim…'."),
        ("R27", "L09", "CTA", "主按钮", "Secondary: replay completed step", "次按钮：重玩已完成", "Play again", "再玩一次", "Ghost / small replay on completed nodes", "Recommended 建议", "When a completed node is selected", "Optional. Do not compete with the primary CTA."),
        # LESSON SIGNBOARD (anchors the path)
        ("R28", "L10", "Lesson signboard", "课程牌", "Lesson type tag", "课型标签", "Hear & Speak", "听说", "Colored pill (type color)", "Required 必出", "On current lesson station / hero", "Fix screenshot English 'Hear of'. Use dictionary in 07_Lesson_Types."),
        ("R29", "L10", "Lesson signboard", "课程牌", "Lesson number", "课次", "Lesson 3", "第 3 课", "Neutral chip", "Required 必出", "Always on current lesson", "Keep. Pair with Level · Unit."),
        ("R30", "L10", "Lesson signboard", "课程牌", "Level · Unit", "级别 · 单元", "Level 4 · Unit 1", "Level 4 · Unit 1", "Overlay chip", "Required 必出", "Always on current lesson", "Keep from screenshot."),
        ("R31", "L10", "Lesson signboard", "课程牌", "Lesson title", "课程标题", "Farm Animals", "农场动物", "Large rounded title", "Required 必出", "Always on current lesson", "Keep large white title. Provide ZH + EN."),
        ("R32", "L10", "Lesson signboard", "课程牌", "Duration", "时长", "10 min", "10 分钟", "Clock icon + time", "Required 必出", "On current lesson", "Keep. Duration may change per step if we later show remaining time; v1 = lesson duration."),
        ("R33", "L10", "Lesson signboard", "课程牌", "Lesson status", "课程状态", "In progress / Not started / Done", "进行中 / 未开始 / 已完成", "Signal bars or status chip", "Required 必出", "On current lesson", "Keep. Map to week-station state too."),
        ("R34", "L10", "Lesson signboard", "课程牌", "Words preview", "单词预告", "Words: friend, classmate…", "单词：friend, classmate…", "Text line under title", "Required 必出", "When the lesson has target words", "Keep. Tells kids what this path is 'about'."),
        ("R35", "L10", "Lesson signboard", "课程牌", "Sentences preview", "句型预告", "Sentences: This is my friend.", "句子：This is my friend.", "Text line under words", "Required 必出", "When the lesson has target sentences", "Keep. Empty-state: hide the line, do not show 'Sentences: —'."),
        ("R36", "L10", "Lesson signboard", "课程牌", "Theme illustration", "主题插画", "—", "—", "3D scene for this lesson", "Required 必出", "Current lesson", "Keep quality from screenshot. The path sits in front / below, not replacing the art."),
        # PAGE CHROME still essential for the route to make sense
        ("R37", "L11", "Header", "顶部", "Current child avatar", "当前孩子头像", "—", "—", "Circular photo/avatar", "Required 必出", "Always", "Same avatar as the traveler on the path."),
        ("R38", "L11", "Header", "顶部", "Sibling / profile switcher", "多孩子切换", "Switch kid", "切换宝贝", "Stacked avatars + swap icon", "Required 必出", "When the family has 2+ kids", "Keep from screenshot. Switching kid switches the path progress."),
        ("R39", "L11", "Header", "顶部", "Screen title", "页面标题", "Weekly Study Plan", "本周学习计划", "Centered rounded title", "Required 必出", "Always", "Bilingual. This is the week-map, not a random class list."),
        ("R40", "L11", "Header", "顶部", "More lessons entry", "更多课程入口", "More lessons", "更多课程", "Pill + lesson thumbnail (submarine in screenshot)", "Required 必出", "Always", "Keep. Must return to the same spot on the path."),
        ("R41", "L12", "Tab bar", "底栏", "Class tab (selected)", "上课 Tab（选中）", "Class", "上课", "Green book + star + yellow glow", "Required 必出", "Always", "Keep selected treatment. Route lives here."),
        ("R42", "L12", "Tab bar", "底栏", "Chat / Explore / Play tabs", "聊天 / 探索 / 玩", "Chat · Explore · Play", "聊天 · 探索 · 玩", "Honey pot / chart / VS", "Required 必出", "Always", "Keep. Not part of the lesson route."),
        # OVERLAYS that belong to the route
        ("R43", "L13", "Overlays", "弹层", "Award celebration", "领奖庆祝", "You earned a star!", "你得到一颗星！", "Chest open + stars + stamp on S5", "Required 必出", "When S5 is claimed", "Then auto-pan to after-class path so Review is obviously next."),
        ("R44", "L13", "Overlays", "弹层", "Locked-step feedback", "未解锁反馈", "Let's finish Teaching first", "先上完课再来", "Lock shake + tiny coach line", "Required 必出", "When a locked node is tapped", "Never dead-end. Tell the child which node to do."),
        ("R45", "L13", "Overlays", "弹层", "Mic permission for Speaking", "口语麦克风授权", "Let me hear you", "让老师听见你", "Friendly mic card", "Required 必出", "First time entering Speaking", "Kids path must not jump into a system dialog without a kid-facing explainer."),
        ("R46", "L13", "Overlays", "弹层", "Report sheet", "报告单", "My lesson report", "我的本课报告", "Stars, words, speaking count, listening score", "Required 必出", "On S9 or after claiming S9", "Kid-first layout. Parent-detail can be a second page / toggle."),
        ("R47", "L07", "Node anatomy", "节点构造", "Stars / stamps on completed nodes", "完成章/星星", "Done!", "完成！", "Star or ink stamp", "Required 必出", "Each completed step", "Makes the walked path feel collected, not just grey checks."),
        ("R48", "L04", "Lesson path", "课内小路线", "Award-to-Review gate", "领奖→复习 分界", "After class starts here", "课后从这里开始", "Arch / bridge / banner after the chest", "Required 必出", "Between S5 and S6", "Without a gate, Award and Review look like the same homework list."),
        ("R49", "L03", "Week path", "本周大路线", "Start-of-week landmark", "本周起点", "Week start", "本周出发", "Flag / camp / school gate", "Recommended 建议", "Beginning of week road", "Helps the map feel like a journey, matching the reference video."),
        ("R50", "L03", "Week path", "本周大路线", "End-of-week chest", "本周终点宝箱", "Week prize", "本周大奖", "Bigger chest after last Report", "Recommended 建议", "After the week's last lesson Report", "Optional extra celebration. Do not confuse with per-lesson Award (S5)."),
        ("R51", "L09", "CTA", "主按钮", "CTA lesson nickname", "按钮上的课名简称", "Farm Animals", "农场动物", "On the pill, full name or 2 lines", "Required 必出", "On primary CTA", "Do not clip to 'Farm Anim…'."),
        ("R52", "L08", "You-are-here", "你在这里", "Teacher companion on path", "路上的老师伙伴", "—", "—", "3D teacher from current UI, pointing to the next node", "Recommended 建议", "On current lesson", "Keep the beloved teacher, but move her from card-left onto the road so she walks with the kid."),
        ("R53", "L06", "Node anatomy", "节点构造", "Remaining-time or step status text", "步骤状态小字", "In progress", "进行中", "Under current label only", "Recommended 建议", "Current node", "Optional. Don't clutter every node."),
        ("R54", "L13", "Overlays", "弹层", "Empty / first-time coach", "首次引导", "We walk this path together", "我们一起走这条路", "Teacher points S1 → S9 once", "Recommended 建议", "First launch of the new Class tab", "One-time. Then the path itself must be self-explanatory."),
        ("R55", "L04", "Lesson path", "课内小路线", "Collapsed completed cluster", "已完成段可收起", "In class done ✓", "课中完成 ✓", "S1–S5 can shrink to a stamped ribbon after Award is claimed", "Recommended 建议", "After S5 claimed, if 9 nodes overflow a phone", "If we collapse, the ribbon must still be tappable to expand. Never delete walked steps."),
        ("R56", "L10", "Lesson signboard", "课程牌", "Unit theme name", "单元主题名", "Farm Animals", "农场动物", "May equal lesson title or sit above it", "Recommended 建议", "When unit has a theme", "Helps the week map feel like one story, not 6 disconnected cards."),
    ]

    pri_fill = {
        "Required 必出": GREEN_SOFT,
        "Recommended 建议": GOLD_SOFT,
    }
    for i, row in enumerate(items):
        r = 4 + i
        bg = pri_fill.get(row[9], WHITE if i % 2 == 0 else GREY)
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.cell(r, 1).font = font(11, True, NAVY)
        ws.cell(r, 10).font = font(11, True, GREEN if "Required" in row[9] else GOLD)
        ws.row_dimensions[r].height = 52
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:L{3+len(items)}"
    ws.auto_filter.add_filter_column(9, ["Required 必出", "Recommended 建议"])


def build_steps(wb):
    ws = wb.create_sheet("03_Route_Steps")
    cols = 14
    title_block(
        ws,
        "The 9-step route (every lesson)",
        "每节课固定 9 步路线",
        "In class: Preview → Teaching → Practice → Summary → Award. After class: Review → Speaking → Listening → Report. Do not reorder. 课中 5 步 + 课后 4 步，顺序不可改。",
        cols,
    )
    headers = [
        "Step ID",
        "Order 顺序",
        "Phase EN",
        "阶段 中文",
        "Name EN",
        "名称 中文",
        "Kid label EN",
        "孩子口吻 中文",
        "Icon",
        "CTA EN",
        "CTA 中文",
        "What happens EN",
        "这一步做什么 中文",
        "Design notes 设计",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [10, 10, 14, 12, 14, 12, 14, 14, 28, 16, 12, 36, 36, 40])

    for i, s in enumerate(ROUTE_STEPS):
        r = 4 + i
        bg = ORANGE_SOFT if s[1] == "in_class" else BLUE_SOFT
        if s[0] in ("S5", "S9"):
            bg = GOLD_SOFT
        phase_en = "In class" if s[1] == "in_class" else "After class"
        phase_zh = "课中" if s[1] == "in_class" else "课后"
        vals = [
            s[0],
            s[2],
            phase_en,
            phase_zh,
            s[4],
            s[3],
            s[6],
            s[5],
            s[7],
            s[9],
            s[8],
            s[11],
            s[10],
            s[12],
        ]
        for c, val in enumerate(vals, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.cell(r, 1).font = font(12, True, NAVY)
        ws.row_dimensions[r].height = 72

    # visual map row
    r = 14
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    header_cell(ws, r, 1, "Visual order on one lesson  ·  一节课在路线上的视觉顺序（从左到右 / 沿路向前）", bg=NAVY2)

    r = 15
    labels = [
        ("IN CLASS 课中", NAVY, WHITE, 2),
        ("1 Preview 预习", ORANGE, WHITE, 1),
        ("2 Teaching 教学", ORANGE, WHITE, 1),
        ("3 Practice 练习", ORANGE, WHITE, 1),
        ("4 Summary 总结", ORANGE, WHITE, 1),
        ("5 Award 领奖 ★", GOLD, NAVY, 1),
        ("AFTER CLASS 课后", NAVY, WHITE, 2),
        ("6 Review 复习", BLUE, WHITE, 1),
        ("7 Speaking 口语", BLUE, WHITE, 1),
        ("8 Listening 听力", BLUE, WHITE, 1),
        ("9 Report 报告 ★", GOLD, NAVY, 1),
    ]
    # put as a single row of merged blocks across 14 cols: 2+1*5 + 2 + 1*4 = 13, leftover 1
    col = 1
    for text, bg, fg, span in labels:
        if span > 1:
            ws.merge_cells(start_row=r, start_column=col, end_row=r, end_column=col + span - 1)
        c = ws.cell(r, col, text)
        c.fill = fill(bg)
        c.font = font(10, True, fg)
        c.alignment = align("center", "center")
        c.border = thin
        col += span
    ws.row_dimensions[r].height = 28

    r = 17
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    header_cell(ws, r, 1, "Unlock rule  ·  解锁规则（设计必须画得出来）", bg=NAVY2)
    rules = [
        "S1 Preview is unlocked when this lesson becomes the current week station (previous lesson's Report is done, or it is Lesson 1 of the week).",
        "Each next step unlocks when the previous step is Completed (or Award Claimed for S5). No skipping forward.",
        "Completed steps stay tappable for replay, but the traveler stays on the first incomplete step.",
        "S6 Review does not unlock until S5 Award is claimed — the celebration is the gate.",
        "S9 Report can open in a 'preview' locked state showing 0s, but full report unlocks after Listening (S8) is done.",
        "Lock tap = shake + coach line naming the step they should do (see R44).",
        "同一周下一课站点，要等本课 Report (S9) 完成后才解锁。",
        "课中与课后之间必须有领奖分界，不能 9 个点排成一排毫无分组。",
    ]
    for i, t in enumerate(rules):
        rr = 18 + i
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=cols)
        text_cell(ws, rr, 1, f"• {t}", bg=WHITE if i % 2 == 0 else GREY)
        ws.row_dimensions[rr].height = 24

    ws.freeze_panes = "A4"
    ws.auto_filter.ref = "A3:N12"


def build_states(wb):
    ws = wb.create_sheet("04_Node_States")
    cols = 9
    title_block(
        ws,
        "Node visual states",
        "节点视觉状态",
        "Every step node must support these states. Design all 6 before polishing illustration. 每个步骤节点都要有这 6 个状态。",
        cols,
    )
    headers = [
        "State ID",
        "State EN",
        "状态 中文",
        "Node look 节点样子",
        "Path segment 连接线",
        "Traveler 旅人",
        "CTA",
        "Badge 角标",
        "Used when 何时",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [12, 16, 14, 36, 24, 24, 24, 18, 36])
    states = [
        ("ST1", "Locked", "未解锁", "Grey icon, reduced saturation, no bounce", "Dotted / dim", "Not here", "None (tap shows lock toast)", "Lock", "A later step. Previous step not completed."),
        ("ST2", "Available", "可开始（未开始）", "Full color, rest pose, smaller than current", "Empty but colored faintly", "Not here", "None until selected; then its CTA", "Empty / faint ring", "Unlocked but not the current step (rare: user selected a replay). Default next incomplete is Current, not Available."),
        ("ST3", "Current / In progress", "当前 / 进行中", "Largest, glow ring, 1.15–1.3×, idle bounce", "Glowing up to this node", "Standing here, facing next", "Primary CTA visible", "Soft glow, no lock", "The first incomplete step. This is 'you are here'."),
        ("ST4", "Completed", "已完成", "Full color + stamp/star, slightly smaller than current", "Solid filled behind", "Has walked past", "Optional 'Play again'", "Check / star stamp", "Kid finished this step."),
        ("ST5", "Claimable", "可领取", "Chest closed, bounce / sparkle (Award & maybe week chest)", "Filled up to this node", "Standing here", "Claim Prize", "Sparkle", "S5 (and optional week chest) finished but reward not opened."),
        ("ST6", "Claimed / Destination done", "已领取 / 终点完成", "Chest open or report stamped", "Fully filled through this node", "Walks toward next section/lesson", "View again", "Open chest / gold stamp", "After Award claimed or Report viewed."),
    ]
    fills_s = [GREY2, BLUE_SOFT, ORANGE_SOFT, GREEN_SOFT, GOLD_SOFT, PURPLE_SOFT]
    for i, row in enumerate(states):
        r = 4 + i
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=fills_s[i])
        ws.row_dimensions[r].height = 56
        ws.cell(r, 1).font = font(12, True, NAVY)

    r = 11
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    header_cell(ws, r, 1, "Lesson-station states on the WEEK path  ·  本周大路线上「课程站点」的状态", bg=NAVY2)
    week_states = [
        ("WS1", "Locked lesson", "未解锁的课", "Grey station + lock. Title still visible.", "Future lessons this week."),
        ("WS2", "Current lesson", "当前课", "Expanded station, hosts 9-step micro path + traveler.", "The lesson the kid should do now."),
        ("WS3", "In-class done, after-class open", "课中完成、课后进行中", "Station shows Award claimed + after-class 4 nodes remaining.", "After S5, before S9."),
        ("WS4", "Lesson cleared", "本课通关", "Stamped station, compact. Path continues to next lesson.", "After S9 Report."),
    ]
    headers2 = ["ID", "State EN", "状态 中文", "Look 样子", "When 何时"]
    paint_header_row(ws, 12, headers2, bg=NAVY2)
    for i, row in enumerate(week_states):
        rr = 13 + i
        bg = WHITE if i % 2 == 0 else GREY
        for c, val in enumerate(row, 1):
            text_cell(ws, rr, c, val, bg=bg)
        ws.row_dimensions[rr].height = 40
    ws.freeze_panes = "A4"


def build_inventory(wb):
    ws = wb.create_sheet("05_Page_Inventory")
    cols = 10
    title_block(
        ws,
        "Full Class page inventory",
        "上课页全量元件（含原图已有）",
        "Everything on Weekly Study Plan, including chrome that is not on the path but must stay. 本周学习计划页上的全部元件，含路线外但必须保留的。",
        cols,
    )
    headers = [
        "ID",
        "Region EN",
        "区域 中文",
        "Element EN",
        "元件 中文",
        "Copy EN",
        "文案 中文",
        "In original screenshot? 原图有吗",
        "Action in new design 新设计怎么处理",
        "Notes",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [8, 16, 14, 28, 22, 26, 20, 22, 28, 40])
    rows = [
        ("P01", "Header", "顶部", "Current profile avatar", "当前头像", "—", "—", "Yes 有", "Keep. Same asset as traveler.", "Top-left circle."),
        ("P02", "Header", "顶部", "Multi-child switcher", "多孩子切换", "Switch", "切换", "Yes 有", "Keep stacked avatars + swap.", "3 small avatars in screenshot."),
        ("P03", "Header", "顶部", "Screen title", "标题", "Weekly Study Plan", "本周学习计划", "Yes 有 (EN)", "Keep, add ZH locale.", "Centered rounded white title."),
        ("P04", "Header", "顶部", "More lessons", "更多课程", "More lessons >", "更多课程 >", "Yes 有", "Keep pill + thumb art.", "Submarine thumbnail in screenshot."),
        ("P05", "Hero card", "主卡片", "Type tag", "课型标签", "Hear & Speak", "听说", "Yes 有 — wrong EN 'Hear of'", "Keep chip; fix copy.", "Yellow chip."),
        ("P06", "Hero card", "主卡片", "Lesson number tag", "课次标签", "Lesson 3", "第 3 课", "Yes 有", "Keep.", "Grey-brown chip."),
        ("P07", "Hero card", "主卡片", "Level · Unit tag", "级别·单元", "Level 4 · Unit 1", "Level 4 · Unit 1", "Yes 有", "Keep.", "Semi-transparent overlay."),
        ("P08", "Hero card", "主卡片", "Lesson title", "课程名", "Farm Animals", "农场动物", "Yes 有 (EN)", "Keep large title; add ZH.", ""),
        ("P09", "Hero card", "主卡片", "Duration", "时长", "10 min", "10 分钟", "Yes 有", "Keep clock + time.", ""),
        ("P10", "Hero card", "主卡片", "Status", "状态", "In progress", "进行中", "Yes 有", "Keep. Share state with station.", "Signal-bars icon today — may restyle."),
        ("P11", "Hero card", "主卡片", "Words line", "单词行", "Words: friend, classmate, name, school", "单词：friend, classmate, name, school", "Yes 有", "Keep.", "English lemmas stay in EN even in ZH UI."),
        ("P12", "Hero card", "主卡片", "Sentences line", "句子行", "Sentences: This is my friend.", "句子：This is my friend.", "Yes 有", "Keep.", ""),
        ("P13", "Hero card", "主卡片", "Theme 3D art", "主题 3D 场景", "—", "—", "Yes 有", "Keep as station/hero backdrop.", "Farm: cow, horse, sheep, chicks, two children."),
        ("P14", "Hero card", "主卡片", "Teacher character", "老师角色", "—", "—", "Yes 有 — left of card", "Move onto the path as companion (R52). Still visible.", "Do not delete; relocate."),
        ("P15", "Old route", "旧路线", "Go to Class CTA", "去上课按钮", "Go to Class", "去上课", "Yes 有", "Reattach to current node (usually Teaching).", "Orange pill + book icon + truncated name — fix truncation."),
        ("P16", "Old route", "旧路线", "Chip: Practice", "标签：练习", "Practice", "练习", "Yes 有 (highlighted)", "Become node S3 on the path.", "Was the only current-step cue."),
        ("P17", "Old route", "旧路线", "Chip: Speaking", "标签：口语", "Speaking", "口语", "Yes 有", "Become node S7.", ""),
        ("P18", "Old route", "旧路线", "Chip: Listening", "标签：听力", "Listening", "听力", "Yes 有", "Become node S8.", ""),
        ("P19", "Old route", "旧路线", "Chip: Report", "标签：报告", "Report", "报告", "Yes 有", "Become node S9 destination.", ""),
        ("P20", "Missing", "原图缺失", "Preview node", "预习节点", "Preview", "预习", "No 无", "ADD as S1.", "Essential."),
        ("P21", "Missing", "原图缺失", "Teaching node", "教学节点", "Teaching", "教学", "No 无 (only CTA)", "ADD as S2 on the path.", "Essential."),
        ("P22", "Missing", "原图缺失", "Summary node", "总结节点", "Summary", "总结", "No 无", "ADD as S4.", "Essential."),
        ("P23", "Missing", "原图缺失", "Award node", "领奖节点", "Award", "领奖", "No 无", "ADD as S5 landmark.", "Essential."),
        ("P24", "Missing", "原图缺失", "Review node", "复习节点", "Review", "复习", "No 无", "ADD as S6.", "Essential."),
        ("P25", "Missing", "原图缺失", "Traveler on path", "路上的旅人", "—", "—", "No 无", "ADD (R23).", "Essential for 'follow the path'."),
        ("P26", "Missing", "原图缺失", "In-class / After-class headers", "课中/课后分段", "In class / After class", "课中 / 课后", "No 无", "ADD (R05/R06).", "Essential grouping."),
        ("P27", "Missing", "原图缺失", "Week road + other lesson stations", "本周道路+其他课站点", "Lesson 1…6", "第 1…6 课", "No 无 — only one card", "ADD macro path.", "So kids see the week journey."),
        ("P28", "Tab bar", "底栏", "Chat", "聊天", "Chat", "聊天", "Yes 有", "Keep honey-pot icon.", ""),
        ("P29", "Tab bar", "底栏", "Class (selected)", "上课（选中）", "Class", "上课", "Yes 有", "Keep book+star+yellow glow.", ""),
        ("P30", "Tab bar", "底栏", "Explore", "探索", "Explore", "探索", "Yes 有", "Keep chart icon.", ""),
        ("P31", "Tab bar", "底栏", "Play", "玩", "Play", "玩", "Yes 有", "Keep VS icon.", ""),
    ]
    for i, row in enumerate(rows):
        r = 4 + i
        shot = row[7]
        if shot.startswith("Yes"):
            bg = GREEN_SOFT
        elif shot.startswith("No"):
            bg = ORANGE_SOFT
        else:
            bg = WHITE if i % 2 == 0 else GREY
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.row_dimensions[r].height = 36
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:J{3+len(rows)}"


def build_catalog(wb):
    ws = wb.create_sheet("06_Lesson_Catalog")
    cols = 12
    title_block(
        ws,
        "Lesson catalog (from original sheet, expanded)",
        "原课表扩充（课型中英 + 路线挂载）",
        "Original columns 级别 / 课次 / 课型 are preserved. Every row uses the same 9-step route. 原表三列保留；每一行都走同一条 9 步路线。",
        cols,
    )
    headers = [
        "Level 级别",
        "Lesson 课次",
        "Lesson code",
        "课型 中文",
        "Lesson type EN",
        "Kid tag 中文",
        "Kid tag EN",
        "In-class route 课中",
        "After-class route 课后",
        "Full route 完整路线",
        "Route same? 路线是否相同",
        "Notes 备注",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [12, 12, 14, 16, 32, 12, 16, 28, 28, 44, 16, 36])

    in_class = "预习 → 教学 → 练习 → 总结 → 领奖"
    after = "复习 → 口语 → 听力 → 报告"
    full = "Preview-Teaching-Practice-Summary-Award · Review-Speaking-Listening-Report"

    for i, (level, lesson, code, typ) in enumerate(CATALOG):
        r = 4 + i
        bg = LEVEL_FILL[level]
        # yellow/gold needs dark text
        fg = NAVY if level == "Level 5" else WHITE
        vals = [
            level,
            lesson,
            code,
            typ,
            TYPE_EN[typ],
            TYPE_TAG_ZH[typ],
            TYPE_TAG_EN[typ],
            in_class,
            after,
            full,
            "YES 相同",
            "Assessment lessons still use Award + Report. Award can be a quiz badge.",
        ]
        for c, val in enumerate(vals, 1):
            cell = text_cell(ws, r, c, val)
            if c <= 3:
                cell.fill = fill(bg)
                cell.font = font(11, True, fg)
            else:
                cell.fill = fill(WHITE if i % 2 == 0 else GREY)
        ws.row_dimensions[r].height = 22
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:L{3+len(CATALOG)}"

    # counts
    r = 4 + len(CATALOG) + 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
    header_cell(ws, r, 1, "Counts  ·  数量（方便排周地图）", bg=NAVY2)
    counts = [
        "Level 1–3: 6 lessons / unit week map (L1…L6). Last is always Review & Assessment 复习测评课.",
        "Level 4–6: 12 lessons / unit (L1…L12 or U1L1…U1L12). Lesson 6 and 12 (or U1L6 / U1L12) are Review & Assessment.",
        "Level 5–6 use U1L# codes instead of Lesson #. On the kid path, still show 第 n 课 / Lesson n plus the code if needed for ops.",
        "Design the week map for 6 stations (L1–L3) and 6 or 12 stations (L4–L6). If 12 is too long for one screen, split Unit into Week A (1–6) and Week B (7–12).",
    ]
    for i, t in enumerate(counts):
        rr = r + 1 + i
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=cols)
        text_cell(ws, rr, 1, "• " + t, bg=WHITE if i % 2 == 0 else GREY)
        ws.row_dimensions[rr].height = 28


def build_types(wb):
    ws = wb.create_sheet("07_Lesson_Types")
    cols = 8
    title_block(
        ws,
        "Lesson type dictionary (i18n)",
        "课型词典（中英 + 孩子标签）",
        "Use these tags on the lesson station and hero card. Do not use 'Hear of'. 课程站点和主卡片上的课型标签用本表。不要再用 Hear of。",
        cols,
    )
    headers = [
        "课型 中文",
        "Lesson type EN",
        "Kid tag 中文",
        "Kid tag EN (on chip)",
        "Type color 色",
        "Appears in 出现于",
        "Hero art hint 主视觉",
        "Notes 备注",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [18, 36, 14, 18, 14, 28, 28, 48])
    appears = {
        "词汇课": "L1, L2",
        "句型课": "L1, L2",
        "主题阅读课": "L1",
        "字母课": "L1",
        "拼读阅读课": "L1, L2",
        "自拼课": "L2",
        "语法阅读课": "L2",
        "词句听说课": "L3–L6",
        "阅读基础课": "L3, L4",
        "语法课": "L3",
        "篇章阅读课": "L4–L6",
        "写作课": "L4–L6",
        "语言筑基课": "L5, L6",
        "复习测评课": "All levels, end of block",
    }
    for i, (zh, en, tag_zh, tag_en, color, note) in enumerate(LESSON_TYPES):
        r = 4 + i
        vals = [zh, en, tag_zh, tag_en, "#" + color, appears.get(zh, ""), note.split(".")[0] + ".", note]
        for c, val in enumerate(vals, 1):
            cell = text_cell(ws, r, c, val)
            if c in (1, 5):
                fg = NAVY if color in ("FFF258", "C9A227") else WHITE
                cell.fill = fill(color)
                cell.font = font(11, True, fg)
            else:
                cell.fill = fill(WHITE if i % 2 == 0 else GREY)
        ws.row_dimensions[r].height = 48
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:H{3+len(LESSON_TYPES)}"


def build_copy(wb):
    ws = wb.create_sheet("08_Copy_i18n")
    cols = 8
    title_block(
        ws,
        "UI copy list (English + 中文)",
        "界面文案表（英 + 中）",
        "Source of truth for strings that will appear on Class. Keep kid labels short. 上课页会露脸的文案以本表为准。孩子标签要短。",
        cols,
    )
    headers = [
        "String ID",
        "Where 位置",
        "English (default EN)",
        "中文",
        "Kid-facing? 孩子可见",
        "Max length hint 长度",
        "Do not 不要",
        "Notes",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [22, 22, 32, 22, 14, 16, 28, 40])

    copies = [
        ("title.weekly_plan", "Header", "Weekly Study Plan", "本周学习计划", "Yes", "22 / 8", "Don't use Study Schedule / Curriculum", "Screen title."),
        ("action.more_lessons", "Header", "More lessons", "更多课程", "Yes", "16 / 6", "Don't use More > only", ""),
        ("action.switch_kid", "Header", "Switch", "切换", "Yes", "10 / 2", "", "Voiceover; on-screen may be icon-only plus stacked avatars."),
        ("nav.chat", "Tab", "Chat", "聊天", "Yes", "8 / 2", "", "Keep honey pot."),
        ("nav.class", "Tab", "Class", "上课", "Yes", "8 / 2", "Don't use Course / Lesson tab", "Selected tab."),
        ("nav.explore", "Tab", "Explore", "探索", "Yes", "10 / 2", "", ""),
        ("nav.play", "Tab", "Play", "玩", "Yes", "8 / 1", "Don't use PK if we want softer EN", "VS icon stays."),
        ("phase.in_class", "Route header", "In class", "课中", "Yes", "12 / 2", "Don't use During lesson", "Section flag."),
        ("phase.after_class", "Route header", "After class", "课后", "Yes", "14 / 2", "Don't use Homework (too heavy)", "Section flag."),
        ("step.preview", "Node S1", "Preview", "预习", "Yes", "10 / 2", "", ""),
        ("step.teaching", "Node S2", "Teaching", "教学", "Yes", "10 / 2", "Don't use Lecture", "Kid label can be Class time / 上课"),
        ("step.teaching.kid", "Node S2 kid", "Class time", "上课", "Yes", "12 / 2", "", "Preferred on-node kid voice."),
        ("step.practice", "Node S3", "Practice", "练习", "Yes", "10 / 2", "", "Keep target icon."),
        ("step.summary", "Node S4", "Summary", "总结", "Yes", "10 / 2", "Don't use Recap as the only word if we already use Review", "Kid: Wrap up / 回顾"),
        ("step.award", "Node S5", "Award", "领奖", "Yes", "8 / 2", "Don't use Claim incentive", "Kid: Prize / 领奖"),
        ("step.review", "Node S6", "Review", "复习", "Yes", "8 / 2", "Don't collide with Summary", "Kid: Replay / 再练练"),
        ("step.speaking", "Node S7", "Speaking", "口语", "Yes", "10 / 2", "", "Keep mic."),
        ("step.listening", "Node S8", "Listening", "听力", "Yes", "12 / 2", "Layout must fit Listening", "Keep headphones."),
        ("step.report", "Node S9", "Report", "报告", "Yes", "8 / 2", "", "Kid: My report / 小报告"),
        ("cta.preview", "CTA S1", "Start Preview", "去预习", "Yes", "16 / 4", "", ""),
        ("cta.teaching", "CTA S2", "Go to Class", "去上课", "Yes", "14 / 4", "Don't truncate lesson name", "Original primary CTA."),
        ("cta.practice", "CTA S3", "Practice Now", "去练习", "Yes", "14 / 4", "", ""),
        ("cta.summary", "CTA S4", "See Summary", "看总结", "Yes", "14 / 4", "", ""),
        ("cta.award", "CTA S5", "Claim Prize", "领奖", "Yes", "14 / 2", "", ""),
        ("cta.review", "CTA S6", "Review Now", "去复习", "Yes", "14 / 4", "", ""),
        ("cta.speaking", "CTA S7", "Start Speaking", "去开口", "Yes", "16 / 4", "", ""),
        ("cta.listening", "CTA S8", "Start Listening", "去听", "Yes", "16 / 3", "", ""),
        ("cta.report", "CTA S9", "View Report", "看报告", "Yes", "14 / 4", "", ""),
        ("cta.replay", "Secondary", "Play again", "再玩一次", "Yes", "12 / 4", "", ""),
        ("status.not_started", "Hero / station", "Not started", "未开始", "Yes", "14 / 3", "", ""),
        ("status.in_progress", "Hero / station", "In progress", "进行中", "Yes", "14 / 3", "", "Original screenshot."),
        ("status.done", "Hero / station", "Done", "已完成", "Yes", "8 / 3", "", ""),
        ("meta.lesson_n", "Hero", "Lesson {n}", "第 {n} 课", "Yes", "12 / 6", "", ""),
        ("meta.level_unit", "Hero", "Level {level} · Unit {unit}", "Level {level} · Unit {unit}", "Yes", "24 / 24", "", "Keep Latin Level/Unit or localize 级别/单元 later."),
        ("meta.duration", "Hero", "{n} min", "{n} 分钟", "Yes", "8 / 8", "", ""),
        ("meta.words", "Hero", "Words: {list}", "单词：{list}", "Yes", "1 line", "Don't dump 20 words", "4-word example in screenshot."),
        ("meta.sentences", "Hero", "Sentences: {list}", "句子：{list}", "Yes", "1 line", "", ""),
        ("lock.need_previous", "Toast", "Let's finish {step} first", "先完成「{step}」再来", "Yes", "32 / 16", "Don't say Locked.", "Friendly coach."),
        ("lock.need_previous_lesson", "Toast", "Finish this lesson first", "先走完这一课", "Yes", "28 / 8", "", ""),
        ("award.celebrate", "Overlay", "You earned a star!", "你得到一颗星！", "Yes", "24 / 10", "Don't use You have successfully claimed", ""),
        ("report.title", "Overlay", "My lesson report", "我的本课报告", "Yes", "22 / 8", "", ""),
        ("mic.title", "Overlay", "Let me hear you", "让老师听见你", "Yes", "22 / 8", "", ""),
        ("coach.first_time", "Overlay", "We walk this path together", "我们一起走这条路", "Yes", "32 / 10", "", "Once."),
        ("week.progress", "HUD", "{done} / {total} lessons", "{done} / {total} 课", "Yes", "16 / 10", "", ""),
        ("week.start", "Landmark", "Week start", "本周出发", "Yes", "12 / 4", "", ""),
        ("week.prize", "Landmark", "Week prize", "本周大奖", "Yes", "12 / 4", "", "Don't confuse with per-lesson Award."),
        ("type.hear_speak", "Type chip", "Hear & Speak", "听说", "Yes", "14 / 2", "NEVER Hear of", "Fixes original screenshot."),
        ("type.words", "Type chip", "Words", "单词", "Yes", "8 / 2", "", ""),
        ("type.sentences", "Type chip", "Sentences", "句子", "Yes", "12 / 2", "", ""),
        ("type.reading", "Type chip", "Reading", "阅读", "Yes", "10 / 2", "", ""),
        ("type.abc", "Type chip", "ABC", "字母", "Yes", "6 / 2", "", ""),
        ("type.phonics", "Type chip", "Phonics", "拼读", "Yes", "10 / 2", "", ""),
        ("type.blend", "Type chip", "Blend", "自拼", "Yes", "8 / 2", "", ""),
        ("type.grammar_read", "Type chip", "Grammar Read", "语法阅读", "Yes", "14 / 4", "", ""),
        ("type.read_basics", "Type chip", "Read Basics", "阅读基础", "Yes", "12 / 4", "", ""),
        ("type.grammar", "Type chip", "Grammar", "语法", "Yes", "10 / 2", "", ""),
        ("type.passage", "Type chip", "Passage", "篇章", "Yes", "10 / 2", "", ""),
        ("type.writing", "Type chip", "Writing", "写作", "Yes", "10 / 2", "", ""),
        ("type.foundations", "Type chip", "Foundations", "筑基", "Yes", "12 / 2", "", ""),
        ("type.review_quiz", "Type chip", "Review Quiz", "测评", "Yes", "12 / 2", "", ""),
        ("you_are_here", "A11y / optional label", "You are here", "你在这里", "Optional", "14 / 4", "", "Can be visual-only if traveler is clear."),
        ("next_step", "Peek", "Next: {step}", "下一步：{step}", "Yes", "18 / 8", "", "R25."),
    ]
    for i, row in enumerate(copies):
        r = 4 + i
        bg = WHITE if i % 2 == 0 else GREY
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        if row[4] == "Yes":
            ws.cell(r, 5).fill = fill(GREEN_SOFT)
        ws.row_dimensions[r].height = 22
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:H{3+len(copies)}"


def build_gap(wb):
    ws = wb.create_sheet("09_Current_vs_Target")
    cols = 6
    title_block(
        ws,
        "Current screenshot vs target route",
        "原图现状 vs 目标路线",
        "What to keep, what to fix, what to add so kids can follow the path. 保留什么、改什么、补什么。",
        cols,
    )
    headers = [
        "Item 项目",
        "Current (screenshot) 现在",
        "Target 目标",
        "Keep / Fix / Add",
        "Why it matters 为什么",
        "Designer instruction 设计指令",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [22, 36, 36, 16, 36, 40])
    rows = [
        (
            "Route metaphor",
            "Horizontal 4-chip bar under one lesson card. Feels like a toolbar.",
            "A road kids walk: week stations + 9-step lesson path, traveler on the current node, next node always in view.",
            "Fix 改",
            "Chips do not feel like a journey. The video reference is a path.",
            "Draw a real trail. Do not restyle the chips and call it done.",
        ),
        (
            "Steps shown",
            "Practice, Speaking, Listening, Report only.",
            "Preview, Teaching, Practice, Summary, Award + Review, Speaking, Listening, Report.",
            "Add 补",
            "5 of 9 steps are invisible. Kids cannot follow what they cannot see.",
            "All 9 nodes on the current lesson. Group 课中 / 课后.",
        ),
        (
            "Go to Class CTA",
            "Orange pill left of the chips, lesson name truncated 'Farm Anim…'.",
            "Primary CTA glued to the current node, full lesson name, verb changes by step.",
            "Fix 改",
            "CTA is off the path; truncated name looks broken.",
            "Attach CTA to traveler/current node. Two-line name if needed.",
        ),
        (
            "Current-step cue",
            "Pale orange plate behind Practice.",
            "Scale + glow + traveler + CTA. Only one current node.",
            "Fix 改",
            "A background tint is too weak for 4–8 year olds.",
            "Make 'you are here' unmissable.",
        ),
        (
            "Teacher character",
            "Stands left, overlapping the card, not related to progress.",
            "Walks the path with the child, pointing to the next node.",
            "Fix 改",
            "She is loved, but she is not helping the route.",
            "Reuse the 3D teacher. Put her on the road.",
        ),
        (
            "Week context",
            "Only one lesson card. Other lessons hidden behind More lessons.",
            "Week road with all stations for this week; More lessons is extra / library.",
            "Add 补",
            "A weekly plan that shows one card is not a plan.",
            "6 (or 6+6) stations on a trail.",
        ),
        (
            "Type tag English",
            "Hear of",
            "Hear & Speak / 听说 (词句听说课)",
            "Fix 改",
            "Broken English will ship into i18n if we copy the screenshot.",
            "Use 07_Lesson_Types + 08_Copy_i18n.",
        ),
        (
            "Profile switcher",
            "Avatar + stacked siblings + swap.",
            "Same. Switching child switches path progress.",
            "Keep 留",
            "Multi-child families are a product fact.",
            "Keep control. Bind traveler avatar to selected child.",
        ),
        (
            "Hero content",
            "Title, duration, status, words, sentences, 3D theme art.",
            "Same content, used as the current station's signboard.",
            "Keep 留",
            "Parents and kids need to know what this path is about.",
            "Don't sacrifice Words/Sentences for decoration.",
        ),
        (
            "Tab bar",
            "Chat / Class / Explore / Play with Class selected glow.",
            "Unchanged.",
            "Keep 留",
            "Route lives inside Class, not in new tabs.",
            "Don't add a 5th tab for the path.",
        ),
        (
            "Award & Report as landmarks",
            "Report is a small chip. Award does not exist.",
            "Award chest after in-class; Report as lesson destination; optional week chest.",
            "Add 补",
            "Without landmarks the path has no 'arrivals'. Kids need ceremonies.",
            "Chests bigger than normal nodes. Celebrate, then pan to next section.",
        ),
        (
            "Lock / complete states",
            "Only one highlighted chip; others look equal.",
            "Locked / current / completed / claimable, plus stamps on walked nodes.",
            "Add 补",
            "Equal chips hide order. Order is the product.",
            "Design the 6 node states in 04_Node_States first.",
        ),
        (
            "i18n space",
            "Chinese chips 练习口语听力报告 fit; English already overflows (Listening).",
            "Reserve 2-line labels; kid EN labels 1–2 words; layout tested in EN and ZH.",
            "Add 补",
            "We will have multilanguage. The old bar cannot hold English.",
            "Build the component with EN strings from 08_Copy_i18n, not Lorem.",
        ),
        (
            "Motion",
            "Static bar.",
            "Road paints forward; traveler walks; chest bounces; camera keeps current+next framed (as in the Lark video).",
            "Add 补",
            "Feeling of following comes from motion along a path.",
            "Spec: complete → paint segment → walk → settle on next node → CTA updates.",
        ),
    ]
    keep_bg = {
        "Keep 留": GREEN_SOFT,
        "Fix 改": ORANGE_SOFT,
        "Add 补": BLUE_SOFT,
    }
    for i, row in enumerate(rows):
        r = 4 + i
        bg = keep_bg.get(row[3], WHITE)
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.cell(r, 4).font = font(12, True, NAVY)
        ws.row_dimensions[r].height = 68
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:F{3+len(rows)}"


def build_map_sheet(wb):
    """A one-page visual spec designers can screenshot into Figma."""
    ws = wb.create_sheet("01b_Route_Map")
    title_block(
        ws,
        "One-page route map (wire in cells)",
        "一页路线地图（用格子示意）",
        "Not final art. Shows grouping, order, and what sits on which layer. 不是终稿，只表示分组、顺序、图层。",
        11,
    )
    set_widths(ws, [14] * 11)

    # week header
    ws.merge_cells("A3:K3")
    header_cell(ws, 3, 1, "MACRO  本周大路线  Weekly stations  (example: Level 4 · Unit 1 · 6-lesson week)", bg=NAVY2)

    week = [
        ("L1 词句听说\nHear & Speak", GREEN, "cleared"),
        ("L2 篇章\nPassage", GREEN, "cleared"),
        ("L3 词句听说\nFarm Animals  ★ YOU ARE HERE", ORANGE, "current"),
        ("L4 篇章\nPassage", LOCK, "locked"),
        ("L5 阅读基础\nRead Basics", LOCK, "locked"),
        ("L6 测评\nReview Quiz", LOCK, "locked"),
    ]
    # 6 stations in row 5 with arrows in row 4
    cols_pos = [1, 3, 5, 7, 9, 11]
    for i, ((label, color, state), col) in enumerate(zip(week, cols_pos)):
        fg = WHITE if color != LOCK else INK
        if color == LOCK:
            color = GREY2
        ws.merge_cells(start_row=5, start_column=col, end_row=6, end_column=col)
        c = ws.cell(5, col, label)
        c.fill = fill(color)
        c.font = font(9, True, fg)
        c.alignment = align("center", "center", True)
        c.border = thin
        if i < 5:
            arrow = ws.cell(5, col + 1, "━━▶" if i < 2 else ("━ ▶" if i == 2 else "┄┄▶"))
            arrow.alignment = align("center", "center")
            arrow.font = font(14, True, GREEN if i < 2 else (ORANGE if i == 2 else LOCK))
    ws.row_dimensions[5].height = 28
    ws.row_dimensions[6].height = 28

    ws.merge_cells("A8:K8")
    header_cell(ws, 8, 1, "MICRO  当前课 Farm Animals  课内 9 步  (only the current station expands this)", bg=NAVY2)

    # in class band
    ws.merge_cells("A9:F9")
    header_cell(ws, 9, 1, "IN CLASS  课中   Preview → Teaching → Practice → Summary → Award", bg=ORANGE)
    ws.merge_cells("G9:K9")
    header_cell(ws, 9, 7, "AFTER CLASS  课后   Review → Speaking → Listening → Report", bg=BLUE)

    nodes = [
        (1, "1\n预习\nPreview\nS1", ORANGE_SOFT, ORANGE),
        (2, "2\n教学\nTeaching\nS2  CURRENT\n[Go to Class]", ORANGE, WHITE),
        (3, "3\n练习\nPractice\nS3", GREY2, MUTED),
        (4, "4\n总结\nSummary\nS4", GREY2, MUTED),
        (5, "5 ★\n领奖\nAward\nS5  chest", GOLD_SOFT, NAVY),
        (6, "gate\n课后\nstarts", NAVY2, WHITE),
        (7, "6\n复习\nReview\nS6", GREY2, MUTED),
        (8, "7\n口语\nSpeaking\nS8", GREY2, MUTED),
        (9, "8\n听力\nListening\nS8", GREY2, MUTED),
        (10, "9 ★\n报告\nReport\nS9", GOLD_SOFT, NAVY),
        (11, "next\nlesson\nlocked", GREY2, MUTED),
    ]
    # I numbered speaking as S8 by mistake in col 8 label - fix: S7 speaking, S8 listening
    nodes[7] = (8, "7\n口语\nSpeaking\nS7", GREY2, MUTED)
    nodes[8] = (9, "8\n听力\nListening\nS8", GREY2, MUTED)

    for col, text, bg, fg in nodes:
        ws.merge_cells(start_row=10, start_column=col, end_row=14, end_column=col)
        c = ws.cell(10, col, text)
        c.fill = fill(bg)
        c.font = font(10, True, fg)
        c.alignment = align("center", "center", True)
        c.border = thin
    ws.row_dimensions[10].height = 22
    for rr in range(11, 15):
        ws.row_dimensions[rr].height = 18

    ws.merge_cells("A16:K16")
    header_cell(ws, 16, 1, "On this example the traveler stands on S2 Teaching. CTA = Go to Class / 去上课. Next peek = Practice.", bg=NAVY)

    notes = [
        "Example matches the original screenshot's lesson: Level 4 · Unit 1 · Lesson 3 · Farm Animals · 词句听说课 (Hear & Speak), status In progress, duration 10 min.",
        "In the old UI the highlighted chip was Practice — that is usually WRONG if class has not been taken. Current node should be the first incomplete step (often Teaching / 去上课).",
        "S5 Award is drawn as a chest (landmark). S9 Report is drawn as a destination. Column 6 is the after-class gate, not a step.",
        "Column 11 is the next lesson station on the week road (locked) so the path never feels like it ends at Report.",
        "Layers from back to front on this map: scene art (not shown) → week road → stations → micro path line → nodes → traveler+CTA → header/tab (not shown).",
        "示例对齐原图课程：Level 4 · Unit 1 · 第 3 课 · Farm Animals · 听说。旅人站在「教学」，主按钮是去上课。",
    ]
    for i, t in enumerate(notes):
        rr = 18 + i
        ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=11)
        text_cell(ws, rr, 1, "• " + t, bg=WHITE if i % 2 == 0 else GREY)
        ws.row_dimensions[rr].height = 32


def add_print_and_meta(wb):
    wb.properties.title = "Class Route Design Structure 上课路线设计结构呈现"
    wb.properties.creator = "Class route design handoff"
    wb.properties.description = (
        "Bilingual (EN/ZH) essential-element and layer list for the Class tab weekly study path. "
        "In class: Preview-Teaching-Practice-Summary-Award. After class: Review-Speaking-Listening-Report."
    )
    # sheet order: 00, 01, 01b, 02...
    # already created in order except 01b after 09. Reorder.
    order = [
        "00_ReadMe",
        "01_Screen_Layers",
        "01b_Route_Map",
        "02_Route_Must_Have",
        "03_Route_Steps",
        "04_Node_States",
        "05_Page_Inventory",
        "06_Lesson_Catalog",
        "07_Lesson_Types",
        "08_Copy_i18n",
        "09_Current_vs_Target",
    ]
    for i, name in enumerate(order):
        wb.move_sheet(name, offset=i - wb.sheetnames.index(name))

    tab_colors = {
        "00_ReadMe": NAVY,
        "01_Screen_Layers": PURPLE,
        "01b_Route_Map": ORANGE,
        "02_Route_Must_Have": GREEN,
        "03_Route_Steps": ORANGE,
        "04_Node_States": BLUE,
        "05_Page_Inventory": "243A6B",
        "06_Lesson_Catalog": VIOLET,
        "07_Lesson_Types": PINK,
        "08_Copy_i18n": GOLD,
        "09_Current_vs_Target": ORANGE,
    }
    for name, color in tab_colors.items():
        wb[name].sheet_properties.tabColor = color


def main():
    wb = Workbook()
    build_readme(wb)
    build_layers(wb)
    build_must_have(wb)
    build_steps(wb)
    build_states(wb)
    build_inventory(wb)
    build_catalog(wb)
    build_types(wb)
    build_copy(wb)
    build_gap(wb)
    build_map_sheet(wb)
    add_print_and_meta(wb)
    wb.save(OUT)
    print("Wrote", OUT, "sheets:", wb.sheetnames)


if __name__ == "__main__":
    main()
