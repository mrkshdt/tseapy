FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TSEAPY_DEBUG=0

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY . /app

RUN python -m pip install --upgrade pip \
    && python -m pip install .

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import json,urllib.request; resp=urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=4); payload=json.load(resp); raise SystemExit(0 if resp.status == 200 and payload.get('status') == 'ok' else 1)"

CMD ["tseapy", "--host", "0.0.0.0", "--port", "5000", "--no-debug"]
