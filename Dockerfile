FROM ubuntu:14.04
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update; apt-get install -y --no-install-recommends \
    git \
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
    python-lxml
RUN pip install -U pip setuptools

# To use forum spiders with Arachnado, clone repos and uncomment lines

# git clone git@github.com:TeamHG-Memex/bot_engines.git
# ADD bot_engines /app/bot_engines
# RUN pip install -e /app/bot_engines

# git clone git@github.com:TeamHG-Memex/bot_spiders.git
# ADD bot_spiders /app/bot_spiders
# RUN pip install -e /app/bot_spiders

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# rebuild static files
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
RUN apt-get install -y nodejs
COPY package.json /app/package.json
RUN npm install

COPY arachnado/static/js /app/arachnado/static/js
COPY webpack.config.js /app/webpack.config.js
RUN npm run build

# install arachnado
COPY . /app
RUN pip install .

# use e.g. -v /path/to/my/arachnado/config.conf:/etc/arachnado.conf
# docker run option to override arachnado parameters
VOLUME /etc/arachnado.conf

# this folder is added to PYTHONPATH, so modules from there are available
# for spider_packages Arachnado option
VOLUME /python-packages
ENV PYTHONPATH $PYTHONPATH:/python-packages

EXPOSE 8888
ENTRYPOINT ["arachnado"]
