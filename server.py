import socket, threading, random, os, platform
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import hashlib

# ---------- console clear ----------
def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

print("Starting server...")
input("Press Enter to continue...")
clear_console()
# ----------------------------------

PORT = 5000

print("Select server mode:")
print("1. Localhost (same PC)")
print("2. LAN (same network)")
print("3. Internet (public IP)")
mode = input("Choice (1/2/3): ")

HOST = {
    "1": "127.0.0.1",
    "2": "0.0.0.0",
    "3": "0.0.0.0"
}.get(mode, "0.0.0.0")

server_name = input("Server name: ").strip()
if not server_name:
    server_name = "PyChat Server"
    
PIN = input("Set PIN: ").strip()
while not PIN:
    print("PIN cannot be empty!")
    PIN = input("Set PIN: ").strip()
    
print(f"\n[Server configured with AES-128 encryption]")
print(f"[All messages will be encrypted end-to-end]\n")

# Generate encryption key from PIN
def get_key_from_pin(pin):
    return hashlib.sha256(pin.encode()).digest()[:16]  # AES-128 needs 16 bytes

def encrypt_message(message, pin):
    try:
        if not message or not pin:
            return None
        key = get_key_from_pin(pin)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()
    except Exception as e:
        print(f"[Server encryption error: {str(e)}]")
        return None

def decrypt_message(encrypted_message, pin):
    try:
        if not encrypted_message or not pin:
            return None
        key = get_key_from_pin(pin)
        data = base64.b64decode(encrypted_message)
        
        if len(data) < 16:
            return None
            
        iv = data[:16]
        encrypted = data[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        message = unpadder.update(padded_data) + unpadder.finalize()
        return message.decode()
    except Exception as e:
        return None

colors_enabled = True
clients = {}          # conn : (name, color)
banned = set()
used_colors = []      # Track colors in use

COLORS = [
    "\033[91m", "\033[92m", "\033[93m",
    "\033[94m", "\033[95m", "\033[96m"
]
RESET = "\033[0m"

def get_unique_color():
    """Get a unique color for a new client"""
    for color in COLORS:
        if color not in used_colors:
            used_colors.append(color)
            return color
    # If all colors used, reuse from start
    color = COLORS[len(used_colors) % len(COLORS)]
    used_colors.append(color)
    return color

def release_color(color):
    """Release a color when client disconnects"""
    if color in used_colors:
        used_colors.remove(color)

def broadcast(msg, sender=None):
    for c in list(clients):
        if c != sender:
            try:
                c.send(msg)
            except:
                pass

def handle_client(conn, addr):
    name = "Unknown"
    try:
        conn.send(b"NAME\n")
        name_data = conn.recv(1024)
        if not name_data:
            conn.close()
            return
            
        name = name_data.decode().strip()
        
        # Validate name
        if not name or len(name) > 50:
            conn.send(b"Invalid name\n")
            conn.close()
            return

        if name in banned:
            conn.send(b"BANNED\n")
            conn.close()
            return

        conn.send(b"PIN\n")
        pin_data = conn.recv(1024)
        if not pin_data:
            conn.close()
            return
            
        pin = pin_data.decode().strip()
        
        # Validate PIN
        if not pin:
            conn.send(b"Invalid PIN\n")
            conn.close()
            return
            
        if pin != PIN:
            conn.send(b"WRONG_PIN\n")
            conn.close()
            print(f"Failed login attempt: {name} (wrong PIN)")
            return

        color = get_unique_color()
        clients[conn] = (name, color)

        header = f"\n=== {server_name} ===\n\033[93m---- Chat is end to end encrypted, until PIN is exposed ----\033[0m\n"
        conn.send(header.encode())

        join_msg = f"\033[93m{name} joined\033[0m\n"
        print(join_msg.strip())
        broadcast(join_msg.encode())

        while True:
            try:
                msg = conn.recv(4096)  # Increased buffer for encrypted data
                if not msg:
                    break

                encrypted_text = msg.decode().strip()
                
                # Skip empty messages
                if not encrypted_text:
                    continue
                
                # Decrypt message
                text = decrypt_message(encrypted_text, PIN)
                if text is None:
                    text = "[Decryption failed - possible wrong PIN or corrupted data]"
                
                if colors_enabled:
                    out = f"{color}{name}: {text}{RESET}\n"
                else:
                    out = f"{name}: {text}\n"

                print(out.strip())
                
                # Encrypt before broadcasting WITH colors
                if colors_enabled:
                    broadcast_msg = f"{color}{name}: {text}{RESET}"
                else:
                    broadcast_msg = f"{name}: {text}"
                    
                encrypted_out = encrypt_message(broadcast_msg, PIN)
                if encrypted_out:
                    broadcast((encrypted_out + "\n").encode(), conn)
                else:
                    print(f"[Failed to encrypt message from {name}]")
                    
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[Error handling message from {name}: {str(e)}]")
                break

    except Exception as e:
        print(f"[Error with client {name}: {str(e)}]")
    finally:
        print(f"\033[91m{name} left\033[0m")
        if conn in clients:
            # Release the color back to pool
            _, color = clients[conn]
            release_color(color)
            del clients[conn]
        try:
            conn.close()
        except:
            pass
        broadcast(f"\033[91m{name} left\033[0m\n".encode())

def server_commands():
    global colors_enabled
    while True:
        cmd = input()
        if cmd == "/colors off":
            colors_enabled = False
            print("Colors disabled")
        elif cmd == "/colors on":
            colors_enabled = True
            print("Colors enabled")
        elif cmd.startswith("/ban "):
            name = cmd.split(" ", 1)[1]
            banned.add(name)
            for c, v in list(clients.items()):
                if v[0] == name:
                    # Send ban message to the banned user only
                    c.send(b"\033[91m\nYou are banned.\033[0m\n")
                    c.close()
                    # Release the color
                    _, color = v
                    release_color(color)
                    del clients[c]
                    # Broadcast to others that user left (not banned)
                    broadcast(f"\033[91m{name} left\033[0m\n".encode())
                    break
            print(f"Banned {name}")
        elif cmd == "/exit":
            print("\n\033[91m[Shutting down server...]\033[0m")
            # Notify all clients in red
            shutdown_msg = b"\033[91m[Server is shutting down]\033[0m\n"
            for c in list(clients):
                try:
                    c.send(shutdown_msg)
                    c.close()
                except:
                    pass
            print("\033[91m[Server stopped]\033[0m")
            os._exit(0)

s = socket.socket()
try:
    s.bind((HOST, PORT))
    s.listen()
    print(f"{server_name} running on {HOST}:{PORT}")
    print("Waiting for connections...\n")
except Exception as e:
    print(f"Failed to start server: {str(e)}")
    exit(1)

threading.Thread(target=server_commands, daemon=True).start()

try:
    while True:
        conn, addr = s.accept()
        print(f"[Connection from {addr[0]}:{addr[1]}]")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("\n[Server shutting down...]")
    s.close()
except Exception as e:
    print(f"\n[Server error: {str(e)}]")
    s.close()
