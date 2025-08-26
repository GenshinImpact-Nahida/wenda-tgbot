import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import redis
import os
import json

# 配置
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Redis连接
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

# 管理员命令
@dp.message(Command("addquestion"))
async def add_question(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    if not command.args:
        return await message.reply("❌ 请提供问题内容\n格式: /addquestion 问题|选项1,选项2,选项3")
    
    try:
        text = command.args.strip()
        if "|" in text:
            question, options = text.split("|", 1)
            question = question.strip()
            options = options.strip()
        else:
            question = text
            options = ""
        
        idx = r.incr("question_count")
        r.hset(f"question:{idx}", "text", question)
        if options:
            r.hset(f"question:{idx}", "options", options)
        
        await message.reply(f"✅ 已添加问题 {idx}: {question}")
        
    except Exception as e:
        await message.reply(f"❌ 添加问题失败: {e}")

@dp.message(Command("addbranch"))
async def add_branch_question(message: Message, command: CommandObject):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    if not command.args:
        return await message.reply("❌ 请提供分支问题内容\n格式: /addbranch 问题|选项1:下一题ID,选项2:下一题ID")
    
    try:
        text = command.args.strip()
        if "|" in text:
            question, options = text.split("|", 1)
            question = question.strip()
            options = options.strip()
        else:
            question = text
            options = ""
        
        idx = r.incr("question_count")
        r.hset(f"question:{idx}", "text", question)
        r.hset(f"question:{idx}", "type", "branch")
        if options:
            r.hset(f"question:{idx}", "options", options)
        
        await message.reply(f"✅ 已添加分支问题 {idx}: {question}")
        
    except Exception as e:
        await message.reply(f"❌ 添加分支问题失败: {e}")

@dp.message(Command("listquestions"))
async def list_questions(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    count = r.get("question_count")
    if not count:
        return await message.reply("📝 还没有添加任何问题")
    
    questions = []
    for i in range(1, int(count) + 1):
        question = r.hget(f"question:{i}", "text")
        options = r.hget(f"question:{i}", "options")
        q_type = r.hget(f"question:{i}", "type")
        
        if options:
            if q_type == "branch":
                questions.append(f"{i}. [分支] {question}\n   选项: {options}")
            else:
                questions.append(f"{i}. {question}\n   选项: {options}")
        else:
            if q_type == "branch":
                questions.append(f"{i}. [分支] {question}")
            else:
                questions.append(f"{i}. {question}")
    
    await message.reply("📋 问题列表:\n" + "\n".join(questions))

@dp.message(Command("clearall"))
async def clear_all_questions(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("❌ 没有权限")
    
    count = r.get("question_count")
    if count:
        for i in range(1, int(count) + 1):
            r.delete(f"question:{i}")
        r.delete("question_count")
    await message.reply("✅ 已清空所有问题")

# 用户开始答题
@dp.message(Command("start"))
async def start_quiz(message: Message):
    count = r.get("question_count")
    if not count or int(count) == 0:
        await message.reply("❌ 还没有设置任何问题，请联系管理员")
        return
    
    user_id = message.from_user.id
    r.set(f"user:{user_id}:q", 1)
    r.set(f"user:{user_id}:started", "true")
    r.set(f"user:{user_id}:path", "main")  # 记录用户路径
    
    await message.reply("🎯 答题开始！请回答以下问题：")
    await send_question(user_id)

async def send_question(user_id: int):
    q_index = r.get(f"user:{user_id}:q")
    if not q_index:
        return
    
    question = r.hget(f"question:{q_index}", "text")
    options = r.hget(f"question:{q_index}", "options")
    q_type = r.hget(f"question:{q_index}", "type")
    
    if not question:
        await bot.send_message(user_id, "🎉 恭喜回答结束 ✅")
        r.delete(f"user:{user_id}:q")
        r.delete(f"user:{user_id}:started")
        r.delete(f"user:{user_id}:path")
        return
    
    kb = None
    if options:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for opt in options.split(","):
            opt_text = opt.split(":")[0].strip() if ":" in opt else opt.strip()
            kb.add(types.KeyboardButton(text=opt_text))
    
    question_text = f"❓ 问题 {q_index}: {question}"
    if q_type == "branch":
        question_text += "\n\n🔄 这是一个分支问题，你的选择将决定下一题"
    
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
    
    question = r.hget(f"question:{q_index}", "text")
    options = r.hget(f"question:{q_index}", "options")
    q_type = r.hget(f"question:{q_index}", "type")
    
    # 创建话题
    thread_name = f"{message.from_user.username or 'user'}_{user_id}"
    thread_id = r.get(f"thread:{user_id}")
    
    if not thread_id:
        try:
            forum_topic = await bot.create_forum_topic(
                GROUP_ID,
                name=thread_name,
                icon_color=0x6FB9F0
            )
            thread_id = forum_topic.message_thread_id
            r.set(f"thread:{user_id}", thread_id)
        except Exception as e:
            thread_id = None
    
    # 准备消息内容
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
    
    # 发送到群组话题
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            await bot.send_photo(
                GROUP_ID, 
                file_id, 
                caption=msg_text, 
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        elif message.video:
            file_id = message.video.file_id
            await bot.send_video(
                GROUP_ID,
                file_id,
                caption=msg_text,
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        elif message.document:
            file_id = message.document.file_id
            await bot.send_document(
                GROUP_ID,
                file_id,
                caption=msg_text,
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
        else:
            await bot.send_message(
                GROUP_ID, 
                msg_text, 
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        pass
    
    # 确定下一题
    next_q = None
    
    if q_type == "branch" and options and message.text:
        # 分支问题：根据答案确定下一题
        for opt in options.split(","):
            if ":" in opt:
                opt_text, next_id = opt.split(":", 1)
                if message.text.strip() == opt_text.strip():
                    next_q = int(next_id.strip())
                    break
        
        if next_q is None:
            # 如果没有匹配的选项，使用默认下一题
            next_q = int(q_index) + 1
    else:
        # 普通问题：按顺序下一题
        next_q = int(q_index) + 1
    
    # 检查下一题是否存在
    if not r.exists(f"question:{next_q}"):
        await bot.send_message(user_id, "🎉 恭喜回答结束！所有问题已完成。")
        r.delete(f"user:{user_id}:q")
        r.delete(f"user:{user_id}:started")
        r.delete(f"user:{user_id}:path")
        r.delete(f"thread:{user_id}")
    else:
        r.set(f"user:{user_id}:q", next_q)
        await send_question(user_id)

@dp.message(Command("status"))
async def check_status(message: Message):
    user_id = message.from_user.id
    current_q = r.get(f"user:{user_id}:q")
    started = r.get(f"user:{user_id}:started")
    
    if not started:
        await message.reply("❌ 你还没有开始答题，请使用 /start 开始")
        return
    
    total_q = r.get("question_count")
    if current_q and total_q:
        progress = int(current_q)
        total = int(total_q)
        percentage = (progress / total) * 100
        
        status_text = f"📊 <b>答题进度</b>\n\n"
        status_text += f"🔄 当前进度: {progress}/{total}\n"
        status_text += f"📈 完成度: {percentage:.1f}%\n"
        
        await message.reply(status_text, parse_mode=ParseMode.HTML)
    else:
        await message.reply("❌ 状态信息获取失败")

@dp.message(Command("help"))
async def show_help(message: Message):
    if message.from_user.id == ADMIN_ID:
        help_text = """
🤖 <b>管理员命令:</b>
/addquestion 问题|选项1,选项2,选项3 - 添加普通问题
/addbranch 问题|选项1:下一题ID,选项2:下一题ID - 添加分支问题
/listquestions - 列出所有问题
/clearall - 清空所有问题

💡 <b>分支问题说明:</b>
- 使用 /addbranch 创建分支问题
- 格式: 问题|选项1:下一题ID,选项2:下一题ID
- 例如: 你喜欢的颜色？|红色:3,蓝色:5,绿色:7
- 用户选择不同选项会跳转到不同的问题

👤 <b>用户命令:</b>
/start - 开始答题
/status - 查看答题进度
/help - 显示此帮助信息
        """
    else:
        help_text = """
🤖 <b>用户命令:</b>
/start - 开始答题
/status - 查看答题进度
/help - 显示此帮助信息

💡 <b>使用说明:</b>
1. 使用 /start 开始答题
2. 选择按钮选项或直接输入文本回答
3. 支持上传图片、视频、文档等作为答案
4. 某些问题会根据你的选择导向不同的问题路径
5. 完成所有问题后会收到完成提示
        """
    
    await message.reply(help_text, parse_mode=ParseMode.HTML)

async def main():
    logging.info("机器人启动中...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
