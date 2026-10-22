FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /srv

RUN useradd --create-home --uid 1000 anviora \
 && mkdir /models && chown anviora /models

COPY requirements.txt .
# PyTorch solo-CPU: evita descargar los ~2 GB de las librerías CUDA, que aquí no se usan
RUN pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt

COPY app ./app
USER anviora

EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
