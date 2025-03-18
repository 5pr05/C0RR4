import socket

REMOTE_SERVER = "one.one.one.one"

internet = None


def is_connected(hostname):
    global internet
    try:
        host = socket.gethostbyname(hostname)
        s = socket.create_connection((host, 80), 2)
        s.close()
        internet = True
    except Exception:
        internet = False
