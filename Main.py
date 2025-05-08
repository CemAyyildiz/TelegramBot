import datetime
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TWEETS_FILE = "tweets.json"
USER_COUNT_FILE = "user_tweet_count.json"
ADMINS = [1299016905, 1032177818]  # Adminlerin Telegram ID'lerini buraya ekleyin

# Yardımcı Fonksiyonlar
def load_tweets():
    if os.path.exists(TWEETS_FILE):
        with open(TWEETS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tweets(tweets):
    with open(TWEETS_FILE, "w") as f:
        json.dump(tweets, f, indent=4)

def load_user_tweet_count():
    if os.path.exists(USER_COUNT_FILE):
        with open(USER_COUNT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_tweet_count(counts):
    with open(USER_COUNT_FILE, "w") as f:
        json.dump(counts, f, indent=4)

# /tweet komutu
async def add_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Lütfen tweet linkini şu şekilde gönderin:\n/tweet [link]")
        return

    user = update.effective_user.username or str(update.effective_user.id)
    tweet_link = context.args[0]
    today = str(datetime.date.today())

    tweets = load_tweets()
    tweet_count = load_user_tweet_count()

    # Kullanıcının günlük tweet limitini kontrol et
    if user not in tweet_count:
        tweet_count[user] = {"count": 0}  # Kullanıcı için başlangıçta count 0 olarak ekle

    if tweet_count[user].get("count", 0) >= 1:
        await update.message.reply_text("Bugün zaten tweet eklediniz. Yarın tekrar deneyin.")
        return

    # Tweet kaydını oluştur
    tweets[tweet_link] = {
        "user": user,
        "date": today,
        "interactions": [],
        "viewed_by": []  # Bu, butona tıklayan kullanıcıları kaydedecek
    }

    tweet_count[user]["count"] += 1  # Kullanıcının tweet sayısını artır

    save_tweets(tweets)
    save_user_tweet_count(tweet_count)

    # Inline buton ekle
    keyboard = [
        [InlineKeyboardButton("Lütfen etkileşim verdikten sonra butona basınız", callback_data=f"engage_{tweet_link}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"Tweet kaydedildi: {tweet_link}", reply_markup=reply_markup)

# /liste komutu
async def list_active_tweets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tweets = load_tweets()
    today = str(datetime.date.today())
    result = []

    for tweet_link, data in tweets.items():
        if data.get("date") == today:
            username = data.get("user", "bilinmeyen")
            result.append(f"👤 @{username} ➤ {tweet_link}")

    if result:
        await update.message.reply_text("📋 Bugünkü tweet listesi:\n\n" + "\n".join(result))
    else:
        await update.message.reply_text("Bugün henüz kimse tweet atmamış.")

# Buton tıklama işlemi
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user.username or str(query.from_user.id)
    tweet_link = query.data.split("_")[1]  # callback_data'dan tweet linkini ayıklama

    # Tweet verisini yükle
    tweets = load_tweets()

    if tweet_link not in tweets:
        await query.answer("Bu tweet sistemde kayıtlı değil.")
        return

    # Kullanıcının etkileşim verdiğini kaydet
    if user not in tweets[tweet_link]["interactions"]:
        tweets[tweet_link]["interactions"].append(user)
        save_tweets(tweets)
        await query.answer("Etkileşim kaydedildi.")
    else:
        await query.answer("Bu tweet'e zaten etkileşim verdiniz.")

# Admin komutları
async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("Bu komutu yalnızca adminler kullanabilir.")
        return
    
    save_tweets({})
    save_user_tweet_count({})
    await update.message.reply_text("Tüm veriler sıfırlandı.")

async def list_user_interactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("Bu komutu yalnızca adminler kullanabilir.")
        return

    tweets = load_tweets()
    interaction_counts = {}

    for tweet_link, data in tweets.items():
        for user in data.get("interactions", []):
            interaction_counts[user] = interaction_counts.get(user, 0) + 1

    if interaction_counts:
        sorted_list = sorted(interaction_counts.items(), key=lambda x: x[1], reverse=True)
        response = "💬 Etkileşim Verenler:\n\n"
        for user, count in sorted_list:
            response += f"@{user}: {count} etkileşim\n"
    else:
        response = "Henüz kimse etkileşim vermemiş."

    await update.message.reply_text(response)

# ✅ Botu başlat
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder
    import logging

    logging.basicConfig(level=logging.INFO)

    app = ApplicationBuilder().token("8043204466:AAEVB8zIxrou-PG0hXzg-IFFo2qA-DiG8X0").build()

    app.add_handler(CommandHandler("tweet", add_tweet))
    app.add_handler(CommandHandler("liste", list_active_tweets))
    app.add_handler(CommandHandler("resetveri", reset_data))
    app.add_handler(CommandHandler("etkilesimler", list_user_interactions))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot çalışıyor...")
    app.run_polling()
