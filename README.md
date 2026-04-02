![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Railway-336791?logo=postgresql)
![React Native](https://img.shields.io/badge/React_Native-Expo-61DAFB?logo=react)
![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway)
![Docker](https://img.shields.io/badge/Docker-2596ED?style=flat&logo=docker&logoColor=white)

# APEXIS

A daily astronomy and vocabulary app. Once a day, APEXIS fetches NASA's Astronomy Picture of the Day and pairs it with a random English word and its definition.

Built with Python, FastAPI, PostgreSQL (previously sqlite3), and React Native.

---

## Apexis Example
<p align="center">
  <img src="example2.jpeg" alt="app_example" width="350" height="700">
</p>

---

## How it works

```
Daily script → PostgreSQL → FastAPI → Mobile app
```

- A scheduled Python script runs every day, fetching the NASA APOD and a random word from a dictionary API.
- Data is stored in a PostgreSQL database hosted on Railway, free tier ;).
- A FastAPI backend serves the data via a REST API.
- A React Native mobile app displays the data on your phone.

---

## Project structure

```
apexis/
│── index.py              ← main script 
├── backend/
│   ├── main.py           ← FastAPI app
│   ├── database.py       ← DB queries
│   └── models.py         ← image and word response models for FastAPI
├── apexis-app/
|   ├── App.js            ← frontend for mobile
├── .env
├── .gitignore
├── Procfile              ← Railway file
├── Dockerfile            ← Docker initializer
├── README.md
└── requirements.txt      ← lists all dependencies
```

---

## Installation

### Download the APK (android only)

Download the latest APK from the [Releases](https://github.com/benaytms/apexis/releases/tag/v.1.0.4) page and install it directly.

> You may need to enable **Install from unknown sources** in your phone's settings.

---

## Running locally

### Prerequisites
- [Docker](https://docs.docker.com/get-started/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- API keys for [Nasa](https://api.nasa.gov/), [Merriam-Webster Dictionary](https://dictionaryapi.com/)
- Discord Server and [Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

### Setup
1. Clone the repository
   ```bash
   git clone https://github.com/benaytms/apexis.git
   cd apexis
   ```
2. Create your own '.env' with your own keys (follow the example)
3. Start it up
   ```bash
   docker compose up --build
   ```
4. The endpoints will be available at http://localhost:8000/docs

### Services
| Service | Description |
|---|---|
|`api`| FastAPI server on port 8000 |
|`cron`| Daily pipeline - runs at 06:00 UTC (03:00 BRT) |
|`db`| PostgreSQL on port 5433 |

### Useful commands
```bash
docker compose up --build -d    # Run in the backgourd
docker compose logs -f          # Follow logs
docker compose down             # Stops the container
docker container prune          # Removes all stopped containers
```

---

## APIs used

- [NASA APOD API](https://api.nasa.gov/) — Astronomy Picture of the Day
- [Merriam-Webster API](https://dictionaryapi.com/)- Word dictionary

---
## Todo

- Add image saving option

---

## Version
v.1.0.4

---
## License

MIT

