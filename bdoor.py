#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import socket
import getopt
import threading
import subprocess


# define some global variables
listen             = False
command            = False
upload             = False
execute            = ""
target             = ""
upload_destination = ""
port               = 0


def usage():
    print "BHP Net Tool"
    print
    print "Usage:CMD -t target_host -p port"
    print "-l --listen          - listen on [host]:[port] for incoming connections"
    print "-e --execute=file_to_run - execute the given file upon reveiving a connection"
    print "-c --command - initialize a command shell"
    print "-u --upload=destination -upon receiving connection upload a file and write to [destination]"

    print
    print
    print "Examples:"
    print "CMD -t 192.168.0.1 -p 555 -l -c"
    print "CMD -t 192.168.0.1 -p 555 -l -u=c:\\target.exe"
    print "CMD -t 192.168.0.1 -p 555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./CMD -t 192.168.0.1 -p 135"
    sys.exit(0)


def client_sender(buff):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((target, port))
        print "start connection"

        if len(buff):
            print "Senddata1:" + buff
            client.send(buff)

        while True:
            rec_len = 1
            response = ""

            while rec_len:
                data = client.recv(4096)
                rec_len = len(data)
                response += data

                if rec_len < 4096:
                    break

            print response,

            buff = raw_input("")
            buff += "\n"
            print "Senddata2:" + buff
            client.send(buff)
    except:
        print "[*] Exception! Exiting."
        client.close()


def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    return output


def client_handler(client_socket):
    global upload
    global execute
    global command
    global upload_destination

    if len(upload_destination):
        print "upload_file"
        file_buffer = ""

        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            else:
                file_buffer += data

        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    if len(execute):
        print "execute file"
        output = run_command(execute)
        client_socket.send(output)

    if command:
        print "run shell command"
        while True:
            client_socket.send("<CMD:#> ")
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            response = run_command(cmd_buffer)
            client_socket.send(response)


def server_loop():
    global target

    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        print "connection accepted form"
        print addr
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu",
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
            print "Listen Mode"
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
            print "Command Mode"
        elif o in ("-u", "--upload"):
            upload_destination = a
            print upload_destination
        elif o in ("-t", "--target"):
            target = a
            print target
        elif o in ("-p", "--port"):
            port = int(a)
            print port
        else:
            assert False, "Unhandled Option"

    if not listen and len(target) and port > 0:
        print "Client Mode"
        buff = sys.stdin.read()
        #buff = ""
        print buff
        client_sender(buff)

    if listen:
        print "Server Mode"
        server_loop()


main()
