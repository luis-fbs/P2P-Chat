import argparse
import time

import constants
from user import User
from peer import Peer


def build_peer(args):
    user = User(args.name or args.nickname, args.nickname)
    return Peer(user, group=args.group, host=args.host, port=args.port)


def interactive_loop(peer):
    print("Type a message and press enter. Commands: /groups, /peers, /quit")
    while True:
        try:
            text = input()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/groups":
            print(f"* groups: {', '.join(peer.list_groups())}")
            continue
        if text == "/peers":
            print(f"* group '{peer.group}': {', '.join(peer.list_peers())}")
            continue
        peer.send_message(text)


def auto_loop(peer, count, delay):
    for i in range(1, count + 1):
        peer.send_message(f"message {i}")
        time.sleep(delay)
    print("* auto messages sent; still listening (Ctrl+C to quit)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description="P2P group chat client")
    parser.add_argument("nickname", help="unique nickname shown in the chat")
    parser.add_argument("group", nargs="?", default=constants.DEFAULT_GROUP,
                        help="group to join (default: %(default)s)")
    parser.add_argument("--name", default=None, help="full name (defaults to nickname)")
    parser.add_argument("--host", default=None,
                        help="IP advertised to other peers (default: get_public_ip())")
    parser.add_argument("--port", type=int, default=constants.PEER_PORT,
                        help="local PUB port (default: %(default)s)")
    parser.add_argument("--list-groups", action="store_true",
                        help="list existing groups and exit")
    parser.add_argument("--auto", type=int, default=0, metavar="N",
                        help="send N automatic demo messages instead of typing")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="seconds between automatic messages (default: %(default)s)")
    args = parser.parse_args()

    peer = build_peer(args)
    peer.bind_name()
    peer.resolve_group_server()
    print(f"* name server: {peer.ns_address}")
    print(f"* group server: {peer.gs_address}")

    if args.list_groups:
        print(f"* groups: {', '.join(peer.list_groups()) or '(none)'}")
        peer.unbind_name()
        return

    print(f"* {peer.register_group().get('message')}")
    peer.register_peer()
    print(f"* {peer.name} joined group '{peer.group}' as {peer.address}")

    peer.listen_group()
    time.sleep(1.5)
    print(f"* connected to {len(peer.connected)} peer(s). Ready.")

    try:
        if args.auto:
            auto_loop(peer, args.auto, args.delay)
        else:
            interactive_loop(peer)
    finally:
        peer.leave()
        print(f"* {peer.name} left the group.")


if __name__ == "__main__":
    main()
