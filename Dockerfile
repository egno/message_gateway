FROM python:3.7-alpine

COPY . /app

RUN apk update && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add postgresql-dev
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

VOLUME ["/app"]

EXPOSE 5000

CMD ["gunicorn", "--reload", "-b", "0.0.0.0:5000", "app:app"]