#!/bin/zsh
colima start

docker build . --tag com-pl-core:latest --label com-pl-core

docker image prune --force --filter='label=com-pl-core'

# kill prev process if any exists
docker ps -a | grep -v CONTAINER | grep com-pl | awk '{ print $1; }' | xargs docker rm -f

docker run \
        --name com-pl \
        --network bridge \
        -e USER=apicore \
        -p 9000:9000 \
        -dt \
        com-pl-core:latest

docker logs -f com-pl
# to get inside container you can use line below
# docker exec -it com-pl bash -c "/bin/bash"
