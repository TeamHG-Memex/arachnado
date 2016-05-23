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

# install nodejs
RUN curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -
RUN apt-get install -y nodejs

# install arachnado
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
RUN npm install
RUN npm run build
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
