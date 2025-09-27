import argparse
import pathlib

from testatrice import TestServer


def main():
    parser = generate_parser()
    args = parser.parse_args()

    match args.command:
        case "server":
            server(args)
        case "build-environment" | "build":
            build_environment(args)
        case "stop":
            stop(args)
        case None:
            parser.print_help()


def generate_parser():
    parser = argparse.ArgumentParser(
        prog="testatrice",
        description="Start servatrice instances in Python.",
    )

    subparsers = parser.add_subparsers(dest="command")

    server_description = "Create all necessary images, start the environment containers, and start a server container with the provided configuration. Already existing images will be reused unless the -r flag is passed."
    build_description = "Create all necessary images and start only the environment containers. Already existing images will be reused unless the -r flag is passed."
    stop_description = "Stop the containers."

    recreate = [
        ("-r", "--recreate"),
        {
            "action": "store_true",
            "help": "Destroy the Podman images stored and recreate them from scratch.",
            "default": False,
        },
    ]
    verbose = [
        ("-v", "--verbose"),
        {
            "action": "store_true",
            "help": "Print more logging information.",
            "default": False,
        },
    ]
    silent = [
        ("-s", "--silent"),
        {
            "action": "store_true",
            "help": "Print nothing.",
            "default": False,
        },
    ]

    parser_server = subparsers.add_parser(
        "server",
        description=server_description,
        help=server_description,
    )
    general_group = parser_server.add_argument_group("General")
    general_group.add_argument(
        "-si",
        "--server-identifier",
        type=str,
        help="Used as part of the container's name, as the database tables prefix, as the log file name, and as part of the email from (default: chosen randomly)",
        default=None,
    )
    general_group.add_argument(
        "-t",
        "--tcp-port",
        type=int,
        help="The exposed port number for TCP connections. The port in the container is always 4747 (default: chosen randomly)",
        default=None,
    )
    general_group.add_argument(
        "-w",
        "--websocket-port",
        type=int,
        help="The exposed port number for WebSocket connections. The port in the container is always 4748 (default: chosen randomly)",
        default=None,
    )
    general_group.add_argument(
        "-l",
        "--log-path",
        type=pathlib.Path,
        help="Directory path for the log file in the local host. This directory is bound to the container as a volume. The log file is named [server_identifier].log (default: no log file on the host)",
        default=None,
    )
    general_group.add_argument(
        "--ini-template",
        type=argparse.FileType("r"),
        help="Path to the Jinja2 template for the server's ini file (default: testatrice.ini.j2 provided with the package)",
        default=None,
    )
    general_group.add_argument(
        "--sql-template",
        type=argparse.FileType("r"),
        help="Path to the Jinja2 template for the database's SQL file (default: testatrice.sql.j2 provided with the package)",
        default=None,
    )
    general_group.add_argument(*recreate[0], **recreate[1])
    general_group.add_argument(*verbose[0], **verbose[1])
    general_group.add_argument(*silent[0], **silent[1])

    servatrice_configuration_group = parser_server.add_argument_group(
        "Servatrice configuration"
    )
    servatrice_configuration_group.add_argument(
        "-ci",
        "--require-client-id",
        action="store_true",
        help="Require the client to provide a client ID (similar to a user agent) on login (default: not required)",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-rf",
        "--required-features",
        type=str,
        help='List of features the client must advertise to be allowed to connect, comma separated. Example: "client_id,client_ver,websocket" (default: "" (empty string, no required features))',
        default="",
    )
    servatrice_configuration_group.add_argument(
        "-to",
        "--idle-client-timeout",
        type=int,
        help="Maximum time a player can stay connected but idle, in seconds. 0 = disabled (default: 3600)",
        default=3600,
    )
    servatrice_configuration_group.add_argument(
        "-am",
        "--authentication-method",
        type=TestServer.AuthenticationMethod,
        help="valid values: none|password|sql (default: sql)",
        choices=[
            authentication_method.value
            for authentication_method in TestServer.AuthenticationMethod
        ],
        default=TestServer.AuthenticationMethod.SQL,
    )
    servatrice_configuration_group.add_argument(
        "-p",
        "--password",
        type=str,
        help="The common password to be used if the 'password' authentication method is selected (default: password)",
        default="password",
    )
    servatrice_configuration_group.add_argument(
        "-er",
        "--enable-registration",
        action="store_true",
        default=False,
        help="Allow users to register an account on the server (default: disabled)",
    )
    servatrice_configuration_group.add_argument(
        "-rr",
        "--require-registration",
        action="store_true",
        default=False,
        help="Require users to register an account on the server (default: not required)",
    )
    servatrice_configuration_group.add_argument(
        "-re",
        "--require-email",
        action="store_true",
        help="Require users to provide an email address to register an account (default: not required)",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-ra",
        "--require-activation",
        action="store_true",
        help="Require users to verify their email address (default: not required)",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-ma",
        "--max-accounts-per-email",
        type=int,
        help="The maximum number of accounts that can be registered to the same email address (default: 2)",
        default=2,
    )
    servatrice_configuration_group.add_argument(
        "-ef",
        "--enable-forgot-password",
        action="store_true",
        help="Allow users to receive a token to their email address to reset their password (default: disabled)",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-tl",
        "--forgot-password-token-life",
        type=int,
        help="Lifetime of the password reset token, in minutes (default: 60)",
        default=60,
    )
    servatrice_configuration_group.add_argument(
        "-efpc",
        "--enable-forgot-password-challenge",
        action="store_true",
        help="Enable the server to challenge the user about their account when making the password reset request  (default: disabled)",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-pm",
        "--password-min-length",
        type=int,
        help="Minimum length allowed for the password (default: 6)",
        default=6,
    )
    servatrice_configuration_group.add_argument(
        "-um",
        "--username-min-length",
        type=int,
        help="Minimum length allowed for the username (default: 6)",
        default=6,
    )
    servatrice_configuration_group.add_argument(
        "-uM",
        "--username-max-length",
        type=int,
        help="Maximum length allowed for the username (more than 255 may create issues) (default: 12)",
        default=12,
    )
    servatrice_configuration_group.add_argument(
        "-udl",
        "--username-disallow-lowercase",
        action="store_false",
        dest="allow_lowercase",
        help="Forbid usernames from containing lowercase letters (default: lowercase letters allowed)",
        default=True,
    )
    servatrice_configuration_group.add_argument(
        "-udu",
        "--username-disallow-uppercase",
        action="store_false",
        dest="allow_uppercase",
        help="Forbid usernames from containing uppercase letters (default: uppercase letters allowed)",
        default=True,
    )
    servatrice_configuration_group.add_argument(
        "-udn",
        "--username-disallow-numerics",
        action="store_false",
        dest="allow_numerics",
        help="Forbid usernames from containing digits (default: digits allowed)",
        default=True,
    )
    servatrice_configuration_group.add_argument(
        "-ap",
        "--allowed-punctuation",
        type=str,
        help="A string of punctuation marks which can be accepted in the username (default: _.-)",
        default="_.-",
    )
    servatrice_configuration_group.add_argument(
        "-app",
        "--allow-punctuation-prefix",
        action="store_true",
        help="Allow a punctuation mark to be the first character in a username (default: disallowed",
        default=False,
    )
    servatrice_configuration_group.add_argument(
        "-dw",
        "--disallowed-words",
        type=str,
        help='Comma separated list of words not to be allowed in a username (default: "" (empty string, all words allowed))',
        default="",
    )
    servatrice_configuration_group.add_argument(
        "-ro",
        "--rooms-method",
        type=TestServer.RoomMethod,
        help="Source for rooms information (default: config)",
        choices=[room_method.value for room_method in TestServer.RoomMethod],
        default=TestServer.RoomMethod.CONFIG,
    )
    servatrice_configuration_group.add_argument(
        "-mgit",
        "--max-game-inactivity-time",
        type=int,
        help="Maximum time all players in a game can stay inactive before the game is closed, in seconds (default: 120)",
        default=120,
    )

    parser_build_environment = subparsers.add_parser(
        "build-environment",
        description=build_description,
        help=build_description,
        aliases=["build"],
    )
    parser_build_environment.add_argument(*recreate[0], **recreate[1])
    parser_build_environment.add_argument(*verbose[0], **verbose[1])
    parser_build_environment.add_argument(*silent[0], **silent[1])

    parser_stop = subparsers.add_parser(
        "stop",
        description=stop_description,
        help=stop_description,
    )
    parser_stop.add_argument(*verbose[0], **verbose[1])
    parser_stop.add_argument(*silent[0], **silent[1])
    parser_stop_group = parser_stop.add_argument_group(
        "Targets (include only one)"
    )
    parser_stop_mutually_exclusive_group = (
        parser_stop_group.add_mutually_exclusive_group(required=True)
    )
    parser_stop_mutually_exclusive_group.add_argument(
        "-si",
        "--server-identifier",
        type=str,
        default=None,
        help="Stop the container of the server instance with the given identifier.",
    )
    parser_stop_mutually_exclusive_group.add_argument(
        "--servers",
        action="store_true",
        default=False,
        help="Stop all server containers while keeping the environment containers running.",
    )
    parser_stop_mutually_exclusive_group.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Stop all server containers and all environment containers.",
    )

    return parser


def server(args):
    pass


def build_environment(args):
    pass


def stop(args):
    pass


if __name__ == "__main__":
    main()
