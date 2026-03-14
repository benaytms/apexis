![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Railway-336791?logo=postgresql)
![React Native](https://img.shields.io/badge/React_Native-Expo-61DAFB?logo=react)
![Deploy](https://img.shields.io/badge/Deploy-Railway-0B0D0E?logo=railway)

# APEXIS

A daily astronomy and vocabulary app. Once a day, APEXIS fetches NASA's Astronomy Picture of the Day and pairs it with a random English word and its definition.

Built with Python, FastAPI, PostgreSQL (previously sqlite3), and React Native.

---

## Apexis Example
<img src="example2.jpeg" alt="app_example" width="350" height="700">

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
├── README.md
└── requirements.txt      ← lists all dependencies
```

---

## Installation

### Download the APK (android only)

Download the latest APK from the [Releases](https://github.com/benaytms/apexis/releases/tag/v.1.0.3) page and install it directly.

> You may need to enable **Install from unknown sources** in your phone's settings.

---

## APIs used

- [NASA APOD API](https://api.nasa.gov/) — Astronomy Picture of the Day
- [Merriam-Webster API](https://dictionaryapi.com/)- Word dictionary

---

## Version
v.1.0.3

---
## License

MIT

