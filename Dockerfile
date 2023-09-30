FROM cfssl/cfssl as base
ENV DEBIAN_FRONTEND noninteractive

COPY --from=hairyhenderson/gomplate:stable /gomplate /bin/gomplate


RUN apt-get update \
    && apt-get install -y \
      jq \
      tini \
    && go install bitbucket.org/liamstask/goose/cmd/goose@latest \
    && mkdir -p /opt/cfssl/persistent/certdb/sqlite/migrations \
    && true
CMD []
SHELL ["/bin/bash", "-lc"]


FROM base as production
COPY ./files/opt/cfssl /opt/cfssl
COPY ./files/docker-entrypoint.sh /docker-entrypoint.sh
COPY ./files/cfssl-start.sh /cfssl-start.sh
COPY ./files/container-env.sh /container-env.sh
WORKDIR /opt/cfssl
ENTRYPOINT ["/usr/bin/tini", "--", "/docker-entrypoint.sh"]


###########
# Hacking #
###########
FROM production as devel_shell
RUN apt-get update && apt-get install -y zsh jq \
    && sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
    && echo "source /root/.profile" >>/root/.zshrc \
    && true
ENTRYPOINT ["/bin/zsh", "-l"]
