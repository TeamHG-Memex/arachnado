FROM ubuntu:12.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    git \
        curl \
        python \
        python-pip \
        python-dev \
    python-scipy \
    python-numpy \
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

# To use forum spiders with Arachnado, clone repos and uncomment lines

# git clone git@github.com:TeamHG-Memex/bot_engines.git
# ADD bot_engines /app/bot_engines
# RUN pip install -e /app/bot_engines

# git clone git@github.com:TeamHG-Memex/bot_spiders.git
# ADD bot_spiders /app/bot_spiders
# RUN pip install -e /app/bot_spiders


WORKDIR /app
ADD requirements.txt /app/requirements.txt
RUN pip install -U -r requirements.txt

ADD package.json /app/package.json
RUN npm install

ADD arachnado/static/js /app/arachnado/static/js
ADD webpack.config.js /app/webpack.config.js
RUN npm run build

ADD . /app

RUN pip install .[mongo]

EXPOSE 8888

CMD [ \
    "/usr/bin/python", \
    "-m",  "arachnado" \
]
