FROM python:3.8 AS base

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         package-to-install \
#     && rm -rf /var/lib/apt/lists/*

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

RUN pip install --upgrade --no-cache-dir pip==20.2.3
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8500


FROM base as dev

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8500"]


FROM base as prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "showroom.wsgi", "-c", "/django/gunicorn-conf.py"]
