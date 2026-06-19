# 📊 FINANZEN | Real-Time Budget Tracker

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

> A full-stack application built to help users set a budget, log daily expenses, and show financial statistics using live, interactive charts.
> 
🚀 **Live Demo:** [Click here to view FINANZEN](https://smon2006.github.io/finanzen/)

---

## ✨ Key Features

* **Custom Budget Cycles:** Users can set strict monthly budgets or define custom day-cycles (e.g., bi-weekly paychecks) with automated rollover logic.
* **Interactive Data Visualization:** Real-time expense breakdown using `Chart.js`, allowing users to filter transactions dynamically by clicking chart segments.
* **Secure Authentication:** Robust user management featuring JWT (JSON Web Tokens) and `bcrypt` password hashing. Strict regex-based password policies enforced at the schema level.
* **Automated System Maintenance:** Implemented cron-triggered API health checks to prevent server cold-starts, reducing initial load latency by over 90% for a seamless login experience.
* **Responsive UI/UX:** Built with Vanilla JavaScript, HTML5, and CSS3. The interface seamlessly adapts to desktop, tablet, and mobile environments without relying on bloated front-end frameworks.

---

## 🏗️ System Architecture & Tech Stack

FINANZEN is built using a modern, decoupled architecture, separating the client interface from the RESTful API engine.

### Backend (The Engine)
* **Framework:** Python / FastAPI (Chosen for high-performance async processing)
* **Database:** PostgreSQL (Hosted via Render)
* **ORM:** SQLAlchemy (For secure database querying and schema management)
* **Validation:** Pydantic (Strict data type enforcement and serialization)
* **Security:** PyJWT & passlib (bcrypt)

### Frontend (The Client)
* **Core:** HTML5, CSS3, Vanilla JavaScript (ES6+)
* **Data Visualization:** Chart.js
* **Alerts:** SweetAlert2
* **Hosting:** GitHub Pages

---

## 🗄️ Database Schema 

The database is highly normalized and utilizes proper indexing (`index=True` on IDs and Emails) to ensure fast query times even as the user base scales.

* **`Users` Table:** Manages credentials, hashed passwords, and individual budget cycle preferences. One-to-Many relationship with Expenses.
* **`Expenses` Table:** Tracks individual transactions, linked to users via foreign keys (`user_id`), optimized with cascading deletes.

---

## 🚀 Local Installation & Setup

Want to run FINANZEN on your local machine? Follow these steps:

### 1. Clone the Repository
```bash
git clone https://github.com/smon2006/finanzen.git
cd finanzen
```

### 2. Set up the Backend Engine
Navigate to the backend directory and create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
Install the required Python dependencies:
```bash
pip install -r requirements.txt
```
### 3. Environment Variables
Create a .env file in the root backend directory and add your database credentials and secret keys:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/finanzen_db
SECRET_KEY=your_secret_jwt_key
```
### 4. Run the Server
Launch the FastAPI Uvicorn server:
```bash
uvicorn main:app --reload
```
The API will be available at http://localhost:8000 and the interactive Swagger Docs at http://localhost:8000/docs

### 5. Launch the Frontend
Simply open index.html in your preferred web browser, or serve it using a local live server extension.
