import errno
import json
import os
import socket
import time
from datetime import datetime
from enum import Enum
from typing import Iterator

import jinja2
import podman
from faker import Faker


## TODO: interface to get registration and password reset tokens
class TestServer:
    """
    The interface to run a testatrice instances in podman containers.

    If a server identifier, TCP port or WebSocket port are not provided or are passed as None,
    they will be chosen randomly.

    Attributes:
        server_identifier (str): The identifier for the server, used in the
          container name, as part of the servatrice instance name, and as the
          database tables prefix.
        container_name (str): The name of the podman container.
        tcp_port (int): The exposed TCP socket port the server listens to.
        ws_url (str): The full websocket URL to connect to the server, in the
          form ``ws://localhost:[port]``.
        log_path (str): The path on the local machine in which servatrice logs
          are stored.

    Raises:
        ValueError: If either of ``tcp_port`` or ``websocket_port`` is already
          in use.
    """

    _DOCKERFILES_CONTEXT: str = f"{os.path.dirname(__file__)}/dockerfiles/"
    _DATABASE_DOCKERFILE: str = "testatrice-database.dockerfile"
    _MAILSERVER_DOCKERFILE: str = "testatrice-mailserver.dockerfile"
    _SERVER_DOCKERFILE: str = "testatrice-server.dockerfile"

    _DATABASE_NAME: str = "testatrice-database"
    _MAILSERVER_NAME: str = "testatrice-mailserver"
    _BASE_SERVER_NAME: str = "testatrice-server"
    _NETWORK_NAME: str = "testatrice-network"

    class AuthenticationMethod(Enum):
        NONE = "none"
        PASSWORD = "password"
        SQL = "sql"

    class RoomMethod(Enum):
        CONFIG = "config"
        SQL = "sql"

    def __init__(
        self,
        *,
        server_identifier: str = None,
        tcp_port: int = None,
        websocket_port: int = None,
        require_client_id: bool = False,
        required_features: str = "",
        idle_client_timeout: int = 3600,
        authentication_method: AuthenticationMethod = AuthenticationMethod.SQL,
        common_password: str = "password",
        enable_registration: bool = False,
        require_registration: bool = False,
        require_email: bool = False,
        require_email_activation: bool = False,
        max_accounts_per_email: int = 2,
        enable_forgot_password: bool = True,
        forgot_password_token_life: int = 60,
        enable_forgot_password_challenge: bool = False,
        password_min_length: int = 6,
        username_min_length: int = 6,
        username_max_length: int = 12,
        allow_lowercase: bool = True,
        allow_uppercase: bool = True,
        allow_numerics: bool = True,
        allowed_punctuation: str = "_.-",
        allow_punctuation_prefix: bool = False,
        rooms_method: RoomMethod = RoomMethod.CONFIG,
        max_game_inactivity_time: int = 120,
        log_path: str = None,
    ):
        if server_identifier is None:
            self.server_identifier: str = TestServer.__create_identifier()
        else:
            self.server_identifier = server_identifier

        self.container_name = (
            TestServer._BASE_SERVER_NAME + "-" + self.server_identifier
        )

        if tcp_port is None:
            tcp_port = TestServer.__get_available_port()
        elif TestServer.__is_port_used(tcp_port):
            raise ValueError(f"Port {websocket_port} is already in use.")
        self.tcp_port = tcp_port

        if websocket_port is None:
            websocket_port = TestServer.__get_available_port()
        elif TestServer.__is_port_used(websocket_port):
            raise ValueError(f"Port {websocket_port} is already in use.")
        self._websocket_port = websocket_port

        self.log_path = log_path
        self.ws_url = f"ws://localhost:{self._websocket_port}"

        self._template_variables = {
            "server_identifier": self.server_identifier,
            "require_client_id": require_client_id,
            "required_features": required_features,
            "idle_client_timeout": idle_client_timeout,
            "authentication_method": authentication_method.value,
            "common_password": common_password,
            "enable_registration": enable_registration,
            "require_registration": require_registration,
            "require_email": require_email,
            "require_email_activation": require_email_activation,
            "max_accounts_per_email": max_accounts_per_email,
            "enable_forgot_password": enable_forgot_password,
            "forgot_password_token_life": forgot_password_token_life,
            "enable_forgot_password_challenge": enable_forgot_password_challenge,
            "password_min_length": password_min_length,
            "username_min_length": username_min_length,
            "username_max_length": username_max_length,
            "allow_lowercase": allow_lowercase,
            "allow_uppercase": allow_uppercase,
            "allow_numerics": allow_numerics,
            "allowed_punctuation": allowed_punctuation,
            "allow_punctuation_prefix": allow_punctuation_prefix,
            "rooms_method": rooms_method.value,
            "max_game_inactivity_time": max_game_inactivity_time,
        }

        for key in self._template_variables:
            if type(self._template_variables[key]) is bool:
                self._template_variables[key] = str(
                    self._template_variables[key]
                ).lower()

    def start(self):
        """
        Starts this testatrice-server instance and, if they are not already
          running, testatrice-database and testatrice-mailserver.

        Raises:
            ConnectionError: If the podman service is not available. Run
              ``podman system service -t 0 &`` to solve.
            RuntimeError: If a container using this same identifier already
              exists.
        """

        with podman.PodmanClient() as podman_client:
            if not podman_client.ping():
                message = "The podman service did not respond."
                TestServer.Logger.log(message)
                raise ConnectionError(message)

            if podman_client.containers.exists(self.container_name):
                message = f"A test server with identifier {self.server_identifier} already exists."
                TestServer.Logger.log(message)
                raise RuntimeError(message)

            TestServer.build_environment(podman_client)

            jinja_environment = jinja2.Environment(
                loader=jinja2.PackageLoader("testatrice"),
                autoescape=jinja2.select_autoescape(),
            )

            ini_template = jinja_environment.get_template("testatrice.ini.j2")
            sql_template = jinja_environment.get_template("testatrice.sql.j2")

            rendered_ini = ini_template.render(self._template_variables)
            rendered_sql = sql_template.render(self._template_variables)

            self.__configure_database(podman_client, rendered_sql)
            self.__start_server(podman_client, rendered_ini)

    @staticmethod
    def build_environment(
        podman_client: podman.PodmanClient, recreate: bool = False
    ):
        """
        Create the ``testatrice-network`` network if not already present,
        build the necessary images if not already present,
        and start the necessary containers if not already started.
        Images built:

        - ``testatrice-database``
        - ``testatrice-mailserver``
        - ``testatrice-server``

        Containers started:

        - ``testatrice-database``
        - ``testatrice-mailserver``

        ``testatrice-mailserver`` listens to port ``1110`` and ``1111`` to
        return the email authentication tokens and the password reset tokens
        respectively.

        Arguments:
            podman_client (podman.PodmanClient): An active podman.PodmanClient
              instance.
            recreate (bool): Set to True if the images should be recreated
              from scratch even if they already exist. The currently existing
              images will be removed.
        """

        TestServer.__create_network(podman_client)
        TestServer.__start_database(podman_client, recreate=recreate)
        TestServer.__start_mailserver(podman_client, recreate=recreate)
        TestServer.__build_base_server(podman_client, recreate=recreate)

    @staticmethod
    def __create_network(podman_client: podman.PodmanClient):
        if not podman_client.networks.exists(TestServer._NETWORK_NAME):
            TestServer.Logger.log("Creating testatrice network...")
            podman_client.networks.create(
                name=TestServer._NETWORK_NAME, dns_enabled=True
            )
        else:
            TestServer.Logger.log(
                "Testatrice network already exists. Skipping creation step."
            )

    @staticmethod
    def __start_database(
        podman_client: podman.PodmanClient, recreate: bool = False
    ):
        if recreate and podman_client.images.exists(TestServer._DATABASE_NAME):
            TestServer.Logger.log(
                f"Removing {TestServer._DATABASE_NAME} image..."
            )
            podman_client.images.remove(TestServer._DATABASE_NAME)

        if not podman_client.images.exists(TestServer._DATABASE_NAME):
            TestServer.Logger.log(
                f"Creating {TestServer._DATABASE_NAME} image..."
            )
            result = podman_client.images.build(
                path=TestServer._DOCKERFILES_CONTEXT,
                dockerfile=TestServer._DATABASE_DOCKERFILE,
                tag=TestServer._DATABASE_NAME,
                nocache=recreate,
            )

            TestServer.Logger.log(result[1])
        else:
            TestServer.Logger.log(
                f"Image {TestServer._DATABASE_NAME} already exists. Skipping build step."
            )

        if not podman_client.containers.exists(TestServer._DATABASE_NAME):
            TestServer.Logger.log(
                f"Creating {TestServer._DATABASE_NAME} container..."
            )
            podman_client.containers.create(
                image=TestServer._DATABASE_NAME,
                auto_remove=True,
                detach=True,
                hostname=TestServer._DATABASE_NAME,
                name=TestServer._DATABASE_NAME,
                network=TestServer._NETWORK_NAME,
                network_mode="bridge",
            )
        else:
            TestServer.Logger.log(
                f"Container {TestServer._DATABASE_NAME} already exists. Skipping creation step."
            )

        database_container = podman_client.containers.get(
            TestServer._DATABASE_NAME
        )

        if database_container.status != "running":
            TestServer.Logger.log(
                f"Running {TestServer._DATABASE_NAME} container..."
            )
            database_container.start()
            TestServer.__wait_until_database_is_up(podman_client)
        else:
            TestServer.Logger.log(
                f"Container {TestServer._DATABASE_NAME} is already running. Skipping run step."
            )

    @staticmethod
    def __start_mailserver(
        podman_client: podman.PodmanClient, recreate: bool = False
    ):
        if recreate and podman_client.images.exists(
            TestServer._MAILSERVER_NAME
        ):
            TestServer.Logger.log(
                f"Removing {TestServer._MAILSERVER_NAME} image..."
            )
            podman_client.images.remove(TestServer._MAILSERVER_NAME)

        if not podman_client.images.exists(TestServer._MAILSERVER_NAME):
            TestServer.Logger.log(
                f"Creating {TestServer._MAILSERVER_NAME} image..."
            )

            result = podman_client.images.build(
                path=TestServer._DOCKERFILES_CONTEXT,
                dockerfile=TestServer._MAILSERVER_DOCKERFILE,
                tag=TestServer._MAILSERVER_NAME,
                nocache=recreate,
            )

            TestServer.Logger.log(result[1])
        else:
            TestServer.Logger.log(
                f"Image {TestServer._MAILSERVER_NAME} already exists. Skipping build step."
            )

        if not podman_client.containers.exists(TestServer._MAILSERVER_NAME):
            TestServer.Logger.log(
                f"Creating {TestServer._MAILSERVER_NAME} container..."
            )
            podman_client.containers.create(
                image=TestServer._MAILSERVER_NAME,
                auto_remove=True,
                detach=True,
                hostname=TestServer._MAILSERVER_NAME,
                name=TestServer._MAILSERVER_NAME,
                network=TestServer._NETWORK_NAME,
                network_mode="bridge",
                ports={"1110/tcp": 1110, "1111/tcp": 1111},
            )
        else:
            TestServer.Logger.log(
                f"Container {TestServer._MAILSERVER_NAME} already exists. Skipping creation step."
            )

        mailserver_container = podman_client.containers.get(
            TestServer._MAILSERVER_NAME
        )
        if mailserver_container.status != "running":
            TestServer.Logger.log(
                f"Running {TestServer._MAILSERVER_NAME} container..."
            )
            mailserver_container.start()
        else:
            TestServer.Logger.log(
                f"Container {TestServer._MAILSERVER_NAME} is already running. Skipping run step."
            )

    @staticmethod
    def __build_base_server(
        podman_client: podman.PodmanClient, recreate: bool = False
    ):
        if recreate and podman_client.images.exists(
            TestServer._BASE_SERVER_NAME
        ):
            TestServer.Logger.log(
                f"Removing {TestServer._BASE_SERVER_NAME} image..."
            )
            podman_client.images.remove(TestServer._BASE_SERVER_NAME)

        if not podman_client.images.exists(TestServer._BASE_SERVER_NAME):
            TestServer.Logger.log(
                f"Creating {TestServer._BASE_SERVER_NAME} image..."
            )
            result = podman_client.images.build(
                path=TestServer._DOCKERFILES_CONTEXT,
                dockerfile=TestServer._SERVER_DOCKERFILE,
                tag=TestServer._BASE_SERVER_NAME,
                nocache=recreate,
            )

            TestServer.Logger.log(result[1])
        else:
            TestServer.Logger.log(
                f"Image {TestServer._BASE_SERVER_NAME} already exists. Skipping build step."
            )

    @staticmethod
    def __wait_until_database_is_up(podman_client: podman.PodmanClient):
        database_container = podman_client.containers.get(
            TestServer._DATABASE_NAME
        )

        TestServer.Logger.log("Waiting for the temporary database to sart...")
        exit_code, _ = database_container.exec_run("mysql")
        while exit_code != 0:
            time.sleep(0.2)
            exit_code, _ = database_container.exec_run("mysql")

        # TODO: I hoped to be able to do everything in a non-hacky way.
        # The database starts, then it restarts. It's not fully operational
        # as soon as the socket is available. Maybe there is a better way to
        # go about this, but for now this will do.

        TestServer.Logger.log("Waiting for the temporary database to stop...")
        max_attempts = 300
        attempt = 0
        exit_code, _ = database_container.exec_run("mysql")
        while exit_code == 0 and attempt < max_attempts:
            attempt += 1
            time.sleep(0.2)
            exit_code, _ = database_container.exec_run("mysql")

        TestServer.Logger.log("Waiting for the real database to start...")
        exit_code, _ = database_container.exec_run("mysql")
        while exit_code != 0:
            time.sleep(0.2)
            exit_code, _ = database_container.exec_run("mysql")

    @staticmethod
    def __configure_database(
        podman_client: podman.PodmanClient, rendered_sql: str
    ):
        database_container = podman_client.containers.get(
            TestServer._DATABASE_NAME
        )

        fixed_sql = rendered_sql.replace("`", "\\`").replace('"', '\\"')
        sql_command = f'/bin/bash -c "mysql <<EOF\n{fixed_sql}\nEOF"'
        TestServer.Logger.log("Building database...")
        database_container.exec_run(
            cmd=sql_command,
            user="root",
        )

    def __start_server(self, podman_client, rendered_ini):
        volumes = {}

        if self.log_path is not None:
            TestServer.Logger.log(
                f"Starting {self.container_name} container with logging at {self.log_path}..."
            )
            volumes[self.log_path] = {
                "bind": "/var/log/servatrice",
                "mode": "rw",
            }
        else:
            TestServer.Logger.log(
                f"Starting {self.container_name} container without logging on host..."
            )

        if not podman_client.containers.exists(self.container_name):
            podman_client.containers.create(
                image=TestServer._BASE_SERVER_NAME,
                auto_remove=True,
                detach=True,
                hostname=self.container_name,
                name=self.container_name,
                network=TestServer._NETWORK_NAME,
                network_mode="bridge",
                ports={
                    "4747/tcp": self.tcp_port,
                    "4748/tcp": self._websocket_port,
                },
                volumes=volumes,
            )

        server_container = podman_client.containers.get(self.container_name)
        server_container.start()

        fixed_ini = rendered_ini.replace('"', '\\"')
        TestServer.Logger.log(
            "Writing servatrice configuration file to the container..."
        )
        config_command = f'/bin/bash -c "cat <<EOF > /home/servatrice/config/testatrice.ini\n{fixed_ini}\nEOF"'
        server_container.exec_run(
            cmd=config_command,
            user="root",
        )

        TestServer.Logger.log(
            "Sleeping for 1 second for the server to start..."
        )
        # TODO: change this to a loop with a ping when it can be done in crow
        time.sleep(1)

    def stop(self):
        """
        Stops this testatrice-server instance.

        Raises:
            ConnectionError: If the podman service is not available. Run
              ``podman system service -t 0 &`` to solve.
            RuntimeError: If a container using this same identifier does not
              exist or is not running.
        """
        with podman.PodmanClient() as podman_client:
            if not podman_client.ping():
                message = "The podman service did not respond."
                TestServer.Logger.log(message)
                raise ConnectionError(message)

            if not podman_client.containers.exists(self.container_name):
                message = f"No test server with identifier {self.server_identifier} exists."
                TestServer.Logger.log(message)
                raise RuntimeError(message)

            server_container = podman_client.containers.get(
                self.container_name
            )

            if server_container.status != "running":
                message = f"No test server with identifier {self.server_identifier} is running."
                TestServer.Logger.log(message)
                raise RuntimeError(message)

            TestServer.Logger.log(
                f"Stopping {self.server_identifier} container..."
            )
            server_container.stop()

    @staticmethod
    def stop_server(server_identifier: str):
        """
        Stops this testatrice-server instance.

        Raises:
            ConnectionError: If the podman service is not available. Run
              ``podman system service -t 0 &`` to solve.
            RuntimeError: If a container using this same identifier does not
              exist or is not running.
        """
        container_name = TestServer._BASE_SERVER_NAME + "-" + server_identifier

        with podman.PodmanClient() as podman_client:
            if not podman_client.ping():
                message = "The podman service did not respond."
                TestServer.Logger.log(message)
                raise ConnectionError(message)

            if not podman_client.containers.exists(container_name):
                message = f"No test server with identifier {server_identifier} exists."
                TestServer.Logger.log(message)
                raise RuntimeError(message)

            server_container = podman_client.containers.get(container_name)

            if server_container.status != "running":
                message = f"No test server with identifier {server_identifier} is running."
                TestServer.Logger.log(message)
                raise RuntimeError(message)

            TestServer.Logger.log(f"Stopping {container_name} container...")
            server_container.stop()

    @staticmethod
    def destroy_environment() -> None:
        """
        Stops all testatrice containers, including ``testatrice-database``
        and ``testatrice-mailserver``.

        Raises:
            ConnectionError: If the podman service is not available. Run
              ``podman system service -t 0 &`` to solve.
        """
        TestServer.stop_all_server_containers()

        with podman.PodmanClient() as podman_client:
            if not podman_client.ping():
                message = "The podman service did not respond."
                TestServer.Logger.log(message)
                raise ConnectionError(message)

            if podman_client.containers.exists(TestServer._MAILSERVER_NAME):
                mailserver_container = podman_client.containers.get(
                    TestServer._MAILSERVER_NAME
                )

                if mailserver_container.status == "running":
                    TestServer.Logger.log(
                        f"Stopping {TestServer._MAILSERVER_NAME} container..."
                    )
                    mailserver_container.stop()
                else:
                    TestServer.Logger.log(
                        f"Container {TestServer._MAILSERVER_NAME} is not running. Skipping stop step."
                    )
            else:
                TestServer.Logger.log(
                    f"Container {TestServer._MAILSERVER_NAME} does not exist. Skipping stop step."
                )

            if podman_client.containers.exists(TestServer._DATABASE_NAME):
                database_container = podman_client.containers.get(
                    TestServer._DATABASE_NAME
                )

                if database_container.status == "running":
                    TestServer.Logger.log(
                        f"Stopping {TestServer._DATABASE_NAME} container..."
                    )
                    database_container.stop()
                else:
                    TestServer.Logger.log(
                        f"Container {TestServer._DATABASE_NAME} is not running. Skipping stop step."
                    )
            else:
                TestServer.Logger.log(
                    f"Container {TestServer._DATABASE_NAME} does not exist. Skipping stop step."
                )

    @staticmethod
    def stop_all_server_containers() -> None:
        """
        Stops all testatrice containers, while keeping ``testatrice-database``
        and ``testatrice-mailserver`` running.

        Raises:
            ConnectionError: If the podman service is not available. Run
              ``podman system service -t 0 &`` to solve.
        """
        TestServer.Logger.log("Stopping all server containers...")
        with podman.PodmanClient() as podman_client:
            if not podman_client.ping():
                message = "The podman service did not respond."
                TestServer.Logger.log(message)
                raise ConnectionError(message)

            all_containers = podman_client.containers.list()

            for container in all_containers:
                if container.name.startswith(TestServer._BASE_SERVER_NAME):
                    # This is weird, but for some reason container.status does
                    # not work for the containers iterated from all_containers
                    container = podman_client.containers.get(container.name)
                    if container.status == "running":
                        container.stop()

    @staticmethod
    def __create_identifier() -> str:
        # TODO: it may be necessary to check that the identifier is unique on generation.
        fake = Faker()
        identifier = fake.word()

        return identifier

    @staticmethod
    def __get_available_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("", 0))
            port = sock.getsockname()[1]
            return port

    @staticmethod
    def __is_port_used(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("", port))
                return False
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    return True
                else:
                    raise

    class Logger:
        _enabled = False

        @staticmethod
        def log(message: str | Iterator[bytes]) -> None:
            if TestServer.Logger._enabled:
                if message.__class__ == str:
                    print(f"[{datetime.now()}] {message}")
                else:  # Iterator from podman logs
                    for line in message:
                        print(
                            TestServer.Logger.__iterator_line_to_string(line),
                            end="",
                        )

        @staticmethod
        def __iterator_line_to_string(line: bytes) -> str:
            return json.loads(line)["stream"]

        @staticmethod
        def enable():
            TestServer.Logger._enabled = True

        @staticmethod
        def disable():
            TestServer.Logger._enabled = False
