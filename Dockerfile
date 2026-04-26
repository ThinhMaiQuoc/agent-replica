FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY main.py .
COPY PLAN.md .
COPY README.md .

RUN mkdir -p docs state screenshots

CMD ["python", "main.py"]
