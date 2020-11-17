# This is the server side of a forum based on TCP
# z5248147 Haoheng Duan
# Encoding: utf-8
# Python3
from socket import *
import sys
import threading
import pickle
import os
from time import sleep

# Global variables
# Server would be running on the same host as Client
data = {
    'logged_clients': [],
    'active_threads': [],
    'server_shutdown': False,
    'connected_sockets': [],
}
server_port = int(sys.argv[1])
admin_passwd = sys.argv[2]
thread_lock = threading.Lock()
#This line creates the server’s IPV4 TCP socket.
server_socket = socket(AF_INET, SOCK_STREAM)
# Binds the portnumber and hostname to the socket
server_socket.bind(('localhost', server_port))
# Start to listen
server_socket.listen(5)

# Handle the authentiacation and user requests of server side by using 2 loops
def client_handle(connection_socket):
    # User Authentication
    while True:
        username = connection_socket.recv(1024).decode('utf-8')
        # This ？、？ symbol is used by the heartbeat packets because
        # these symbols are not included in the username
        if username == '？、？':
            # Connected with the heartbeat socket of the client side
            while True:
                alive_message = "is_alive"
                connection_socket.send(alive_message.encode('utf-8'))
                sleep(3)
                recv_message = connection_socket.recv(1024)
                if len(recv_message) == 0:
                    # When the heartbeat socket is closed
                    thread_lock.acquire()
                    data['connected_sockets'].remove(connection_socket)
                    thread_lock.release()
                    connection_socket.close()
                    return
        print(f"Client connected")
        # Use thread lock to avoid mess
        thread_lock.acquire()
        # check if the user has already logged in
        if username in data['logged_clients']:
            reply_message = 'already logged in'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
            continue
        with open('credentials.txt', 'a+') as user_file:
            user_exist = False
            user_file.seek(0, 0)
            line = user_file.readline()
            # find if username exist in this file
            while line:
                if line[-1] != '\n':
                    user_file.write('\n')
                # each line includes username and password
                user = line.split()
                if user != [] and username == user[0]:
                    user_exist = True
                    break
                line = user_file.readline()
            if user_exist:
                # user exist
                reply_message = 'user exists'
                connection_socket.send(reply_message.encode('utf-8'))
                password = connection_socket.recv(1024).decode('utf-8')
                if password == user[1]:
                    # password correct
                    print(f"{username} successfully login")
                    reply_message = 'successfully login'
                    data['logged_clients'].append(username)
                    connection_socket.send(reply_message.encode('utf-8'))
                    user_file.close()
                    thread_lock.release()
                    break
                else:
                    # password incorrect
                    print('Incorrect password')
                    reply_message = 'incorrect password'
                    connection_socket.send(reply_message.encode('utf-8'))
                    user_file.close()
                    thread_lock.release()
                    continue
            else:
                # user doesn't exist
                print('New user')
                reply_message = 'new user'
                connection_socket.send(reply_message.encode('utf-8'))
                password = connection_socket.recv(1024).decode('utf-8')
                # write the user information to the end of the file
                new_user = f"{username} {password}\n"
                user_file.seek(0, 2)
                user_file.write(new_user)
                print(f"{username} successfully logged in")
                reply_message = 'successfully login'
                connection_socket.send(reply_message.encode('utf-8'))
                data['logged_clients'].append(username)
                user_file.close()
                thread_lock.release()
                break

    # Process user requests
    while True:
        request = connection_socket.recv(1024).decode('utf-8')
        # use thread lock to avoid conflict
        thread_lock.acquire()
        if request == 'XIT':
            # Exit
            print(f"{username} exited")
            data['logged_clients'].remove(username)
            data['connected_sockets'].remove(connection_socket)
            connection_socket.close()
            thread_lock.release()
            break
        elif request == 'CRT':
            # Creat thread
            print(f"{username} issued CRT command")
            reply_message = 'enter name'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_title = connection_socket.recv(1024).decode('utf-8')
            # check if thread exists
            if thread_title in data['active_threads']:
                print(f"Thread {thread_title} exists")
                reply_message = 'thread exists'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            data['active_threads'].append(thread_title)
            print(f"Thread {thread_title} created")
            reply_message = 'thread created'
            connection_socket.send(reply_message.encode('utf-8'))
            # write the creator name to the thread
            with open(f"{thread_title}", 'w') as new_thread:
                new_thread.write(f"{username}\n")
                new_thread.close()
            thread_lock.release()
        elif request == 'LST':
            # List threads
            print(f"{username} issued LST command")
            if len(data['active_threads']) == 0:
                # Threads list is empty
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            else:
                reply_message = " ".join(data['active_threads'])
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
        elif request == 'MSG':
            # Post message
            print(f"{username} issued MSG command")
            reply_message = 'rest messages'
            connection_socket.send(reply_message.encode('utf-8'))
            rest_messages = connection_socket.recv(2048).decode('utf-8')
            rest_messages = rest_messages.split()
            thread_title = rest_messages[0]
            # check if thread exists
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            message = " ".join(rest_messages[1:])
            with open(f"{thread_title}", 'a+') as thread:
                thread.seek(0, 0)
                lines = thread.readlines()
                # Find message number by using number of all the lines
                # minus non-message lines
                message_num = len(lines)
                for line in lines[1:]:
                    line = line.split()
                    if line[1] == 'uploaded':
                        message_num -= 1
                message = f"{message_num} {username}: {message}\n"
                thread.seek(0, 2)
                thread.write(message)
                thread.close()
            print(f"Message posted to {thread_title} thread")
            reply_message = 'posted successfully'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
        elif request == 'RDT':
            # Read thread
            print(f"{username} issued RDT command")
            connection_socket.send('enter name'.encode('utf-8'))
            thread_title = connection_socket.recv(1024).decode('utf-8')
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            print(f"Thread {thread_title} read")
            with open(f"{thread_title}", 'r') as thread:
                content = thread.readlines()
                # Only include username of the creator
                if len(content) == 1:
                    reply_message = 'empty thread'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                # Remove the spaces and the username of creator
                content = list(map(lambda message: message.strip(), content))[1:]
                # transfer it to binary and send it as well as the length to client
                content = pickle.dumps(content)
                reply_message = f"{len(content)}"
                connection_socket.send(reply_message.encode('utf-8'))
                assert connection_socket.recv(1024).decode('utf-8') == 'ready'
                connection_socket.send(content)
                thread.close()
                thread_lock.release()
        elif request == 'EDT':
            # Edit message
            print(f"{username} issued EDT command")
            reply_message = 'rest messages'
            connection_socket.send(reply_message.encode('utf-8'))
            rest_messages = connection_socket.recv(2048).decode('utf-8')
            rest_messages = rest_messages.split()
            thread_title = rest_messages[0]
            message_num = int(rest_messages[1])
            message = ' '.join(rest_messages[2:])
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            with open(f"{thread_title}", 'r+') as thread:
                lines = thread.readlines()
                # Find how many lines of messages by using number of all the lines
                # minus non-message lines
                num_message_lines = len(lines) - 1
                for line in lines[1:]:
                    line = line.split()
                    if line[1] == 'uploaded':
                        num_message_lines -= 1
                if message_num < 1 or message_num > (num_message_lines):
                    print('Invalid message number')
                    reply_message = 'invalid number'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                # Find this message from the second line
                for line_num, line in enumerate(lines[1:], 1):
                    line = line.split()
                    if line[1] != 'uploaded' and int(line[0]) == message_num:
                        break
                # Check if the user is the creator of message
                if line[1][0:-1] != username:
                    print('Message cannot be edited')
                    reply_message = 'invalid user'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                message = f"{message_num} {username}: {message}\n"
                lines[line_num] = message
                thread.close()
            # write the messages back to the thread
            with open(f"{thread_title}", 'w+') as thread:
                for line in lines:
                    thread.write(line)
                thread.close()
            print('Message has been edited')
            reply_message = 'edited successfully'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
        elif request == 'DLT':
            # Delete message
            print(f"{username} issued DLT command")
            reply_message = 'rest messages'
            connection_socket.send(reply_message.encode('utf-8'))
            rest_messages = connection_socket.recv(2048).decode('utf-8')
            rest_messages = rest_messages.split()
            thread_title = rest_messages[0]
            message_num = int(rest_messages[1])
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            with open(f"{thread_title}", 'r+') as thread:
                lines = thread.readlines()
                # Find how many lines of messages by using number of all the lines
                # minus non-message lines
                num_message_lines = len(lines) - 1
                for line in lines[1:]:
                    line = line.split()
                    if line[1] == 'uploaded':
                        num_message_lines -= 1
                if message_num < 1 or message_num > (num_message_lines):
                    print('Invalid message number')
                    reply_message = 'invalid number'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                # Find this message from the second line
                for line_num, line in enumerate(lines[1:], 1):
                    line = line.split()
                    if line[1] != 'uploaded' and int(line[0]) == message_num:
                        break
                # Check if the user is the creator of message
                if line[1][0:-1] != username:
                    print('Message cannot be edited')
                    reply_message = 'invalid user'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                # delete relevant message
                del lines[line_num]
                # Change the message number after this message
                for num, line in enumerate(lines[line_num:], line_num):
                    line = line.split()
                    if line[1] != 'uploaded':
                        line[0] = str(message_num)
                        line = " ".join(line) + '\n'
                        lines[num] = line
                        message_num += 1
                thread.close()
            # write the messages back to the thread
            with open(f"{thread_title}", 'w+') as thread:
                for line in lines:
                    thread.write(line)
                thread.close()
            print('Message has been deleted')
            reply_message = 'deleted successfully'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
        elif request == 'UPD':
            # Upload file
            print(f"{username} issued UPD command")
            reply_message = 'rest messages'
            connection_socket.send(reply_message.encode('utf-8'))
            rest_messages = connection_socket.recv(2048).decode('utf-8')
            rest_messages = rest_messages.split()
            thread_title = rest_messages[0]
            filename = rest_messages[1]
            filesize = int(rest_messages[2])
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            reply_message = 'thread exists'
            connection_socket.send(reply_message.encode('utf-8'))
            # Start to receive file
            full_file = b''
            while True:
                file = connection_socket.recv(10000000)
                full_file += file
                # When the whole file is received, break the loop
                if len(full_file) == filesize:
                    break
            # write this file in current directory
            with open(f"{thread_title}-{filename}", 'wb') as file:
                file.write(full_file)
                file.close()
            # add file entry in thread
            with open(f"{thread_title}", 'a+') as thread:
                line = f"{username} uploaded {filename}\n"
                thread.write(line)
                thread.close()
            print(f"{username} uploaded file {filename} to {thread_title} thread")
            reply_message = 'uploaded successfully'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
        elif request == 'DWN':
            # Download file
            print(f"{username} issued DWN command")
            reply_message = 'rest messages'
            connection_socket.send(reply_message.encode('utf-8'))
            rest_messages = connection_socket.recv(2048).decode('utf-8')
            rest_messages = rest_messages.split()
            thread_title = rest_messages[0]
            filename = rest_messages[1]
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            with open(f"{thread_title}", 'r+') as thread:
                # Check if this file exists in the thread
                lines = thread.readlines()
                file_exist = False
                for line in lines[1:]:
                    line = line.split()
                    if line[1] == 'uploaded' and line[2] == filename:
                        file_exist = True
                        break
                if not file_exist:
                    print(f"File {filename} doesn't exist")
                    reply_message = 'no file'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                thread.close()
            # Find the length of the file
            with open(f"{thread_title}-{filename}", 'rb') as file:
                file_content = file.read()
                filesize = len(file_content)
                file.close()
            reply_message = f"{filesize}"
            connection_socket.send(reply_message.encode('utf-8'))
            assert connection_socket.recv(1024).decode('utf-8') == 'ready'
            # Read the binary file that needs to be downloaded
            with open(f"{thread_title}-{filename}", 'rb') as file:
                file_content = file.read()
                connection_socket.send(file_content)
                file.close()
            print(f"{filename} downloaded from Thread {thread_title}")
            thread_lock.release()
        elif request == 'RMV':
            # Remove thread
            print(f"{username} issued RMV command")
            reply_message = 'thread_title'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_title = connection_socket.recv(1024).decode('utf-8')
            if thread_title not in data['active_threads']:
                print(f"Thread {thread_title} doesn't exist")
                reply_message = 'no threads'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            with open(f"{thread_title}", 'r') as thread:
                line = thread.readline().strip()
                # check if the user is the creator of the thread
                if line != username:
                    print('Thread cannot be deleted')
                    reply_message = 'invalid user'
                    connection_socket.send(reply_message.encode('utf-8'))
                    thread.close()
                    thread_lock.release()
                    continue
                thread.close()
            data['active_threads'].remove(thread_title)
            # delete all the files uploaded to this thread
            with open(f"{thread_title}", 'r') as thread:
                lines = thread.readlines()
                for line in lines[1:]:
                    line = line.split()
                    if line[1] == 'uploaded':
                        os.remove(f"{thread_title}-{line[2]}")
            # delete the thread
            os.remove(f"{thread_title}")
            print(f"Thread {thread_title} removed")
            reply_message = 'deleted successfully'
            connection_socket.send(reply_message.encode('utf-8'))
            thread_lock.release()
        elif request == 'SHT':
            # Shutdown
            print(f"{username} issued SHT command")
            reply_message = 'admin_passwd'
            connection_socket.send(reply_message.encode('utf-8'))
            provided_passwd = connection_socket.recv(1024).decode('utf-8')
            # check if the provided password matches the admin_passwd
            if provided_passwd != admin_passwd:
                print('password is incorrect')
                reply_message = 'incorrect password'
                connection_socket.send(reply_message.encode('utf-8'))
                thread_lock.release()
                continue
            reply_message = 'shutdown'
            connection_socket.send(reply_message.encode('utf-8'))
            # delete all the threads as well as the files uploaded to them and
            # delete credentials file
            for thread_title in data['active_threads']:
                with open(f"{thread_title}", 'r') as thread:
                    lines = thread.readlines()
                    for line in lines[1:]:
                        line = line.split()
                        if line[1] == 'uploaded':
                            os.remove(f"{thread_title}-{line[2]}")
                os.remove(f"{thread_title}")
            os.remove('credentials.txt')
            # close all the active sockets
            for each_socket in data['connected_sockets']:
                each_socket.close()
            thread_lock.release()
            data['server_shutdown'] = True
            break

# Loop to accept clients and creat new connection sockets
def client_accept():
    while True:
        # Create a connection socket.
        connection_socket, addr = server_socket.accept()
        # use a new thread to handle the clients' requests
        client_handle_thread = threading.Thread(target=client_handle, args=(connection_socket,))
        thread_lock.acquire()
        data['connected_sockets'].append(connection_socket)
        thread_lock.release()
        client_handle_thread.setDaemon(True)
        client_handle_thread.start()

if __name__ == '__main__':
    print("Waiting for clients")
    # use a new thread to accept new connection sockets
    accept_thread = threading.Thread(target=client_accept)
    accept_thread.setDaemon(True)
    accept_thread.start()
    # The main thread loops and shutdown when required
    while True:
        if data['server_shutdown']:
            print('Server shutting down')
            break
