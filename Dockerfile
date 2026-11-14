FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pg/ pg/
COPY seed/ seed/
COPY eval/ eval/
COPY static/ static/
COPY data/processed/ data/processed/
EXPOSE 8080
CMD ["sh", "-c", "uvicorn pg.main:app --host 0.0.0.0 --port ${PORT}"]
