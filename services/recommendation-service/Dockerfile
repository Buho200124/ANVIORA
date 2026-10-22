FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Usuario sin privilegios: el contenedor no corre como root
RUN useradd --create-home --uid 1000 anviora

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
USER anviora

EXPOSE 8003
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
