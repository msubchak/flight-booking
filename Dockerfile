FROM python:3.11-slim
LABEL maintainer="subchak.maksym@gmail.com"

ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles
RUN adduser --disabled-password --no-create-home my_user
RUN chown -R my_user:my_user /app/staticfiles

USER my_user
