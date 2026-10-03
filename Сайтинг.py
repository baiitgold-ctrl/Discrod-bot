import os
import json
import re
import asyncio
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks

# ============================================================
# НАСТРОЙКИ
# ============================================================

GUILD_ID = 1540768352014704810
REVIEW_CHANNEL_ID = 1540770203170766908
SENIOR_ROLE_ID = 1540768998969446451
CANDIDATE_CHANNEL_ID = 1555858889495289866

APPLICATION_CHANNELS = {
    1540770139543445596: ("Команда", "🚀", [
        "Ваш никнейм",
        "Ваш возраст",
        "Ваш часовой пояс",
        "Сколько времени готовы уделять проекту?",
        "Есть ли у вас опыт работы в команде?",
        "Почему хотите попасть в нашу команду?",
        "Расскажите немного о себе",
    ]),
    1540770143792140448: ("Модератор", "🛡️", [
        "Ваш никнейм",
        "Ваш возраст",
        "Ваш часовой пояс",
        "Есть ли опыт модерации?",
        "Сколько времени готовы уделять серверу?",
        "Почему хотите стать модератором?",
        "Как поступите при нарушении правил?",
    ]),
    1540770151061000292: ("Разработчик", "💻", [
        "Ваш никнейм",
        "Ваш возраст",
        "Какие языки программирования знаете?",
        "Какой у вас опыт разработки?",
        "Ссылка на ваши проекты или работы",
        "Сколько времени готовы уделять проекту?",
        "Почему хотите стать разработчиком?",
    ]),
    1540770155578261544: ("Дизайнер", "🎨", [
        "Ваш никнейм",
        "Ваш возраст",
        "Какими программами для дизайна пользуетесь?",
        "Какой у вас опыт?",
        "Ссылка на портфолио",
        "Какие виды дизайна создаёте?",
        "Почему хотите работать с нами?",
    ]),
    1540770159671906404: ("Контентмейкер", "🎥", [
        "Ваш никнейм",
        "Ваш возраст",
        "На каких платформах создаёте контент?",
        "Ссылка на ваш канал или социальные сети",
        "Какой контент создаёте?",
        "Как часто готовы выпускать контент?",
        "Почему хотите сотрудничать с нами?",
    ]),
    1540770163673010336: ("Тестировщик", "🧪", [
        "Ваш никнейм",
        "Ваш возраст",
        "Какими устройствами пользуетесь?",
        "Есть ли опыт тестирования игр или приложений?",
        "Сколько времени готовы уделять тестированию?",
        "Умеете подробно описывать найденные ошибки?",
        "Почему хотите стать тестировщиком?",
    ]),
}

SCORING = {
    "Команда": [
        ("Ваш никнейм", 1),
        ("Ваш часовой пояс", 1),
        ("Сколько времени готовы уделять проекту?", 2),
        ("Есть ли у вас опыт работы в команде?", 1),
        ("Почему хотите попасть в нашу команду?", 2),
        ("Расскажите немного о себе", 2),
        ("Полнота заявки", 1),
    ],
    "Модератор": [
        ("Ваш никнейм", 1),
        ("Ваш часовой пояс", 1),
        ("Есть ли опыт модерации?", 2),
        ("Сколько времени готовы уделять серверу?", 1),
        ("Почему хотите стать модератором?", 1),
        ("Как поступите при нарушении правил?", 3),
        ("Полнота заявки", 1),
    ],
    "Разработчик": [
        ("Ваш никнейм", 1),
        ("Какие языки программирования знаете?", 2),
        ("Какой у вас опыт разработки?", 2),
        ("Ссылка на ваши проекты или работы", 2),
        ("Сколько времени готовы уделять проекту?", 1),
        ("Почему хотите стать разработчиком?", 1),
        ("Полнота заявки", 1),
    ],
    "Дизайнер": [
        ("Ваш никнейм", 1),
        ("Какими программами для дизайна пользуетесь?", 1),
        ("Какой у вас опыт?", 2),
        ("Ссылка на портфолио", 2),
        ("Какие виды дизайна создаёте?", 1),
        ("Почему хотите работать с нами?", 2),
        ("Полнота заявки", 1),
    ],
    "Контентмейкер": [
        ("Ваш никнейм", 1),
        ("На каких платформах создаёте контент?", 1),
        ("Ссылка на ваш канал или социальные сети", 2),
        ("Какой контент создаёте?", 1),
        ("Как часто готовы выпускать контент?", 2),
        ("Почему хотите сотрудничать с нами?", 2),
        ("Полнота заявки", 1),
    ],
    "Тестировщик": [
        ("Ваш никнейм", 1),
        ("Какими устройствами пользуетесь?", 1),
        ("Есть ли опыт тестирования игр или приложений?", 1),
        ("Сколько времени готовы уделять тестированию?", 1),
        ("Умеете подробно описывать найденные ошибки?", 2),
        ("Почему хотите стать тестировщиком?", 2),
        ("Полнота заявки", 2),
    ],
}

DATA_FILE = "applications.json"


# ============================================================
# ТОКЕН TEMALIX
# ============================================================

def get_token():
    """
    Temalix должен передать токен через переменную окружения.
    Поддерживаем также TOKEN на случай, если в панели названо так.
    """
    token = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")

    if token:
        token = token.strip().strip('"').strip("'")

    return token


TOKEN = get_token()

if not TOKEN:
    print("=" * 60)
    print("ОШИБКА: DISCORD_TOKEN НЕ НАЙДЕН")
    print("=" * 60)
    print("Создай переменную окружения:")
    print("DISCORD_TOKEN=ТВОЙ_ТОКЕН_БОТА")
    print()
    print("Также можно использовать имя TOKEN:")
    print("TOKEN=ТВОЙ_ТОКЕН_БОТА")
    print("=" * 60)
    raise SystemExit(1)


# ============================================================
# DISCORD
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

processed = {}
last_candidate_post = None


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def load_data():
    global processed, last_candidate_post

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        processed = data.get("processed", {})

        value = data.get("last_candidate_post")

        if value:
            last_candidate_post = datetime.fromisoformat(value)

    except Exception:
        processed = {}
        last_candidate_post = None


def save_data():
    data = {
        "processed": processed,
        "last_candidate_post":
            last_candidate_post.isoformat()
            if last_candidate_post else None
    }

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )
    except Exception as error:
        print(f"Не удалось сохранить applications.json: {error}")


# ============================================================
# ПАРСИНГ
# ============================================================

def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        text.lower().replace("ё", "е")
    ).strip()


def clean_answer(text):
    text = text.strip()
    text = re.sub(r"^\s*[-•*]\s*", "", text)
    text = re.sub(r"^\s*\d+[\).:-]\s*", "", text)
    return text.strip()


def is_empty(text):
    if not text:
        return True

    return normalize(text) in {
        "",
        "-",
        "нет",
        "нету",
        "не знаю",
        "отсутствует",
    }


def contains_link(text):
    return bool(
        re.search(
            r"(https?://|www\.|discord\.gg/|t\.me/|vk\.com/|github\.com/)",
            text.lower()
        )
    )


def extract_answers(message, questions):
    lines = [
        line.strip()
        for line in message.content.replace("\r", "").split("\n")
        if line.strip()
    ]

    answers = {}
    current = None

    for line in lines:
        line_norm = normalize(line)

        matched = None

        for question in questions:
            if normalize(question) in line_norm:
                matched = question
                break

        if matched:
            current = matched

            answer = re.sub(
                r"^\s*\d+[\).:-]?\s*",
                "",
                line
            )

            answer = re.sub(
                re.escape(matched),
                "",
                answer,
                count=1,
                flags=re.IGNORECASE
            )

            answer = re.sub(
                r"^\s*[:\-–—]\s*",
                "",
                answer
            )

            answers[current] = clean_answer(answer)

        elif current:
            extra = clean_answer(line)

            if extra:
                if answers.get(current):
                    answers[current] += " " + extra
                else:
                    answers[current] = extra

    # Запасной вариант для формата:
    # 1. ответ
    # 2. ответ
    numbered = []

    for line in lines:
        match = re.match(
            r"^\s*(\d+)[\).:-]\s*(.*)$",
            line
        )

        if match:
            numbered.append(
                (
                    int(match.group(1)),
                    clean_answer(match.group(2))
                )
            )

    if len(numbered) >= len(questions):
        for number, answer in numbered:
            if 1 <= number <= len(questions):
                question = questions[number - 1]

                if is_empty(answers.get(question, "")):
                    answers[question] = answer

    return answers


def good_answer(criterion, answer):
    if is_empty(answer):
        return False

    value = normalize(answer)

    if criterion in {
        "Ссылка на ваши проекты или работы",
        "Ссылка на портфолио",
        "Ссылка на ваш канал или социальные сети",
    }:
        return contains_link(answer) or len(value) >= 10

    if criterion == "Ваш никнейм":
        return len(value) >= 2

    if criterion == "Ваш часовой пояс":
        return len(value) >= 2

    if criterion in {
        "Сколько времени готовы уделять проекту?",
        "Сколько времени готовы уделять серверу?",
        "Сколько времени готовы уделять тестированию?",
        "Как часто готовы выпускать контент?",
    }:
        return len(value) >= 2

    if criterion == "Какие языки программирования знаете?":
        return any(
            word in value
            for word in [
                "python", "javascript", "java", "c++",
                "c#", "html", "css", "php", "kotlin",
                "swift", "lua", "sql", "typescript",
                "go", "rust"
            ]
        )

    if criterion == "Какими программами для дизайна пользуетесь?":
        return any(
            word in value
            for word in [
                "photoshop", "figma", "illustrator",
                "canva", "blender", "corel",
                "after effects", "premiere",
                "procreate", "krita"
            ]
        ) or len(value) >= 8

    if criterion == "На каких платформах создаёте контент?":
        return any(
            word in value
            for word in [
                "youtube", "tiktok", "telegram",
                "vk", "instagram", "rutube",
                "discord", "shorts"
            ]
        ) or len(value) >= 5

    if criterion == "Как поступите при нарушении правил?":
        return any(
            word in value
            for word in [
                "правил", "провер", "зафикс",
                "предупред", "накаж", "доклад",
                "админ", "сообщ"
            ]
        ) or len(value) >= 20

    if criterion == "Умеете подробно описывать найденные ошибки?":
        return any(
            word in value
            for word in [
                "да", "умею", "могу",
                "подробно", "описать", "репорт"
            ]
        )

    if criterion.startswith("Почему"):
        return len(value) >= 10

    if criterion.startswith("Расскажите"):
        return len(value) >= 10

    return len(value) >= 3


# ============================================================
# ОЦЕНКА
# ============================================================

def evaluate(role, answers):
    criteria = SCORING[role]

    maximum = sum(
        points for _, points in criteria
    )

    score = 0
    details = []
    filled = 0

    regular = [
        item for item in criteria
        if item[0] != "Полнота заявки"
    ]

    for criterion, points in regular:
        answer = answers.get(criterion, "")

        if not is_empty(answer):
            filled += 1

        if good_answer(criterion, answer):
            score += points
            details.append(
                f"✅ {criterion}: +{points}/{points}"
            )
        else:
            details.append(
                f"⚠️ {criterion}: +0/{points}"
            )

    completeness = dict(criteria).get(
        "Полнота заявки",
        0
    )

    ratio = filled / len(regular) if regular else 0

    if ratio >= 0.85:
        score += completeness
        details.append(
            f"✅ Полнота заявки: +{completeness}/{completeness}"
        )
    elif ratio >= 0.60:
        partial = completeness // 2
        score += partial
        details.append(
            f"⚠️ Полнота заявки: +{partial}/{completeness}"
        )
    else:
        details.append(
            f"❌ Полнота заявки: +0/{completeness}"
        )

    return {
        "score": score,
        "maximum": maximum,
        "percent": round(score / maximum * 100),
        "approved": score >= 6,
        "details": details
    }


# ============================================================
# ПРОВЕРКА ЗАЯВКИ
# ============================================================

async def process_application(message, force=False):
    if message.author.bot:
        return

    channel_id = message.channel.id

    if channel_id not in APPLICATION_CHANNELS:
        return

    message_key = str(message.id)

    if message_key in processed and not force:
        return

    role, emoji, questions = APPLICATION_CHANNELS[channel_id]

    answers = extract_answers(
        message,
        questions
    )

    result = evaluate(
        role,
        answers
    )

    processed[message_key] = {
        "channel_id": channel_id,
        "user_id": message.author.id,
        "role": role,
        "score": result["score"],
        "maximum": result["maximum"],
        "approved": result["approved"],
        "time": datetime.now(timezone.utc).isoformat()
    }

    save_data()

    try:
        await message.add_reaction(
            "✅" if result["approved"] else "❌"
        )
    except Exception as error:
        print(f"Ошибка реакции: {error}")

    review_channel = bot.get_channel(
        REVIEW_CHANNEL_ID
    )

    if review_channel is None:
        print("Канал проверки не найден.")
        return

    status = (
        "🟢 ПРЕДВАРИТЕЛЬНО ОДОБРЕНА"
        if result["approved"]
        else
        "🔴 НЕ ПРОШЛА ПРЕДВАРИТЕЛЬНЫЙ ОТБОР"
    )

    embed = discord.Embed(
        title=f"{emoji} Проверка заявки",
        description=(
            f"**Кандидат:** {message.author.mention}\n"
            f"**Должность:** {role}\n"
            f"**Статус:** {status}\n"
            f"**Оценка:** `{result['score']}/{result['maximum']}` "
            f"({result['percent']}%)\n\n"
            f"**Разбор:**\n"
            + "\n".join(result["details"])
        ),
        color=(
            discord.Color.green()
            if result["approved"]
            else discord.Color.red()
        ),
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="🔗 Заявка",
        value=f"[Открыть заявку]({message.jump_url})",
        inline=False
    )

    embed.set_footer(
        text=(
            "Автоматическая предварительная проверка. "
            "Финальное решение принимает старший состав."
        )
    )

    await review_channel.send(
        content=(
            f"<@&{SENIOR_ROLE_ID}>\n"
            f"Кандидат: {message.author.mention}\n"
            f"Результат: **{status}**"
        ),
        embed=embed
    )


# ============================================================
# СООБЩЕНИЯ
# ============================================================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id in APPLICATION_CHANNELS:
        await process_application(message)

    elif message.channel.id == REVIEW_CHANNEL_ID:
        guild = message.guild

        if guild:
            role = guild.get_role(
                SENIOR_ROLE_ID
            )

            if role and role in message.author.roles:
                await message.reply(
                    f"<@&{SENIOR_ROLE_ID}> "
                    "Время обзвона/собеседования объявит "
                    "старший администратор."
                )

    await bot.process_commands(message)


# ============================================================
# СПИСОК КАНДИДАТОВ
# ============================================================

async def publish_candidates():
    channel = bot.get_channel(
        CANDIDATE_CHANNEL_ID
    )

    if channel is None:
        print("Канал кандидатов не найден.")
        return

    approved = [
        item
        for item in processed.values()
        if item.get("approved") is True
    ]

    if not approved:
        await channel.send(
            "📋 **Список кандидатов**\n\n"
            "За текущий период одобренных кандидатов нет."
        )

    else:
        grouped = {}

        for item in approved:
            grouped.setdefault(
                item.get("role", "Неизвестно"),
                []
            ).append(item)

        text = (
            "📋 **СПИСОК КАНДИДАТОВ**\n\n"
            "Кандидаты прошли автоматическую "
            "предварительную проверку.\n"
            "Финальное решение принимает старший состав.\n\n"
        )

        for role in [
            "Команда",
            "Модератор",
            "Разработчик",
            "Дизайнер",
            "Контентмейкер",
            "Тестировщик"
        ]:
            candidates = grouped.get(role, [])

            if not candidates:
                continue

            text += f"### {role}\n"

            for item in candidates:
                text += (
                    f"• <@{item['user_id']}> — "
                    f"`{item['score']}/{item['maximum']}`\n"
                )

            text += "\n"

        text += (
            f"<@&{SENIOR_ROLE_ID}>\n"
            "🕐 Время обзвона/собеседования "
            "объявит старший администратор."
        )

        await channel.send(text)

    global last_candidate_post
    last_candidate_post = datetime.now(timezone.utc)
    save_data()


# ============================================================
# АВТОМАТИЧЕСКИЕ 3 ДНЯ
# ============================================================

@tasks.loop(minutes=10)
async def candidates_timer():
    global last_candidate_post

    now = datetime.now(timezone.utc)

    if last_candidate_post is None:
        last_candidate_post = now
        save_data()
        return

    if now - last_candidate_post >= timedelta(days=3):
        await publish_candidates()


@candidates_timer.before_loop
async def before_timer():
    await bot.wait_until_ready()


# ============================================================
# КОМАНДЫ
# ============================================================

@bot.command(name="helpbot")
async def helpbot(ctx):
    embed = discord.Embed(
        title="🤖 Команды бота",
        description="Система проверки заявок BackGame.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="!helpbot",
        value="Показать команды.",
        inline=False
    )

    embed.add_field(
        name="!status",
        value="Статистика заявок. Только администратор.",
        inline=False
    )

    embed.add_field(
        name="!candidates",
        value="Сразу опубликовать список кандидатов.",
        inline=False
    )

    embed.add_field(
        name="!rescan",
        value="Проверить последние 100 сообщений в каналах заявок.",
        inline=False
    )

    embed.add_field(
        name="!review ID",
        value="Повторно проверить заявку по ID сообщения.",
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command(name="status")
@commands.has_permissions(administrator=True)
async def status(ctx):
    total = len(processed)

    approved = sum(
        1
        for item in processed.values()
        if item.get("approved")
    )

    rejected = total - approved

    await ctx.send(
        "📊 **Статистика**\n"
        f"Всего: `{total}`\n"
        f"Одобрено предварительно: `{approved}`\n"
        f"Не прошло: `{rejected}`"
    )


@bot.command(name="candidates")
@commands.has_permissions(administrator=True)
async def candidates(ctx):
    await publish_candidates()
    await ctx.send(
        "✅ Список кандидатов опубликован."
    )


@bot.command(name="rescan")
@commands.has_permissions(administrator=True)
async def rescan(ctx):
    await ctx.send(
        "🔎 Начинаю сканирование последних 100 сообщений..."
    )

    count = 0

    for channel_id in APPLICATION_CHANNELS:
        channel = bot.get_channel(channel_id)

        if channel is None:
            continue

        try:
            async for message in channel.history(
                limit=100
            ):
                if message.author.bot:
                    continue

                if str(message.id) not in processed:
                    await process_application(message)
                    count += 1

                await asyncio.sleep(0.2)

        except Exception as error:
            print(
                f"Ошибка сканирования {channel_id}: {error}"
            )

    await ctx.send(
        f"✅ Готово. Новых заявок обработано: `{count}`"
    )


@bot.command(name="review")
@commands.has_permissions(administrator=True)
async def review(ctx, message_id: int):
    for channel_id in APPLICATION_CHANNELS:
        channel = bot.get_channel(channel_id)

        if channel is None:
            continue

        try:
            message = await channel.fetch_message(
                message_id
            )

            await process_application(
                message,
                force=True
            )

            await ctx.send(
                "✅ Заявка повторно проверена."
            )
            return

        except discord.NotFound:
            continue

        except Exception as error:
            print(error)
            continue

    await ctx.send(
        "❌ Заявка с таким ID не найдена."
    )


# ============================================================
# ОШИБКИ КОМАНД
# ============================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(
        error,
        commands.MissingPermissions
    ):
        await ctx.send(
            "❌ Команда доступна только администраторам."
        )
        return

    if isinstance(
        error,
        commands.MissingRequiredArgument
    ):
        await ctx.send(
            "❌ Укажи аргумент. Пример: `!review 123456789`"
        )
        return

    if isinstance(
        error,
        commands.BadArgument
    ):
        await ctx.send(
            "❌ Неверный формат команды."
        )
        return

    if isinstance(
        error,
        commands.CommandNotFound
    ):
        return

    print(
        f"Ошибка команды: {error}"
    )


# ============================================================
# ЗАПУСК
# ============================================================

@bot.event
async def on_ready():
    load_data()

    print(
        f"✅ Бот запущен: {bot.user} "
        f"(ID: {bot.user.id})"
    )

    guild = bot.get_guild(GUILD_ID)

    if guild:
        print(
            f"✅ Сервер найден: {guild.name}"
        )
    else:
        print(
            "⚠️ Сервер с указанным ID не найден."
        )

    if not candidates_timer.is_running():
        candidates_timer.start()

    print(
        "✅ Система автоматической проверки заявок активна."
    )


bot.run(TOKEN)
