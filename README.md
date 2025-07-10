# Chat App Internship Project

## Overview

This repository contains solutions for internship tasks:
- **Group A:** Core chat application (JWT authentication, RBAC, WebSocket chat)
- **Group B:** Admin dashboard & analytics (SQLAdmin)
- **Group C:** *(Optional)* Sentiment analysis notebook

---

## 🚀 Setup Instructions (All Tasks)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/suneelgiree/chat-app.git
   cd chat-app
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your database URI, JWT secret, etc.

5. **Run the app:**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📑 Task Breakdown

### Group A: Chat Application

- User signup/login with hashed passwords (`/signup`, `/login`)
- JWT authentication (HS256, role included in JWT)
- Role-Based Access Control (admin/user)
- WebSocket chat (`/ws/{room_id}`) secured with JWT
- Recent messages fetched with cursor-based pagination
- PostgreSQL persistence

### Group B: Admin Dashboard & Analytics

- `/admin` dashboard (SQLAdmin)
- Analytics endpoints: messages per room, user activity, date filters, CSV export
- Dashboard protected by RBAC (admin only)

### Group C: Sentiment Analysis *(Optional)*

- See `notebooks/sentiment_analysis.ipynb`
- Clean, commented code with markdown explanations and visualizations

---

## 🔗 Endpoints Overview

| Endpoint              | Description                           |
|-----------------------|---------------------------------------|
| `/signup`             | Register a user (role: admin/user)    |
| `/login`              | JWT login                             |
| `/ws/{room_id}`       | WebSocket chat                        |
| `/admin`              | Admin dashboard (SQLAdmin)            |
| `/analytics/...`      | Analytics endpoints                   |

---

## 🛠️ Notes

- If you see errors about package versions (e.g., `'str' object has no attribute 'parameter_name'`), delete `.venv` and reinstall.
- For Group B, only admin users can access `/admin` and analytics routes.
- For Group C, see the `notebooks/` folder.

---

## 🧑‍💻 Author

Suneel Giree  
[GitHub: suneelgiree](https://github.com/suneelgiree)

---

## 📄 License

[MIT License](LICENSE)