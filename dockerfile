FROM cfssl/cfssl


COPY ./files/opt/cfssl /opt/cfssl
COPY ./files/docker-entrypoint.sh /docker-entrypoint.sh



ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y \
    jq
RUN mkdir -p /opt/cfssl/persistent


ENTRYPOINT ["/bin/bash"]
CMD ["/docker-entrypoint.sh"]