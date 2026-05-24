# Trip Planner App

## Requirements

Before running the application make sure you have installed:

- Python 3.11+
- `uv`
- Node.js
- npm

---

# Environment Configuration

Both frontend and backend require `.env` files.

## Backend `.env`

Inside the `backend` directory:

1. Copy:

```bash
.env.example
```

to:

```bash
.env
```

2. Fill in your own values.

Example:

```env
GOOGLE_MAPS_API_KEY=your_api_key
API_BASE_URL=http://localhost:8000
```

---

## Frontend `.env`

Inside the `frontend` directory:

1. Copy:

```bash
.env.example
```

to:

```bash
.env
```

2. Fill in your own values.

Example:

```env
VITE_GOOGLE_MAPS_API_KEY=your_api_key
VITE_API_BASE_URL=http://localhost:8000
```

---

# Running Backend

Go to the backend directory:

```bash
cd backend
```

Install dependencies:

```bash
uv sync
```

Run backend server:

```bash
uv run uvicorn main:app --reload
```

Backend will be available at:

```text
http://localhost:8000
```

---

# Running Frontend

Go to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Frontend will usually be available at:

```text
http://localhost:5173
```

---

# Running Tests

Go to the backend directory:

```bash
cd backend
```

Run tests:

```bash
uv run python -m tests.test_greedy_vs_bruteforce
```

The tests compare:

- Greedy algorithm
- Bruteforce algorithm

and report:

- request execution time
- total trip duration
- visited places count
- average duration per place
- total difference score
- speedup ratio