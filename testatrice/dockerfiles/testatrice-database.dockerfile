FROM mariadb:latest

USER mysql
ENV MYSQL_ALLOW_EMPTY_PASSWORD=true

USER root
RUN echo "[mysqld]" >> /etc/mysql/conf.d/my.cnf
RUN echo "sql_mode = NO_AUTO_VALUE_ON_ZERO" >> /etc/mysql/conf.d/my.cnf

RUN ln -s /usr/bin/mariadb /usr/bin/mysql
