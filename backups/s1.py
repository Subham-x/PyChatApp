import socket, threading, random

# ---------- COLORS ----------
COLORS = [
    "\033[91m",  # red
    "\033[92m",  # green
    "\033[93m",  # yellow
    "\033[94m",  # blue
    "\033[95m",  # magenta
    "\033[96m",  # cyan
]
RESET = "\033[0m"
color_enabled = True

# ---------- SERVER SETUP ----------
print("1) Localhost (same PC)")
print("2) LAN / Internet")
mode = input("Select mode (1/2): ").strip()

HOST = "127.0.0.1" if mode == "1" else "0.0.0.0"
PORT = 5000

server_name = input("Server name: ")
PIN = input("Set PIN: ")

clients = {}      # conn -> name
user_colors = {}  # name -> color
banned = set()

# ---------- FUNCTIONS ----------
def broadcast(msg):
    for c in list(clients):
        try:
            c.send(msg)
        except:
            remove_client(c)

def remove_client(conn):
    name = clients.get(conn)
    if name:
        del user_colors[name]
        del clients[conn]
        broadcast(f"{name} left the chat\n".encode())
    conn.close()

def handle_client(conn):
    conn.send(b"Enter your name: ")
    name = conn.recv(1024).decode().strip()

    if name in banned:
        conn.send(b"You are banned.\n")
        conn.close()
        return

    conn.send(b"Enter PIN: ")
    if conn.recv(1024).decode().strip() != PIN:
        conn.send(b"Wrong PIN.\n")
        conn.close()
        return

    clients[conn] = name
    user_colors[name] = random.choice(COLORS)

    broadcast(f"{name} joined the chat\n".encode())
    print(f"{name} connected")

    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            color = user_colors[name] if color_enabled else ""
            reset = RESET if color_enabled else ""
            text = f"{color}{name}: {msg}{reset}"

            print(text.strip())
            broadcast(text.encode())
        except:
            break

    remove_client(conn)

def server_commands():
    global color_enabled
    while True:
        cmd = input().strip()

        if cmd == "/color off":
            color_enabled = False
            print("Colors disabled")

        elif cmd == "/color on":
            color_enabled = True
            print("Colors enabled")

        elif cmd.startswith("/ban "):
            name = cmd.split(" ", 1)[1]
            banned.add(name)
            for c, n in list(clients.items()):
                if n == name:
                    c.send(b"You are banned.\n")
                    remove_client(c)
            print(f"{name} banned")

        else:
            print("Commands: /color on | /color off | /ban <name>")

# ---------- START ----------
s = socket.socket()
s.bind((HOST, PORT))
s.listen()

print(f"{server_name} running on {HOST}:{PORT}")

threading.Thread(target=server_commands, daemon=True).start()

while True:
    conn, _ = s.accept()
    threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
