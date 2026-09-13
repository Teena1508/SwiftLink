# ⚡ SwiftLink - Flask URL Shortener & Analytics Platform

SwiftLink is a production-grade, lightweight Flask web application that shortens URLs, redirects visitors, tracks analytics, and exposes a secure REST API with comprehensive edge-case handling, multi-user isolation, custom sliding-window rate limiting, and collision-free hash code generation.

---

## 🌟 Features

- **Hash-Based Short Code Generation**: Deterministic SHA-256 + Base62 encoding with attempt-counter fallback for collision resolution.
- **Custom Alias Support**: Validation against character sets (`[a-zA-Z0-9_-]`), length boundaries, and reserved application slugs.
- **Link Expiration & TTL**: Optional link lifetime support; expired URLs respond with `HTTP 410 Gone`.
- **API Key Protection**: `DELETE /<code>` endpoints and user metrics protected via API key authentication (`X-API-Key` or `Authorization: Bearer <key>`).
- **Custom Sliding Window Rate Limiting**: Built from scratch per IP without `flask-limiter`, enforcing configurable request limits and returning `HTTP 429 Too Many Requests` with `Retry-After` header.
- **Multi-User Data Isolation**: User authentication (register/login/logout), auto-generated API keys, and user-scoped URL dashboard.
- **Analytics & Leaderboard**: Public top-5 leaderboard (`GET /analytics/top` & UI page) and per-link detailed click tracking.
- **Full Test Suite**: 100% passing `pytest` test suite covering validation, redirection, rate limiting, expiry, and authorization.

---

## 🏗️ Design Decisions & Architecture

### 1. Hash-Based Collision Resolution Strategy
To fulfill the requirement of hash-based code generation without relying on external libraries (`shortuuid`, `pyshorteners`):
1. **SHA-256 Digest**: The target URL, a cryptographic salt, and an attempt counter are hashed using SHA-256.
2. **Base62 Character Encoding**: The first 8 bytes of the digest are converted into an integer and mapped to a Base62 alphabet (`0-9`, `a-z`, `A-Z`).
3. **Collision Detection & Retry**: Before persisting, the application checks if the generated code exists in SQLite. If a collision is detected, the `attempt` counter is incremented and re-hashed. If collisions persist beyond threshold limits, code length is dynamically extended.

### 2. URL Safety & Input Validation
URLs are parsed using `urllib.parse.urlparse`:
- **Forbidden Protocols**: Rejects `javascript:`, `data:`, `file:`, `vbscript:`, `ftp:`, etc. Only `http://` and `https://` are allowed.
- **Hostname Check**: Ensures non-empty netloc and prevents malformed characters or injection patterns.

### 3. Custom Rate Limiting (No `flask-limiter`)
Implemented via `app/utils/rate_limiter.py` using a thread-safe sliding window log:
- Tracks timestamped requests per client IP address within a 60-second window.
- When an IP exceeds the allowed threshold (default: 10 shorten requests/min), the server returns `HTTP 429 Too Many Requests` along with a `Retry-After` header indicating seconds remaining.

### 4. Link Expiration (TTL)
- URLs can be created with a `ttl_seconds` parameter.
- `GET /<code>` checks `expires_at` against UTC `datetime.now(timezone.utc)`.
- Expired links return `HTTP 410 Gone`.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+
- `pip`

### 1. Clone & Set Up Environment

```bash
# Navigate to directory
cd /Users/teenamunjal/Desktop/gdg

# Create virtual environment
python3 -m venv venv
source venv/bin/venv/activate  # Or ./venv/bin/activate on macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Application Server

```bash
PYTHONPATH=. python3 run.py
```

The application will start at `http://127.0.0.1:5001`.

### 3. Run Automated Tests

```bash
PYTHONPATH=. ./venv/bin/pytest -v
```

---

## 📖 API Documentation

### 1. Shorten a URL
- **Endpoint**: `POST /shorten`
- **Headers**: `Content-Type: application/json`
- **Body Options**:
  - `url` (string, required): The target URL.
  - `custom_alias` (string, optional): Desired custom short code (`[a-zA-Z0-9_-]`).
  - `ttl_seconds` (integer, optional): Time-to-live in seconds.

#### Request Example:
```bash
curl -X POST http://127.0.0.1:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://python.org",
    "custom_alias": "python-docs",
    "ttl_seconds": 3600
  }'
```

#### Response (`201 Created`):
```json
{
  "short_code": "python-docs",
  "short_url": "http://127.0.0.1:5000/python-docs",
  "original_url": "https://python.org",
  "is_custom_alias": true,
  "click_count": 0,
  "created_at": "2026-09-13T14:40:00+00:00",
  "expires_at": "2026-09-13T15:40:00+00:00",
  "is_expired": false,
  "is_deleted": false,
  "user_id": null
}
```

---

### 2. Redirect to Original URL
- **Endpoint**: `GET /<code>`
- **Description**: Redirects visitor to the original URL with `302 Found` and increments click count.
- **Error Responses**:
  - `404 Not Found`: If link is missing or deleted.
  - `410 Gone`: If link TTL has expired.

#### Request Example:
```bash
curl -i http://127.0.0.1:5000/python-docs
```

---

### 3. Get Link Statistics
- **Endpoint**: `GET /stats/<code>`

#### Request Example:
```bash
curl -X GET http://127.0.0.1:5000/stats/python-docs
```

#### Response (`200 OK`):
```json
{
  "short_code": "python-docs",
  "short_url": "http://127.0.0.1:5000/python-docs",
  "original_url": "https://python.org",
  "click_count": 1,
  "created_at": "2026-09-13T14:40:00+00:00",
  "expires_at": "2026-09-13T15:40:00+00:00",
  "is_expired": false,
  "is_deleted": false
}
```

---

### 4. Delete URL Mapping (Protected)
- **Endpoint**: `DELETE /<code>`
- **Headers**: Requires `X-API-Key: <your_api_key>` or `Authorization: Bearer <your_api_key>`

#### Request Example:
```bash
curl -X DELETE http://127.0.0.1:5000/python-docs \
  -H "X-API-Key: your_user_api_key_here"
```

#### Response (`200 OK`):
```json
{
  "message": "Short code 'python-docs' deleted successfully.",
  "short_code": "python-docs"
}
```

---

### 5. Top 5 Analytics Leaderboard
- **Endpoint**: `GET /analytics/top`

#### Request Example:
```bash
curl -X GET http://127.0.0.1:5000/analytics/top
```

#### Response (`200 OK`):
```json
{
  "count": 1,
  "top_links": [
    {
      "short_code": "python-docs",
      "short_url": "http://127.0.0.1:5000/python-docs",
      "original_url": "https://python.org",
      "click_count": 42
    }
  ]
}
```

---

### 6. User Auth & API Key Registration
- **Endpoint**: `POST /register`
- **Body**: `{ "username": "alice", "email": "alice@example.com", "password": "secretpassword" }`

#### Response (`201 Created`):
```json
{
  "message": "User registered successfully.",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "api_key": "e4f8b9...62a1"
  }
}
```

---

## 📁 Repository Structure

```
/Users/teenamunjal/Desktop/gdg/
├── app/
│   ├── __init__.py          # Application Factory
│   ├── models.py            # User, URLMapping, ClickLog models
│   ├── utils/
│   │   ├── generator.py     # Base62 SHA-256 hash generator & collision handling
│   │   ├── validator.py     # URL security & custom alias validation
│   │   ├── rate_limiter.py  # Manual sliding window rate limiter
│   │   └── auth.py          # API key & session auth decorators
│   ├── routes/
│   │   ├── api.py           # REST API endpoints
│   │   ├── redirect.py      # GET /<code> redirection & click tracking
│   │   ├── auth.py          # User register, login, logout, key regen
│   │   └── web.py           # Web UI views
│   ├── templates/           # Modern Glassmorphism HTML5 templates
│   └── static/              # CSS & JS frontend assets
├── tests/                   # Automated pytest suite (19 test cases)
├── config.py                # Configuration classes
├── run.py                   # Server startup script
├── requirements.txt         # Dependencies
└── README.md                # Technical Documentation
```
