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
            "Start with 01_Screen_Layers + 01c_Video_Feel, then 02_Route_Must_Have. Do not invent extra steps.",
        ),
        (
            "Why we are changing it",
            "Current Weekly Study Plan card (original screenshot) only shows Practice / Speaking / Listening / Report in a horizontal pill. Kids cannot see where they came from or where they go next. Preview, Teaching, Summary, Award, Review are missing.",
            "现有「本周学习计划」卡片底部只有 练习-口语-听力-报告 四个横条。孩子看不到从哪来、到哪去。预习、教学、总结、领奖、复习都没有出现在路线上。",
            "Keep the 3D art, teacher, lesson card, profile switcher, and tab bar. Rebuild the route.",
        ),
        (
            "Reference video — LAYER FEELING",
            "The Lark frames are the layer language we want: a themed WORLD behind, a shared GROUND PLANE, objects sitting on that plane in a HORIZONTAL scroll, sticky header + sticky tab bar as overlays. Big yellow-bordered CARDS = main events. Treasure CHESTS = tasks/rewards on the floor. Mini-steps with green/grey locks live ON the lesson card. A mascot talks ('Come with me') and a next locked card peeks from the right. Not a chip toolbar, not a vertical list.",
            "飞书视频帧就是我们要的图层语言：主题世界在后，共用地面，物件都坐在这条水平地面上横向滑。大黄边卡片=主事件。宝箱=地上的任务/奖励。小步骤带绿锁/灰锁长在主课卡片上。角色说话（跟我走），下一张未解锁卡片从右边探出来。不要标签条，也不要竖着列表。",
            "Copy STRUCTURE and DEPTH from the video. Keep OUR 3D teacher, farm/ocean art, Chat/Class/Explore/Play tabs, and our 9 steps. Do not copy their 1V1/小班 tabs, parrot brand, or PaperHomework naming.",
        ),
        (
            "Route law (do not break)",
            "INSIDE every lesson: Preview → Teaching → Practice → Summary → Award. AFTER every lesson: Review → Speaking → Listening → Report. Same 9 steps for every lesson type in the catalog (vocab, phonics, reading, writing, assessment…).",
            "每节课课中固定：预习 → 教学 → 练习 → 总结 → 领奖。每节课课后固定：复习 → 口语 → 听力 → 报告。课表里所有课型都走同一条 9 步路线。",
            "You may restyle nodes by lesson type color, but never drop, reorder, or rename the 9 steps.",
        ),
        (
            "Two scales of route (video language)",
            "MACRO (horizontal unit path): Lesson 1 CARD → after-class CHESTS → Lesson 2 CARD → … → unit test CARD → stage report CARD. MICRO (on the current lesson): 5 in-class steps sit ON the big lesson card; 4 after-class steps sit as chests on the floor AFTER that card. Kids always know which lesson card they are on, and which lock on that card / which chest is next.",
            "大路线（横向单元路）：第1课大卡片 → 课后宝箱 → 第2课大卡片 → … → 单元测评大卡片 → 阶段报告大卡片。小路线（当前课）：课中 5 步长在大卡片上；课后 4 步是卡片后面地上的宝箱。孩子随时知道自己在哪张课卡、下一步是卡片上的哪把锁还是地上的哪个宝箱。",
            "Match the video: big card = class, chests = follow-up tasks, test/report = destination cards. Do not put all 9 steps as equal dots.",
        ),
        (
            "How to read the sheets",
            "00 ReadMe · 01 z-order layers · 01b wire map · 01c video layer-feel (copy vs don't copy) · 02 must-have elements · 03 the 9 steps · 04 node states · 05 page inventory · 06 catalog · 07 types · 08 copy · 09 current vs target.",
            "00 说明 · 01 图层 · 01b 示意 · 01c 视频图层感觉（学什么/不学什么） · 02 必出元素 · 03 九步 · 04 状态 · 05 全页 · 06 课表 · 07 课型 · 08 文案 · 09 对照。",
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
        "Build Figma in this stack. Feeling from the video: WORLD in back, FLOOR in the middle, CARDS/CHESTS/MASCOT in front, HEADER + TAB BAR as sticky overlays that do not scroll with the path. 按此叠 Figma。视频感觉：世界在后，地面在中，卡片/宝箱/角色在前，顶栏底栏是不跟着路滑的浮层。",
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
            "World background",
            "主题世界（后景）",
            "Back · 后景",
            "Themed full-bleed world. Video: soft ocean + low-contrast line-art whale, turtle, fish, coral — atmosphere, not content. Ours: keep 3D farm/ocean/city the same way — pretty, quiet, not tappable.",
            "Slow parallax. Video silhouettes drift; ours can idle (chicks, clouds). Never steals taps.",
            "Yes — keep our 3D quality. Copy the video's quiet-wallpaper discipline.",
            "VIDEO FEEL: if a kid can't tell the path from the whale, the layer failed. Path objects must be brighter/sharper than the world.",
        ),
        (
            "L01",
            "Ground plane / sea floor",
            "共用地面（路线平面）",
            "Mid-back · 中后",
            "One shared horizontal floor. Video: the sea floor. Every card, chest, signpost, and mascot SITS on this plane. Left-to-right scroll along the floor — not a vertical feed, not a chip bar.",
            "World + floor + objects scroll together horizontally. Header and tab bar do NOT scroll.",
            "New — old UI had one floating card, no floor.",
            "MOST IMPORTANT FEEL LAYER. Align object bottoms. Soft contact shadow under every object. Random Y = not the video.",
        ),
        (
            "L02",
            "Wayfinding props",
            "路标层",
            "Mid · 中景",
            "Unit signpost (video: yellow arrow 'Unit 11'), floating section title (video: yellow pill 'Language Booster 3'), floor label (video: blue/yellow pill 'lesson 1'). Ours: Unit n · theme · 第 n 课.",
            "Signpost planted on the floor. Section title hovers above the current cluster. Lesson pill sits under the card/chests it belongs to.",
            "New.",
            "VIDEO FEEL: kids read WHERE they are from signs on the road, not only from a header.",
        ),
        (
            "L03",
            "Big event cards",
            "主事件大卡片",
            "Mid-front · 中前",
            "Large rounded white cards with a thick friendly border (video: yellow). One card = one MAIN event: the lesson (教学), later Progress Test / Graduation Test / Stage Report. Current card biggest. Next card peeks from the right with a lock.",
            "Horizontal scroll. Peek 24–40 pt of the next card. Locked card dimmer; CTA greyed.",
            "Partial — we already have a farm hero card. Plant it on the floor and add more cards to the right.",
            "VIDEO HIERARCHY: CARD > chest. Never make 口语/听力 as large as the lesson card. Lesson card still carries type, title, duration, words, sentences, 3D art.",
        ),
        (
            "L04",
            "Mini-route ON the lesson card",
            "主卡片上的课中小路线",
            "Front- · 卡片内",
            "Horizontal row ON the lesson card (video: Preview · Live Class · Review · PaperHomework with green/grey locks). Ours on the card: 预习 Preview · 教学 Teaching · 练习 Practice · 总结 Summary · 领奖 Award. After-class steps do NOT live on this row.",
            "Current step highlighted (video: yellow Preview tab). Completed = green. Locked = grey lock. Illegal tap = lock shake + mascot line.",
            "Replace the old 4-chip bar that mixed 练习/口语/听力/报告.",
            "VIDEO FEEL: in-class path lives IN the card. After-class becomes floor chests (L05).",
        ),
        (
            "L05",
            "Floor chests (after class)",
            "地面宝箱（课后）",
            "Mid-front · 中前",
            "Smaller than cards. Video: yellow chests with blue buttons Review / PaperHomework sitting on the floor. Ours to the right of each lesson card: 复习, 口语, 听力, plus 领奖 as a chest. 报告 may be a chest or a destination card.",
            "Same floor as the card. Claimable chest bounces. Locked chest closed + grey button.",
            "New — old UI had no chests.",
            "VIDEO HIERARCHY: chests = collectible tasks, cards = main events. One button family on every chest.",
        ),
        (
            "L06",
            "Mascot guide + speech",
            "向导角色 + 说话",
            "Front · 前景",
            "Video: parrot with headphones, white bubble ('Hey! Your unit test treasure chest is still waiting. Come with me!') + blue Go. Ours: 3D teacher and/or kid avatar standing ON the floor beside the current card/chest, pointing forward.",
            "Idle bounce. Speech for the current unfinished landmark (unclaimed 领奖 / unit test). Go pans to that object.",
            "Partial — move the existing teacher off the card-left and onto the floor as a guide.",
            "VIDEO FEEL: character is a GUIDE on the path. Do not copy their parrot. Bilingual speech in 08_Copy_i18n.",
        ),
        (
            "L07",
            "CTA button family",
            "主按钮家族",
            "Front · 前景",
            "Video: one rounded blue button language on cards AND chests — Enter, Go, Review, Start, Report. Disabled = grey/translucent. Ours: keep orange 去上课 energy, same shape/size on every path object.",
            "Only the current step's CTA is vivid. Others grey until unlocked.",
            "Yes — keep 去上课; stop truncating Farm Anim…",
            "VIDEO FEEL: kids learn 'this pill = do this'. One family, not a unique button per module.",
        ),
        (
            "L08",
            "Lock / unlock markers",
            "锁与解锁标记",
            "Front · 前景",
            "Video: small lock under each mini-step — green = open, grey = closed. Greyed Go to Class / Start when the card is not current. Peeked next card shows a lock.",
            "Lock shake on illegal tap. Green pop when a step opens.",
            "New (old UI only tinted Practice).",
            "VIDEO FEEL: order is visible as locks. Use lock+label, never color-only.",
        ),
        (
            "L09",
            "Sticky header overlay",
            "顶部浮层（不随路滚动）",
            "Overlay · 浮层",
            "Pinned while the path scrolls. Video: avatar, name, stars, 外教1V1/中教小班 pills, Task Wall, Self Study, Level. Ours: child avatar, sibling switcher, Weekly Study Plan, More lessons. Do NOT copy their 1V1/小班 IA.",
            "Does not move when the path pans.",
            "Yes — keep our header content.",
            "VIDEO FEEL: header is HUD, path is a world. Never put the 9 steps in the header.",
        ),
        (
            "L10",
            "Sticky tab bar overlay",
            "底部导航浮层（不随路滚动）",
            "Overlay · 浮层",
            "Video: 6 colorful circles (songs, diary, AI, games…). Ours stays Chat · Class (selected glow) · Explore · Play. Path lives INSIDE Class. Video's yellow 'lesson 2' oval above a tab is optional — if used, it marks the floor position, not a 5th tab.",
            "Selection glow only. Pad the scroll so chests are not hidden under the bar.",
            "Yes — keep our 4 tabs and Class selected treatment.",
            "VIDEO FEEL: footer is overlay, not part of the sea floor. Do not replace our tabs with their 6 circles.",
        ),
        (
            "L11",
            "Overlays & celebrations",
            "弹层与庆祝",
            "Top · 最前",
            "Lock coach, mic permission, chest-open, report sheet, offline. Prefer on-path mascot speech (L06) over a modal for 'come with me'.",
            "Chest-open is the biggest beat. Then auto-pan right so 复习 is in view.",
            "New / expand.",
            "VIDEO FEEL: the path itself invites. Don't full-screen popup every next step.",
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


def build_video_feel(wb):
    ws = wb.create_sheet("01c_Video_Feel")
    cols = 8
    title_block(
        ws,
        "Video layer-feel: copy this, not their product",
        "视频图层感觉：学结构，不抄产品",
        "Frames from Lark20260825-162130.mp4. Copy DEPTH, FLOOR, CARD vs CHEST, LOCKS, sticky chrome. Keep our 9 steps, 3D teacher, Chat/Class/Explore/Play. 学纵深/地面/卡片vs宝箱/锁/浮层。课步、老师、底栏用我们的。",
        cols,
    )
    headers = [
        "ID",
        "In the video EN",
        "视频里有什么 中文",
        "Feeling to copy 要学的感觉",
        "Do NOT copy 不要照搬",
        "Maps to OUR element 对应我们",
        "Layer",
        "Designer note 设计备注",
    ]
    paint_header_row(ws, 3, headers)
    set_widths(ws, [8, 28, 26, 40, 32, 32, 10, 40])
    rows = [
        ("V01", "Soft ocean world + line-art whale/turtle/fish/coral", "浅蓝海底世界 + 低对比线描鲸/龟/鱼/珊瑚", "Quiet wallpaper behind the path. Theme can change (farm/ocean) but it stays BACK.", "Do not paste their ocean into Farm Animals. Do not make background characters tappable.", "L00 world. Our 3D farm animals stay decoration.", "L00", "Contrast test: desaturate the file — cards/chests must still pop."),
        ("V02", "Everything sits on one sea floor; swipe left-right", "所有物件坐在同一片海底，左右滑", "Shared ground plane + horizontal journey. Bottoms aligned. Contact shadows.", "Not a vertical list. Not a winding mountain map. Not a 4-chip toolbar.", "L01 floor. Week = one long floor from lesson 1 → test cards.", "L01", "If Y positions wander, it will not feel like the video."),
        ("V03", "Sticky header (avatar Jerry, stars, 1V1 / 中教小班, Task Wall, Level 2)", "顶栏固定（头像、星星、1V1/小班、任务墙、Level）", "Header is a HUD overlay. It does not scroll with the path.", "Do not add 外教1V1 / 中教小班. Do not add their star score unless we have it. Do not add Task Wall/Self Study unless they exist in our app.", "L09: our avatar, sibling switcher, Weekly Study Plan, More lessons.", "L09", "Two layers: HUD vs world."),
        ("V04", "Yellow Unit 11 arrow signpost on a stand", "黄色 Unit 11 箭头路标", "Unit is a physical sign on the road.", "Do not keep 'Unit 11' as dummy copy. Use the real unit index.", "R03 unit signpost.", "L02", "Plant it on the floor, not in the header."),
        ("V05", "Yellow pill 'Language Booster 3' above the parrot", "黄色胶囊标题 Language Booster 3", "A chapter name floats above the current cluster.", "Do not use their course-line name. Use our unit theme / 课型.", "R49 section header + R56 theme.", "L02", "One label per cluster, not per chest."),
        ("V06", "Parrot + bubble 'Hey! Your unit test treasure chest is still waiting. Come with me!' + Go", "鹦鹉+气泡邀请去宝箱 + Go", "A guide ON the path talks and offers Go. Invitation is the route.", "Do not use their parrot. Do not write long English paragraphs.", "Our 3D teacher + R58/R59. Copy: 08_Copy_i18n coach.*", "L06", "Speech points at a real object that is on screen or one pan away."),
        ("V07", "Large white card, thick yellow border (Unit Printouts / lesson card)", "大白卡 + 粗黄边（主事件）", "CARD = main event. Biggest object. Friendly thick border. Rounded.", "Border color can stay our orange/warm brand. Do not copy printouts as a new lesson type unless we have it.", "L03 lesson card. Keep Words/Sentences/art from our current hero.", "L03", "CARD > chest is the hierarchy."),
        ("V08", "On the lesson card: Preview / Live Class / Review / PaperHomework + green/grey locks", "卡片上的四步 + 绿锁/灰锁", "Mini-route lives IN the card. Locks under icons. Current step highlighted (yellow Preview tab). Greyed Go to Class when not ready.", "Do not copy their 4 step names. Do not put 口语/听力 on this row.", "On-card: 预习 教学 练习 总结 领奖. Teaching = Go to Class.", "L04+L08", "This replaces our old 练习-口语-听力-报告 chip bar."),
        ("V09", "Yellow treasure chests on the floor with blue Review / PaperHomework buttons + lesson 1 pill", "地上黄宝箱 + 蓝按钮 + lesson 1 胶囊", "CHEST = smaller follow-up task on the floor after the card. Button on the chest. Lesson number on the floor.", "Do not name a step PaperHomework. Do not make chests as tall as the lesson card.", "After-class: 复习 口语 听力 as chests. 领奖 is a chest. Floor pill = 第 n 课.", "L05+L02", "Chests belong to the lesson on their left."),
        ("V10", "Next lesson card peeking from the right with teacher photo, 30th, Preview, green lock", "右边探出下一张课卡 + 锁", "The path continues off-screen. Peek + lock = destination.", "Do not require a live-class calendar ('30th Aug 10:00') unless we have scheduled class.", "R04 / R25 next-card peek. Grey CTA + lock.", "L03", "Always show a slice of 'later'."),
        ("V11", "Progress Test / Graduation Test / Stage Report as large illustrated cards + Start/Report", "阶段测 / 毕业测 / 阶段报告 也是大卡片", "End-of-unit destinations are CARDS with mascot art, not tiny chips.", "Do not add extra lesson types. Map onto 复习测评课 + 报告.", "R63/R64/R17.", "L03", "Same card chrome as the lesson card, different illustration."),
        ("V12", "One blue rounded button family: Enter, Go, Review, Start, Report; disabled = grey/translucent", "统一蓝圆角按钮；不能点就变灰", "One CTA shape everywhere. Disabled is still visible.", "Button color can be our orange. Do not invent a new control per module.", "L07 CTA family. 去上课 / 去预习 / 领奖 / 去复习 / 看报告.", "L07", "Kids learn one affordance."),
        ("V13", "Foreground mascot & buttons, mid chests/signposts, background sea life", "前景角色按钮、中景宝箱路标、后景生物", "Three depths. Shadows. Nothing important lives in the wallpaper.", "Do not flatten into one layer.", "L00 back · L01–L05 mid · L06–L07 front · L09–L11 overlay.", "all", "Figma: name groups exactly these depths."),
        ("V14", "Bottom colorful circles (songs, diary, AI, games, globe…)", "底栏一排彩色圆图标", "Footer is a STICKY overlay, not on the sea floor.", "Do not replace Chat / Class / Explore / Play with their 6 circles. Do not put a 'lesson 2' tab that leaves Class.", "L10 our 4 tabs. Optional floor pill already covers 'lesson n'.", "L10", "Path lives inside Class."),
        ("V15", "Teacher photo + class time on the lesson card", "卡片上老师头像+上课时间", "The card can show WHO and WHEN for teaching.", "Do not force a calendar class if our 教学 is on-demand AI class.", "Optional on L03. Our 教学 is Go to Class with the AI teacher. Time/duration we already have (10 min).", "L03", "Prefer duration + status we already show."),
    ]
    copy_bg = GREEN_SOFT
    skip_bg = ORANGE_SOFT
    for i, row in enumerate(rows):
        r = 4 + i
        bg = WHITE if i % 2 == 0 else GREY
        for c, val in enumerate(row, 1):
            text_cell(ws, r, c, val, bg=bg)
        ws.cell(r, 4).fill = fill(copy_bg)
        ws.cell(r, 5).fill = fill(skip_bg)
        ws.row_dimensions[r].height = 64
        ws.cell(r, 1).font = font(11, True, NAVY)
    # rule strip
    rr = 20
    ws.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=cols)
    header_cell(ws, rr, 1, "Object scale on OUR path  ·  我们这条路上的物件大小（对齐视频）", bg=NAVY2)
    scale = [
        "BIG CARD 大卡片 — Lesson (教学) · 复习测评课 Progress Test · optional Graduation / Stage Report. One main CTA.",
        "ON THE CARD 卡片内 — 预习 Preview · 教学 Teaching (Live Class) · 练习 Practice · 总结 Summary · 领奖 Award icon. Green/grey locks under each.",
        "FLOOR CHEST 地上宝箱 — 领奖 (if not on card) · 复习 Review · 口语 Speaking · 听力 Listening. Smaller than the card. Button on the chest.",
        "FLOOR PILL 地面胶囊 — lesson n / 第 n 课 under that cluster.",
        "SIGN 路标 — Unit n arrow + section title pill.",
        "GUIDE 向导 — teacher on the floor, speech, Go.",
        "PEEK 探出 — next locked card on the right edge.",
        "OVERLAY 浮层 — header + Class tab bar, do not scroll.",
    ]
    for i, t in enumerate(scale):
        r = 21 + i
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols)
        text_cell(ws, r, 1, "• " + t, bg=GOLD_SOFT if i < 3 else (WHITE if i % 2 == 0 else GREY))
        ws.row_dimensions[r].height = 26
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:H{3+len(rows)}"


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
        ("R01", "L01", "Ground plane", "共用地面", "Shared floor / sea-floor path", "共用地面（横向路）", "This week's path", "本周路线", "One horizontal floor; all objects sit on it with contact shadows", "Required 必出", "Always on Class weekly plan", "VIDEO FEEL: sea floor. Objects share one Y. Horizontal scroll. Not a winding map and not a chip bar."),
        ("R02", "L03", "Big cards", "主事件卡片", "Lesson event card", "课程大卡片", "Lesson 3", "第 3 课", "Large rounded card, thick friendly border (video: yellow), sits on the floor", "Required 必出", "One for every lesson this week", "VIDEO HIERARCHY: CARD > chest. Current card biggest. Carries type, title, duration, words, sentences, 3D art, plus the in-class mini-route (L04)."),
        ("R03", "L02", "Wayfinding", "路标", "Unit signpost", "单元路标", "Unit 1", "Unit 1", "Yellow arrow signpost planted on the floor (video: Unit 11)", "Required 必出", "At the start of the current unit cluster", "Kids read unit from the road, not only the header."),
        ("R04", "L03", "Big cards", "主事件卡片", "Next-card peek + lock", "下一张卡片探出+锁", "Finish this lesson first", "先走完这一课", "24–40 pt of the next card visible on the right; lock + grey CTA", "Required 必出", "Whenever another lesson/test exists to the right", "VIDEO FEEL: the path continues off-screen. Never dead-end the current card."),
        # MICRO PATH
        ("R05", "L04", "On-card mini-route", "卡片内小路线", "In-class section on the card", "课中分段（在卡片上）", "In class", "课中", "The 5 in-class steps as a row inside the lesson card", "Required 必出", "On every lesson card", "VIDEO: Preview / Live Class / Review / Homework sit ON the card. Ours: 预习-教学-练习-总结-领奖 on the card. Do not mix 口语听力 onto this row."),
        ("R06", "L05", "Floor chests", "地面宝箱", "After-class chest cluster", "课后宝箱组", "After class", "课后", "Chests sitting on the floor to the right of the lesson card", "Required 必出", "After each lesson card", "VIDEO: Review + PaperHomework chests on the floor. Ours: 复习-口语-听力-报告 as chests (报告 may upgrade to a destination card)."),
        ("R07", "L01", "Ground plane", "共用地面", "Left-to-right object order", "从左到右的物件顺序", "—", "—", "Card then chests then next card — reading order is X, not a line graphic", "Required 必出", "Always", "VIDEO FEEL: the route is the arrangement on the floor. A drawn road is optional; alignment is required."),
        ("R08", "L03", "Big cards", "主事件卡片", "Current-card emphasis", "当前卡片强调", "You are here", "你在这里", "Current card larger, full color; others smaller/dimmer", "Required 必出", "Always one current event", "VIDEO: the live lesson card dominates. Tests to the right wait their turn."),
        # 9 NODES — listed also in sheet 03, but they MUST appear on the route
        ("R09", "L04", "On-card mini-route", "卡片内小路线", "Node: Preview", "节点：预习", "Peek first", "预习", "Document / binoculars on the card row (video: yellow Preview tab)", "Required 必出", "Step 1 of every lesson — ON the lesson card", "MISSING in our old chip bar. First in-class lock."),
        ("R10", "L04", "On-card mini-route", "卡片内小路线", "Node: Teaching", "节点：教学", "Class time", "教学", "TV / teacher / play-class icon (video: Live Class)", "Required 必出", "Step 2 — ON the lesson card AND as the card's main Go to Class", "Main event. Video's 'Go to Class' on the card is this step."),
        ("R11", "L04", "On-card mini-route", "卡片内小路线", "Node: Practice", "节点：练习", "Try it", "练习", "Target / bullseye — keep", "Required 必出", "Step 3 — ON the lesson card", "Was the only highlighted chip. Now one of five on-card steps."),
        ("R12", "L04", "On-card mini-route", "卡片内小路线", "Node: Summary", "节点：总结", "Wrap up", "总结", "Star notebook / recap", "Required 必出", "Step 4 — ON the lesson card", "MISSING before. Still in-class, still on the card."),
        ("R13", "L05", "Floor chests", "地面宝箱", "Chest: Award (landmark)", "宝箱：领奖", "Prize", "领奖", "Treasure chest on/just after the card — bigger bounce than other chests", "Required 必出", "Step 5, end of in-class", "VIDEO language: chests = rewards. Gate before after-class chests."),
        ("R14", "L05", "Floor chests", "地面宝箱", "Chest: Review", "宝箱：复习", "Replay", "复习", "Chest + blue/orange button (video: Review chest)", "Required 必出", "Step 6, first after-class chest", "VIDEO maps almost 1:1. Sits on the floor after the lesson card."),
        ("R15", "L05", "Floor chests", "地面宝箱", "Chest: Speaking", "宝箱：口语", "Say it", "口语", "Chest or mic-on-chest; keep mic icon", "Required 必出", "Step 7", "Do not put on the lesson-card row. Floor object, smaller than the card."),
        ("R16", "L05", "Floor chests", "地面宝箱", "Chest: Listening", "宝箱：听力", "Listen", "听力", "Chest or headphone-on-chest; keep headphone icon", "Required 必出", "Step 8", "Same as Speaking — floor chest, not a 4th chip on the card."),
        ("R17", "L03", "Big cards", "主事件卡片", "Destination: Report", "终点：报告", "My report", "报告", "Stage Report-style card (video) or a chest that opens a report sheet", "Required 必出", "Step 9, end of the lesson cluster", "VIDEO: Stage Report is a BIG card with mascot + Report button. Prefer card at lesson end; unit 复习测评课 uses Progress Test / Graduation Test card scale."),
        # NODE ANATOMY (each node needs these sub-elements)
        ("R18", "L04", "On-card mini-route", "卡片内小路线", "Step icon", "步骤图标", "—", "—", "Simple, 1 concept, readable at 32–40 pt", "Required 必出", "Every on-card step and chest", "Different silhouette so grey+lock still works."),
        ("R19", "L04", "On-card mini-route", "卡片内小路线", "Step label ZH", "步骤中文名", "预习 / 教学 / …", "预习 / 教学 / …", "Under the icon, always visible", "Required 必出", "Every step", "Never hide Chinese. 2 characters preferred."),
        ("R20", "L04", "On-card mini-route", "卡片内小路线", "Step label EN", "步骤英文名", "Preview / Teaching / …", "Preview / Teaching / …", "Locale swap or second line", "Required 必出", "When language = EN; reserve space even in ZH build", "Layout must survive Listening / Practice."),
        ("R21", "L08", "Locks", "锁", "Green vs grey lock under step", "步骤下的绿锁/灰锁", "—", "—", "Video: small lock below each mini-step", "Required 必出", "Every mini-step and peeked card", "THIS is the video's state language. Lock under icon, not a badge covering art."),
        ("R22", "L04", "On-card mini-route", "卡片内小路线", "Tap target", "点击热区", "—", "—", "Min 44×44 pt", "Required 必出", "Every step and chest", "Video cards are generous. Do not go back to tiny chips."),
        # GUIDE + CTA
        ("R23", "L06", "Mascot guide", "向导", "Guide character on the floor", "站在地上的向导", "—", "—", "Our 3D teacher (not their parrot) + optional kid avatar", "Required 必出", "Beside the current card or chest", "VIDEO FEEL: guide stands ON the path with speech + Go."),
        ("R24", "L03", "Big cards", "主事件卡片", "Current-card scale", "当前卡片强调", "You are here", "你在这里", "Largest card, full saturation", "Required 必出", "Current lesson", "Video: the live lesson card dominates the frame."),
        ("R25", "L03", "Big cards", "主事件卡片", "Next-card peek", "下一张预告", "Next: Lesson 4", "下一课", "Right-edge peek + lock", "Required 必出", "If something exists to the right", "Video already peeks the next locked card."),
        ("R26", "L07", "CTA family", "主按钮家族", "Primary CTA on current object", "当前物件主按钮", "(see step CTA)", "（见各步 CTA）", "Same rounded pill on cards AND chests (video: blue Enter/Go/Start)", "Required 必出", "Whenever the current step is playable", "One family. Grey when locked. No 'Farm Anim…' truncation."),
        ("R27", "L07", "CTA family", "主按钮家族", "Secondary: replay", "次按钮：重玩", "Play again", "再玩一次", "Ghost / small replay", "Recommended 建议", "When a completed object is selected", "Do not compete with the primary CTA."),
        # LESSON SIGNBOARD (anchors the path)
        ("R28", "L03", "Lesson signboard", "课程牌", "Lesson type tag", "课型标签", "Hear & Speak", "听说", "Colored pill (type color)", "Required 必出", "On current lesson station / hero", "Fix screenshot English 'Hear of'. Use dictionary in 07_Lesson_Types."),
        ("R29", "L03", "Lesson signboard", "课程牌", "Lesson number", "课次", "Lesson 3", "第 3 课", "Neutral chip", "Required 必出", "Always on current lesson", "Keep. Pair with Level · Unit."),
        ("R30", "L03", "Lesson signboard", "课程牌", "Level · Unit", "级别 · 单元", "Level 4 · Unit 1", "Level 4 · Unit 1", "Overlay chip", "Required 必出", "Always on current lesson", "Keep from screenshot."),
        ("R31", "L03", "Lesson signboard", "课程牌", "Lesson title", "课程标题", "Farm Animals", "农场动物", "Large rounded title", "Required 必出", "Always on current lesson", "Keep large white title. Provide ZH + EN."),
        ("R32", "L03", "Lesson signboard", "课程牌", "Duration", "时长", "10 min", "10 分钟", "Clock icon + time", "Required 必出", "On current lesson", "Keep. Duration may change per step if we later show remaining time; v1 = lesson duration."),
        ("R33", "L03", "Lesson signboard", "课程牌", "Lesson status", "课程状态", "In progress / Not started / Done", "进行中 / 未开始 / 已完成", "Signal bars or status chip", "Required 必出", "On current lesson", "Keep. Map to week-station state too."),
        ("R34", "L03", "Lesson signboard", "课程牌", "Words preview", "单词预告", "Words: friend, classmate…", "单词：friend, classmate…", "Text line under title", "Required 必出", "When the lesson has target words", "Keep. Tells kids what this path is 'about'."),
        ("R35", "L03", "Lesson signboard", "课程牌", "Sentences preview", "句型预告", "Sentences: This is my friend.", "句子：This is my friend.", "Text line under words", "Required 必出", "When the lesson has target sentences", "Keep. Empty-state: hide the line, do not show 'Sentences: —'."),
        ("R36", "L03", "Lesson signboard", "课程牌", "Theme illustration", "主题插画", "—", "—", "3D scene for this lesson", "Required 必出", "Current lesson", "Keep quality from screenshot. The path sits in front / below, not replacing the art."),
        # PAGE CHROME still essential for the route to make sense
        ("R37", "L09", "Header", "顶部", "Current child avatar", "当前孩子头像", "—", "—", "Circular photo/avatar", "Required 必出", "Always", "Same avatar as the traveler on the path."),
        ("R38", "L09", "Header", "顶部", "Sibling / profile switcher", "多孩子切换", "Switch kid", "切换宝贝", "Stacked avatars + swap icon", "Required 必出", "When the family has 2+ kids", "Keep from screenshot. Switching kid switches the path progress."),
        ("R39", "L09", "Header", "顶部", "Screen title", "页面标题", "Weekly Study Plan", "本周学习计划", "Centered rounded title", "Required 必出", "Always", "Bilingual. This is the week-map, not a random class list."),
        ("R40", "L09", "Header", "顶部", "More lessons entry", "更多课程入口", "More lessons", "更多课程", "Pill + lesson thumbnail (submarine in screenshot)", "Required 必出", "Always", "Keep. Must return to the same spot on the path."),
        ("R41", "L10", "Tab bar", "底栏", "Class tab (selected)", "上课 Tab（选中）", "Class", "上课", "Green book + star + yellow glow", "Required 必出", "Always", "Keep selected treatment. Route lives here."),
        ("R42", "L10", "Tab bar", "底栏", "Chat / Explore / Play tabs", "聊天 / 探索 / 玩", "Chat · Explore · Play", "聊天 · 探索 · 玩", "Honey pot / chart / VS", "Required 必出", "Always", "Keep. Not part of the lesson route."),
        # OVERLAYS that belong to the route
        ("R43", "L11", "Overlays", "弹层", "Award celebration", "领奖庆祝", "You earned a star!", "你得到一颗星！", "Chest open + stars + stamp on S5", "Required 必出", "When S5 is claimed", "Then auto-pan to after-class path so Review is obviously next."),
        ("R44", "L11", "Overlays", "弹层", "Locked-step feedback", "未解锁反馈", "Let's finish Teaching first", "先上完课再来", "Lock shake + tiny coach line", "Required 必出", "When a locked node is tapped", "Never dead-end. Tell the child which node to do."),
        ("R45", "L11", "Overlays", "弹层", "Mic permission for Speaking", "口语麦克风授权", "Let me hear you", "让老师听见你", "Friendly mic card", "Required 必出", "First time entering Speaking", "Kids path must not jump into a system dialog without a kid-facing explainer."),
        ("R46", "L11", "Overlays", "弹层", "Report sheet", "报告单", "My lesson report", "我的本课报告", "Stars, words, speaking count, listening score", "Required 必出", "On S9 or after claiming S9", "Kid-first layout. Parent-detail can be a second page / toggle."),
        ("R47", "L08", "Node anatomy", "节点构造", "Stars / stamps on completed nodes", "完成章/星星", "Done!", "完成！", "Star or ink stamp", "Required 必出", "Each completed step", "Makes the walked path feel collected, not just grey checks."),
        ("R48", "L05", "Floor chests", "地面宝箱", "Card-to-chest gap (Award → Review)", "卡片到宝箱的分界", "After class starts here", "课后从这里开始", "Physical gap on the floor after the lesson card / award chest", "Required 必出", "Between S5 and S6", "VIDEO: chests sit AFTER the card, not inside it. That gap IS the 课中/课后 gate."),
        ("R49", "L02", "Wayfinding", "路标", "Section header pill", "段落标题胶囊", "Language Booster / unit theme", "单元主题名", "Floating yellow rounded title above the cluster (video: Language Booster 3)", "Required 必出", "Above the current unit/lesson cluster", "VIDEO FEEL: a named chapter in the world, not only in the app bar."),
        ("R50", "L03", "Big cards", "主事件卡片", "Unit test / graduation cards", "单元测评 / 毕业测卡片", "Progress Test · Graduation Test", "阶段测评 · 毕业测", "Large illustrated cards with mascot + Start (video end of path)", "Required 必出", "At unit end — maps to 复习测评课", "VIDEO: Progress Test, Graduation Test, Stage Report are CARDS not chips. Use this scale for 复习测评课 and the final 报告."),
        ("R51", "L07", "CTA", "主按钮", "CTA lesson nickname", "按钮上的课名简称", "Farm Animals", "农场动物", "On the pill, full name or 2 lines", "Required 必出", "On primary CTA", "Do not clip to 'Farm Anim…'."),
        ("R52", "L06", "You-are-here", "你在这里", "Teacher companion on path", "路上的老师伙伴", "—", "—", "3D teacher from current UI, pointing to the next node", "Recommended 建议", "On current lesson", "Keep the beloved teacher, but move her from card-left onto the road so she walks with the kid."),
        ("R53", "L04", "Node anatomy", "节点构造", "Remaining-time or step status text", "步骤状态小字", "In progress", "进行中", "Under current label only", "Recommended 建议", "Current node", "Optional. Don't clutter every node."),
        ("R54", "L06", "Overlays", "弹层", "Empty / first-time coach", "首次引导", "We walk this path together", "我们一起走这条路", "Teacher points S1 → S9 once", "Recommended 建议", "First launch of the new Class tab", "One-time. Then the path itself must be self-explanatory."),
        ("R55", "L04", "Lesson path", "课内小路线", "Collapsed completed cluster", "已完成段可收起", "In class done ✓", "课中完成 ✓", "S1–S5 can shrink to a stamped ribbon after Award is claimed", "Recommended 建议", "After S5 claimed, if 9 nodes overflow a phone", "If we collapse, the ribbon must still be tappable to expand. Never delete walked steps."),
        ("R56", "L02", "Wayfinding", "路标", "Unit theme name", "单元主题名", "Farm Animals", "农场动物", "May equal lesson title or sit in the section pill", "Recommended 建议", "When unit has a theme", "Helps the week feel like one story. Video: Language Booster 3."),
        # VIDEO-FEEL ELEMENTS (from Lark frames)
        ("R57", "L02", "Wayfinding", "路标", "Floor lesson pill", "地面课次胶囊", "lesson 3", "第 3 课", "Small pill sitting ON the floor under the card/chests (video: lesson 1 / lesson 2)", "Required 必出", "Under each lesson cluster", "VIDEO FEEL: the lesson number lives in the world, not only on the card header."),
        ("R58", "L06", "Mascot guide", "向导", "Speech bubble", "说话气泡", "Hey! Your prize chest is still waiting. Come with me!", "嘿！奖品宝箱还在等你，跟我走！", "White rounded bubble from the guide, 1–2 short lines", "Required 必出", "When a landmark is waiting (unclaimed 领奖 / unit test)", "VIDEO: parrot invites the next chest. Ours: teacher. Keep it spoken-kid, not marketing."),
        ("R59", "L06", "Mascot guide", "向导", "Go on the speech", "气泡上的出发", "Go", "出发", "Small blue/orange pill inside or under the bubble (video: Go)", "Required 必出", "Together with R58", "Tapping Go pans to the invited object and focuses its CTA."),
        ("R60", "L01", "Ground plane", "共用地面", "Contact shadow under objects", "物件落地震影", "—", "—", "Soft oval shadow so cards/chests look planted", "Required 必出", "Every floor object", "VIDEO depth: foreground objects, mid chests, quiet world. Shadows sell the plane."),
        ("R61", "L01", "Ground plane", "共用地面", "Horizontal pan / scroll", "横向滑动", "—", "—", "Swipe left-right along the unit. Header and tabs stay.", "Required 必出", "Always", "VIDEO FEEL: you walk the path by scrolling the world, not by switching pages."),
        ("R62", "L07", "CTA family", "主按钮家族", "Disabled / grey CTA", "未解锁灰按钮", "Go to Class (disabled)", "去上课（不可点）", "Video: greyed Go to Class / translucent Start", "Required 必出", "When the card/chest is locked or not current", "Kids see the button exists but cannot press it yet — plus a lock."),
        ("R63", "L03", "Big cards", "主事件卡片", "Progress Test card", "阶段测评卡片", "Progress Test", "阶段测评", "Mascot + chest + A+ art, subtitle Unit learning test, Start", "Required 必出", "Maps to 复习测评课 (mid-unit, e.g. L6)", "Copy the VIDEO card type, not their copy deck. Keep our lesson-type name."),
        ("R64", "L03", "Big cards", "主事件卡片", "Graduation / stage report cards", "毕业测 / 阶段报告卡片", "Graduation Test · Stage Report", "毕业测 · 阶段报告", "Large illustrated destination cards at the end of a block", "Recommended 建议", "End of unit / after last Report", "Video has both. We can merge into 复习测评课 + 报告 if we must not add extra lesson types."),
        ("R65", "L00", "World", "主题世界", "Low-contrast ambient creatures", "低对比氛围生物", "—", "—", "Video: line-art whale/turtle. Ours: farm animals stay in L00, never covering CTAs", "Required 必出", "Always", "Decoration only. Safe margin around every tappable object."),
        ("R66", "L09", "Header overlay", "顶部浮层", "Header does not scroll with the path", "顶栏不跟路线滚动", "—", "—", "Pinned HUD", "Required 必出", "Always", "VIDEO: world moves, chrome stays. Two layers."),
        ("R67", "L10", "Tab overlay", "底栏浮层", "Tab bar does not scroll with the path", "底栏不跟路线滚动", "—", "—", "Pinned overlay + scroll padding", "Required 必出", "Always", "Do not put Chat/Explore/Play icons onto the sea floor."),
        ("R68", "L07", "CTA family", "主按钮家族", "Chest action button", "宝箱上的行动按钮", "Review / Start Speaking / …", "去复习 / 去开口 / …", "Same pill on every chest (video: blue Review, PaperHomework)", "Required 必出", "Every floor chest", "One control, one verb. Do not invent a second UI on the chest."),
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
        ("coach.prize_waiting", "Mascot bubble", "Hey! Your prize chest is still waiting. Come with me!", "嘿！奖品宝箱还在等你，跟我走！", "Yes", "40 / 18", "Don't write unit test treasure chest if we mean 领奖", "Video parrot line, rewritten for our Award chest."),
        ("cta.go", "Mascot bubble", "Go", "出发", "Yes", "4 / 2", "Don't use Enter if the mascot is inviting a pan", "Video Go."),
        ("cta.enter", "Card / printouts", "Enter", "进入", "Yes", "8 / 2", "", "Video uses Enter on some cards."),
        ("cta.start", "Test card", "Start", "开始", "Yes", "8 / 2", "", "Video Progress/Graduation Test."),
        ("test.progress.title", "Test card", "Progress Test", "阶段测评", "Yes", "18 / 4", "", "Maps to 复习测评课."),
        ("test.progress.sub", "Test card", "Unit learning test", "本单元学习测验", "Yes", "22 / 8", "", ""),
        ("test.graduation.title", "Test card", "Graduation Test", "毕业测", "Yes", "18 / 4", "", "Optional end-of-block card."),
        ("test.graduation.sub", "Test card", "Test for learning results", "检验学习成果", "Yes", "28 / 8", "", ""),
        ("test.stage_report.title", "Report card", "Stage Report", "阶段报告", "Yes", "16 / 4", "", "Video destination card. Maps to 报告."),
        ("wayfinding.unit", "Signpost", "Unit {n}", "Unit {n}", "Yes", "10 / 10", "", "Yellow arrow on the floor."),
        ("wayfinding.lesson_pill", "Floor pill", "lesson {n}", "第 {n} 课", "Yes", "12 / 6", "", "Video: lesson 1 under chests."),
        ("cta.go_to_class_off", "Lesson card", "Go to Class", "去上课", "Yes", "14 / 4", "", "Same string as cta.teaching; grey + lock when not ready (video)."),
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
            "Video feel: a themed WORLD, a shared FLOOR, swipe left-right. BIG lesson CARD (in-class 5 steps + locks on the card) → CHESTS on the floor (复习/口语/听力) → next card peeking. Sticky header + tabs.",
            "Fix 改",
            "Chips do not feel like a journey. The video is cards and chests on a sea floor.",
            "Build the floor first. Then plant cards and chests. Do not restyle the chips and call it done.",
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
            "VIDEO: parrot stands ON the floor, talks, offers Go. Ours: 3D teacher on the floor beside the current card/chest.",
            "Fix 改",
            "She is loved, but she is not helping the route.",
            "Reuse the 3D teacher. Put her on the road.",
        ),
        (
            "Card vs chest scale",
            "Every step is the same size chip.",
            "VIDEO HIERARCHY: lesson / test / report = BIG CARD. 复习 口语 听力 领奖 = smaller CHESTS on the floor. Mini-locks live ON the card.",
            "Fix 改",
            "Equal chips hide what is the main event. Kids follow the big card first.",
            "If 口语 is as large as Farm Animals, the layer failed.",
        ),
        (
            "Week context",
            "Only one lesson card. Other lessons hidden behind More lessons.",
            "Horizontal floor of cards this week; More lessons is extra / library. Next card always peeks.",
            "Add 补",
            "A weekly plan that shows one card is not a plan.",
            "Plant every lesson as a card on the floor, like the video's left-to-right stations.",
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
            "Horizontal pan of the world; mascot Go; lock shake; grey CTA until unlocked; chest bounce; auto-pan to the next chest after Award (video: Come with me).",
            "Add 补",
            "Feeling of following comes from walking a floor, not from a highlight tint.",
            "Spec: complete on-card step → next lock turns green → after Award, pan to 复习 chest.",
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
        "Not final art. Horizontal floor like the video: signpost → big lesson CARD (5 in-class locks) → floor CHESTS → next card peek. 不是终稿。按视频做成横向地面：路标 → 大课卡（课中五锁） → 地上宝箱 → 下一张探出。",
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
    header_cell(ws, 8, 1, "HORIZONTAL FLOOR  当前课 Farm Animals  像视频一样从左滑到右  CARD then CHESTS then PEEK", bg=NAVY2)

    # in class band
    ws.merge_cells("A9:F9")
    header_cell(ws, 9, 1, "ON THE CARD  课中五步锁在卡片上   Preview → Teaching → Practice → Summary → Award", bg=ORANGE)
    ws.merge_cells("G9:K9")
    header_cell(ws, 9, 7, "ON THE FLOOR  课后宝箱   Review · Speaking · Listening · Report card peek", bg=BLUE)

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
        "Layers like the video: L00 world (not shown) → L01 floor → L02 signs → L03 CARD → L04 locks on card → L05 chests → L06 teacher+bubble → L07 CTA → L09/L10 sticky chrome.",
        "示例对齐原图课程：Level 4 · Unit 1 · 第 3 课 · Farm Animals · 听说。老师站在地上说话，主按钮是去上课。下一张课卡从右边探出并带锁。",
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
        "01c_Video_Feel",
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
        "01c_Video_Feel": BLUE,
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
    build_video_feel(wb)
    add_print_and_meta(wb)
    wb.save(OUT)
    print("Wrote", OUT, "sheets:", wb.sheetnames)


if __name__ == "__main__":
    main()
