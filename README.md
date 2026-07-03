# P2P Group Chat

A **peer-to-peer group chat** for the Distributed Systems course.

## Client options

Usage: `python client.py <nickname> [group] [options]`

| Option | Description                                             | Default |
|--------|---------------------------------------------------------|---------|
| `nickname` | unique nickname shown in the chat (positional)          | — |
| `group` | group to join (optional positional; created if missing) | `chat` |
| `--name` | name                                                    | = nickname |
| `--host` | IP advertised to other peers                            | `get_public_ip()` |
| `--port` | local PUB port                                          | `5679` |
| `--list-groups` | list existing groups and exit                           | (off) |
| `--auto N` | send N automatic messages instead of typing             | `0` (interactive) |
| `--delay` | seconds between automatic messages                      | `1.0` |

In interactive mode, type a message and press Enter to send it to the group.
In-chat commands:

- `/groups` — list existing groups.
- `/peers` — list members of the current group.
- `/quit` — leave the group.
