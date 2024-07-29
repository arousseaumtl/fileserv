FROM debian:latest

ENV PATH="/home/app/pythonenv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

RUN DEBIAN_FRONTEND=noninteractive \
    apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
    && groupadd app; useradd -m -g app -s $(which nologin) app

WORKDIR /home/app

USER app

COPY --chown=app:app src/* ./src/

RUN python3 -m venv /home/app/pythonenv \
    && pip3 install -r src/requirements.txt

ENTRYPOINT ["python3", "src/main.py"]