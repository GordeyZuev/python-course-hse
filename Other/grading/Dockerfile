FROM python:3.12.8-slim
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
COPY container_check.py /checker.py
