FROM python:3.11

ENV PYTHONUNBUFFERED 1

RUN pip install -qq --upgrade --no-cache-dir pip==23.2.1

COPY requirements.txt /tmp/requirements.txt
RUN pip install -qq --disable-pip-version-check --no-cache-dir -r /tmp/requirements.txt

WORKDIR /docs
VOLUME /docs
