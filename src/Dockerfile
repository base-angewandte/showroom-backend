FROM python:3.8 AS base

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PIP_QUIET 2
ENV PIP_USER 1
ENV PYTHONUSERBASE /djangoenv
ENV PATH="$PYTHONUSERBASE/bin:$PATH"

# RUN apt-get update && apt-get install -y --no-install-recommends \
#         package-to-install \
#     && rm -rf /var/lib/apt/lists/*

RUN mkdir /logs
VOLUME /logs

WORKDIR /django

RUN pip install pip==22.0.4
COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 8500


FROM base as dev

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8500"]


FROM base as prod

COPY . .

CMD ["rainbow-saddle", "--pid", "/var/run/django.pid", "--gunicorn-pidfile", "/var/run/gunicorn.pid", "gunicorn", "showroom.wsgi", "-c", "/django/gunicorn-conf.py"]
