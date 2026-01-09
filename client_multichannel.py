import socket, threading, os, platform, time
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

# Color codes
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
ORANGE = "\033[93m"
BLUE = "\033[96m"

clear_console()

print(f"{BLUE}{'='*50}{RESET}")
print(f"{BLUE}    PyChat Client - Multi-Channel Support{RESET}")
print(f"{BLUE}{'='*50}{RESET}\n")

print(f"{ORANGE}Step 1: Connect to Server{RESET}")
print(f"{ORANGE}(Press Enter to use localhost){RESET}\n")

SERVER_IP = input(f"{BLUE}Server IP address [127.0.0.1]: {RESET}").strip() or "127.0.0.1"
PORT = 5000

print(f"\n{ORANGE}Note: Channel name & PIN will be asked after connection{RESET}")

PIN = ""
connected = False
input_enabled = False
my_name = ""
channel_name = ""

# Generate encryption key from PIN
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

# Connect to server
s = socket.socket()
try:
    print(f"\n{BLUE}[Connecting to {SERVER_IP}:{PORT}...]{RESET}")
    s.connect((SERVER_IP, PORT))
    print(f"{GREEN}[Connected successfully]{RESET}\n")
except Exception as e:
    print(f"\n{RED}[CONNECTION FAILED]{RESET}")
    print(f"{RED}Error: {str(e)}{RESET}\n")
    print(f"{ORANGE}[SOLUTION]{RESET}")
    print("1. Make sure the server is running")
    print(f"2. Run: {BLUE}start_server.bat{RESET} or {BLUE}python server_multichannel.py{RESET}")
    print(f"3. Check if server IP ({SERVER_IP}) is correct\n")
    input("Press Enter to exit...")
    exit(1)

def receive():
    global PIN, connected, input_enabled, my_name, channel_name
    while True:
        try:
            data = s.recv(4096).decode()
            if not data:
                print(f"\n{RED}[Disconnected from server]{RESET}")
                break

            if data == "CHANNEL_NAME\n":
                print(f"\n{GREEN}{'='*50}{RESET}")
                print(f"{GREEN}Step 2: Join or Create Channel{RESET}")
                print(f"{GREEN}{'='*50}{RESET}\n")
                channel_name = input(f"{BLUE}Channel Name: {RESET}")
                if not channel_name.strip():
                    print(f"{RED}[Channel name cannot be empty]{RESET}")
                    s.close()
                    break
                s.send(channel_name.encode())
                
            elif data == "INVALID_CHANNEL\n":
                print(f"\n{RED}[ERROR: Invalid channel name]{RESET}")
                s.close()
                break
                
            elif data == "PIN\n":
                print(f"{ORANGE}(If channel doesn't exist, it will be created){RESET}")
                pin_input = input(f"{BLUE}Channel PIN: {RESET}")
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
                
            elif data == "NAME\n":
                print()
                name = input(f"{BLUE}Your Name: {RESET}")
                if not name.strip():
                    print(f"{RED}[Name cannot be empty]{RESET}")
                    s.close()
                    break
                my_name = name
                s.send(name.encode())
                
            elif data == "INVALID_NAME\n":
                print(f"\n{RED}[ERROR: Invalid name]{RESET}")
                s.close()
                break
                
            elif data == "WRONG_PIN\n":
                print(f"\n{RED}[ERROR: Wrong PIN - Connection closed]{RESET}")
                s.close()
                break
                
            elif data == "BANNED\n":
                print(f"\n{RED}[ERROR: You are banned from this channel]{RESET}")
                s.close()
                break
                
            else:
                # Connection established
                if not connected:
                    connected = True
                    input_enabled = True
                    print(f"\n{GREEN}[Connected to channel: {channel_name}]{RESET}")
                    print(f"{GREEN}[Encryption active - You can now send messages]{RESET}\n")
                
                # Process received messages
                lines = data.split("\n")
                for line in lines:
                    if line.strip():
                        decrypted = decrypt_message(line.strip(), PIN)
                        if decrypted:
                            # Remove color codes to check username
                            plain_text = re.sub(r'\033\[[0-9;]+m', '', decrypted)
                            
                            # Check if this is user's own message
                            if plain_text.startswith(f"{my_name}: "):
                                message_text = plain_text[len(my_name) + 2:]
                                print(f"You: {message_text}")
                            else:
                                # Display with colors from server
                                print(decrypted)
                        else:
                            # System messages (join/leave/ban)
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

# Wait for connection to be established
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
            
        # Encrypt and send
        if PIN:
            encrypted_msg = encrypt_message(msg, PIN)
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
