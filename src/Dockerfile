FROM python:3.11-slim-bookworm

ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1
ENV DIRECTORY="/code"
ENV PATH="${PATH}:$HOME/.local/bin"

RUN \
  DEPENDENCIES=' \
    curl \
    git \
    gpg \
    lsb-release \
    netcat-openbsd \
    vim \
  ' \
  && apt-get update -y \
  && apt-get install --no-install-recommends -y $DEPENDENCIES \
  && apt-get autoremove -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man /usr/share/locale \
  && mkdir -p $DIRECTORY \
  && echo "set mouse-=a" >> /root/.vimrc \
  && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg \
  && mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg \
  && sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/debian/$(lsb_release -rs | cut -d'.' -f 1)/prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list' \
  && apt-get update -y \
  && apt-get install -y \
    azure-functions-core-tools-4

COPY ./requirements.txt /tmp/requirements.txt

RUN \
  pip install --upgrade pip setuptools wheel && \
  pip install -r /tmp/requirements.txt

WORKDIR $DIRECTORY

COPY . $DIRECTORY
