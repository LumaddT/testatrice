FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3

COPY ./mock_mailserver.py /mailserver/mock_mailserver.py

ENTRYPOINT python3 /mailserver/mock_mailserver.py
