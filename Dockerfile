# Week 17: single-stage API image. Train on the host first — COPY of model.joblib
# fails if artifacts/ is empty (.gitignore). Not a multi-stage build yet.
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
# Dependency layer is cached until pyproject/src change.
RUN pip install --no-cache-dir . && useradd -m appuser
COPY artifacts/model.joblib /app/artifacts/model.joblib
# Non-root: copy the model before dropping privileges so the file is readable.
USER appuser
EXPOSE 8000
# 0.0.0.0 is required inside Docker so compose port mapping can reach uvicorn.
# Local README uses 127.0.0.1 so a laptop bind is not advertised on the LAN.
CMD ["uvicorn", "energy_ml.api:app", "--host", "0.0.0.0", "--port", "8000"]
