FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /code/product_service

EXPOSE 8002

CMD ["uvicorn", "product_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
