import logging
import asyncio
import os
import redis
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# 配置
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
GROUP_ID = os.getenv("GROUP_ID")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Redis连接
try:
    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    r.ping()
    logging.info("✅ 成功连接到 Redis。")
except redis.exceptions.ConnectionError as e:
    logging.critical(f"❌ 无法连接到 Redis: {e}")
    r = None

# 问卷分页配置
ITEMS_PER_PAGE = 10

# 欢迎和帮助文本
WELCOME_TEXT = """
🎉 <b>欢迎使用问卷Bot！</b>

本bot交流群 @chat1of5 
📋 <b>功能说明：</b>
• 选择问卷并开始填写
• 支持文字、语音、图片、视频
• 可跳过标记为【可跳过】的问题
🔧 <b>操作命令：</b>
• /start - 选择问卷
• /end - 结束当前问卷
• /help - 显示帮助信息

💡 <b>使用提示：</b>
• 点击下方按钮选择问卷
• 按照问题要求回答
• 文字题可用语音回答
• 可随时使用 /end 结束问卷

⚠️ <b>注意：</b>由于服务器配置，Bot回复可能较慢，请耐心等待。若遇点击按钮无效问题，请随便在输入框输入点文本，就可以触发下一题了。
"""

ADMIN_HELP_TEXT = """
🤖 <b>机器人已启动！</b>
<b>管理员命令:</b>
/new 目录名 - 创建一个新的问卷目录，并设置为当前目录
/addquestion 问题|选项1,选项2 - 添加普通问题
/addquestion 问题 -skip |选项1,选项2 - 添加可跳过问题
/addbranch 问题|选项1:下一题ID,选项2:下一题ID - 添加分支问题
/listquestions - 列出所有问题 (按目录分组)
/clearall - 清空所有问题和目录
/help - 显示此帮助信息

💡 <b>分支问题说明:</b>
- 使用 /addbranch 创建分支问题
- 格式: 问题|选项1:下一题ID,选项2:下一题ID
- 例如: 你喜欢的颜色？|红色:3,蓝色:5,绿色:7
- 用户选择不同选项会跳转到不同的问题

<b>🖼️ 添加图片问题:</b>
- 发送图片，并在图片标题中输入命令
- 格式: &lt;图片标题&gt; /addquestion 问题
- 例如: (图片) /addquestion 你喜欢这张图片吗？
"""

# 管理员命令
@dp.message(Command("new"))
async def new_category(message: Message, command: CommandObject):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    category_name = command.args
    if not category_name:
        return await message.reply("❌ 请提供目录名，例如：/new 新人入群问卷")
    
    r.sadd("categories", category_name)
    r.set(f"admin:{ADMIN_ID}:current_category", category_name)
    await message.reply(f"✅ 已创建目录：<b>{category_name}</b>\n后续添加的问题都将自动归入此目录。", parse_mode=ParseMode.HTML)

@dp.message(Command("addquestion", magic=F.caption), F.photo)
@dp.message(Command("addquestion", magic=F.caption), F.document)
@dp.message(Command("addquestion", magic=F.caption), F.video)
@dp.message(Command("addquestion"))
async def add_question(message: Message, command: CommandObject):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.reply("❌ 没有权限")

    current_category = r.get(f"admin:{ADMIN_ID}:current_category")
    if not current_category:
        return await message.reply("❌ 请先使用 /new <目录名> 创建一个目录。")
    
    args = command.args or message.caption
    if not args:
        return await message.reply("❌ 请提供问题内容\n格式: /addquestion 问题|选项1,选项2,选项3")

    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith("image/"):
        photo_file_id = message.document.file_id
    elif message.video:
        photo_file_id = message.video.file_id

    try:
        text = args.strip()
        is_skippable = False
        if " -skip" in text:
            text = text.replace(" -skip", "").strip()
            is_skippable = True
        
        if "|" in text:
            question, options = text.split("|", 1)
            question = question.strip()
            options = options.strip()
        else:
            question = text
            options = ""
        
        idx = r.incr("question_count")
        
        question_data = {
            "text": question,
            "category": current_category,
            "options": options,
            "skippable": "true" if is_skippable else "false"
        }
        
        if photo_file_id:
            question_data["media_type"] = "photo"
            question_data["media_id"] = photo_file_id
            
        r.hmset(f"question:{idx}", question_data)
        r.sadd(f"category_questions:{current_category}", idx)
        
        await message.reply(f"✅ 已添加问题 {idx} 到目录 <b>{current_category}</b>: {question}", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logging.exception("添加问题失败")
        await message.reply(f"❌ 添加问题失败: {e}")

@dp.message(Command("addbranch", magic=F.caption), F.photo)
@dp.message(Command("addbranch", magic=F.caption), F.document)
@dp.message(Command("addbranch", magic=F.caption), F.video)
@dp.message(Command("addbranch"))
async def add_branch_question(message: Message, command: CommandObject):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    current_category = r.get(f"admin:{ADMIN_ID}:current_category")
    if not current_category:
        return await message.reply("❌ 请先使用 /new <目录名> 创建一个目录。")
    
    args = command.args or message.caption
    if not args:
        return await message.reply("❌ 请提供分支问题内容\n格式: /addbranch 问题|选项1:下一题ID,选项2:下一题ID")

    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith("image/"):
        photo_file_id = message.document.file_id
    elif message.video:
        photo_file_id = message.video.file_id

    try:
        text = args.strip()
        if "|" in text:
            question, options = text.split("|", 1)
            question = question.strip()
            options = options.strip()
        else:
            question = text
            options = ""
        
        idx = r.incr("question_count")
        
        question_data = {
            "text": question,
            "type": "branch",
            "category": current_category,
            "options": options
        }
        
        if photo_file_id:
            question_data["media_type"] = "photo"
            question_data["media_id"] = photo_file_id
        
        r.hmset(f"question:{idx}", question_data)
        r.sadd(f"category_questions:{current_category}", idx)
        
        await message.reply(f"✅ 已添加分支问题 {idx} 到目录 <b>{current_category}</b>: {question}", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logging.exception("添加分支问题失败")
        await message.reply(f"❌ 添加分支问题失败: {e}")

@dp.message(Command("listquestions"))
async def list_questions(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.reply("❌ 没有权限")

    categories = r.smembers("categories")
    if not categories:
        return await message.reply("📝 还没有任何问卷目录。")
    
    response = "📋 <b>问卷目录及问题列表:</b>\n\n"
    
    for category in categories:
        question_count = r.scard(f"category_questions:{category}")
        response += f"📁 <b>{category} ({question_count}题)</b>\n"
        
        question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{category}")])
        for q_id in question_ids:
            q_data = r.hgetall(f"question:{q_id}")
            if q_data:
                status = ""
                if q_data.get("type") == "branch":
                    status += "[分支]"
                if q_data.get("skippable") == "true":
                    status += "[可跳过]"
                
                response += f"  - 问题 {q_id}. {status} {q_data['text']}\n"
        response += "\n"
        
    await message.reply(response, parse_mode=ParseMode.HTML)

@dp.message(Command("clearall"))
async def clear_all_questions(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    for key in r.scan_iter("question:*"):
        r.delete(key)
    for key in r.scan_iter("category_questions:*"):
        r.delete(key)
    r.delete("question_count")
    r.delete("categories")
    await message.reply("✅ 已清空所有问题和目录。")

# 用户命令
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.reply(WELCOME_TEXT)
    await show_categories_page(message, 0)

@dp.callback_query(F.data.startswith("start_quiz:"))
async def start_quiz_callback(callback: types.CallbackQuery):
    selected_category = callback.data.split(":")[1]
    
    await callback.message.edit_reply_markup(reply_markup=None) 
    
    user_id = callback.from_user.id
    
    question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{selected_category}")])
    
    if not question_ids:
        await callback.message.reply(f"❌ 目录 <b>{selected_category}</b> 下没有问题，请联系管理员。", parse_mode=ParseMode.HTML)
        return
    
    first_q_index = question_ids[0]
    
    r.set(f"user:{user_id}:q", first_q_index)
    r.set(f"user:{user_id}:started", "true")
    r.set(f"user:{user_id}:category", selected_category)
    
    await callback.message.reply(f"🎯 问卷 <b>{selected_category}</b> 开始！请回答以下问题：", parse_mode=ParseMode.HTML, reply_markup=types.ReplyKeyboardRemove())
    await send_question(user_id)

@dp.callback_query(F.data.startswith("cat_page:"))
async def show_categories_page(callback_or_message, page_str=None):
    if isinstance(callback_or_message, types.CallbackQuery):
        callback = callback_or_message
        page = int(callback.data.split(":")[1])
        await callback.message.edit_reply_markup(reply_markup=await generate_categories_keyboard(page))
    else:
        message = callback_or_message
        page = int(page_str) if page_str else 0
        await message.reply("请选择一个问卷目录开始：", reply_markup=await generate_categories_keyboard(page))

async def generate_categories_keyboard(page):
    categories = sorted(list(r.smembers("categories")))
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    page_categories = categories[start_index:end_index]

    keyboard = []
    for category in page_categories:
        question_count = r.scard(f"category_questions:{category}")
        keyboard.append([types.InlineKeyboardButton(text=f"{category} ({question_count}题)", callback_data=f"start_quiz:{category}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="上一页", callback_data=f"cat_page:{page-1}"))
    if end_index < len(categories):
        nav_buttons.append(types.InlineKeyboardButton(text="下一页", callback_data=f"cat_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)

    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("end"))
async def end_quiz(message: Message):
    user_id = message.from_user.id
    
    if r.get(f"user:{user_id}:started"):
        r.delete(f"user:{user_id}:q")
        r.delete(f"user:{user_id}:started")
        r.delete(f"user:{user_id}:category")
        r.delete(f"thread:{user_id}")
        await message.reply("✅ 你已结束答题，欢迎随时再次使用 /start。", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.reply("❌ 你没有正在进行的问卷")

async def send_question(user_id: int):
    q_index = r.get(f"user:{user_id}:q")
    if not q_index:
        return
    
    question_data = r.hgetall(f"question:{q_index}")
    if not question_data:
        await bot.send_message(user_id, "🎉 恭喜回答结束 ✅", reply_markup=types.ReplyKeyboardRemove())
        r.delete(f"user:{user_id}:q")
        r.delete(f"user:{user_id}:started")
        r.delete(f"user:{user_id}:category")
        r.delete(f"thread:{user_id}")
        return
    
    question = question_data.get("text")
    options = question_data.get("options")
    q_type = question_data.get("type")
    is_skippable = question_data.get("skippable") == "true"
    media_id = question_data.get("media_id")
    media_type = question_data.get("media_type")
    
    kb = None
    question_text = f"❓ 问题 {q_index}: {question}"
    
    if options:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for opt in options.split(","):
            opt_text = opt.split(":")[0].strip() if ":" in opt else opt.strip()
            kb.add(types.KeyboardButton(text=opt_text))
    
    if is_skippable:
        if kb:
            kb.add(types.KeyboardButton(text="跳过"))
        else:
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            kb.add(types.KeyboardButton(text="跳过"))

    if q_type == "branch":
        question_text += "\n\n🔄 这是一个分支问题，你的选择将决定下一题"
    
    if media_id and media_type:
        try:
            if media_type == "photo":
                await bot.send_photo(user_id, media_id)
            elif media_type == "video":
                await bot.send_video(user_id, media_id)
            # 可以添加其他媒体类型，如 document 等
        except Exception as e:
            logging.error(f"发送媒体文件失败: {e}")
    
    await bot.send_message(user_id, question_text, reply_markup=kb)

# 接收用户回答
@dp.message()
async def handle_answer(message: Message):
    user_id = message.from_user.id
    
    if not r.get(f"user:{user_id}:started"):
        return
    
    q_index = r.get(f"user:{user_id}:q")
    if not q_index:
        return
    
    if message.text == "跳过":
        current_category = r.get(f"user:{user_id}:category")
        question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{current_category}")])
        try:
            current_q_pos = question_ids.index(int(q_index))
            next_q = question_ids[current_q_pos + 1]
        except (ValueError, IndexError):
            next_q = None

        if not next_q:
            await message.reply("🎉 恭喜回答结束！所有问题已完成。", reply_markup=types.ReplyKeyboardRemove())
            r.delete(f"user:{user_id}:q")
            r.delete(f"user:{user_id}:started")
            r.delete(f"user:{user_id}:category")
            r.delete(f"thread:{user_id}")
        else:
            r.set(f"user:{user_id}:q", next_q)
            await message.reply("⏩ 已跳过此题，请回答下一题：", reply_markup=types.ReplyKeyboardRemove())
            await send_question(user_id)
        return

    question_data = r.hgetall(f"question:{q_index}")
    question = question_data.get("text")
    options = question_data.get("options")
    q_type = question_data.get("type")
    
    thread_name = f"{message.from_user.username or 'user'}_{user_id}"
    thread_id = r.get(f"thread:{user_id}")
    
    if not thread_id:
        try:
            forum_topic = await bot.create_forum_topic(
                int(GROUP_ID),
                name=thread_name,
                icon_color=0x6FB9F0
            )
            thread_id = forum_topic.message_thread_id
            r.set(f"thread:{user_id}", thread_id)
        except Exception as e:
            thread_id = None
            logging.exception("创建话题失败")
    
    msg_text = f"👤 <b>{message.from_user.full_name}</b>\n"
    msg_text += f"🆔 <code>{user_id}</code>\n"
    msg_text += f"❓ <b>问题 {q_index}:</b> {question}\n"
    
    if message.text:
        msg_text += f"💬 <b>答案:</b> {message.text}"
    elif message.photo:
        msg_text += f"🖼️ <b>答案:</b> [图片]"
    elif message.video:
        msg_text += f"🎥 <b>答案:</b> [视频]"
    elif message.document:
        msg_text += f"📄 <b>答案:</b> [文档]"
    else:
        msg_text += f"💬 <b>答案:</b> [其他类型内容]"
    
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            await bot.send_photo(
                int(GROUP_ID), 
                file_id, 
                caption=msg_text, 
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        elif message.video:
            file_id = message.video.file_id
            await bot.send_video(
                int(GROUP_ID),
                file_id,
                caption=msg_text,
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        elif message.document:
            file_id = message.document.file_id
            await bot.send_document(
                int(GROUP_ID),
                file_id,
                caption=msg_text,
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                int(GROUP_ID), 
                msg_text, 
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logging.exception("发送消息到群组失败")
    
    next_q = None
    if q_type == "branch" and options and message.text:
        for opt in options.split(","):
            if ":" in opt:
                opt_text, next_id = opt.split(":", 1)
                if message.text.strip() == opt_text.strip():
                    next_q = int(next_id.strip())
                    break
        if next_q is None:
            next_q = int(q_index) + 1
    else:
        next_q = int(q_index) + 1
    
    current_category = r.get(f"user:{user_id}:category")
    question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{current_category}")])
    
    final_next_q = None
    try:
        if q_type == "branch" and next_q in question_ids:
            final_next_q = next_q
        else:
            current_q_pos = question_ids.index(int(q_index))
            final_next_q = question_ids[current_q_pos + 1]
    except (ValueError, IndexError):
        final_next_q = None
    
    if not final_next_q:
        await bot.send_message(user_id, "🎉 恭喜回答结束！所有问题已完成。", reply_markup=types.ReplyKeyboardRemove())
        r.delete(f"user:{user_id}:q")
        r.delete(f"user:{user_id}:started")
        r.delete(f"user:{user_id}:category")
        r.delete(f"thread:{user_id}")
    else:
        r.set(f"user:{user_id}:q", final_next_q)
        await send_question(user_id)

@dp.message(Command("status"))
async def check_status(message: Message):
    user_id = message.from_user.id
    current_q_index = r.get(f"user:{user_id}:q")
    started = r.get(f"user:{user_id}:started")
    current_category = r.get(f"user:{user_id}:category")
    
    if not started:
        await message.reply("❌ 你还没有开始答题，请使用 /start 开始")
        return
    
    if not current_q_index or not current_category:
        await message.reply("❌ 状态信息获取失败，请尝试重新开始或联系管理员。")
        return

    question_ids = sorted([int(q) for q in r.smembers(f"category_questions:{current_category}")])
    
    if not question_ids:
        await message.reply("❌ 状态信息获取失败，当前问卷无问题。")
        return
        
    try:
        current_progress = question_ids.index(int(current_q_index)) + 1
        total_questions = len(question_ids)
        percentage = (current_progress / total_questions) * 100
        
        status_text = f"📊 <b>答题进度</b>\n\n"
        status_text += f"🔄 当前问卷: <b>{current_category}</b>\n"
        status_text += f"➡️ 当前进度: {current_progress}/{total_questions}\n"
        status_text += f"📈 完成度: {percentage:.1f}%\n"
        
        await message.reply(status_text, parse_mode=ParseMode.HTML)
    except ValueError:
        await message.reply("❌ 状态信息获取失败，当前问题ID不在目录列表中。")

@dp.message(Command("help"))
async def show_help(message: Message):
    if str(message.from_user.id) == ADMIN_ID:
        await message.reply(ADMIN_HELP_TEXT, parse_mode=ParseMode.HTML)
    else:
        await message.reply(WELCOME_TEXT, parse_mode=ParseMode.HTML)

async def main():
    logging.info("机器人启动中...")
    
    # 在启动前检查 Redis 连接，如果没有连接成功就直接退出
    if r is None:
        logging.critical("❌ Redis 连接失败，程序将退出。请检查 Redis 服务是否正常运行。")
        return
    
    if ADMIN_ID and GROUP_ID:
        try:
            await bot.send_message(
                chat_id=int(ADMIN_ID),
                text=ADMIN_HELP_TEXT,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.exception("无法发送启动通知，请检查ADMIN_ID和机器人权限")
    else:
        logging.warning("ADMIN_ID 或 GROUP_ID 环境变量未设置，无法发送启动通知。")

    try:
        await dp.start_polling(bot)
    finally:
        logging.info("机器人已停止。")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
