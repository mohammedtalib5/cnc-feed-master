# =========================
# CNC PROFESSIONAL BOT V5 - WORKSHOP EXPERT
# Author: CNC Workshop Assistant
# =========================
# Replace TOKEN only.
# Requirements:
# python-telegram-bot==21.6

import math
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

TOKEN = "8988980195:AAEznSXisHEEqA2R3IjbTnve3IEAe1ibu4Y"

(
    PROCESS,
    MACHINE,
    MATERIAL_GROUP,
    MATERIAL_TYPE,
    OP_SUBTYPE,
    TOOL_KIND,
    INSERT,
    NOSE,
    COOLANT,
    CLAMP,
    MODE,
    DIAMETER,
    SECOND_VALUE,
    THIRD_VALUE,
    TEETH,
    DEPTH,
    PITCH,
    C_COUNT,
    DIAG_SOUND,
    DIAG_CHIP,
    DIAG_FINISH,
    REPORT_PROGRAM,
    REPORT_QTY,
    REPORT_TIME,
) = range(24)

# =========================
# MAIN DATA
# =========================

PROCESSES = [
    "خراطة خارجية",
    "خراطة داخلية",
    "تفريز",
    "ثقب",
    "قلوظ",
    "سن خارجي",
    "سن داخلي",
    "Groove",
    "Cut Off",
    "C-Axis",
    "تشخيص تشغيل",
    "G-code Helper",
    "تقرير عدة",
]

MACHINES = {
    "Z-MAT T500": {"max_rpm": 3500, "stability": 0.95},
    "VIVA TURN": {"max_rpm": 3500, "stability": 0.92},
    "CK40": {"max_rpm": 3000, "stability": 0.85},
    "GSK": {"max_rpm": 3000, "stability": 0.88},
    "SIEMENS": {"max_rpm": 4000, "stability": 1.00},
    "SYNTEC MILL": {"max_rpm": 8000, "stability": 1.00},
}

MATERIAL_GROUPS = ["حديد", "ستانلس", "ألمنيوم", "براص / نحاس", "بلاستك"]

MATERIAL_TYPES = {
    "حديد": [
        "Mild Steel", "ST37", "ST52", "C45", "CK45",
        "Tool Steel", "Hardened Steel", "Hard Chrome"
    ],
    "ستانلس": ["304", "316", "310", "420", "430", "Duplex"],
    "ألمنيوم": ["6061", "7075", "5083", "6082", "Cast Aluminum"],
    "براص / نحاس": ["Brass", "Free Cutting Brass", "Bronze", "Phosphor Bronze", "Copper"],
    "بلاستك": ["Delrin", "Nylon", "PVC"],
}

# Vc base m/min
MATERIAL_DB = {
    "Mild Steel": {"vc": 130, "hardness": 1.0},
    "ST37": {"vc": 140, "hardness": 0.9},
    "ST52": {"vc": 115, "hardness": 1.05},
    "C45": {"vc": 110, "hardness": 1.15},
    "CK45": {"vc": 95, "hardness": 1.25},
    "Tool Steel": {"vc": 55, "hardness": 1.6},
    "Hardened Steel": {"vc": 35, "hardness": 2.0},
    "Hard Chrome": {"vc": 30, "hardness": 2.2},

    "304": {"vc": 70, "hardness": 1.4},
    "316": {"vc": 60, "hardness": 1.5},
    "310": {"vc": 45, "hardness": 1.7},
    "420": {"vc": 50, "hardness": 1.6},
    "430": {"vc": 80, "hardness": 1.25},
    "Duplex": {"vc": 45, "hardness": 1.8},

    "6061": {"vc": 280, "hardness": 0.6},
    "7075": {"vc": 220, "hardness": 0.8},
    "5083": {"vc": 200, "hardness": 0.75},
    "6082": {"vc": 240, "hardness": 0.7},
    "Cast Aluminum": {"vc": 180, "hardness": 0.85},

    "Brass": {"vc": 220, "hardness": 0.7},
    "Free Cutting Brass": {"vc": 280, "hardness": 0.55},
    "Bronze": {"vc": 120, "hardness": 1.0},
    "Phosphor Bronze": {"vc": 90, "hardness": 1.2},
    "Copper": {"vc": 130, "hardness": 0.8},

    "Delrin": {"vc": 300, "hardness": 0.4},
    "Nylon": {"vc": 220, "hardness": 0.45},
    "PVC": {"vc": 160, "hardness": 0.5},
}

INSERTS_BY_GROUP = {
    "حديد": [
        "CNMG", "CNMM", "WNMG", "DNMG", "TNMG", "SNMG",
        "CCMT", "DCMT", "MGMN", "GTN", "Cut-Off",
        "16ER", "16IR", "11ER", "11IR", "APMT", "R390", "RPMT"
    ],
    "ستانلس": [
        "TNMG160404R-VF", "VCMT160404-OTM", "VCMT331-OTM",
        "CNMG Stainless", "WNMG Stainless", "CCMT Stainless", "DCMT Stainless",
        "MGMN Stainless", "Cut-Off Stainless", "16ER Stainless", "16IR Stainless",
        "APMT Stainless", "R390 Stainless", "RPMT Stainless", "MTT603", "HLT316"
    ],
    "ألمنيوم": [
        "VCGT", "CCGT", "DCGT", "TCGT", "Polished Insert",
        "Aluminum Endmill", "2F Aluminum", "3F Aluminum", "APKT Aluminum"
    ],
    "براص / نحاس": [
        "VCGT", "CCGT", "DCGT", "DNMG", "Brass Insert", "Polished Insert",
        "2F Brass", "3F Brass", "APKT Brass"
    ],
    "بلاستك": ["HSS", "Polished Insert", "2F Plastic", "VCGT", "CCGT"],
}

NOSES = ["0.2", "0.4", "0.8", "1.2"]
COOLANTS = ["Flood", "Mist", "Air", "Dry"]
CLAMPS = ["قوي", "متوسط", "ضعيف"]
MODES = ["Roughing", "Semi Finish", "Finishing"]

TURNING_SUBTYPES = ["Rough OD", "Finish OD", "Facing"]
BORING_SUBTYPES = ["Boring Rough", "Boring Finish"]
MILLING_SUBTYPES = [
    "Face Milling", "Side Milling", "Slot", "Pocket",
    "Adaptive", "Helical", "Chamfer", "Thread Milling"
]
DRILL_SUBTYPES = ["HSS Drill", "Carbide Drill", "Insert Drill", "Deep Drill"]
TAP_SUBTYPES = ["HSS Tap", "Spiral Tap", "Form Tap", "Carbide Tap"]
GROOVE_SUBTYPES = ["External Groove", "Internal Groove", "Face Groove"]
CUT_SUBTYPES = ["Straight Cut", "Peck Cut"]
CAXIS_SUBTYPES = ["Cross Drill", "Cross Tap", "C Milling", "Helical C-Axis"]

# =========================
# HELPERS
# =========================

def keyboard(items, cols=2):
    return ReplyKeyboardMarkup([items[i:i+cols] for i in range(0, len(items), cols)], resize_keyboard=True)

def to_float(text):
    return float(str(text).strip().replace(",", "."))

def safe_rpm(vc, diameter):
    if diameter <= 0:
        return 0
    return (vc * 1000) / (math.pi * diameter)

def machine_data(name):
    return MACHINES.get(name, {"max_rpm": 3500, "stability": 0.90})

def material_vc(material):
    return MATERIAL_DB.get(material, {"vc": 100, "hardness": 1.0})["vc"]

def correction_factor(coolant, clamp, mode, nose, machine_name):
    factor = machine_data(machine_name)["stability"]

    if coolant == "Dry":
        factor *= 0.78
    elif coolant == "Air":
        factor *= 0.88
    elif coolant == "Mist":
        factor *= 0.95
    elif coolant == "Flood":
        factor *= 1.00

    if clamp == "ضعيف":
        factor *= 0.70
    elif clamp == "متوسط":
        factor *= 0.90
    elif clamp == "قوي":
        factor *= 1.00

    if mode == "Finishing":
        factor *= 0.90
    elif mode == "Semi Finish":
        factor *= 0.95

    try:
        n = float(nose)
        if n >= 1.2:
            factor *= 1.05
        elif n <= 0.2:
            factor *= 0.85
    except Exception:
        pass

    return factor

def base_insert_feed(insert, mode):
    # mm/rev for turning-like operations
    ins = insert.upper()

    if any(x in ins for x in ["MGMN", "GTN", "GROOVE"]):
        rough, finish = 0.06, 0.035
    elif "CUT" in ins:
        rough, finish = 0.05, 0.03
    elif any(x in ins for x in ["16ER", "16IR", "11ER", "11IR", "THREAD"]):
        rough, finish = 0.04, 0.04
    elif any(x in ins for x in ["VCGT", "CCGT", "DCGT", "POLISHED"]):
        rough, finish = 0.10, 0.04
    elif any(x in ins for x in ["CN", "WN", "SN"]):
        rough, finish = 0.25, 0.11
    elif any(x in ins for x in ["DN", "TN"]):
        rough, finish = 0.18, 0.08
    elif any(x in ins for x in ["CC", "DC", "TC", "VC", "VB"]):
        rough, finish = 0.10, 0.05
    elif any(x in ins for x in ["AP", "R390", "RPMT", "SE", "XO"]):
        rough, finish = 0.05, 0.025
    else:
        rough, finish = 0.12, 0.06

    if mode == "Roughing":
        return rough
    if mode == "Semi Finish":
        return (rough + finish) / 2
    return finish

def doc_suggestion(process, insert, nose, mode, diameter=0):
    try:
        n = float(nose)
    except Exception:
        n = 0.4

    if process in ["سن خارجي", "سن داخلي", "قلوظ"]:
        return "حسب خطوة السن"
    if process == "Cut Off":
        return "Peck خفيف حسب القطر"
    if process == "Groove":
        return "نزلات خفيفة حسب عرض القلم"
    if process == "تفريز":
        if mode == "Roughing":
            return f"{max(0.2, diameter*0.10):.2f} - {max(0.4, diameter*0.25):.2f} mm لكل شوط"
        return f"{max(0.05, diameter*0.03):.2f} - {max(0.15, diameter*0.08):.2f} mm لكل شوط"
    if mode == "Roughing":
        return f"{max(0.3, n*1.2):.2f} - {max(1.0, n*3.0):.2f} mm"
    if mode == "Semi Finish":
        return f"{max(0.15, n*0.6):.2f} - {max(0.5, n*1.5):.2f} mm"
    return f"{max(0.05, n*0.2):.2f} - {max(0.25, n*0.8):.2f} mm"

def g50_limit(machine, diameter):
    max_rpm = machine_data(machine)["max_rpm"]
    if diameter >= 150:
        return min(max_rpm, 1200)
    if diameter >= 100:
        return min(max_rpm, 1800)
    if diameter >= 50:
        return min(max_rpm, 2500)
    return min(max_rpm, 3500)

def thread_depth_60(pitch):
    return 0.6134 * pitch

def internal_thread_drill(diameter, pitch):
    return diameter - 1.0825 * pitch

def tap_drill_size(diameter, pitch, tap_type):
    if tap_type == "Form Tap":
        return diameter - 0.50 * pitch
    return diameter - pitch

def warning_common(process, material, rpm_calc, g50, coolant, clamp):
    warnings = []
    if rpm_calc > g50:
        warnings.append("RPM المحسوب أعلى من G50، الماكنة راح تحدده تلقائيًا.")
    if coolant == "Dry" and material in ["304", "316", "310", "Duplex", "Hard Chrome"]:
        warnings.append("بدون تبريد على هذا المعدن خطر، قلل السرعة والفيد.")
    if clamp == "ضعيف":
        warnings.append("التثبيت ضعيف: قلل DOC و Feed.")
    if material in ["304", "316", "Duplex"]:
        warnings.append("ستانلس: لا تخلي العدة تحك بدون قطع واستخدم تبريد جيد.")
    if material in ["Hard Chrome", "Hardened Steel"]:
        warnings.append("معدن صلد: استخدم عدة مناسبة و DOC خفيف.")
    return warnings

def choose_subtypes(process):
    if process == "خراطة خارجية":
        return TURNING_SUBTYPES
    if process == "خراطة داخلية":
        return BORING_SUBTYPES
    if process == "تفريز":
        return MILLING_SUBTYPES
    if process == "ثقب":
        return DRILL_SUBTYPES
    if process == "قلوظ":
        return TAP_SUBTYPES
    if process == "Groove":
        return GROOVE_SUBTYPES
    if process == "Cut Off":
        return CUT_SUBTYPES
    if process == "C-Axis":
        return CAXIS_SUBTYPES
    return ["Standard"]

# =========================
# CONVERSATION
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "CNC Professional Bot V4\n\nاختار العملية:",
        reply_markup=keyboard(PROCESSES, 2)
    )
    return PROCESS

async def process_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    process = update.message.text.strip()
    if process not in PROCESSES:
        await update.message.reply_text("اختار من الأزرار فقط.")
        return PROCESS
    context.user_data["process"] = process

    if process == "تشخيص تشغيل":
        await update.message.reply_text(
            "شنو المشكلة بالصوت؟",
            reply_markup=keyboard(["طبيعي", "اهتزاز", "صرير", "طرق", "صوت عالي"], 2)
        )
        return DIAG_SOUND

    if process == "G-code Helper":
        await update.message.reply_text(
            "ادخل Vc والقطر بهذا الشكل:\nمثال: 180 40",
            reply_markup=ReplyKeyboardRemove()
        )
        return DIAMETER

    if process == "تقرير عدة":
        await update.message.reply_text(
            "ادخل اسم البرنامج / اسم الشغلة:",
            reply_markup=ReplyKeyboardRemove()
        )
        return REPORT_PROGRAM

    await update.message.reply_text("اختار الماكنة:", reply_markup=keyboard(list(MACHINES.keys()), 2))
    return MACHINE

async def machine_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["machine"] = update.message.text.strip()
    process = context.user_data["process"]

    # Thread and tapping still need material for speed.
    await update.message.reply_text("اختار نوع المعدن:", reply_markup=keyboard(MATERIAL_GROUPS, 2))
    return MATERIAL_GROUP

async def material_group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group = update.message.text.strip()
    if group not in MATERIAL_TYPES:
        await update.message.reply_text("اختار معدن من الأزرار فقط.")
        return MATERIAL_GROUP
    context.user_data["material_group"] = group
    await update.message.reply_text("اختار نوع المعدن التفصيلي:", reply_markup=keyboard(MATERIAL_TYPES[group], 2))
    return MATERIAL_TYPE

async def material_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mat = update.message.text.strip()
    group = context.user_data["material_group"]
    if mat not in MATERIAL_TYPES[group]:
        await update.message.reply_text("اختار النوع من الأزرار فقط.")
        return MATERIAL_TYPE
    context.user_data["material_type"] = mat

    process = context.user_data["process"]
    subtypes = choose_subtypes(process)
    await update.message.reply_text("اختار نوع العملية الفرعي:", reply_markup=keyboard(subtypes, 2))
    return OP_SUBTYPE

async def subtype_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["op_subtype"] = update.message.text.strip()
    process = context.user_data["process"]

    if process == "تفريز":
        tool_options = ["Endmill 2F", "Endmill 3F", "Endmill 4F", "Ball Nose", "Roughing Endmill", "Face Mill", "Chamfer Mill"]
        await update.message.reply_text("اختار نوع الكتر:", reply_markup=keyboard(tool_options, 2))
        return TOOL_KIND

    if process == "ثقب":
        # tool kind already subtype enough, continue to coolant/settings after insert-like tool selection.
        context.user_data["tool_kind"] = context.user_data["op_subtype"]
        await update.message.reply_text("اختار نوع التبريد:", reply_markup=keyboard(COOLANTS, 2))
        return COOLANT

    if process == "قلوظ":
        context.user_data["tool_kind"] = context.user_data["op_subtype"]
        await update.message.reply_text("اختار نوع التبريد:", reply_markup=keyboard(COOLANTS, 2))
        return COOLANT

    if process == "C-Axis":
        context.user_data["tool_kind"] = context.user_data["op_subtype"]
        await update.message.reply_text("اختار نوع التبريد:", reply_markup=keyboard(COOLANTS, 2))
        return COOLANT

    group = context.user_data["material_group"]
    await update.message.reply_text("اختار رمز الإنسيرت المناسب:", reply_markup=keyboard(INSERTS_BY_GROUP[group], 2))
    return INSERT

async def tool_kind_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["tool_kind"] = update.message.text.strip()
    group = context.user_data["material_group"]

    # For milling, show only material-related tool inserts.
    await update.message.reply_text("اختار رمز / نوع العدة:", reply_markup=keyboard(INSERTS_BY_GROUP[group], 2))
    return INSERT

async def insert_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["insert"] = update.message.text.strip()
    process = context.user_data["process"]

    if process in ["سن خارجي", "سن داخلي"]:
        await update.message.reply_text("اختار نوع التبريد:", reply_markup=keyboard(COOLANTS, 2))
        return COOLANT

    await update.message.reply_text("اختار نوز الإنسيرت:", reply_markup=keyboard(NOSES, 2))
    return NOSE

async def nose_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nose"] = update.message.text.strip()
    await update.message.reply_text("اختار نوع التبريد:", reply_markup=keyboard(COOLANTS, 2))
    return COOLANT

async def coolant_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["coolant"] = update.message.text.strip()
    await update.message.reply_text("اختار قوة التثبيت:", reply_markup=keyboard(CLAMPS, 2))
    return CLAMP

async def clamp_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["clamp"] = update.message.text.strip()
    process = context.user_data["process"]

    if process in ["ثقب", "قلوظ", "سن خارجي", "سن داخلي", "C-Axis"]:
        context.user_data["mode"] = "Standard"
        return await ask_diameter(update, context)

    await update.message.reply_text("اختار نوع التشغيل:", reply_markup=keyboard(MODES, 2))
    return MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = update.message.text.strip()
    return await ask_diameter(update, context)

async def ask_diameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    process = context.user_data["process"]
    subtype = context.user_data.get("op_subtype", "")

    if process == "تفريز":
        msg = "ادخل قطر الكتر mm"
    elif process == "ثقب":
        msg = "ادخل قطر البريمة mm"
    elif process == "قلوظ":
        msg = "ادخل قطر القلوظ mm\nمثال M10 اكتب 10"
    elif process in ["سن خارجي", "سن داخلي"]:
        msg = "ادخل قطر السن mm\nمثال M40 اكتب 40"
    elif process == "خراطة داخلية":
        msg = "ادخل قطر الحفرة الداخلي mm"
    elif process == "C-Axis":
        msg = "ادخل قطر الشغلة mm"
    else:
        msg = "ادخل قطر الشغلة mm"

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return DIAMETER

async def diameter_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    process = context.user_data["process"]

    if process == "G-code Helper":
        try:
            parts = str(update.message.text).replace(",", ".").split()
            vc = float(parts[0])
            d = float(parts[1])
            calc = safe_rpm(vc, d)
            g50 = 1200 if d >= 150 else 1800 if d >= 100 else 2500 if d >= 50 else 3500
            result = (
                "G-code Helper:\n\n"
                f"Vc = {vc:.0f} m/min\n"
                f"Diameter = {d:g} mm\n"
                f"RPM حسابي = {calc:.0f}\n\n"
                "كود مقترح للخراطة:\n"
                f"G50 S{g50}\n"
                f"G96 S{vc:.0f} M3\n"
                "G99\n\n"
                "للثقب أو السن استخدم G97 بدل G96:\n"
                f"G97 S{min(calc, g50):.0f} M3"
            )
        except Exception:
            result = "ادخل القيم هكذا: 180 40"
        await update.message.reply_text(result)
        await update.message.reply_text("للبدء من جديد اضغط /start")
        return ConversationHandler.END

    try:
        d = to_float(update.message.text)
        if d <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return DIAMETER

    context.user_data["diameter"] = d

    if process == "خراطة داخلية":
        await update.message.reply_text("ادخل قطر قلم البورنك mm")
        return SECOND_VALUE

    if process == "تفريز":
        await update.message.reply_text("ادخل طول / بروز الكتر mm")
        return SECOND_VALUE

    if process == "ثقب":
        await update.message.reply_text("ادخل عمق الثقب mm")
        return SECOND_VALUE

    if process == "قلوظ":
        await update.message.reply_text("ادخل خطوة القلوظ mm")
        return PITCH

    if process in ["سن خارجي", "سن داخلي"]:
        await update.message.reply_text("ادخل خطوة السن mm")
        return PITCH

    if process == "C-Axis":
        await update.message.reply_text("ادخل عدد التقسيمات / الفتحات")
        return C_COUNT

    if process == "Groove":
        await update.message.reply_text("ادخل عرض القلم / الكروف mm")
        return SECOND_VALUE

    if process == "Cut Off":
        await update.message.reply_text("ادخل عرض قلم القطع mm")
        return SECOND_VALUE

    await update.message.reply_text("ادخل DOC mm")
    return DEPTH

async def second_value_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = to_float(update.message.text)
        if value <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return SECOND_VALUE

    context.user_data["second_value"] = value
    process = context.user_data["process"]

    if process == "تفريز":
        await update.message.reply_text("ادخل عدد الأسنان")
        return TEETH

    if process == "خراطة داخلية":
        await update.message.reply_text("ادخل طول بروز البورنك mm")
        return THIRD_VALUE

    if process == "ثقب":
        return await drill_result(update, context)

    if process in ["Groove", "Cut Off"]:
        await update.message.reply_text("ادخل عمق القطع / النزلة mm")
        return DEPTH

    await update.message.reply_text("ادخل DOC mm")
    return DEPTH

async def third_value_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = to_float(update.message.text)
        if value <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return THIRD_VALUE

    context.user_data["third_value"] = value
    await update.message.reply_text("ادخل DOC mm")
    return DEPTH

async def teeth_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        teeth = int(update.message.text.strip())
        if teeth <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل عدد أسنان صحيح.")
        return TEETH

    context.user_data["teeth"] = teeth
    await update.message.reply_text("ادخل عمق القطع لكل شوط mm")
    return DEPTH

async def pitch_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pitch = to_float(update.message.text)
        if pitch <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل خطوة صحيحة.")
        return PITCH

    context.user_data["pitch"] = pitch
    process = context.user_data["process"]

    if process == "قلوظ":
        await update.message.reply_text("ادخل عمق القلوظ mm")
        return DEPTH

    return await thread_result(update, context)

async def c_count_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text.strip())
        if count <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل عدد صحيح.")
        return C_COUNT

    context.user_data["c_count"] = count
    await update.message.reply_text("ادخل قطر الأداة / البريمة mm")
    return SECOND_VALUE

# =========================
# RESULTS
# =========================

async def depth_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        depth = to_float(update.message.text)
        if depth < 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return DEPTH

    context.user_data["depth"] = depth
    process = context.user_data["process"]

    if process == "تفريز":
        return await milling_result(update, context)
    if process == "قلوظ":
        return await tapping_result(update, context)
    if process in ["Groove", "Cut Off"]:
        return await groove_cut_result(update, context)

    return await turning_result(update, context)

async def turning_result(update, context):
    process = context.user_data["process"]
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    insert = context.user_data.get("insert", "General")
    nose = context.user_data.get("nose", "0.4")
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    mode = context.user_data.get("mode", "Roughing")
    diameter = context.user_data["diameter"]
    depth = context.user_data.get("depth", 0)

    vc = material_vc(material) * correction_factor(coolant, clamp, mode, nose, machine)
    calc = safe_rpm(vc, diameter)
    g50 = g50_limit(machine, diameter)
    feed = base_insert_feed(insert, mode)
    g98 = calc * feed

    extra = ""
    warnings = warning_common(process, material, calc, g50, coolant, clamp)

    if process == "خراطة داخلية":
        bar_d = context.user_data.get("second_value", 0)
        bar_len = context.user_data.get("third_value", 0)
        ld = bar_len / bar_d if bar_d else 0
        extra += f"قطر قلم البورنك = {bar_d:g} mm\n"
        extra += f"بروز البورنك = {bar_len:g} mm\n"
        extra += f"نسبة L/D = {ld:.1f}\n"
        if ld > 4:
            warnings.append("بروز البورنك طويل: قلل DOC و Feed.")
        if bar_d < diameter * 0.35:
            warnings.append("قطر قلم البورنك صغير نسبة للحفرة، احتمال اهتزاز.")

    result = (
        "نتيجة الخراطة:\n\n"
        f"العملية: {process}\n"
        f"الماكنة: {machine}\n"
        f"المادة: {material}\n"
        f"الإنسيرت: {insert}\n"
        f"Nose: {nose}\n"
        f"التبريد: {coolant}\n"
        f"التثبيت: {clamp}\n"
        f"التشغيل: {mode}\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {calc:.0f}\n"
        f"G50 S{g50}\n"
        f"G96 S{vc:.0f}\n"
        f"G99 = {feed:.3f} mm/rev\n"
        f"G98 = {g98:.0f} mm/min\n\n"
        f"DOC المدخل = {depth:g} mm\n"
        f"DOC مقترح = {doc_suggestion(process, insert, nose, mode, diameter)}\n\n"
        f"{extra}"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.") +
        "\n\nالقيم تقريبية وتحتاج تعديل حسب الصوت والرايش."
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def milling_result(update, context):
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    group = context.user_data["material_group"]
    subtype = context.user_data["op_subtype"]
    tool_kind = context.user_data["tool_kind"]
    insert = context.user_data.get("insert", tool_kind)
    nose = context.user_data.get("nose", "0.4")
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    mode = context.user_data["mode"]
    diameter = context.user_data["diameter"]
    length = context.user_data["second_value"]
    teeth = context.user_data["teeth"]
    step_depth = context.user_data["depth"]

    vc = material_vc(material) * correction_factor(coolant, clamp, mode, nose, machine)

    if subtype == "Slot":
        vc *= 0.85
    elif subtype == "Adaptive":
        vc *= 1.05
    elif subtype == "Helical":
        vc *= 0.80
    elif subtype == "Chamfer":
        vc *= 0.70

    calc = safe_rpm(vc, diameter)
    g50 = min(machine_data(machine)["max_rpm"], 12000)

    # Fz by material and mode
    if group == "ألمنيوم":
        fz = 0.045
    elif group == "ستانلس":
        fz = 0.018
    elif group == "براص / نحاس":
        fz = 0.035
    elif material in ["Hard Chrome", "Hardened Steel", "Tool Steel"]:
        fz = 0.010
    else:
        fz = 0.025

    if mode == "Finishing":
        fz *= 0.55
    elif mode == "Semi Finish":
        fz *= 0.75

    ld = length / diameter
    warnings = warning_common("تفريز", material, calc, g50, coolant, clamp)

    if ld > 4:
        fz *= 0.55
        warnings.append("بروز الكتر طويل L/D>4: تم تقليل الفيد.")
    elif ld > 3:
        fz *= 0.75
        warnings.append("بروز الكتر متوسط/طويل: راقب الاهتزاز.")

    if subtype == "Slot":
        fz *= 0.70
        stepover = 100
    elif subtype == "Adaptive":
        stepover = 8 if group == "ستانلس" else 12
    elif subtype == "Face Milling":
        stepover = 60
    elif subtype == "Pocket":
        stepover = 30
    else:
        stepover = 20

    feed = calc * teeth * fz

    if mode == "Roughing":
        max_doc = diameter * 0.25
    elif mode == "Semi Finish":
        max_doc = diameter * 0.12
    else:
        max_doc = diameter * 0.06

    if group == "ستانلس":
        max_doc *= 0.65
    if ld > 3:
        max_doc *= 0.65

    if step_depth > max_doc:
        warnings.append(f"عمق الشوط عالي، المقترح لا يتجاوز {max_doc:.2f} mm.")

    if subtype == "Helical":
        helix_pitch = max(0.2, diameter * 0.08)
        helix_text = f"Helix pitch مقترح = {helix_pitch:.2f} mm/rev\n"
    else:
        helix_text = ""

    result = (
        "نتيجة التفريز الاحترافية:\n\n"
        f"نوع التفريز: {subtype}\n"
        f"نوع الكتر: {tool_kind}\n"
        f"المادة: {material}\n"
        f"العدة: {insert}\n"
        f"قطر الكتر = {diameter:g} mm\n"
        f"بروز الكتر = {length:g} mm\n"
        f"L/D = {ld:.1f}\n"
        f"عدد الأسنان = {teeth}\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {calc:.0f}\n"
        f"Fz = {fz:.3f} mm/tooth\n"
        f"Feed = {feed:.0f} mm/min\n\n"
        f"Step Over مقترح = {stepover}% من قطر الكتر\n"
        f"عمق الشوط المدخل = {step_depth:g} mm\n"
        f"عمق شوط مقترح = {max_doc:.2f} mm\n"
        f"{helix_text}\n"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.") +
        "\n\nالقيم تقريبية كبداية آمنة."
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def drill_result(update, context):
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    group = context.user_data["material_group"]
    drill_type = context.user_data["tool_kind"]
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    diameter = context.user_data["diameter"]
    drill_depth = context.user_data["second_value"]

    vc = material_vc(material)
    if drill_type == "HSS Drill":
        vc *= 0.35
        feed_rev = 0.04 + diameter * 0.003
    elif drill_type == "Carbide Drill":
        vc *= 0.65
        feed_rev = 0.06 + diameter * 0.004
    elif drill_type == "Insert Drill":
        vc *= 0.55
        feed_rev = 0.08 + diameter * 0.005
    else:
        vc *= 0.40
        feed_rev = 0.035 + diameter * 0.002

    if group == "ستانلس":
        feed_rev *= 0.75
    if coolant == "Dry":
        vc *= 0.70
        feed_rev *= 0.75
    if clamp == "ضعيف":
        feed_rev *= 0.70

    calc = safe_rpm(vc, diameter)
    feed = calc * feed_rev
    depth_ratio = drill_depth / diameter

    if depth_ratio <= 3:
        peck = diameter
    elif depth_ratio <= 6:
        peck = diameter * 0.6
    else:
        peck = diameter * 0.35

    warnings = warning_common("ثقب", material, calc, machine_data(machine)["max_rpm"], coolant, clamp)
    if depth_ratio > 5:
        warnings.append("ثقب عميق: استخدم Peck وتبريد قوي.")

    result = (
        "نتيجة الثقب:\n\n"
        f"نوع البريمة: {drill_type}\n"
        f"المادة: {material}\n"
        f"قطر البريمة = {diameter:g} mm\n"
        f"عمق الثقب = {drill_depth:g} mm\n"
        f"نسبة العمق D = {depth_ratio:.1f}x\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {calc:.0f}\n"
        f"Feed/rev = {feed_rev:.3f} mm/rev\n"
        f"Feed = {feed:.0f} mm/min\n"
        f"Peck مقترح = {peck:.1f} mm\n\n"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.")
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def tapping_result(update, context):
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    tap_type = context.user_data["tool_kind"]
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    diameter = context.user_data["diameter"]
    pitch = context.user_data["pitch"]
    depth = context.user_data["depth"]

    vc = material_vc(material) * 0.18
    if tap_type == "Carbide Tap":
        vc *= 1.3
    elif tap_type == "Form Tap":
        vc *= 0.9
    elif tap_type == "HSS Tap":
        vc *= 0.75

    if coolant == "Dry":
        vc *= 0.55
    if material in ["304", "316", "Duplex"]:
        vc *= 0.70

    calc = safe_rpm(vc, diameter)
    calc = min(calc, 500)  # safe tapping limit for many lathes/mills
    feed = calc * pitch
    drill = tap_drill_size(diameter, pitch, tap_type)

    warnings = []
    if tap_type == "Form Tap":
        warnings.append("Form Tap يحتاج ثقب أدق وزيت جيد لأنه يكبس بدون رايش.")
    if coolant == "Dry":
        warnings.append("القلوظ بدون تبريد/زيت خطر، خصوصًا بالستانلس.")
    if depth > diameter * 2:
        warnings.append("عمق قلوظ كبير: استخدم Spiral وراجع الرايش.")
    if clamp == "ضعيف":
        warnings.append("التثبيت ضعيف: خطر كسر القلوظ.")

    result = (
        "نتيجة القلوظ:\n\n"
        f"نوع القلوظ: {tap_type}\n"
        f"المادة: {material}\n"
        f"المقاس: M{diameter:g} x {pitch:g}\n"
        f"عمق القلوظ = {depth:g} mm\n\n"
        f"قطر الثقب قبل القلوظ ≈ {drill:.2f} mm\n"
        f"RPM = {calc:.0f}\n"
        f"Feed = {feed:.0f} mm/min\n"
        f"G99 = {pitch:.3f} mm/rev\n\n"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.")
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def thread_result(update, context):
    process = context.user_data["process"]
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    insert = context.user_data.get("insert", "Thread Insert")
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    diameter = context.user_data["diameter"]
    pitch = context.user_data["pitch"]

    vc = material_vc(material) * 0.35
    if coolant == "Dry":
        vc *= 0.75
    if clamp == "ضعيف":
        vc *= 0.75

    calc = safe_rpm(vc, diameter)
    g50 = g50_limit(machine, diameter)
    depth = thread_depth_60(pitch)
    first_pass = pitch * 0.22
    finish_pass = pitch * 0.03
    passes = max(6, math.ceil(depth / 0.12))

    if process == "سن خارجي":
        prep = f"قطر التجهيز الخارجي ≈ {diameter - 0.05:.2f} إلى {diameter:.2f} mm"
        best = "يفضل 16ER أو 11ER"
    else:
        drill = internal_thread_drill(diameter, pitch)
        prep = f"قطر الثقب قبل السن ≈ {drill:.2f} mm"
        best = "يفضل 16IR أو 11IR"

    warnings = warning_common(process, material, calc, g50, coolant, clamp)
    if process == "سن خارجي" and not any(x in insert for x in ["16ER", "11ER", "Thread"]):
        warnings.append("للخارجي الأفضل 16ER / 11ER.")
    if process == "سن داخلي" and not any(x in insert for x in ["16IR", "11IR", "Thread"]):
        warnings.append("للداخلي الأفضل 16IR / 11IR.")

    result = (
        "نتيجة السن:\n\n"
        f"العملية: {process}\n"
        f"المادة: {material}\n"
        f"الإنسيرت: {insert}\n"
        f"المقاس: M{diameter:g} x {pitch:g}\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {calc:.0f}\n"
        f"G50 S{g50}\n"
        f"G97 S{calc:.0f} M3\n"
        f"G99 = {pitch:.3f} mm/rev\n"
        f"G98 = {calc*pitch:.0f} mm/min\n\n"
        f"عمق السن الشعاعي ≈ {depth:.3f} mm\n"
        f"أول مشوار ≈ {first_pass:.3f} mm\n"
        f"آخر مشوار تنظيف ≈ {finish_pass:.3f} mm\n"
        f"عدد المشاوير التقريبي = {passes}\n"
        f"{prep}\n"
        f"{best}\n\n"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.") +
        "\n\nاستخدم G76 أو G92 حسب الماكنة."
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def groove_cut_result(update, context):
    process = context.user_data["process"]
    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    insert = context.user_data.get("insert", "MGMN")
    nose = context.user_data.get("nose", "0.4")
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    mode = context.user_data.get("mode", "Roughing")
    diameter = context.user_data["diameter"]
    width = context.user_data["second_value"]
    depth = context.user_data["depth"]

    vc = material_vc(material) * correction_factor(coolant, clamp, mode, nose, machine)
    vc *= 0.55 if process == "Cut Off" else 0.65

    calc = safe_rpm(vc, diameter)
    g50 = g50_limit(machine, diameter)
    feed = 0.05 if process == "Cut Off" else 0.06
    if mode == "Finishing":
        feed *= 0.65
    if material in ["304", "316", "Duplex", "Hard Chrome"]:
        feed *= 0.75
    g98 = calc * feed

    warnings = warning_common(process, material, calc, g50, coolant, clamp)
    if process == "Groove" and not any(x in insert.upper() for x in ["MGMN", "MGGN", "GTN"]):
        warnings.append("للكروف الأفضل MGMN / MGGN / GTN.")
    if process == "Cut Off" and "CUT" not in insert.upper():
        warnings.append("للقطع الأفضل Cut-Off insert.")
    if width < 2 and diameter > 80:
        warnings.append("قلم رفيع مع قطر كبير: اشتغل Peck وخفف الفيد.")

    result = (
        f"نتيجة {process}:\n\n"
        f"المادة: {material}\n"
        f"الإنسيرت: {insert}\n"
        f"قطر الشغلة = {diameter:g} mm\n"
        f"عرض القلم = {width:g} mm\n"
        f"عمق النزلة = {depth:g} mm\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {calc:.0f}\n"
        f"G50 S{g50}\n"
        f"G96 S{vc:.0f}\n"
        f"G99 = {feed:.3f} mm/rev\n"
        f"G98 = {g98:.0f} mm/min\n\n"
        "اقتراح: استخدم Peck خفيف وتبريد جيد، وقلل السرعة قرب السنتر بالقطع.\n\n"
        "تحذيرات:\n" + ("\n".join(warnings) if warnings else "الوضع طبيعي كبداية آمنة.")
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def caxis_result(update, context):
    return ConversationHandler.END

async def second_value_for_caxis(update, context):
    # Reuse second value for tool diameter
    try:
        tool_d = to_float(update.message.text)
        if tool_d <= 0:
            raise ValueError
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return SECOND_VALUE

    context.user_data["second_value"] = tool_d
    process = context.user_data["process"]
    if process != "C-Axis":
        return await second_value_entered(update, context)

    machine = context.user_data["machine"]
    material = context.user_data["material_type"]
    subtype = context.user_data["op_subtype"]
    coolant = context.user_data["coolant"]
    clamp = context.user_data["clamp"]
    diameter = context.user_data["diameter"]
    count = context.user_data["c_count"]

    vc = material_vc(material) * 0.45
    if coolant == "Dry":
        vc *= 0.75
    if clamp == "ضعيف":
        vc *= 0.75

    rpm_tool = safe_rpm(vc, tool_d)
    angle = 360 / count

    positions = []
    for i in range(count):
        positions.append(f"C{angle*i:.3f}")

    result = (
        "نتيجة C-Axis:\n\n"
        f"العملية: {subtype}\n"
        f"المادة: {material}\n"
        f"قطر الشغلة = {diameter:g} mm\n"
        f"قطر الأداة = {tool_d:g} mm\n"
        f"عدد التقسيمات = {count}\n"
        f"زاوية كل تقسيم = {angle:.3f} درجة\n\n"
        f"RPM للأداة = {rpm_tool:.0f}\n"
        f"Vc = {vc:.0f} m/min\n\n"
        "مواقع C:\n" + "\n".join(positions[:30]) +
        ("\n..." if count > 30 else "") +
        "\n\nملاحظة: تأكد من تفعيل C-Axis وقفل السبيندل حسب ماكنتك."
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

# Override router for SECOND_VALUE to support C-Axis
async def second_router(update, context):
    if context.user_data.get("process") == "C-Axis":
        return await second_value_for_caxis(update, context)
    return await second_value_entered(update, context)


async def diag_sound_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diag_sound"] = update.message.text.strip()
    await update.message.reply_text(
        "شكل الرايش شلون؟",
        reply_markup=keyboard(["طبيعي", "طويل", "قصير", "أزرق", "بودرة", "يلتصق بالعدة"], 2)
    )
    return DIAG_CHIP

async def diag_chip_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["diag_chip"] = update.message.text.strip()
    await update.message.reply_text(
        "سطح القطعة شلون؟",
        reply_markup=keyboard(["ناعم", "خشن", "متموج", "محروق", "فيه خطوط"], 2)
    )
    return DIAG_FINISH

async def diag_finish_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sound = context.user_data.get("diag_sound", "")
    chip = context.user_data.get("diag_chip", "")
    finish = update.message.text.strip()

    advice = []

    if sound in ["اهتزاز", "طرق"]:
        advice.append("قلل RPM بنسبة 20-30٪.")
        advice.append("قلل DOC.")
        advice.append("إذا بورنك: قلل البروز أو استخدم قلم أكبر.")
    if sound == "صرير":
        advice.append("الفيد غالبًا قليل أو العدة تحك؛ زيد G99 قليلًا أو استخدم عدة حادة.")
    if sound == "صوت عالي":
        advice.append("راجع تثبيت الشغلة والعدة، وقلل السرعة أولًا.")

    if chip == "طويل":
        advice.append("الرايش طويل: زيد الفيد قليلًا أو استخدم chip breaker مناسب.")
    if chip == "أزرق":
        advice.append("حرارة عالية: قلل Vc أو زيد التبريد.")
    if chip == "بودرة":
        advice.append("الفيد قليل جدًا أو المادة صلدة؛ زيد الفيد شوي وراقب الصوت.")
    if chip == "يلتصق بالعدة":
        advice.append("التصاق: استخدم تبريد/زيت، عدة ملساء، وقلل السرعة خصوصًا للألمنيوم والنحاس.")

    if finish == "خشن":
        advice.append("لتحسين السطح: قلل الفيد، استخدم نوز أكبر 0.8، وخذ مشوار فنش خفيف.")
    if finish == "متموج":
        advice.append("تموج: مشكلة اهتزاز؛ قلل البروز أو غير السرعة 10-15٪.")
    if finish == "محروق":
        advice.append("سطح محروق: حرارة عالية، قلل Vc وزيد التبريد.")
    if finish == "فيه خطوط":
        advice.append("خطوط: افحص رأس الإنسيرت، النوز، أو backlash.")

    if not advice:
        advice.append("الوضع طبيعي. حافظ على القيم الحالية وراقب الرايش.")

    result = (
        "تشخيص التشغيل:\\n\\n"
        f"الصوت: {sound}\\n"
        f"الرايش: {chip}\\n"
        f"السطح: {finish}\\n\\n"
        "اقتراحات:\\n- " + "\\n- ".join(advice)
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def report_program_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["report_program"] = update.message.text.strip()
    await update.message.reply_text("ادخل عدد القطع المنتجة:")
    return REPORT_QTY

async def report_qty_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        qty = int(update.message.text.strip())
    except Exception:
        await update.message.reply_text("ادخل رقم صحيح.")
        return REPORT_QTY
    context.user_data["report_qty"] = qty
    await update.message.reply_text("ادخل وقت التشغيل، مثال: 3 ساعات أو من 8 إلى 12")
    return REPORT_TIME

async def report_time_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    program = context.user_data.get("report_program", "")
    qty = context.user_data.get("report_qty", 0)
    work_time = update.message.text.strip()

    result = (
        "تقرير عدة / إنتاج:\\n\\n"
        f"البرنامج / الشغلة: {program}\\n"
        f"عدد القطع: {qty}\\n"
        f"وقت التشغيل: {work_time}\\n\\n"
        "ملاحظة عدة:\\n"
        "- إذا بدأ السطح يخشن أو الرايش يتغير، افحص الإنسيرت.\\n"
        "- إذا الستانلس صار يطلع رايش أزرق، قلل السرعة أو زيد التبريد.\\n"
        "- احتفظ بهذا التقرير للمقارنة بالشغل القادم."
    )
    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("تم الإلغاء. اكتب /start للبدء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_selected)],
            MACHINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, machine_selected)],
            MATERIAL_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, material_group_selected)],
            MATERIAL_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, material_type_selected)],
            OP_SUBTYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, subtype_selected)],
            TOOL_KIND: [MessageHandler(filters.TEXT & ~filters.COMMAND, tool_kind_selected)],
            INSERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_selected)],
            NOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nose_selected)],
            COOLANT: [MessageHandler(filters.TEXT & ~filters.COMMAND, coolant_selected)],
            CLAMP: [MessageHandler(filters.TEXT & ~filters.COMMAND, clamp_selected)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mode_selected)],
            DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, diameter_entered)],
            SECOND_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_router)],
            THIRD_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_value_entered)],
            TEETH: [MessageHandler(filters.TEXT & ~filters.COMMAND, teeth_entered)],
            PITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, pitch_entered)],
            DEPTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, depth_entered)],
            C_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, c_count_entered)],
            DIAG_SOUND: [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_sound_entered)],
            DIAG_CHIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_chip_entered)],
            DIAG_FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_finish_entered)],
            REPORT_PROGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_program_entered)],
            REPORT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_qty_entered)],
            REPORT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_time_entered)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
    )

    app.add_handler(conv)
    print("BOT STARTED CNC V5 WORKSHOP EXPERT...")
    app.run_polling()

if __name__ == "__main__":
    main()
