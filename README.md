# Account Generator Bot

## Description
This Discord bot allows managing and distributing account credentials securely via Discord.  
Admins can add and sync account lists from GitHub raw URLs, and authorized users can generate accounts with cooldown restrictions. Accounts are delivered privately via DM.

---

## Features

- **Add & Remove Lists** — Manage account lists stored locally and synced from GitHub.  
- **Generate Accounts** — Users request accounts and receive them privately.  
- **Cooldown System** — Prevents spamming account generation with configurable cooldowns.  
- **Stock Checking** — See how many accounts remain in each list.  
- **Role-Based Permissions** — Controlled access via `genadm` and `gen` roles.

---

## Commands

| Command       | Description                                   | Usage Example                               | Permissions     |
| ------------- | --------------------------------------------- | ------------------------------------------- | --------------- |
| `/add_list`   | Add a new account list from GitHub raw URL   | `/add_list name:netflix link:<github_url>` | `genadm` only   |
| `/del_list`   | Remove an existing account list               | `/del_list name:netflix`                     | `genadm` only   |
| `/lists`      | Display all available lists with account counts | `/lists`                                  | Everyone        |
| `/gen`        | Generate and receive an account via DM       | `/gen name:netflix`                         | `gen` or `genadm` |
| `/stock`      | Check remaining accounts per list             | `/stock`                                    | Everyone        |
| `/cooldown`   | Set cooldown time between generations (seconds) | `/cooldown seconds:300`                    | `genadm` only   |

---

## Permissions & Roles

- **genadm** — Full admin access: add/remove lists, set cooldown.  
- **gen** — Allowed to generate accounts, subject to cooldown.  
- Other users cannot generate accounts.

---

## Setup & Requirements

- Python 3.11+  
- `discord.py` library installed (`pip install discord.py`)  
- Create folders:  
  - `accounts/` for storing account files  
- Files used:  
  - `data.json` — stores list names and URLs  
  - `cooldowns.json` — manages cooldown settings and user timestamps

---

## How It Works

1. Admin adds a new list using `/add_list`, bot downloads and saves it locally.  
2. Users with `gen` role generate accounts using `/gen`.  
3. Bot checks cooldown timers, sends a random account from the list via DM, and updates stock.  
4. Users can check stock with `/stock`.  
5. Admins adjust cooldown via `/cooldown`.

---

## Example

```bash
/add_list name:netflix link:https://raw.githubusercontent.com/user/repo/main/netflix.txt
/gen name:netflix
/stock
/cooldown seconds:300
