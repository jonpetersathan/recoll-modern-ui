FROM debian:trixie-slim

ARG APP_VERSION

LABEL org.opencontainers.image.title: "Recoll Modern UI" \
      org.opencontainers.image.version: "${APP_VERSION}" \
      org.opencontainers.image.authors: "Jonathan Peters <jonathan.peters@tenasi.de>"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp \
    RECOLL_CONFDIR=/root/.recoll

# Install system python, pip and waitress/bottle dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip git && \
    pip3 install bottle waitress --break-system-packages

# Install Recoll and python3-recoll C-bindings
RUN apt-get install -y --no-install-recommends gnupg recollcmd python3-recoll && \
    apt-get autoremove -y

# Install document extractors, utilities and filters
RUN apt-get install -y --no-install-recommends poppler-utils unrtf antiword unzip python3-mutagen untex file aspell && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup data, export and recoll configuration directories
RUN mkdir -p /data /root/.recoll /export && \
    chmod 755 /root && \
    chmod -R 777 /root/.recoll /data /export
COPY recoll.conf /root/.recoll/recoll.conf
RUN echo topdirs = /data >> /root/.recoll/recoll.conf && \
    chmod 666 /root/.recoll/recoll.conf

# Copy modern web UI application
ARG CACHEBUST=1
RUN echo "Context sync: ${CACHEBUST}"
COPY . /app
WORKDIR /app

RUN chmod -R a+rX /app && \
    chmod +x /app/entrypoint.sh /app/src/webui-standalone.py

VOLUME /data
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "src/webui-standalone.py", "-a", "0.0.0.0"]
