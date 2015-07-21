FROM google/debian:wheezy
MAINTAINER Sharif Salah <sharif.salah+docker@gmail.com>

RUN apt-get update && \
    apt-get install -y python-pip && \
    pip install google-api-python-client

ADD app /app

CMD [ "python", "/app/sqladmin.py" ]