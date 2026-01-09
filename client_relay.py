import socket, threading, time, os, platform
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import hashlib
import re

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
ORANGE = "\033[93m"
BLUE = "\033[96m"

clear_console()

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}    PyChat Client - Connect to Any Server{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

# Default relay server (change this to your VPS IP after deployment)
DEFAULT_RELAY = "127.0.0.1"  # For testing locally
# DEFAULT_RELAY = "your-vps-ip-here"  # Change this when deploying

print(f"{GREEN}[Centralized Relay System]{RESET}")
print(f"{ORANGE}No need to know server IP - just enter Server Name!{RESET}\n")

custom_ip = input(f"{BLUE}Relay IP [{DEFAULT_RELAY}]: {RESET}").strip()
RELAY_IP = custom_ip if custom_ip else DEFAULT_RELAY
PORT = 5000

PIN = ""
connected = False
input_enabled = False
username = ""
server_name = ""

def get_key_from_pin(pin):
    return hashlib.sha256(pin.encode()).digest()[:16]

def encrypt_message(message, pin):
    try:
        if not message or not pin:
            return message
        key = get_key_from_pin(pin)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode()) + padder.finalize()
        
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode()
    except Exception as e:
        print(f"{RED}[Encryption error: {str(e)}]{RESET}")
        return None

def decrypt_message(encrypted_message, pin):
    try:
        if not encrypted_message or not pin:
            return encrypted_message
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
    except Exception:
        return None

# Connect to relay
s = socket.socket()
try:
    print(f"{BLUE}[Connecting to relay {RELAY_IP}:{PORT}...]{RESET}")
    s.connect((RELAY_IP, PORT))
    print(f"{GREEN}[Connected to relay]{RESET}\n")
except Exception as e:
    print(f"\n{RED}[CONNECTION FAILED]{RESET}")
    print(f"{RED}Error: {str(e)}{RESET}\n")
    print(f"{ORANGE}[SOLUTION]{RESET}")
    print("1. Make sure the relay server is running")
    print(f"2. Run: {BLUE}python relay_server.py{RESET} on your VPS or locally")
    print(f"3. Check if relay IP ({RELAY_IP}) is correct\n")
    input("Press Enter to exit...")
    exit(1)

def receive():
    global PIN, connected, input_enabled, username, server_name
    while True:
        try:
            data = s.recv(4096).decode()
            if not data:
                print(f"\n{RED}[Disconnected from relay]{RESET}")
                break

            if data == "SERVER_NAME\n":
                print(f"{GREEN}{'='*60}{RESET}")
                print(f"{GREEN}Step 1: Enter Server Name{RESET}")
                print(f"{GREEN}{'='*60}{RESET}\n")
                print(f"{ORANGE}(Think of this as your private server - like 'MyGaming' or 'WorkTeam'){RESET}")
                server_name = input(f"{BLUE}Server Name: {RESET}")
                if not server_name.strip():
                    print(f"{RED}[Server name cannot be empty]{RESET}")
                    s.close()
                    break
                s.send(server_name.encode())
                
            elif data == "INVALID_SERVER\n":
                print(f"\n{RED}[ERROR: Invalid server name]{RESET}")
                s.close()
                break
                
            elif data == "PIN\n":
                print(f"\n{ORANGE}(If server doesn't exist, it will be created){RESET}")
                print(f"{ORANGE}(Share this PIN only with trusted users){RESET}")
                pin_input = input(f"{BLUE}Server PIN: {RESET}")
                if not pin_input.strip():
                    print(f"{RED}[PIN cannot be empty]{RESET}")
                    s.close()
                    break
                PIN = pin_input
                s.send(PIN.encode())
                
            elif data == "INVALID_PIN\n":
                print(f"\n{RED}[ERROR: Invalid PIN]{RESET}")
                s.close()
                break
                
            elif data == "USERNAME\n":
                print()
                name = input(f"{BLUE}Your Username: {RESET}")
                if not name.strip():
                    print(f"{RED}[Username cannot be empty]{RESET}")
                    s.close()
                    break
                username = name
                s.send(username.encode())
                
            elif data == "INVALID_USERNAME\n":
                print(f"\n{RED}[ERROR: Invalid username]{RESET}")
                s.close()
                break
            
            elif data == "USERNAME_TAKEN\n":
                print(f"\n{RED}[ERROR: Username already in use in this server]{RESET}")
                s.close()
                break
                
            else:
                if not connected:
                    connected = True
                    input_enabled = True
                    print(f"\n{GREEN}[Connected to server: {server_name}]{RESET}")
                    print(f"{GREEN}[Encryption active with your PIN]{RESET}\n")
                
                lines = data.split("\n")
                for line in lines:
                    if line.strip():
                        decrypted = decrypt_message(line.strip(), PIN)
                        if decrypted:
                            plain_text = re.sub(r'\033\[[0-9;]+m', '', decrypted)
                            
                            if plain_text.startswith(f"{username}: "):
                                message_text = plain_text[len(username) + 2:]
                                print(f"You: {message_text}")
                            else:
                                print(decrypted)
                        else:
                            if "joined" in line:
                                print(f"{ORANGE}{line}{RESET}")
                            elif "left" in line or "banned" in line.lower():
                                print(f"{RED}{line}{RESET}")
                            else:
                                print(line)
                            
        except ConnectionResetError:
            print(f"\n{RED}[Connection lost]{RESET}")
            break
        except Exception as e:
            print(f"\n{RED}[Error: {str(e)}]{RESET}")
            break
    
    input_enabled = False

threading.Thread(target=receive, daemon=True).start()

while not input_enabled:
    time.sleep(0.1)

# Main input loop
while True:
    try:
        msg = input()
        
        if not input_enabled:
            print(f"{RED}[Not connected]{RESET}")
            break
            
        if not msg.strip():
            continue
        
        # Format with username and encrypt
        formatted_msg = f"{username}: {msg}"
        if PIN:
            encrypted_msg = encrypt_message(formatted_msg, PIN)
            if encrypted_msg:
                s.send(encrypted_msg.encode())
            else:
                print(f"{RED}[Failed to encrypt message]{RESET}")
        else:
            print(f"{RED}[No PIN available]{RESET}")
            break
            
    except KeyboardInterrupt:
        print(f"\n{ORANGE}[Disconnecting...]{RESET}")
        break
    except Exception as e:
        print(f"\n{RED}[Error: {str(e)}]{RESET}")
        break

try:
    s.close()
except:
    pass
