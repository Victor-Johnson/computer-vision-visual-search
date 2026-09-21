FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 VISUAL_SEARCH_DATA=/app/data OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 app && mkdir -p /app/data && chown app:app /app/data
COPY --chown=app:app src ./src
COPY --chown=app:app .streamlit ./.streamlit
USER app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["streamlit", "run", "src/streamlit-app.py", "--server.address=0.0.0.0", "--server.port=8501"]
