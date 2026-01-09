import socket, threading, os, platform
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import hashlib

def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

SERVER_IP = "127.0.0.1"
PORT = 5000

clear_console()

PIN = ""
connected = False
input_enabled = False
my_name = ""

# Color codes
RESET = "\033[0m"
RED = "\033[91m"
ORANGE = "\033[93m"

# Generate encryption key from PIN
def get_key_from_pin(pin):
    return hashlib.sha256(pin.encode()).digest()[:16]  # AES-128 needs 16 bytes

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
        print(f"[Encryption error: {str(e)}]")
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

s = socket.socket()
try:
    s.connect((SERVER_IP, PORT))
    print("Connected to server")
except Exception as e:
    print(f"Connection failed: {str(e)}")
    exit(1)

def receive():
    global PIN, connected, input_enabled, my_name
    while True:
        try:
            data = s.recv(4096).decode()  # Increased buffer for encrypted data
            if not data:
                print(f"\n{RED}[Disconnected from server]{RESET}")
                break

            if data == "NAME\n":
                name = input("Your name: ")
                if not name.strip():
                    print(f"{RED}[Name cannot be empty]{RESET}")
                    s.close()
                    break
                my_name = name
                s.send(name.encode())
                
            elif data == "PIN\n":
                pin_input = input("PIN: ")
                if not pin_input.strip():
                    print(f"{RED}[PIN cannot be empty]{RESET}")
                    s.close()
                    break
                PIN = pin_input
                s.send(PIN.encode())
                
            elif data == "WRONG_PIN\n":
                print(f"\n{RED}[ERROR: Wrong PIN - Connection closed]{RESET}")
                s.close()
                break
                
            elif data == "BANNED\n":
                print(f"\n{RED}[ERROR: You are banned from this server]{RESET}")
                s.close()
                break
                
            else:
                # Connection established, enable input
                if not connected:
                    connected = True
                    input_enabled = True
                    print("[Encryption active - You can now send messages]\n")
                
                # Try to decrypt if it looks like encrypted data
                lines = data.split("\n")
                for line in lines:
                    if line.strip():
                        decrypted = decrypt_message(line.strip(), PIN)
                        if decrypted:
                            # Remove color codes to check username
                            import re
                            plain_text = re.sub(r'\033\[[0-9;]+m', '', decrypted)
                            
                            # Check if this is the user's own message
                            if plain_text.startswith(f"{my_name}: "):
                                # Extract message after name
                                message_text = plain_text[len(my_name) + 2:]
                                print(f"You: {message_text}")
                            else:
                                # Display with colors from server
                                print(decrypted)
                        else:
                            # Not encrypted, handle system messages
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
import time
while not input_enabled:
    time.sleep(0.1)

while True:
    try:
        msg = input()
        
        # Check if still connected
        if not input_enabled:
            print(f"{RED}[Not connected]{RESET}")
            break
            
        # Skip empty messages
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
            print(f"{RED}[No PIN available - cannot send encrypted message]{RESET}")
            break
            
    except KeyboardInterrupt:
        print(f"\n{ORANGE}[Disconnecting...]{RESET}")
        break
    except Exception as e:
        print(f"\n{RED}[Error sending message: {str(e)}]{RESET}")
        break

try:
    s.close()
except:
    pass
