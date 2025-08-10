FROM mysql:latest

USER mysql
ENV MYSQL_ALLOW_EMPTY_PASSWORD=true
COPY testatrice.sql /docker-entrypoint-initdb.d/
