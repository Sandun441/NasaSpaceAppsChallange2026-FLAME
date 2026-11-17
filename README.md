# 🔥 NASA FLAME — Scientific Fire Research Platform

NASA FLAME is an AI-powered scientific research platform developed for the **NASA Space Apps Challenge 2026**. It helps researchers analyze NASA microgravity combustion experiments, visualize fire behavior, identify research gaps, and explore fire safety improvements.

## 🚀 Features

- Interactive scientific data visualization
- Gemini AI-powered research assistant with RAG
- Predictive modeling and CSV exports
- Research gap detection
- Fire safety research and Earth applications
- Interactive fire behavior simulation

## ⚙️ Installation

### 1. Clone the Repository

Clone this GitHub repository and open the project folder.

### 2. Backend Setup (FastAPI)

```powershell
cd data-pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure Gemini AI:

```powershell
$env:GEMINI_API_KEY = "AQ.Ab8RN6KsAgeUXBkZaW1n_KsTdZuP0WiS2ufsRvAi5igqLhgHBw"
$env:GEMINI_MODEL = "gemini-3.5-flash-lite"
```

Start the backend from the directory containing the FastAPI entry point:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**Note:** If `main.py` is located in a subdirectory, use its actual Python module path instead of `main:app`.

### 3. Frontend Setup (React)

Open a new terminal in the frontend project directory:

```powershell
npm install
npm run dev
```

Open the local URL displayed in the terminal.

## 🛠️ Technology Stack

React | Python | FastAPI | Google Gemini | RAG | NASA Scientific Datasets

## 🌍 Mission

Transforming complex microgravity combustion data into accessible scientific insights to support safer space exploration and fire safety research on Earth.

**NASA Space Apps Challenge 2026**
