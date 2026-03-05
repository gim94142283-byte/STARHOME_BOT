 import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

TOKEN = "8697768952:AAEOsFwTwbjtfKmNHgN0TTChewCwBEJM0Us"

conn = sqlite3.connect("members.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS members(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
phone TEXT,
birth TEXT,
note TEXT
)
""")
conn.commit()

NAME, PHONE, BIRTH, NOTE = range(4)
EDIT_NAME, EDIT_PHONE, EDIT_BIRTH, EDIT_NOTE = range(4)

# 시작
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"""
회원관리 봇

/add 회원추가
/list 전체회원
/find 이름검색
/edit id 회원수정
/delete id 삭제
"""
)

# 회원 추가
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("이름 입력")
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("전화번호 입력")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("생년월일 입력")
    return BIRTH

async def birth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["birth"] = update.message.text
    await update.message.reply_text("특이사항 입력")
    return NOTE

async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["note"] = update.message.text

    cursor.execute(
        "INSERT INTO members (name, phone, birth, note) VALUES (?, ?, ?, ?)",
        (
            context.user_data["name"],
            context.user_data["phone"],
            context.user_data["birth"],
            context.user_data["note"],
        ),
    )
    conn.commit()

    await update.message.reply_text("저장 완료")
    return ConversationHandler.END

# 전체 회원
async def list_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM members")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("회원 없음")
        return

    msg = ""
    for r in rows:
        msg += f"""
ID:{r[0]}
이름:{r[1]}
전화:{r[2]}
생일:{r[3]}
특이:{r[4]}
-----------
"""
    await update.message.reply_text(msg)

# 이름 검색
async def find_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("사용: /find 이름")
        return

    keyword = context.args[0]

    cursor.execute(
        "SELECT * FROM members WHERE name LIKE ?",
        ('%' + keyword + '%',)
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("검색결과 없음")
        return

    msg = ""
    for r in rows:
        msg += f"""
ID:{r[0]}
이름:{r[1]}
전화:{r[2]}
생일:{r[3]}
특이:{r[4]}
-----------
"""
    await update.message.reply_text(msg)

# 삭제
async def delete_member(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("사용: /delete id")
        return

    id = context.args[0]

    cursor.execute("DELETE FROM members WHERE id=?", (id,))
    conn.commit()

    await update.message.reply_text("삭제 완료")

# 수정 시작
async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("사용: /edit id")
        return ConversationHandler.END

    context.user_data["edit_id"] = context.args[0]

    await update.message.reply_text("새 이름 입력")
    return EDIT_NAME

async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("새 전화번호")
    return EDIT_PHONE

async def edit_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("새 생년월일")
    return EDIT_BIRTH

async def edit_birth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["birth"] = update.message.text
    await update.message.reply_text("새 특이사항")
    return EDIT_NOTE

async def edit_note(update: Update, context: ContextTypes.DEFAULT_TYPE):

    id = context.user_data["edit_id"]
    note = update.message.text

    cursor.execute(
        """
        UPDATE members
        SET name=?, phone=?, birth=?, note=?
        WHERE id=?
        """,
        (
            context.user_data["name"],
            context.user_data["phone"],
            context.user_data["birth"],
            note,
            id,
        ),
    )

    conn.commit()

    await update.message.reply_text("수정 완료")
    return ConversationHandler.END


# 봇 실행
app = ApplicationBuilder().token(TOKEN).build()

add_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        BIRTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, birth)],
        NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, note)],
    },
    fallbacks=[],
)

edit_handler = ConversationHandler(
    entry_points=[CommandHandler("edit", edit)],
    states={
        EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        EDIT_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_phone)],
        EDIT_BIRTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_birth)],
        EDIT_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_note)],
    },
    fallbacks=[],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_members))
app.add_handler(CommandHandler("find", find_member))
app.add_handler(CommandHandler("delete", delete_member))
app.add_handler(add_handler)
app.add_handler(edit_handler)

print("봇 실행중")

app.run_polling()
