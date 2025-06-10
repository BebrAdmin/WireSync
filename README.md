# WIRESYNC

[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/BebrAdmin/WireSync)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-wiresync--bot-blue?logo=docker)](https://hub.docker.com/r/bebradmin/wiresync-bot)
![Docker Pulls](https://img.shields.io/docker/pulls/bebradmin/wiresync-bot)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Code Size](https://img.shields.io/github/languages/code-size/BebrAdmin/WireSync)

WireSync Bot is a modern Telegram bot for managing WireGuard VPN users and servers through a convenient chat interface.  
The project is built to work with [WireGuard Portal API](https://github.com/h44z/wg-portal) and is intended for use with WireGuard Portal servers.

On [DeepWiki](https://deepwiki.com/BebrAdmin/WireSync) you can read more about the project’s architecture, how it works, and find answers to common questions.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Automatic Installation (Recommended)](#automatic-installation-recommended)
  - [Manual Deployment (Advanced)](#manual-deployment-advanced)
- [Features](#features)
- [How It Works](#how-it-works)
- [Credits & Thanks](#credits--thanks)

## Overview

WireSync Bot is a Telegram bot for managing WireGuard VPN users, servers, and invites.  
It is tightly integrated with PostgreSQL for persistent storage and is designed to be deployed via Docker Compose for easy setup and reliability.

**Key points:**
- Works with [WireGuard Portal](https://github.com/h44z/wg-portal) servers via their API.
- Intended for sysadmins and teams who want to manage VPN access through Telegram.
- Provides a web admin interface via pgAdmin for database management.

## Getting Started

### Automatic Installation (Recommended)

Just run on your server:
```sh
bash <(curl -Ls https://raw.githubusercontent.com/BebrAdmin/WireSync/main/scripts/install.sh)
```
The script will create all necessary files and launch the containers.

> **After installation, you must open your bot in Telegram and complete the initial setup as the first admin user.**

### Manual Deployment (Advanced)

#### 1. Create `.env` file

Copy and edit the following example, or use [example_.env](https://github.com/BebrAdmin/WireSync/blob/main/example_.env):

```env
TOKEN=123456789:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
DATABASE_URL=postgresql+asyncpg://admin:Aa123456@wiresync-postgres:5432/wiresync_db
SERVER_HEALTH_INTERVAL=300
USER_SYNC_INTERVAL=60
TIMEZONE=Europe/Moscow

POSTGRES_USER=admin
POSTGRES_PASSWORD=Aa123456
POSTGRES_DB=wiresync_db

PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=Aa123456
```

#### 2. Create `servers.json`

Use the following template, or see [example_servers.json](https://github.com/BebrAdmin/WireSync/blob/main/example_servers.json):

```json
{
  "Servers": {
    "1": {
      "Name": "WireSync DB",
      "Group": "Servers",
      "Host": "wiresync-postgres",
      "Port": 5432,
      "MaintenanceDB": "wiresync_db",
      "Username": "admin",
      "SSLMode": "prefer"
    }
  }
}
```

#### 3. Create `docker-compose.yml`

You can use the [docker-compose.yml](https://github.com/BebrAdmin/WireSync/blob/main/docker-compose.yml) from the repository, or use this example:

```yaml
version: '3.8'

services:
  wiresync-postgres:
    image: postgres:17.5
    container_name: wiresync-postgres
    restart: always
    env_file:
      - .env
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - wiresync_network
    healthcheck:
      test: [ "CMD-SHELL", "pg_isready -U ${POSTGRES_USER}" ]
      interval: 10s
      retries: 5
      start_period: 10s

  wiresync-pgadmin:
    image: dpage/pgadmin4:9.4
    container_name: wiresync-pgadmin
    restart: always
    env_file:
      - .env
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    volumes:
      - pgadmin_data:/var/lib/pgadmin
      - ./servers.json:/pgadmin4/servers.json
    ports:
      - "5050:80"
    depends_on:
      wiresync-postgres:
        condition: service_healthy
    networks:
      - wiresync_network

  wiresync-bot:
    image: bebradmin/wiresync-bot
    container_name: wiresync-bot
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      wiresync-postgres:
        condition: service_healthy
    volumes:
      - ./app/logs:/app/app/logs
    networks:
      - wiresync_network

volumes:
  postgres_data:
  pgadmin_data:

networks:
  wiresync_network:
```

#### 4. Launch the stack

```sh
docker compose up -d
```

> **After installation, you must open your bot in Telegram and complete the initial setup as the first admin user.**

## Features

- Manage WireGuard VPN users and servers via Telegram
- PostgreSQL integration for reliable data storage
- Invite management and user synchronization
- Admin web interface via pgAdmin
- Health checks and user sync intervals configurable via `.env`
- Designed for WireGuard Portal API

## How It Works

WireSync Bot is built on top of the following technologies and libraries:
- **Python 3.12** (main language)
- **aiogram** for Telegram Bot API
- **asyncpg** and **SQLAlchemy** for async PostgreSQL access
- **Docker** and **Docker Compose** for deployment
- **WireGuard Portal API** ([h44z/wg-portal](https://github.com/h44z/wg-portal)) for VPN server management
- **pgAdmin** for database administration

The bot communicates with your WireGuard Portal server using its API, allowing you to manage VPN peers, users, and server status directly from Telegram.

## Credits & Thanks

WireSync Bot is built on the shoulders of giants. Special thanks to:

- [WireGuard (official)](https://www.wireguard.com/) — for the VPN protocol and tools
- [WireGuard Portal](https://github.com/h44z/wg-portal) — for the API and management platform
- [aiogram](https://github.com/aiogram/aiogram) — for the Telegram bot framework
- [asyncpg](https://github.com/MagicStack/asyncpg) and [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) — for database access
- [pgAdmin](https://github.com/pgadmin-org/pgadmin4) — for database administration

**WireSync Bot** — simple, secure, and efficient VPN management for your team, designed for WireGuard Portal servers!
