FROM ubuntu:12.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        curl \
        python \
        python-pip \
        python-dev \
        build-essential \
        pkg-config \
        libsqlite3-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        libssl-dev \
        python-joblib

RUN pip install -U pip
RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash -
RUN apt-get install -y --no-install-recommends nodejs

ADD . /app
WORKDIR /app
RUN pip install -U -r requirements.txt
RUN pip install .
RUN npm install
RUN npm run build

EXPOSE 8888

CMD [ \
    "/usr/bin/python", \
    "-m",  "arachnado" \
]
