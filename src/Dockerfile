FROM python:3.8

ENV PYTHONUNBUFFERED 1

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         package-to-install \
#     && rm -rf /var/lib/apt/lists/*

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

RUN pip install --upgrade pip==20.2.3
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "showroom.wsgi", "-c", "/django/gunicorn-conf.py"]


EXPOSE 8000
