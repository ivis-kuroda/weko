FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        ca-certificates \
        curl \
        fonts-liberation \
        libasound2t64 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libexpat1 \
        libgbm1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libpango-1.0-0 \
        libx11-6 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        nodejs \
        npm \
        wget \
        xauth \
        xvfb \
        xdg-utils \
    && npm install -g agent-browser \
    && agent-browser install \
    && mkdir -p /root/.agent-browser \
    && printf '%s\n' '{"ignoreHttpsErrors":true,"headed":true,"args":"--no-sandbox,--disable-dev-shm-usage"}' > /root/.agent-browser/config.json \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

ENV DISPLAY=:99

# RUN curl -fsSL https://browser-use.com/cli/install.sh | bash

COPY entrypoint.sh /usr/local/bin/agent-browser-entrypoint
RUN chmod +x /usr/local/bin/agent-browser-entrypoint

ENTRYPOINT ["agent-browser-entrypoint"]
CMD ["sleep", "infinity"]
