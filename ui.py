import os

from peer import Peer
from group import Group
from user import User


def validade_menu_choice(choice):
    try:
        return int(choice) in range(4)
    except Exception:
        return False

def validate_group_join_choice(choice, groups):
    try:
        return int(choice) in range(1, len(groups)+1)
    except Exception:
        return False

def show_groups(groups):
    counter = 1
    for group in groups:
        print(f"{counter} - {group}")
        counter += 1

def handle_chat(peer, group):
    peer.listen_group()
    while True:
        message = input("> ")

        if message == "/quit":
            break

        peers = peer.list_peers(group).get("message")
        adresses = [(ip, port) for (_, ip, port) in peers]
        peer.broadcast_message(adresses, message)

def handle_group_creation(peer):
    group_name = input("Enter your group name: ")
    group = Group(group_name)
    peer.register_group(group)

def handle_group_list(peer):
    groups = peer.list_groups().get("message")
    if groups:
        print("Group List:\n")
        show_groups(groups)
    else:
        print("No Groups Yet")

def handle_group_join(peer):
    groups = peer.list_groups().get("message")
    if groups:
        print("Group Join:\n")
        show_groups(groups)
        choice = input("\nEnter your choice: ")
        if validate_group_join_choice(choice, groups):
            choice = int(choice) - 1
            group = Group(groups[choice])
            peer.register_peer(group)
            handle_chat(peer, group)
        else:
            print("Invalid choice")
    else:
        print("No Groups Yet")

handler = ["", handle_group_creation, handle_group_list, handle_group_join]

name = input("Enter your name: ")
nickname = input("Enter your nickname: ")
user = User(name, nickname)
peer = Peer(user)

menu_options = """
1 - Create Group
2 - List Groups
3 - Join Group
0 - Exit
"""

while True:
    os.system("clear")
    print("MENU")
    print(menu_options)
    choice = input("Enter your choice: ")
    if validade_menu_choice(choice):
        choice = int(choice)
        if choice == 0: break
        os.system("clear")
        handler[choice](peer)
        input("\nPress enter to continue...")


