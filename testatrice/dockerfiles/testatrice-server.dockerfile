FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# RUN apt-get update && apt-get install -y\
#   build-essential \
#   cmake \
#   file \
#   g++ \
#   git \
#   libmariadb-dev-compat \
#   libprotobuf-dev \
#   libqt6sql6-mysql \
#   qt6-websockets-dev \
#   protobuf-compiler \
#   qt6-tools-dev \
#   qt6-tools-dev-tools

# RUN git clone --depth 1 https://github.com/Cockatrice/Cockatrice.git
#
# WORKDIR ./Cockatrice/build
#
# RUN cmake .. -DWITH_SERVER=1 -DWITH_CLIENT=0 -DWITH_ORACLE=0 -DWITH_DBCONVERTER=0
# RUN cmake --build . --parallel3
# RUN make install

RUN mkdir -p /var/log/servatrice
RUN mkdir -p /home/servatrice/config
COPY ./resources/server_entry_point.sh /home/servatrice/server_entry_point.sh
RUN chmod 555 /home/servatrice/server_entry_point.sh

RUN apt-get update
RUN apt-get install -y curl wget libqt6sql6-mysql
RUN release_url=$(curl -s https://api.github.com/repos/Cockatrice/Cockatrice/releases/latest | grep -o https.*Ubuntu24.04.deb) && \
    wget -q -O cockatrice.deb ${release_url}
RUN apt-get install -y ./cockatrice.deb

ENTRYPOINT /home/servatrice/server_entry_point.sh
