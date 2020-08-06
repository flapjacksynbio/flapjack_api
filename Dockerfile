FROM python:3.7
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && apt-get -y install postgresql-client

RUN mkdir -p /var/app/flap
WORKDIR /var/app/flap

# Allows docker to cache installed dependencies between builds
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Adds application code to the image
COPY . .

EXPOSE $PORT