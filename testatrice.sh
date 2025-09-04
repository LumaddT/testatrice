#!/bin/bash

tcp_port='4747'
websocket_port='4748'
server_identifier='testatrice'
require_client_id='false'
required_features=''
idle_client_timeout='3600'

authentication_method='sql'
common_password='password'
enable_registration='false'
require_registration='false'
require_email='false'
require_email_activation='false'
max_accounts_per_email='2'
enable_forgot_password='false'
forgot_password_token_life='60'
enable_forgot_password_challenge='false'

password_min_length='6'
username_min_length='6'
username_max_length='12'

allow_lowercase='true'
allow_uppercase='true'
allow_numerics='true'
allowed_punctuation='_.-'
allow_punctuation_prefix='false'
username_disallowed_words=''

rooms_method='config'
max_game_inactivity_time='120'
log_path='./logs'
sleep_time=30
ini_template='./testatrice.ini.envsubst-template'
sql_template='./testatrice.sql.envsubst-template'

print_usage() {
  echo "None of the arguments is validated."
  echo ""
  echo "Server:"
  echo "  -s, --server-identifier [string]          : used for database prefix, log file name and email from ['testatrice']"
  echo "  -t, --tcp, --socket [int]                 : TCP socket port exposed to host [4747]"
  echo "  -w, --ws, --websocket [int]               : websocket port exposed to host [4748]"
  echo "  -ci, --require-client-id                  : require client id on login"
  echo "  -rf, --required-features [string]         : client required features, comma separated ['']"
  echo "  -to, --idle-client-timeout [int]          : max time a player can stay connected but idle, in seconds. 0 = disabled [3600]"
  echo "Registration and authentication:"
  echo "  -am, --authentication-method [string]     : valid values: none|password|sql ['sql']"
  echo "  -p, --password [string]                   : the common password to be used if the 'password' authentication method is selected ['password']"
  echo "  -er, --enable-registration"
  echo "  -rr, --require-registration"
  echo "  -re, --require-email                      : require an email address to register"
  echo "  -ra, --require-activation                 : require email activation"
  echo "  -ma, --max-accounts-per-email [int]       : [2]"
  echo "  -ef, --enable-forgot-password"
  echo "  -tl, --forgot-password-token-life [int]   : lifetime of the password reset token, in minutes [60]"
  echo "  -efpc, --enable-forgot-password-challenge"
  echo "Usernames and passwords:"
  echo "  -pm, --password-min-length [int]          : minimum length allowed for the password [6]"
  echo "  -um, --username-min-length [int]          : minimum length allowed for the username [6]"
  echo "  -uM, --username-max-length [int]          : maximum length allowed for the username (more than 255 may create issues) [12]"
  echo "  -udl, --username-disallow-lowercase       : do not allow lowercase letters in the username"
  echo "  -udu, --username-disallow-uppercase       : do not allow uppercase letters in the username"
  echo "  -udn, --username-disallow-numerics        : do not allow digits in the username"
  echo "  -ap, --allowed-punctuation [string]       : a string of punctuation marks which can be accepted in the username ['_.-']"
  echo "  -app, --allow-punctuation-prefix          : allow a punctuation mark to be the first character in a username"
  echo "  -dw, --disallowed-words [string]          : comma separated list of words not to be allowed in a username ['']"
  echo "Misc:"
  echo "  -r, --rooms-method [string]               : source for rooms information. Valid values: config|sql [config]"
  echo "  -i, --max-game-inactivity-time [int]      : max time all players in a game can stay inactive before the game is closed, in seconds [120]"
  echo "  -l, --log-path [string]                   : directory path for the log file in the local host ['./logs']"
  echo "  --sleep [int]                             : how long to sleep after the database image is started, in seconds [30]"
  echo "                                              The database requires some time to start completely and become usable."
  echo "  --ini-template [string]                   : path to the envsub template file for testatrice.ini ['./testatrice.ini.envsubst-template']"
  echo "  --sql-template [string]                   : path to the envsub template file for testatrice.sql ['./testatrice.sql.envsubst-template']"
}

while [ $# -gt 0 ]; do
  case $1 in
    -s|--server-identifier) server_identifier=$2; shift 2 ;;
    -t|--tcp|--socket) tcp_port=$2; shift 2 ;;
    -w|--ws|--websocket) websocket_port=$2; shift 2 ;;
    -ci|--require-client-id) require_client_id='true'; shift ;;
    -rf|--required-features) required_features=$2; shift 2 ;;
    -to|--idle-client-timeout) idle_client_timeout=$2; shift 2 ;;
    -am|--authentication-method) authentication_method=$2; shift 2 ;;
    -p|--password) common_password=$2; shift 2 ;;
    -er|--enable-registration) enable_registration='true'; shift ;;
    -rr|--require-registration) require_registration='true'; shift ;;
    -re|--require-email) require_email='true'; shift ;;
    -ra|--require-activation) require_email_activation='true'; shift ;;
    -ma|--max-accounts-per-email) max_accounts_per_email=$2; shift 2 ;;
    -ef|--enable-forgot-password) enable_forgot_password='true'; shift ;;
    -tl|--forgot-password-token-life) forgot_password_token_life=$2; shift 2 ;;
    -efpc|--enable-forgot-password-challenge) enable_forgot_password_challenge='true'; shift ;;
    -pm|--password-min-length) password_min_length=$2; shift 2 ;;
    -um|--username-min-length) username_min_length=$2; shift 2 ;;
    -uM|--username-max-length) username_max_length=$2; shift 2 ;;
    -udl|--username-disallow-lowercase) allow_lowercase='false', shift ;;
    -udu|--username-disallow-uppercase) allow_uppercase='false', shift ;;
    -udn|--username-disallow-numerics) allow_numerics='false', shift ;;
    -ap|--allowed-punctuation) allowed_punctuation=$2; shift 2 ;;
    -app|--allow-punctuation-prefix) allow_punctuation_prefix='true', shift ;;
    -dw|--disallowed-words) username_disallowed_words=$2; shift 2 ;;
    -r|--rooms-method) rooms_method=$2; shift 2 ;;
    -i|--max-game-inactivity-time) max_game_inactivity_time=$2; shift 2 ;;
    -l|--log-path) log_path=$2; shift 2 ;;
    --sleep) sleep_time=$2; shift 2 ;;
    --ini-template) ini_template=$2; shift 2 ;;
    --sql-template) sql_template=$2; shift 2 ;;
    -h|--help) print_usage; exit 0 ;;
    *) echo "Unknown flag $1"; echo ""; print_usage; exit 1 ;;
  esac
done

if [ ! -f "${ini_template}" ]; then
    echo "File ${ini_template} not found."
    exit 3;
fi

if [ ! -f "${sql_template}" ]; then
    echo "File ${sql_template} not found."
    exit 4;
fi

mkdir -p "${log_path}/mails"

podman container exists testatrice-server-${server_identifier}
if [ $? -eq 0 ]; then
  echo "Testatrice instance with identifier ${server_identifier} already running. Specify a different identifier with the -s flag. Run with -h to see usage info."
  exit 2
fi

podman network exists testatrice-network
if [ $? -ne 0 ]; then
  echo "Creating testatrice-network network..."
  sed -i 's/"cniVersion": "1\.0\.0"/"cniVersion": "0\.4\.0"/' $(podman network create testatrice-network)
fi

podman image exists testatrice-server
if [ $? -ne 0 ]; then
  echo "Building testatrice-server image. This may take a while..."
  podman build --file testatrice-server.dockerfile -t testatrice-server > /dev/null
fi

podman image exists testatrice-database
if [ $? -ne 0 ]; then
  echo "Building testatrice-database image..."
  podman build --file testatrice-database.dockerfile -t testatrice-database > /dev/null
fi

podman container exists testatrice-database
if [ $? -ne 0 ]; then
  echo "Starting testatrice-database container (this causes the script to sleep for ${sleep_time} seconds)..."
  podman run --network=testatrice-network --detach --rm -h testatrice-database --name testatrice-database testatrice-database --sql-mode="NO_AUTO_VALUE_ON_ZERO" > /dev/null
  sleep ${sleep_time}s
fi

podman image exists testatrice-mailserver
if [ $? -ne 0 ]; then
  echo "Building testatrice-mailserver image..."
  podman build --file testatrice-mailserver.dockerfile -t testatrice-mailserver > /dev/null
fi

podman container exists testatrice-mailserver
if [ $? -ne 0 ]; then
  echo "Starting testatrice-mailserver container..."
  podman run --network=testatrice-network --detach -v "${log_path}/mails":/mailserver/mails --rm -h testatrice-mailserver --name testatrice-mailserver -p 1110:1110 -p 1111:1111 testatrice-mailserver > /dev/null
fi

export TESTATRICE_SERVER_IDENTIFIER=${server_identifier}
export TESTATRICE_REQUIRE_CLIENT_ID=${require_client_id}
export TESTATRICE_REQUIRED_FEATURES=${required_features}
export TESTATRICE_IDLE_CLIENT_TIMEOUT=${idle_client_timeout}
export TESTATRICE_AUTHENTICATION_METHOD=${authentication_method}
export TESTATRICE_COMMON_PASSWORD=${common_password}
export TESTATRICE_ENABLE_REGISTRATION=${enable_registration}
export TESTATRICE_REQUIRE_REGISTRATION=${require_registration}
export TESTATRICE_REQUIRE_EMAIL=${require_email}
export TESTATRICE_REQUIRE_EMAIL_ACTIVATION=${require_email_activation}
export TESTATRICE_MAX_ACCOUNTS_PER_EMAIL=${max_accounts_per_email}
export TESTATRICE_ENABLE_FORGOT_PASSWORD=${enable_forgot_password}
export TESTATRICE_FORGOT_PASSWORD_TOKEN_LIFE=${forgot_password_token_life}
export TESTATRICE_ENABLE_FORGOT_PASSWORD_CHALLENGE=${enable_forgot_password_challenge}
export TESTATRICE_USERNAME_MIN_LENGTH=${username_min_length}
export TESTATRICE_USERNAME_MAX_LENGTH=${username_max_length}
export TESTATRICE_PASSWORD_MIN_LENGTH=${password_min_length}
export TESTATRICE_ALLOW_LOWERCASE=${allow_lowercase}
export TESTATRICE_ALLOW_UPPERCASE=${allow_uppercase}
export TESTATRICE_ALLOW_NUMERICS=${allow_numerics}
export TESTATRICE_ALLOWED_PUNCTUATION=${allowed_punctuation}
export TESTATRICE_ALLOW_PUNCTUATION_PREFIX=${allow_punctuation_prefix}
export TESTATRICE_USERNAME_DISALLOWED_WORDS=${username_disallowed_words}
export TESTATRICE_ROOMS_METHOD=${rooms_method}
export TESTATRICE_MAX_GAME_INACTIVITY_TIME=${max_game_inactivity_time}

tmp_dir=$(mktemp -d --tmpdir testatrice.XXXXXXXXXX)
ini_dir=${tmp_dir}/config
sql_dir=${tmp_dir}/sql

mkdir ${ini_dir}
mkdir ${sql_dir}

envsubst < "${ini_template}" > ${ini_dir}/testatrice.ini
envsubst < "${sql_template}" > ${sql_dir}/testatrice.sql

echo "Setting up testatrice-database..."
podman exec -u root testatrice-database /bin/bash -c "mkdir -p /home/mysql"
podman cp ${sql_dir}/testatrice.sql testatrice-database:/home/mysql/${server_identifier}.sql
podman exec -u root testatrice-database /bin/bash -c "mysql < /home/mysql/${server_identifier}.sql"

echo "Running testatrice-server-${server_identifier} container..."
podman run --network=testatrice-network --detach -v "${log_path}":/var/log/servatrice -v ${ini_dir}:/home/servatrice/config --rm -h testatrice-server-${server_identifier} --name testatrice-server-${server_identifier} -p ${tcp_port}:4747 -p ${websocket_port}:4748 testatrice-server > /dev/null

echo ${tmp_dir}
