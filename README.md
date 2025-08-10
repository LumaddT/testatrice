# Testatrice

A rough but quick way to start a servatrice instance with database connection.

NB: This configuration is intended excludively for testing purposes. No security consideration was taken into account.

## Running testatrice

```
git clone https://github.com/LumaddT/testatrice.git
cd testatrice

podman build --file testatrice-database.dockerfile -t testatrice-database
podman build --file testatrice-server.dockerfile -t testatrice-server

sed -i 's/"cniVersion": "1\.0\.0"/"cniVersion": "0\.4\.0"/' $(podman network create testatrice-network)

podman run --network=testatrice-network --detach --rm -h testatrice-database --name testatrice-database testatrice-database --sql-mode="NO_AUTO_VALUE_ON_ZERO"
podman run --network=testatrice-network --detach -v ./logs:/var/log/servatrice --rm -h testatrice-server --name testatrice-server -p 4747:4747 -p 4748:4748 testatrice-server
```

You should wait approximately 30 seconds between the two `podman run` commands to allow the database to start properly.

The server can be reached at `localhost:4747` and `localhost:4748`.  
Logs are stored in `./logs/server.log`.  
After the initial ocnfiguration the server can be started by running only the `podman run` commands.

To stop the containers run:
```
podman stop testatrice-server
podman stop testatrice-database
```

### I'm using Docker

This configuration was tested using Podman in an environment based on Debian.
Replacing `podman` with `docker` in the above commands should still work as intended. `docker network create servatrice-network` can replace the entirety of line 3, as the `sed` is necessary due to a presumed bug in Podman (or my own skill issue).
The database hostname in `testatrice.ini` should also be changed to be compatible with Docker's DNS resolution.

## TODO

* `testatrice.yaml` for Podman Compose.
* A version of `testatrice-database.dockerfile` which pulls servatrice source code from a local directory instead of the repository.
* Populate the database with mock data via crow.

## testatrice.ini

Most of `testatrice.ini` is in its default state.

### server
* The server expects connections on the default ports 4747 (TCP) and 4748 (WebSocket).
* The server logs as verbosely as possible to the file `/var/log/servatrice/server.log`.
* The rest of the section is in the default state.

### authentication
* The server allows, but does not require, registration and authentication.
* No global password is configured.

### users
* No minimum username length is configured. A maximum of 35 characters is set, as that is the limit from `testatrice.sql`.
* Lowecase and uppercase letters are allowed, as are digits and the special characters `_`, `.`, and `-`.
* The special characters are allowed to be the first character in a username.
* No work is forbidden from appearing in a username.
* The minimum password length is set to 1.

### registration
* An email address is not required for registration.

### forgotpassword
* The forgot password functionality is disabled.

### smtp
* The SMTP server is disabled.

### database
* The MySQL server is expected to be running at `testatrice-database.dns.podman`. This value should be edited if the containers are run through Docker instead.
* The database is expected to be named `servatrice`, the tables prefix to be `cockatrice`, the database user to be `servatrice` with password `password`.

#### rooms
* 4 rooms, one for each permission level (none, registered, moderator, administrator), are configured, all autojoined.

### game
* The inactivity timer in game is virtually unlimited, at 240 hours.
* Replays are stored.
* Players are allowed to create games as judges.

### security
* No maximum number of connected player is set.
* Users can be in as many games as they wish.
* 99999 chat messages, for a total of 999999 characters,  are allowed per second by the configuration.
* 99999 game commands are allowed per second by the configuration.

### logging
* Moderators are allowed to query logs.
* The server logs all chat messages.

### audit
* All enabled.

### servernetwork
* Disabled.
