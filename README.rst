cfssl Submodule
================

![Build Status](https://github.com/pvarki/docker-rasenmaeher-cfssl/actions/workflows/build.yml/badge.svg)

Used as git submodule
---------------------

This repo is used as submodule in https://github.com/pvarki/docker-rasenmaeher-integration
it is probably a good idea to handle all development via it because it has docker composition
for bringin up all the other services rasenmaeher-api depends on

Development
-----------

The cfssl itself we can't do much about but the FastAPI thing uses poetry and in
any case use pre-commit::

    poetry install
    pre-commit install --install-hooks
    pre-commit run --all-files


Docker
------

For more controlled deployments and to get rid of "works on my computer" -syndrome, we always
make sure our software works under docker.

It's also a quick way to get started with a standard development environment.

SSH agent forwarding
^^^^^^^^^^^^^^^^^^^^

We need buildkit_::

    export DOCKER_BUILDKIT=1

.. _buildkit: https://docs.docker.com/develop/develop-images/build_enhancements/

And also the exact way for forwarding agent to running instance is different on OSX::

    export DOCKER_SSHAGENT="-v /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock -e SSH_AUTH_SOCK=/run/host-services/ssh-auth.sock"

and Linux::

    export DOCKER_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build image, create container and start it::

    docker build --ssh default --target devel_shell -t ocsprest:devel_shell .
    docker create --name ocsprest_devel -v `pwd`/../":/app" -it `echo $DOCKER_SSHAGENT` ocsprest:devel_shell
    docker start -i ocsprest_devel

Or just pwd if working under separate checkout instead of the integration repo.

pre-commit considerations
^^^^^^^^^^^^^^^^^^^^^^^^^

If working in Docker instead of native env you need to run the pre-commit checks in docker too::

    docker exec -i ocsprest_devel /bin/bash -c "pre-commit install --install-hooks"
    docker exec -i ocsprest_devel /bin/bash -c "pre-commit run --all-files"

You need to have the container running, see above. Or alternatively use the docker run syntax but using
the running container is faster::

    docker run --rm -it -v `pwd`":/app" ocsprest:devel_shell -c "pre-commit run --all-files"

Production docker
^^^^^^^^^^^^^^^^^

There's a "production" target as well for running the application, remember to change that
architecture tag to arm64 if building on ARM::

    docker build --ssh default --target ocsprest -t ocsprest:amd64-latest .
    docker run -it --name ocsprest ocsprest:amd64-latest

There is also a specific target for just dumping the openapi.json::

    docker build --ssh default --target openapi -t ocsprest:amd64-openapi .
    docker run --rm -it --name rasenmaeher_openapijson ocsprest:amd64-openapi
