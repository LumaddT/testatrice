# Testatrice

A rough but quick way to start a servatrice instance with database connection.

| ⚠️ Warning                                                                                                         |
|--------------------------------------------------------------------------------------------------------------------|
| This configuration is intended exclusively for testing purposes. No security consideration was taken into account. |

## Running testatrice

```
git clone https://github.com/LumaddT/testatrice.git
cd testatrice

chomd +x testatrice.sh

./testatrice.sh --help
```

### Options

```
None of the arguments is validated.

Server:
  -s, --server-identifier [string]          : used for container name, database prefix, log file name and email from ['testatrice']
  -t, --tcp, --socket [int]                 : TCP socket port exposed to host [4747]
  -w, --ws, --websocket [int]               : websocket port exposed to host [4748]
  -ci, --require-client-id                  : require client id on login
  -rf, --required-features [string]         : client required features, comma separated ['']
  -to, --idle-client-timeout [int]          : max time a player can stay connected but idle, in seconds. 0 = disabled [3600]
Registration and authentication:
  -am, --authentication-method [string]     : valid values: none|password|sql [sql]
  -p, --password [string]                   : the common password to be used if the 'password' authentication method is selected ['password']
  -er, --enable-registration
  -rr, --require-registration
  -re, --require-email                      : require an email address to register
  -ra, --require-activation                 : require email activation
  -ma, --max-accounts-per-email [int]       : [2]
  -ef, --enable-forgot-password
  -tl, --forgot-password-token-life [int]   : lifetime of the password reset token, in minutes [60]
  -efpc, --enable-forgot-password-challenge
Usernames and passwords:
  -pm, --password-min-length [int]          : minimum length allowed for the password [6]
  -um, --username-min-length [int]          : minimum length allowed for the username [6]
  -uM, --username-max-length [int]          : maximum length allowed for the username (more than 255 may create issues) [12]
  -udl, --username-disallow-lowercase       : do not allow lowercase letters in the username
  -udu, --username-disallow-uppercase       : do not allow uppercase letters in the username
  -udn, --username-disallow-numerics        : do not allow digits in the username
  -ap, --allowed-punctuation [string]       : a string of puncutation marks which can be accepted in the username [_.-]
  -app, --allow-punctuation-prefix          : allow a punctuation mark to be the first character in a username
  -dw, --disallowed-words [string]          : comma separated list of words not to be allowed in a username ['']
Misc:
  -r, --rooms-method [string]               : source for rooms information. Valid values: config|sql [config]
  -i, --max-game-inactivity-time [int]      : max time all players in a game can stay inactive before the game is closed, in seconds [120]
  -l, --log-path [string]                   : directory path for the log file in the local host ['./logs']
  --sleep [int]                             : how long to sleep after the database image is started, in seconds [30]
                                              The database requires some time to start completely and become usable.
```

For each server instance, a user with server admin privileges is created in the database with username `Admin` and
password `password`.

In newer versions of podman the containers can be stopped with the command

```
podman stop --filter name=testatrice
```

### I'm using Docker

This configuration was tested using Podman in an environment based on Debian.
Replacing `podman` with `docker` in the script should still work as intended. `docker network create servatrice-network`
can replace the entirety of line 119, as the `sed` is necessary due to a presumed bug in the Podman version I run.
The hostnames of the database and the mail server in `testatrice.ini.envsubst-template` should also be changed to be
compatible with Docker's DNS resolution.

## Mail server

The testatrice-mailserver container runs a rough (_it works_) Python script which pretends to be an SMTP server. It
receives emails on port 25 (not exposed) and it prints them to a file. No email is actually sent outside the
containerized environment.

The container listens to port 1110 (registration tokens) and 1111 (forgot password tokens), both exposed to localhost.
It is possible to open a socket to those ports and send a username. If and when a token is received by the server for
that username, the token is returned and the socket is closed.

## TODO

* `testatrice.yaml` for Podman Compose.
* A version of `testatrice-database.dockerfile` which pulls servatrice source code from a local directory instead of the
  repository.
* Populate the database with mock data via crow.
