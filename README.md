# 🎬 MovieMate

> Your personal movie recommendation assistant in Telegram

A Telegram bot that helps you discover, track, and manage your movie watchlist using The Movie Database (TMDb) API.

---

## ✨ Features

- 🔍 **Search Movies** - Find any movie by title
- 🔥 **Trending** - See what's hot today or this week
- ⭐ **Popular** - Discover most popular movies
- 🎯 **Recommendations** - Get personalized suggestions based on your favorites
- ❤️ **Favorites** - Save movies you love
- ✅ **Watch History** - Track what you've watched
- 🎥 **Trailers** - Watch movie trailers on YouTube
- 📊 **Statistics** - View your movie stats

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- TMDb API Key (from [themoviedb.org](https://www.themoviedb.org/settings/api))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/michaeeeel1/moviemate.git
cd moviemate
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
```

Edit `.env`:
```env
BOT_TOKEN=your_telegram_bot_token
TMDB_API_KEY=your_tmdb_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/moviemate
```

5. **Create database**
```bash
python create_db.py
```

6. **Run the bot**
```bash
python run.py
```

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11
- **Bot Framework**: python-telegram-bot 21.5
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **API**: TMDb API v3
- **External Libraries**: tmdbv3api, psycopg2, python-dotenv

---

## 📁 Project Structure

```
moviemate/
├── bot/
│   ├── handlers/       # Command and message handlers
│   ├── keyboards/      # Telegram keyboards
│   ├── utils/          # Helper functions and API wrapper
│   └── main.py         # Bot initialization
├── config/
│   └── settings.py     # Configuration
├── database/
│   ├── models.py       # SQLAlchemy models
│   ├── crud.py         # Database operations
│   └── connection.py   # Database connection
├── create_db.py        # Database setup script
├── run.py              # Main entry point
└── requirements.txt    # Dependencies
```

---

## 🎮 Usage

1. **Start the bot**: Send `/start` to your bot
2. **Search movies**: Click 🔍 Search Movies and enter a title
3. **View details**: Tap on any movie to see full information
4. **Add to favorites**: Click ❤️ on movies you like
5. **Get recommendations**: Bot learns your taste and suggests similar movies
6. **Track your watches**: Mark movies as watched to build your stats

---

## 🌟 Screenshots

### Main Menu
![Main Menu](docs/screenshots/main_menu.png)

### Search Results
![Search Results](docs/screenshots/search.png)

### Movie Details
![Movie Details](docs/screenshots/details.png)

---

## 📊 Database Schema

- **users** - User accounts
- **user_preferences** - User settings
- **favorites** - Favorite movies
- **watch_history** - Watched movies
- **search_history** - Search queries
- **recommendations_cache** - Cached recommendations
- **daily_stats** - Daily statistics

---

## 🔧 Configuration

Edit `config/settings.py` or use environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token | ✅ |
| `TMDB_API_KEY` | TMDb API Key | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |

---

## 🚀 Deployment

### Railway

1. Fork this repository
2. Create new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Add PostgreSQL database
5. Set environment variables
6. Deploy!

### Render

1. Create new Web Service
2. Connect repository
3. Add PostgreSQL database
4. Set environment variables
5. Deploy!


## 👤 Author

**Michaeeeel1**

- GitHub: [@michaeeeel1](https://github.com/michaeeeel1)
- Telegram: [@michaeeeel1](https://t.me/michaeeeel1)

---

## 🙏 Acknowledgments

- [TMDb](https://www.themoviedb.org/) - Movie database and API
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot framework
- [tmdbv3api](https://github.com/AnthonyBloomer/tmdbv3api) - TMDb API wrapper


Made with ❤️ and Python 🐍