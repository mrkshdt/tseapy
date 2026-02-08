# External Integrations

**Analysis Date:** 2026-02-08

## APIs & External Services

**Not Detected**
- No third-party API integrations found
- No external service SDKs imported (Stripe, Supabase, AWS, etc.)
- No webhook endpoints or external event handling

## Data Storage

**Databases:**
- Not used - Application is in-memory only
- Loads sample data from local CSV: `data/AirQualityUCI.csv`
- No database ORM or query libraries detected

**File Storage:**
- Local filesystem only
- CSV loading in `tseapy/data/examples.py` uses relative path `data/AirQualityUCI.csv`
- Static assets served from `static/` directory
- No S3, cloud storage, or external file systems

**Caching:**
- Flask-Caching SimpleCache (in-memory only)
- Configuration in `app.py` line 28-34
- Cache key: `'data'` stores pandas DataFrame
- 3600 second default timeout
- No external cache services (Redis, Memcached)

## Authentication & Identity

**Auth Provider:**
- Custom/None - No external auth providers detected
- Flask session management only
- Session secret key: Generated dynamically via `secrets.token_hex()`
- Implementation: Line 32 in `app.py` - `app.secret_key = secrets.token_hex()`
- No OAuth, JWT, or third-party auth libraries

## Monitoring & Observability

**Error Tracking:**
- Not detected - No Sentry, Rollbar, or similar service

**Logs:**
- Console output only
- Flask debug logging (enabled in development mode)
- No structured logging framework

## CI/CD & Deployment

**Hosting:**
- Local development only (per README)
- Flask development server: `app.run(debug=True)` at line 226 in `app.py`
- No cloud hosting configuration detected (no Docker, Heroku configs, etc.)
- Runs on `http://localhost:5000`

**CI Pipeline:**
- Not detected - No GitHub Actions, Jenkins, or CI configs

## Environment Configuration

**Required env vars:**
- None explicitly required
- Application loads hardcoded sample data (Air Quality UCI dataset)

**Secrets location:**
- Secrets are NOT stored in environment variables
- Flask secret key generated at runtime dynamically
- No `.env` files or secret management system in use

## Data Sources

**Input Data:**
- Hardcoded local CSV: `data/AirQualityUCI.csv`
- Loaded via pandas `read_csv()` in `tseapy/data/examples.py` (line 9)
- No dynamic data loading or API endpoints for data ingestion

**Data Pipeline:**
```
CSV File (data/AirQualityUCI.csv)
  ↓
pandas.read_csv() with delimiter ";" and date parsing
  ↓
In-memory DataFrame stored in Flask cache with key 'data'
  ↓
Tasks perform analysis on cached DataFrame
  ↓
Plotly visualizations rendered to JSON and sent to client
```

## Webhooks & Callbacks

**Incoming:**
- Not used

**Outgoing:**
- Callback URL generation in `tseapy/core/analysis_backends.py` (line 22-24)
- Used for internal task/algorithm routing, not external webhooks
- Pattern: `create_callback_url(task: str, algo: str, *args)` → internal HTTP routes

## Client-Side Integrations

**JavaScript Libraries:**
- Plotly.js (via `plotly==5.6.0`)
- Bokeh.js (referenced in `tseapy/view/visualizer.py` but incomplete/unused)

## Bottlenecks & Limitations

**Scalability:**
- In-memory caching limits concurrent users
- Single CSV file data source (hardcoded)
- No multi-user data isolation
- No persistent storage between sessions

**Data Limitations:**
- Fixed Air Quality UCI dataset (1000 rows by default in `app.py` line 91)
- No user-provided file upload capability
- No database for historical analysis results

---

*Integration audit: 2026-02-08*
