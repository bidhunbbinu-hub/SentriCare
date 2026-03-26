# Smart Care System

A real-time patient monitoring system that detects falls, monitors heart rate, and sends alerts to caregivers through a web dashboard.

The system integrates **computer vision, real-time streaming, WebSockets, and a full-stack web application**.

---

# Features

* Fall Detection using computer vision
* Heart Rate Monitoring
* Real-time alerts via WebSocket
* Live camera streaming
* Emergency call system
* Alert history and confirmation
* Web dashboard for monitoring

---

# System Architecture

```
Camera
   │
   ▼
Frame Engine
   │
   ▼
AI Modules
(Fall Detection + Heart Rate)
   │
   ▼
Alert Manager
   │
   ├── Database (Alert History)
   └── WebSocket (Real-time alerts)
           │
           ▼
      Frontend Dashboard
           │
           ▼
       Caregivers
```

---

# Project Structure

```
smart-care-system/

backend/
│
├── main.py
├── frame_engine.py
│
├── fall_detection/
├── evm_module/
├── camera/
│
├── alerts/
├── websocket/
├── auth/
├── users/
├── patients/
│
├── database/
│
└── requirements.txt


frontend/
│
├── src/
│   ├── components/
│   │   ├── VideoStream.jsx
│   │   ├── AlertPanel.jsx
│   │   ├── HealthStats.jsx
│   │   └── EmergencyPanel.jsx
│   │
│   ├── pages/
│   │   └── Dashboard.jsx
│   │
│   ├── services/
│   │   ├── api.js
│   │   └── websocket.js
│   │
│   ├── App.jsx
│   └── main.jsx
│
└── package.json
```

---

# Requirements

Install the following:

* Python 3.9+
* Node.js (v18+ recommended)
* Miniconda or Anaconda
* Git

---

# 1. Clone the Repository

```
git clone https://github.com/your-repo/smart-care-system.git
cd smart-care-system
```

---

# 2. Backend Setup (Miniconda)

Create a conda environment:

```
conda create -n smartcare python=3.9
```

Activate it:

```
conda activate smartcare
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# 3. Run Backend Server

Navigate to backend:

```
cd backend
```

Run FastAPI server:

```
uvicorn main:app --reload
```

Backend will run at:

```
http://localhost:8000
```

---

# 4. Frontend Setup

Open another terminal.

Navigate to frontend:

```
cd frontend
```

Install dependencies:

```
npm install
```

---

# 5. Run Frontend

```
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

# 6. Live Camera Stream

The frontend loads the live stream from:

```
http://localhost:8000/video-stream
```

Make sure the backend camera module is running.

---

# 7. WebSocket Alerts

The frontend connects to:

```
ws://localhost:8000/ws/alerts
```

When AI detects events like:

* Fall detected
* Abnormal heart rate

alerts will appear instantly on the dashboard.

---

# 8. Alert Actions

Users can:

* Confirm alert
* Mark false alarm
* Call emergency contact

---

# 9. Tailwind CSS

The frontend UI uses Tailwind CSS.

If styles fail to load, run:

```
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

---

# 10. Development Notes

Make sure:

* Backend runs before frontend
* Camera module is connected
* WebSocket server is active

---

# Future Improvements

* Auto emergency escalation
* Activity recognition (sleep, walking, inactivity)
* Mobile push notifications
* Multi-patient monitoring
* Mobile application

---

# Contributors

Smart Care System Development Team
