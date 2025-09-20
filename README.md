# Testatrice

Start `servatrice` instances in Python.

| ⚠️ Warning                                                                                                         |
|--------------------------------------------------------------------------------------------------------------------|
| This configuration is intended exclusively for testing purposes. No security consideration was taken into account. |

## Requirements

Runtime: `pip install faker jinja2 podman`  
Dev: `pip install black isort`

## Description

This module can be used to create configured `servatrice` instances for testing purposes.

For each server instance, a user with server admin privileges is created in the database with username `Admin` and
password `password`.

## Mail server

The testatrice-mailserver container runs a rough (*it works*) Python script which pretends to be an SMTP server. It
receives emails on port 25 (not exposed) and it prints them to a file. No email is actually sent outside the
containerized environment.

The container listens to port 1110 (registration tokens) and 1111 (forgot password tokens), both exposed to localhost.
It is possible to open a socket to those ports and send a username. If and when a token is received by the server for
that username, the token is returned and the socket is closed.

## TODO

* Command line interface
* A version of `testatrice-server.dockerfile` which pulls servatrice source code from the repository or a local
  directory instead of the binary.
* Populate the database with mock data via crow.
