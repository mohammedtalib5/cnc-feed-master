import math
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

TOKEN = "8988980195:AAEznSXisHEEqA2R3IjbTnve3IEAe1ibu4Y"

(
    PROCESS, MATERIAL, INSERT, MODE,
    DIAMETER, TOOL_DIAMETER, MILL_LENGTH,
    DEPTH, TEETH, PITCH
) = range(10)

PROCESSES = [
    "خراطة خارجية", "خراطة داخلية", "ثقب",
    "تفريز", "Groove", "Cut",
    "سن خارجي", "سن داخلي"
]

MATERIALS = ["ألمنيوم", "حديد", "ستانلس", "كروم", "نحاس", "ديلرين"]
MODES = ["Roughing", "Finishing"]

INSERTS = [
    "CNMG","CNMM","CNMA","WNMG","WNMM","DNMG","DNMM",
    "TNMG","TNMM","TNMG160404R-VF",
    "VNMG","VNMM","SNMG","SNMM","SCMT","SNMA",
    "CCMT","CCGT","DCMT","DCGT","TCMT","TCGT",
    "VBMT","VBGT","VCMT","VCGT","VCMT160404-OTM","VCMT331-OTM",
    "RCMT","RPGT","RPMT","APMT","APKT","SEKT","SEHT",
    "XOEX","R390","MGMN","MGGN","GTN","Cut-Off",
    "16ER","16IR","11ER","11IR","Thread Insert","HSS"
]

MATERIAL_VC = {
    "ألمنيوم": 250,
    "حديد": 120,
    "ستانلس": 70,
    "كروم": 55,
    "نحاس": 180,
    "ديلرين": 300,
}

def keyboard(items, cols=2):
    return ReplyKeyboardMarkup(
        [items[i:i+cols] for i in range(0, len(items), cols)],
        resize_keyboard=True
    )

def calc_rpm(vc, d):
    return (vc * 1000) / (math.pi * d)

def g50_limit(d):
    if d >= 150:
        return 1200
    if d >= 100:
        return 1800
    if d >= 50:
        return 2500
    return 3500

def insert_data(insert):
    if insert == "TNMG160404R-VF":
        return 0.18, 0.08, "0.5 - 2 mm", "ستانلس وتشطيب متوسط"
    if insert in ["VCMT160404-OTM", "VCMT331-OTM"]:
        return 0.08, 0.04, "0.1 - 0.8 mm", "خراطة داخلية وتشطيب"
    if insert.startswith(("CN", "WN", "SN")):
        return 0.25, 0.12, "1 - 3 mm", "خراطة قوية"
    if insert.startswith(("DN", "TN")):
        return 0.18, 0.08, "0.5 - 2 mm", "خراطة عامة"
    if insert.startswith(("VN", "VB", "VC")):
        return 0.10, 0.05, "0.1 - 1 mm", "تشطيب وزوايا"
    if insert.startswith(("CC", "DC", "TC", "SC")):
        return 0.10, 0.05, "0.1 - 1 mm", "خراطة داخلية"
    if insert.startswith(("AP", "SE", "XO", "R390", "RPMT", "RPGT", "RC")):
        return 0.05, 0.03, "حسب التفريز", "تفريز"
    if insert.startswith(("MGMN", "MGGN", "GTN")):
        return 0.06, 0.04, "حسب عرض القلم", "Groove"
    if insert == "Cut-Off":
        return 0.05, 0.03, "Peck خفيف", "قطع"
    if insert in ["16ER", "16IR", "11ER", "11IR", "Thread Insert"]:
        return 0.04, 0.04, "حسب خطوة السن", "سن"
    if insert == "HSS":
        return 0.08, 0.04, "خفيف", "HSS"
    return 0.12, 0.06, "0.5 - 1 mm", "عام"

def get_vc(material, insert, process):
    vc = MATERIAL_VC.get(material, 100)

    if insert == "HSS":
        vc *= 0.45
    if insert.startswith(("MGMN", "MGGN", "GTN")):
        vc *= 0.70
    if insert == "Cut-Off":
        vc *= 0.60
    if insert in ["16ER", "16IR", "11ER", "11IR", "Thread Insert"]:
        vc *= 0.45

    if process == "ثقب":
        vc *= 0.45
    elif process == "Groove":
        vc *= 0.70
    elif process == "Cut":
        vc *= 0.60
    elif process in ["سن خارجي", "سن داخلي"]:
        vc *= 0.45

    return vc

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "CNC Professional Bot\n\nاختار العملية:",
        reply_markup=keyboard(PROCESSES, 2)
    )
    return PROCESS

async def process_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    process = update.message.text.strip()
    if process not in PROCESSES:
        await update.message.reply_text("اختار من الأزرار فقط.")
        return PROCESS

    context.user_data["process"] = process
    await update.message.reply_text("اختار المادة:", reply_markup=keyboard(MATERIALS, 2))
    return MATERIAL

async def material_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["material"] = update.message.text.strip()
    await update.message.reply_text("اختار رمز الإنسيرت:", reply_markup=keyboard(INSERTS, 3))
    return INSERT

async def insert_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["insert"] = update.message.text.strip()
    await update.message.reply_text("اختار نوع التشغيل:", reply_markup=keyboard(MODES, 2))
    return MODE

async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = update.message.text.strip()
    process = context.user_data["process"]

    if process == "ثقب":
        msg = "ادخل قطر البريمة mm"
    elif process == "خراطة داخلية":
        msg = "ادخل قطر الحفرة الداخلي mm"
    elif process == "تفريز":
        msg = "ادخل قطر الكتر mm"
    elif process in ["سن خارجي", "سن داخلي"]:
        msg = "ادخل قطر السن mm\nمثال: M40 اكتب 40"
    else:
        msg = "ادخل قطر الشغلة mm"

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return DIAMETER

async def diameter_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        d = float(update.message.text.strip())
        if d <= 0:
            raise ValueError
    except:
        await update.message.reply_text("ادخل رقم صحيح.")
        return DIAMETER

    context.user_data["diameter"] = d
    process = context.user_data["process"]

    if process == "خراطة داخلية":
        await update.message.reply_text("ادخل قطر قلم البورنك mm")
        return TOOL_DIAMETER

    if process == "تفريز":
        await update.message.reply_text("ادخل طول / بروز الكتر mm")
        return MILL_LENGTH

    if process in ["سن خارجي", "سن داخلي"]:
        await update.message.reply_text("ادخل خطوة السن mm\nمثال: M40x2 اكتب 2")
        return PITCH

    await update.message.reply_text("ادخل DOC mm")
    return DEPTH

async def tool_diameter_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["tool_diameter"] = float(update.message.text.strip())
    except:
        await update.message.reply_text("ادخل رقم صحيح.")
        return TOOL_DIAMETER

    await update.message.reply_text("ادخل DOC mm")
    return DEPTH

async def mill_length_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        length = float(update.message.text.strip())
        if length <= 0:
            raise ValueError
    except:
        await update.message.reply_text("ادخل طول صحيح.")
        return MILL_LENGTH

    context.user_data["mill_length"] = length
    await update.message.reply_text("ادخل عدد أسنان الكتر")
    return TEETH

async def teeth_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        teeth = int(update.message.text.strip())
        if teeth <= 0:
            raise ValueError
    except:
        await update.message.reply_text("ادخل عدد أسنان صحيح.")
        return TEETH

    context.user_data["teeth"] = teeth
    await update.message.reply_text("ادخل عمق القطع لكل شوط mm")
    return DEPTH

async def pitch_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pitch = float(update.message.text.strip())
        if pitch <= 0:
            raise ValueError
    except:
        await update.message.reply_text("ادخل خطوة سن صحيحة.")
        return PITCH

    context.user_data["pitch"] = pitch
    return await thread_result(update, context)

async def thread_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    process = context.user_data["process"]
    material = context.user_data["material"]
    insert = context.user_data["insert"]
    diameter = context.user_data["diameter"]
    pitch = context.user_data["pitch"]

    vc = get_vc(material, insert, process)
    rpm = calc_rpm(vc, diameter)
    g50 = g50_limit(diameter)

    thread_depth = 0.6134 * pitch
    first_pass = 0.25 * pitch
    finish_pass = 0.03 * pitch
    passes = max(6, math.ceil(thread_depth / 0.15))

    if process == "سن خارجي":
        prep = diameter - 0.05
        prep_text = f"قطر التجهيز الخارجي ≈ {prep:.2f} إلى {diameter:.2f} mm"
        insert_note = "الأفضل 16ER أو 11ER للسن الخارجي"
        direction = "خارجي"
    else:
        tap_drill = diameter - (1.0825 * pitch)
        prep_text = f"قطر الثقب قبل السن ≈ {tap_drill:.2f} mm"
        insert_note = "الأفضل 16IR أو 11IR للسن الداخلي"
        direction = "داخلي"

    warning = ""
    if process == "سن خارجي" and insert not in ["16ER", "11ER", "Thread Insert"]:
        warning += "تنبيه: للسن الخارجي الأفضل 16ER أو 11ER.\n"
    if process == "سن داخلي" and insert not in ["16IR", "11IR", "Thread Insert"]:
        warning += "تنبيه: للسن الداخلي الأفضل 16IR أو 11IR.\n"
    if rpm > g50:
        warning += "RPM أعلى من G50 وسيتم تحديده تلقائيًا.\n"
    if material in ["ستانلس", "كروم"]:
        warning += "استخدم تبريد جيد وخلي المشاوير خفيفة.\n"
    if warning == "":
        warning = "الوضع طبيعي كبداية آمنة."

    result = (
        "نتيجة السن CNC:\n\n"
        f"نوع السن: {direction}\n"
        f"المادة: {material}\n"
        f"الإنسيرت: {insert}\n"
        f"قطر السن = M{diameter:g}\n"
        f"Pitch = {pitch:g} mm\n\n"

        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {rpm:.0f}\n"
        f"G97 S{rpm:.0f} M3\n"
        f"G50 S{g50}\n\n"

        f"G99 = {pitch:.3f} mm/rev\n"
        f"G98 = {rpm * pitch:.0f} mm/min\n\n"

        f"عمق السن الشعاعي الكلي ≈ {thread_depth:.3f} mm\n"
        f"أول مشوار مقترح ≈ {first_pass:.3f} mm\n"
        f"آخر مشوار تنظيف ≈ {finish_pass:.3f} mm\n"
        f"عدد المشاوير التقريبي = {passes}\n\n"

        f"{prep_text}\n"
        f"{insert_note}\n\n"

        "أكواد مقترحة:\n"
        f"G50 S{g50}\n"
        f"G97 S{rpm:.0f} M3\n"
        f"G99\n"
        "استخدم G76 أو G92 حسب نظام ماكنتك.\n\n"

        f"تحذيرات:\n{warning}\n\n"
        "ملاحظة: عمق السن محسوب للسن المتري 60 درجة كبداية عملية."
    )

    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def depth_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        depth = float(update.message.text.strip())
        if depth < 0:
            raise ValueError
    except:
        await update.message.reply_text("ادخل رقم صحيح.")
        return DEPTH

    process = context.user_data["process"]
    material = context.user_data["material"]
    insert = context.user_data["insert"]
    mode = context.user_data["mode"]
    diameter = context.user_data["diameter"]

    rough_feed, finish_feed, doc, use = insert_data(insert)
    vc = get_vc(material, insert, process)
    rpm = calc_rpm(vc, diameter)
    g99 = rough_feed if mode == "Roughing" else finish_feed
    g98 = rpm * g99
    g50 = g50_limit(diameter)

    extra = ""
    warning = ""

    if process == "تفريز":
        teeth = context.user_data["teeth"]
        length = context.user_data["mill_length"]
        fz = 0.035 if mode == "Roughing" else 0.015

        if material == "ألمنيوم":
            fz *= 1.4
        elif material in ["ستانلس", "كروم"]:
            fz *= 0.65

        if length > diameter * 3:
            fz *= 0.6
            warning += "تحذير: بروز الكتر طويل، قلل الفيد وعمق الشوط.\n"

        feed = rpm * teeth * fz
        max_step = diameter * 0.25 if mode == "Roughing" else diameter * 0.08

        if material in ["ستانلس", "كروم"]:
            max_step *= 0.6

        if depth > max_step:
            warning += f"تنبيه: عمق الشوط عالي، المقترح لا يتجاوز {max_step:.2f} mm.\n"

        extra = (
            f"قطر الكتر = {diameter:g} mm\n"
            f"طول / بروز الكتر = {length:g} mm\n"
            f"نسبة البروز L/D = {length / diameter:.1f}\n"
            f"عدد الأسنان = {teeth}\n"
            f"Fz = {fz:.3f} mm/tooth\n"
            f"Feed = {feed:.0f} mm/min\n"
            f"عمق القطع لكل شوط = {depth:g} mm\n"
            f"عمق شوط مقترح = {max_step:.2f} mm\n"
        )

    elif process == "خراطة داخلية":
        tool_d = context.user_data["tool_diameter"]
        extra = (
            f"قطر قلم البورنك = {tool_d:g} mm\n"
            f"نسبة القلم للحفرة = {(tool_d / diameter) * 100:.0f}%\n"
        )
        if tool_d < diameter * 0.35:
            warning += "تحذير: قلم البورنك ضعيف نسبة للحفرة، احتمال اهتزاز.\n"

    elif process == "ثقب":
        extra = f"Peck مقترح = {diameter * 0.7:.1f} mm\n"

    if rpm > g50:
        warning += "RPM أعلى من G50 وسيتم تحديده تلقائيًا.\n"
    if process == "Groove" and not insert.startswith(("MGMN", "MGGN", "GTN")):
        warning += "يفضل MGMN أو GTN للكروف.\n"
    if process == "Cut" and insert != "Cut-Off":
        warning += "يفضل Cut-Off للقطع.\n"
    if material == "ستانلس":
        warning += "استخدم تبريد جيد مع الستانلس.\n"
    if warning == "":
        warning = "الوضع طبيعي كبداية آمنة."

    result = (
        "نتيجة CNC:\n\n"
        f"العملية: {process}\n"
        f"المادة: {material}\n"
        f"الإنسيرت: {insert}\n"
        f"استخدام الإنسيرت: {use}\n"
        f"نوع التشغيل: {mode}\n\n"
        f"Vc = {vc:.0f} m/min\n"
        f"RPM = {rpm:.0f}\n"
        f"G99 = {g99:.3f} mm/rev\n"
        f"G98 = {g98:.0f} mm/min\n\n"
        f"G50 S{g50}\n"
        f"G96 S{vc:.0f}\n\n"
        f"DOC = {depth:g} mm\n"
        f"DOC مقترح = {doc}\n\n"
        f"{extra}\n"
        f"تحذيرات:\n{warning}\n\n"
        "القيم تقريبية كبداية آمنة."
    )

    await update.message.reply_text(result)
    await update.message.reply_text("للبدء من جديد اضغط /start")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PROCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_selected)],
            MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, material_selected)],
            INSERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, insert_selected)],
            MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mode_selected)],
            DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, diameter_entered)],
            TOOL_DIAMETER: [MessageHandler(filters.TEXT & ~filters.COMMAND, tool_diameter_entered)],
            MILL_LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, mill_length_entered)],
            TEETH: [MessageHandler(filters.TEXT & ~filters.COMMAND, teeth_entered)],
            PITCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, pitch_entered)],
            DEPTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, depth_entered)],
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   CommandHandler("start", start)],
    )

    app.add_handler(conv)
    print("BOT STARTED...")
    app.run_polling()

if __name__ == "__main__":
    main()