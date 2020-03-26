FROM python:3.7

ENV PYTHONUNBUFFERED 1

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         package-to-install \
#     && rm -rf /var/lib/apt/lists/*

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

RUN pip install --upgrade pip==19.1.1
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . .

CMD rainbow-saddle --pid /var/run/django.pid --gunicorn-pidfile /var/run/gunicorn.pid gunicorn showroom.wsgi -w 3 -b :8000 -t 300 --max-requests 1000 --log-level=info --access-logfile=/logs/gunicorn.access.log --error-logfile=/logs/gunicorn.error.log

EXPOSE 8000
