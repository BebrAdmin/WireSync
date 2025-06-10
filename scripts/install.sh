#!/bin/bash

echo
echo
echo "██╗    ██╗██╗██████╗ ███████╗███████╗██╗   ██╗███╗   ██╗ ██████╗"
echo "██║    ██║██║██╔══██╗██╔════╝██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝"
echo "██║ █╗ ██║██║██████╔╝█████╗  ███████╗ ╚████╔╝ ██╔██╗ ██║██║     "
echo "██║███╗██║██║██╔══██╗██╔══╝  ╚════██║  ╚██╔╝  ██║╚██╗██║██║     "
echo "╚███╔███╔╝██║██║  ██║███████╗███████║   ██║   ██║ ╚████║╚██████╗"
echo " ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝"
echo
echo "=============================================="
echo "      Welcome to WireSync Installer!"
echo "=============================================="
echo

read -p "Do you want to continue with the installation? (y/n): " CONTINUE
if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
    echo "Installation aborted."
    exit 0
fi

read -p "Enter installation directory [/opt]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/opt}
WIRE_DIR="$INSTALL_DIR/wiresync"
echo "WireSync will be installed to: $WIRE_DIR"
mkdir -p "$WIRE_DIR"
cd "$WIRE_DIR" || exit 1

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed! Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Docker Compose is not installed or not available as 'docker compose'! Please install Docker Compose v2+."
    exit 1
fi

if [[ ! -f "docker-compose.yml" ]]; then
    echo "docker-compose.yml not found, downloading from GitHub..."
    curl -fsSL -o docker-compose.yml https://raw.githubusercontent.com/BebrAdmin/WireSync/main/docker-compose.yml
    if [[ $? -ne 0 ]]; then
        echo "Failed to download docker-compose.yml! Please check your internet connection."
        exit 1
    fi
fi

ENV_FILE=".env"
SERVERS_FILE="servers.json"

DEFAULT_POSTGRES_USER="admin"
DEFAULT_POSTGRES_PASSWORD="Aa123456"
DEFAULT_POSTGRES_DB="wiresync_db"
DEFAULT_PGADMIN_EMAIL="admin@example.com"
DEFAULT_PGADMIN_PASSWORD="Aa123456"
DEFAULT_SERVER_HEALTH_INTERVAL="300"
DEFAULT_USER_SYNC_INTERVAL="60"
DEFAULT_TIMEZONE="Europe/Moscow"

ask_var() {
    local var_name="$1"
    local prompt="$2"
    local default="$3"
    local value=""
    while [[ -z "$value" ]]; do
        if [[ -n "$default" ]]; then
            read -p "$prompt [$default]: " value
            value=${value:-$default}
        else
            read -p "$prompt: " value
        fi
    done
    echo "$value"
}

files_exist=0
if [[ -f "$ENV_FILE" || -f "$SERVERS_FILE" ]]; then
    files_exist=1
    echo
    echo "Detected existing .env and/or servers.json files."
    read -p "Do you want to overwrite them and reconfigure from scratch? (y/n): " OVERWRITE
    if [[ "$OVERWRITE" == "y" || "$OVERWRITE" == "Y" ]]; then
        rm -f "$ENV_FILE" "$SERVERS_FILE"
        files_exist=0
    fi
fi

declare -A prompts=(
    [TOKEN]="Enter your Telegram bot TOKEN"
    [POSTGRES_USER]="Enter PostgreSQL username"
    [POSTGRES_PASSWORD]="Enter PostgreSQL password"
    [PGADMIN_EMAIL]="Enter pgAdmin email"
    [PGADMIN_PASSWORD]="Enter pgAdmin password"
)

declare -A defaults=(
    [POSTGRES_USER]="$DEFAULT_POSTGRES_USER"
    [POSTGRES_PASSWORD]="$DEFAULT_POSTGRES_PASSWORD"
    [POSTGRES_DB]="$DEFAULT_POSTGRES_DB"
    [PGADMIN_EMAIL]="$DEFAULT_PGADMIN_EMAIL"
    [PGADMIN_PASSWORD]="$DEFAULT_PGADMIN_PASSWORD"
    [SERVER_HEALTH_INTERVAL]="$DEFAULT_SERVER_HEALTH_INTERVAL"
    [USER_SYNC_INTERVAL]="$DEFAULT_USER_SYNC_INTERVAL"
    [TIMEZONE]="$DEFAULT_TIMEZONE"
)

declare -A values

if [[ $files_exist -eq 0 ]]; then
    for var in TOKEN POSTGRES_USER POSTGRES_PASSWORD PGADMIN_EMAIL PGADMIN_PASSWORD; do
        if [[ "$var" == "TOKEN" ]]; then
            values[$var]=$(ask_var "$var" "${prompts[$var]}")
        else
            values[$var]=$(ask_var "$var" "${prompts[$var]}" "${defaults[$var]}")
        fi
    done
    values[POSTGRES_DB]="$DEFAULT_POSTGRES_DB"
    values[SERVER_HEALTH_INTERVAL]="$DEFAULT_SERVER_HEALTH_INTERVAL"
    values[USER_SYNC_INTERVAL]="$DEFAULT_USER_SYNC_INTERVAL"
    values[TIMEZONE]="$DEFAULT_TIMEZONE"
else
    mapfile -t env_vars < <(grep -oP '^\w+(?==)' "$ENV_FILE")
    for var in TOKEN POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB PGADMIN_EMAIL PGADMIN_PASSWORD SERVER_HEALTH_INTERVAL USER_SYNC_INTERVAL TIMEZONE; do
        if ! grep -q "^$var=" "$ENV_FILE"; then
            if [[ "$var" == "TOKEN" ]]; then
                values[$var]=$(ask_var "$var" "${prompts[$var]}")
            else
                values[$var]=$(ask_var "$var" "${prompts[$var]}" "${defaults[$var]}")
            fi
        fi
    done
    for var in "${!values[@]}"; do
        if ! grep -q "^$var=" "$ENV_FILE"; then
            echo "$var=${values[$var]}" >> "$ENV_FILE"
        fi
    done
fi

DATABASE_URL="postgresql+asyncpg://${values[POSTGRES_USER]:-$DEFAULT_POSTGRES_USER}:${values[POSTGRES_PASSWORD]:-$DEFAULT_POSTGRES_PASSWORD}@wiresync-postgres:5432/$DEFAULT_POSTGRES_DB"

if [[ ! -f "$ENV_FILE" ]]; then
cat > "$ENV_FILE" <<EOF
TOKEN=${values[TOKEN]}
DATABASE_URL=$DATABASE_URL
SERVER_HEALTH_INTERVAL=$DEFAULT_SERVER_HEALTH_INTERVAL
USER_SYNC_INTERVAL=$DEFAULT_USER_SYNC_INTERVAL
TIMEZONE=$DEFAULT_TIMEZONE

POSTGRES_USER=${values[POSTGRES_USER]:-$DEFAULT_POSTGRES_USER}
POSTGRES_PASSWORD=${values[POSTGRES_PASSWORD]:-$DEFAULT_POSTGRES_PASSWORD}
POSTGRES_DB=$DEFAULT_POSTGRES_DB

PGADMIN_EMAIL=${values[PGADMIN_EMAIL]:-$DEFAULT_PGADMIN_EMAIL}
PGADMIN_PASSWORD=${values[PGADMIN_PASSWORD]:-$DEFAULT_PGADMIN_PASSWORD}
EOF
    echo ".env file created."
else
    echo ".env file updated (missing variables added if needed)."
fi

if [[ ! -f "$SERVERS_FILE" || $files_exist -eq 0 ]]; then
cat > "$SERVERS_FILE" <<EOF
{
    "Servers": {
        "1": {
            "Name": "WireSync DB",
            "Group": "Servers",
            "Host": "wiresync-postgres",
            "Port": 5432,
            "MaintenanceDB": "$DEFAULT_POSTGRES_DB",
            "Username": "${values[POSTGRES_USER]:-$DEFAULT_POSTGRES_USER}",
            "SSLMode": "prefer"
        }
    }
}
EOF
    echo "servers.json file created."
else
    echo "servers.json file left unchanged."
fi

echo
echo "Starting WireSync services with Docker Compose..."
docker compose up -d

SERVER_ADDR=$(hostname -I 2>/dev/null | awk '{print $1}')
if [[ -z "$SERVER_ADDR" ]]; then
    SERVER_ADDR=$(hostname)
fi

echo
echo "=============================================="
echo "WireSync installation complete!"
echo
echo "1. The first user to start the bot will become the admin."
echo "2. Please open your bot in Telegram and continue the setup process."
echo "3. pgAdmin is available at: http://$SERVER_ADDR:5050"
echo "   Login: ${values[PGADMIN_EMAIL]:-$DEFAULT_PGADMIN_EMAIL}"
echo "   Password: ${values[PGADMIN_PASSWORD]:-$DEFAULT_PGADMIN_PASSWORD}"
echo
echo "If you need to change any settings, edit the .env file and restart the containers."
echo "=============================================="