FROM cfssl/cfssl


COPY ./files/opt/cfssl /opt/cfssl
COPY ./files/docker-entrypoint.sh /docker-entrypoint.sh


ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y \
    jq
RUN mkdir -p /opt/cfssl/persistent


# SETUP GOOSE ( SQLITE DB MIGRATION APP )
# GOOSE / CERTDB base configuration files will be under /opt/cfssl/template/goose/
WORKDIR /opt/cfssl
RUN go install bitbucket.org/liamstask/goose/cmd/goose@latest
RUN mkdir -p /opt/cfssl/persistent/certdb/sqlite/migrations

#
# THESE SHOULD BE STATIC FILES THAT ARE STORED UNDER template/goose
# cd "/opt/cfssl/persistent/certdb/sqlite" ;  wget 'https://raw.githubusercontent.com/cloudflare/cfssl/master/certdb/sqlite/dbconf.yml'
# cd "/opt/cfssl/persistent/certdb/sqlite/migrations" ; wget https://raw.githubusercontent.com/cloudflare/cfssl/master/certdb/sqlite/migrations/001_CreateCertificates.sql
# cd "/opt/cfssl/persistent/certdb/sqlite/migrations" ; wget https://raw.githubusercontent.com/cloudflare/cfssl/master/certdb/sqlite/migrations/002_AddMetadataToCertificates.sql


 

ENTRYPOINT ["/bin/bash"]
CMD ["/docker-entrypoint.sh"]