# This is the client side of a forum based on TCP
# z5248147 Haoheng Duan
# Encoding: utf-8
# Python3
from socket import *
import sys
import pickle
import threading
from time import sleep
import os

# Global variables
# Server would be running on the same host as Client
server_name = sys.argv[1]
server_port = int(sys.argv[2])
# All the possible commands
commands = ['CRT', 'MSG', 'DLT', 'EDT', 'LST', 'RDT',
    'UPD', 'DWN', 'RMV', 'XIT', 'SHT']
# Creates the client’s IPV4 TCP socket and initiates the TCP connection
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((server_name, server_port))
# Creates the client’s heartbeat socket and initiates the TCP connection
heartbeat_socket = socket(AF_INET, SOCK_STREAM)
heartbeat_socket.connect((server_name, server_port))

# Check if the username and password have invalid character
def check_username_password(input):
    special_character = r'~!@#$%^&*_-+=`|\(){}[]:;"' + r"'<>,.?/"
    for character in input:
        if character.isupper() or character.islower() or character.isdigit()\
            or character in special_character:
            pass
        else:
            return False
    return True

# Check if the argements of requests have invalid character
def check_arguments(input):
    special_character = '!@#$%.?,'
    for character in input:
        if character.isupper() or character.islower() or character.isdigit()\
            or character in special_character:
            pass
        else:
            return False
    return True

# Handle the authentiacation and user requests of client side by using 2 loops
def server_handle():
    # User Authentication
    while True:
        username = input('Enter username: ')
        # loop until username contains only valid characters
        while not check_username_password(username) or username == '':
            username = input('Format error, enter username again: ')
        client_socket.send(username.encode('utf-8'))
        recv_message = client_socket.recv(1024).decode('utf-8')
        if recv_message == 'already logged in':
            print('User already logged in')
            continue
        elif recv_message == 'user exists':
            password = input('Enter password: ')
            # loop until password contains only valid characters
            while not check_username_password(password) or password == '':
                password = input('Format error, enter password again: ')
            client_socket.send(password.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'successfully login':
                print('Welcome to the forum')
                break
            elif recv_message == 'incorrect password':
                print('Invalid password')
                continue
        elif recv_message == 'new user':
            password = input(f"Enter new password for {username}: ")
            # loop until password contains only valid characters
            while not check_username_password(password) or password == '':
                password = input(f"Format error, enter new password for {username} again: ")
            client_socket.send(password.encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'successfully login'
            print('Welcome to the forum')
            break

    # Processing commands
    while True:
        command = input('Enter one of the following commands: CRT, MSG, DLT, \nEDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ')
        command = command.split()
        # check if the command is valid
        if command[0] not in commands:
            print('Invalid command')
            continue
        # check if the argements are valid
        if len(command) > 1:
            valid_arguments = True
            for argument in command[1:]:
                if not check_arguments(argument):
                    valid_arguments = False
            if not valid_arguments:
                print('Argument format error')
                continue
        if command[0] == 'XIT':
            # Exit
            if len(command) != 1:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            print('Goodbye')
            client_socket.close()
            heartbeat_socket.close()
            break
        elif command[0] == 'CRT':
            # Create thread
            if len(command) != 2:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            assert recv_message == 'enter name'
            client_socket.send(command[1].encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'thread exists':
                print(f"Thread {command[1]} exists")
                continue
            elif recv_message == 'thread created':
                print(f"Thread {command[1]} created")
                continue
        elif command[0] == 'LST':
            # List threads
            if len(command) != 1:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            recv_message = client_socket.recv(2048).decode('utf-8')
            if recv_message == 'no threads':
                print('No threads to list')
                continue
            else:
                threads = recv_message.split()
                print('The list of active threads:')
                for thread in threads:
                    print(thread)
        elif command[0] == 'MSG':
            # send messages
            if len(command) < 3:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'rest messages'
            rest_messages = ' '.join(command[1:])
            client_socket.send(rest_messages.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'posted successfully':
                print(f"Message posted to {command[1]} thread")
        elif command[0] == 'RDT':
            # read threads
            if len(command) != 2:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'enter name'
            client_socket.send(command[1].encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'empty thread':
                print(f"Thread {command[1]} is empty")
                continue
            else:
                # recv_message is the length of the message
                reply_message = 'ready'
                client_socket.send(reply_message.encode('utf-8'))
                # use a loop to receive all the binary messages
                full_msg = b''
                while True:
                    msg = client_socket.recv(100)
                    full_msg += msg
                    if len(full_msg) == int(recv_message):
                        break
                content = pickle.loads(full_msg)
                for message in content:
                    print(message)
        elif command[0] == 'EDT':
            # edit message
            if len(command) < 4:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'rest messages'
            rest_messages = ' '.join(command[1:])
            client_socket.send(rest_messages.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'invalid number':
                print(f"The message number is invalid")
                continue
            elif recv_message == 'invalid user':
                print('The message belongs to another user and cannot be edited')
                continue
            elif recv_message == 'edited successfully':
                print('The message has been edited')
                continue
        elif command[0] == 'DLT':
            # delete message
            if len(command) != 3:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'rest messages'
            rest_messages = ' '.join(command[1:])
            client_socket.send(rest_messages.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'invalid number':
                print(f"The message number is invalid")
                continue
            elif recv_message == 'invalid user':
                print('The message belongs to another user and cannot be deleted')
                continue
            elif recv_message == 'deleted successfully':
                print('The message has been deleted')
                continue
        elif command[0] == 'UPD':
            # upload file
            if len(command) != 3:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'rest messages'
            rest_messages = ' '.join(command[1:])
            # find the file size
            with open(f"{command[2]}", 'rb') as file:
                file_content = file.read()
                file_size = len(file_content)
                rest_messages += f" {file_size}"
                file.close()
            client_socket.send(rest_messages.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'thread exists':
                # read the binary file and send
                with open(f"{command[2]}", 'rb') as file:
                    file_content = file.read()
                    client_socket.send(file_content)
                    file.close()
                assert client_socket.recv(1024).decode('utf-8') == 'uploaded successfully'
                print(f"{command[2]} uploaded to {command[1]} thread")
        elif command[0] == 'DWN':
            # download file
            if len(command) != 3:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'rest messages'
            rest_messages = ' '.join(command[1:])
            client_socket.send(rest_messages.encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'no file':
                print(f"{command[2]} doesn't exist")
                continue
            else:
                file_size = int(recv_message)
                reply_message = 'ready'
                client_socket.send(reply_message.encode('utf-8'))
                # use a loop to receive all the binary file
                full_file = b''
                while True:
                    file = client_socket.recv(10000000)
                    full_file += file
                    if len(full_file) == file_size:
                        break
                # write the file in the current directory
                with open(f"{command[2]}", 'wb') as file:
                    file.write(full_file)
                    file.close()
                print(f"{command[2]} successfully downloaded")
        elif command[0] == 'RMV':
            # remove threads
            if len(command) != 2:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'thread_title'
            client_socket.send(command[1].encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'no threads':
                print(f"{command[1]} thread doesn't exist")
                continue
            elif recv_message == 'invalid user':
                print(f"Thread cannot be deleted")
                continue
            elif recv_message == 'deleted successfully':
                print('The thread has been removed')
        elif command[0] == 'SHT':
            # shut down the server
            if len(command) != 2:
                print('Incorrect number of arguments')
                continue
            client_socket.send(command[0].encode('utf-8'))
            assert client_socket.recv(1024).decode('utf-8') == 'admin_passwd'
            client_socket.send(command[1].encode('utf-8'))
            recv_message = client_socket.recv(1024).decode('utf-8')
            if recv_message == 'incorrect password':
                print(f"Password is incorrect")
                continue
            elif recv_message == 'shutdown':
                print('Goodbye. Server shutting down')
                client_socket.close()
                heartbeat_socket.close()
                break

# Heartbeat packets are used to detect whether the server is alive
def heartbeat_packet():
    # This ？、？ symbol is used by the heartbeat packets because
    # these symbols are not included in the username
    heartbeat_socket.send('？、？'.encode('utf-8'))
    while True:
        recv_message = heartbeat_socket.recv(1024)
        # if the server socket is closed
        if len(recv_message) == 0:
            print('\nGoodbye. Server shutting down')
            client_socket.close()
            heartbeat_socket.close()
            os._exit(0)
        sleep(3)
        heartbeat_socket.send('is_alive'.encode('utf-8'))

if __name__ == '__main__':
    # create a new thread to send heartbeat packets
    heartbeat_thread = threading.Thread(target=heartbeat_packet)
    heartbeat_thread.setDaemon(True)
    heartbeat_thread.start()
    server_handle()
