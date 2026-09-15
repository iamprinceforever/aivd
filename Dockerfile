FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml requirements.txt README.md ./
COPY aivd ./aivd
COPY docs ./docs
COPY tests ./tests
RUN pip install --no-cache-dir -e ".[dev]"
EXPOSE 8000
CMD ["uvicorn", "aivd.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
