# Recruitment Suite — MockIT & Speed-Dating Bot

An AI-powered recruiting toolkit that automates two key workflows:

- **MockIT** — uploads a candidate's CV and generates a structured technical interview plan (questions, expected answers, red flags)
- **Speed-Dating Bot** — generates a personalized recruiter outreach message and internal HR notes based on the same CV

Built with **FastAPI** (backend) + **Streamlit** (frontend), powered by **OpenRouter AI**.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- An [OpenRouter](https://openrouter.ai/) API key

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/MykhailoTymoshenko08/MockIT-MVP.git
cd your-repo
```

### 2. Set your API key

Open `docker-compose.yml` and replace the placeholder value:

```yaml
environment:
  - OPENROUTER_API_KEY=your_key_here
```

> ⚠️ Never commit a real API key to version control. Consider using a `.env` file instead (see [tip below](#using-a-env-file)).

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

This starts two services:

| Service  | URL                    |
|----------|------------------------|
| Frontend | http://localhost:8501  |
| Backend  | http://localhost:8000  |

Open **http://localhost:8501** in your browser to use the app.

---

## Usage

1. Pick a tab — **MockIT** or **Speed-Dating Bot**
2. Enter the candidate's target role (e.g. `Senior Backend Engineer`)
3. Upload a PDF resume
4. Click **Generate** and wait a few seconds for the AI response

---

## Project Structure

```
.
├── backend/
│   ├── main.py            # FastAPI app — /analyze/ and /screening/ endpoints
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py             # Streamlit UI
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml
```

---

## Running Without Docker (local dev)

**Backend:**

```bash
cd backend
pip install -r requirements.txt
OPENROUTER_API_KEY=your_key uvicorn main:app --reload --port 8000
```

**Frontend** (in a separate terminal):

```bash
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

---

## API Endpoints

| Method | Path         | Description                                      |
|--------|--------------|--------------------------------------------------|
| POST   | `/analyze/`  | Accepts `role` + PDF → returns 5 interview Q&As  |
| POST   | `/screening/`| Accepts `role` + PDF → returns outreach message  |

Both endpoints accept `multipart/form-data` with fields `role` (string) and `file` (PDF).

---

## Using a `.env` File

Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_key_here
```

Then update `docker-compose.yml` to reference it:

```yaml
env_file:
  - .env
```

Add `.env` to `.gitignore` to keep your key safe.

---

## Notes

- The AI model used is `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter — free tier, so responses may be slow under load
- Only the first **1500 characters** of the CV text are sent to the model to reduce latency
- The backend retries failed AI calls up to **3 times** with exponential backoff