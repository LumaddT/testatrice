FROM ubuntu:24.04 as base

ARG DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /var/log/servatrice
RUN mkdir -p /home/servatrice/config
COPY ./resources/server_entry_point.sh /home/servatrice/server_entry_point.sh
RUN chmod 555 /home/servatrice/server_entry_point.sh

RUN apt-get update
RUN apt-get install -y curl wget libqt6sql6-mysql

RUN release_url=$(curl -s https://api.github.com/repos/Cockatrice/Cockatrice/releases/latest | grep -o https.*Ubuntu24.04.deb) && \
    wget -q -O /home/servatrice/cockatrice.deb ${release_url}
RUN apt-get install -y /home/servatrice/cockatrice.deb

ENTRYPOINT /home/servatrice/server_entry_point.sh
