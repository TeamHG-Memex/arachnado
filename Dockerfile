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
        libssl-dev

RUN pip install -U pip
RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash -
RUN apt-get install -y --no-install-recommends nodejs

ADD . /app
RUN pip install -U -r app/requirements.txt
RUN pip install /app
RUN cd /app; npm install
RUN cd /app; npm build

EXPOSE 8888

ENTRYPOINT [ \
    "/usr/bin/python", \
    "-m",  "arachnado" \
]
