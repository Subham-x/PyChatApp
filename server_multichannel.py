import socket, threading, random, os, platform, time
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import hashlib
import urllib.request

# ---------- console clear ----------
def clear_console():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

print("Starting Multi-Channel PyChat Server...")
print("=" * 50)
# ----------------------------------

PORT = 5000

print("\nSelect server mode:")
print("1. Localhost (same PC)")
print("2. LAN (same network)")
print("3. Internet (public IP)")
mode = input("Choice (1/2/3): ").strip() or "1"

HOST = {
    "1": "127.0.0.1",
    "2": "0.0.0.0",
    "3": "0.0.0.0"
}.get(mode, "0.0.0.0")

# Get and display IPs with easy sharing format
if mode == "1":
    share_ip = "127.0.0.1"
    print(f"\n\033[96m{'='*50}\033[0m")
    print(f"\033[96m           LOCALHOST MODE\033[0m")
    print(f"\033[96m{'='*50}\033[0m")
    print(f"\n\033[93m  Share this IP with clients on SAME PC:\033[0m")
    print(f"\n  ┌{'─'*46}┐")
    print(f"  │  \033[92m{share_ip:^44}\033[0m  │")
    print(f"  └{'─'*46}┘\n")
elif mode == "2":
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        share_ip = local_ip
        print(f"\n\033[96m{'='*50}\033[0m")
        print(f"\033[96m           LAN MODE (Same WiFi/Network)\033[0m")
        print(f"\033[96m{'='*50}\033[0m")
        print(f"\n\033[93m  Share this IP with clients on SAME NETWORK:\033[0m")
        print(f"\n  ┌{'─'*46}┐")
        print(f"  │  \033[92m{share_ip:^44}\033[0m  │")
        print(f"  └{'─'*46}┘\n")
        print(f"\033[90m  (All devices must be on same WiFi)\033[0m\n")
    except Exception as e:
        print(f"\n\033[91m[Could not get local IP: {str(e)}]\033[0m")
        share_ip = "Unknown"
elif mode == "3":
    print(f"\n\033[96m[Fetching your public IP...]\033[0m")
    try:
        public_ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
        share_ip = public_ip
        print(f"\n\033[96m{'='*50}\033[0m")
        print(f"\033[96m           INTERNET MODE\033[0m")
        print(f"\033[96m{'='*50}\033[0m")
        print(f"\n\033[93m  Share this IP with clients ANYWHERE:\033[0m")
        print(f"\n  ┌{'─'*46}┐")
        print(f"  │  \033[92m{share_ip:^44}\033[0m  │")
        print(f"  └{'─'*46}┘\n")
        print(f"\033[91m  ⚠ IMPORTANT: Port forward port {PORT} in your router!\033[0m")
        print(f"\033[90m  (Router settings → Port Forwarding → TCP {PORT})\033[0m\n")
    except Exception as e:
        print(f"\n\033[91m[Could not fetch public IP: {str(e)}]\033[0m")
        print(f"\033[93m[Find your IP at: https://whatismyip.com]\033[0m")
        share_ip = "Unknown"

print(f"\n[Server configured with AES-128 encryption]")
print(f"[Multi-channel support enabled]")
print(f"[Channels are created automatically when first user joins]\n")

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

# Color pool
COLORS = [
    "\033[91m", "\033[92m", "\033[93m",
    "\033[94m", "\033[95m", "\033[96m"
]
RESET = "\033[0m"

# Multi-channel structure
channels = {}  # channel_key: {name, pin, clients, banned, used_colors, colors_enabled}
channels_lock = threading.Lock()

def get_channel_key(channel_name, pin):
    """Generate unique key for channel"""
    return hashlib.sha256(f"{channel_name}:{pin}".encode()).hexdigest()[:16]

def create_or_get_channel(channel_name, pin):
    """Create channel if doesn't exist, or return existing one"""
    channel_key = get_channel_key(channel_name, pin)
    
    with channels_lock:
        if channel_key not in channels:
            channels[channel_key] = {
                'name': channel_name,
                'pin': pin,
                'clients': {},  # conn: (name, color)
                'banned': set(),
                'used_colors': [],
                'colors_enabled': True,
                'created_at': time.time()
            }
            print(f"\033[92m[NEW CHANNEL] '{channel_name}' created\033[0m")
        return channels[channel_key]

def get_unique_color(channel):
    """Get a unique color for a client in a channel"""
    used_colors = channel['used_colors']
    for color in COLORS:
        if color not in used_colors:
            used_colors.append(color)
            return color
    # If all colors used, reuse from start
    color = COLORS[len(used_colors) % len(COLORS)]
    used_colors.append(color)
    return color

def release_color(channel, color):
    """Release a color when client disconnects"""
    if color in channel['used_colors']:
        channel['used_colors'].remove(color)

def broadcast(channel, msg, sender=None):
    """Broadcast message to all clients in a channel"""
    for c in list(channel['clients']):
        if c != sender:
            try:
                c.send(msg)
            except:
                pass

def handle_client(conn, addr):
    channel = None
    name = "Unknown"
    color = None
    
    try:
        # Get channel name
        conn.send(b"CHANNEL_NAME\n")
        channel_data = conn.recv(1024)
        if not channel_data:
            conn.close()
            return
            
        channel_name = channel_data.decode().strip()
        
        if not channel_name or len(channel_name) > 50:
            conn.send(b"INVALID_CHANNEL\n")
            conn.close()
            return
        
        # Get PIN
        conn.send(b"PIN\n")
        pin_data = conn.recv(1024)
        if not pin_data:
            conn.close()
            return
            
        pin = pin_data.decode().strip()
        
        if not pin:
            conn.send(b"INVALID_PIN\n")
            conn.close()
            return
        
        # Create or join channel
        channel = create_or_get_channel(channel_name, pin)
        
        # Get user name
        conn.send(b"NAME\n")
        name_data = conn.recv(1024)
        if not name_data:
            conn.close()
            return
            
        name = name_data.decode().strip()
        
        if not name or len(name) > 50:
            conn.send(b"INVALID_NAME\n")
            conn.close()
            return

        if name in channel['banned']:
            conn.send(b"BANNED\n")
            conn.close()
            return

        # Assign color and add to channel
        color = get_unique_color(channel)
        channel['clients'][conn] = (name, color)

        # Send welcome header
        header = f"\n=== {channel_name} ===\n\033[93m---- Chat is end to end encrypted, until PIN is exposed ----\033[0m\n"
        conn.send(header.encode())

        # Broadcast join message
        join_msg = f"\033[93m{name} joined\033[0m\n"
        print(f"[{channel_name}] {name} joined")
        broadcast(channel, join_msg.encode())

        # Handle messages
        while True:
            try:
                msg = conn.recv(4096)
                if not msg:
                    break

                encrypted_text = msg.decode().strip()
                
                if not encrypted_text:
                    continue
                
                # Decrypt message
                text = decrypt_message(encrypted_text, pin)
                if text is None:
                    text = "[Decryption failed]"
                
                # Handle /ban command
                if text.startswith("/ban "):
                    target_name = text[5:].strip()
                    if target_name:
                        # Add to banned list
                        channel['banned'].add(target_name)
                        ban_msg = f"\033[91m{target_name} has been banned by {name}\033[0m"
                        print(f"[{channel_name}] {ban_msg}")
                        
                        # Find and disconnect the banned user
                        for c, (uname, ucolor) in list(channel['clients'].items()):
                            if uname == target_name:
                                try:
                                    c.send(f"{ban_msg}\n".encode())
                                    c.send(b"BANNED\n")
                                    c.close()
                                except:
                                    pass
                                release_color(channel, ucolor)
                                del channel['clients'][c]
                                break
                        
                        # Broadcast ban message to all
                        broadcast(channel, f"{ban_msg}\n".encode())
                    continue
                
                # Format message with color
                if channel['colors_enabled']:
                    out = f"{color}{name}: {text}{RESET}\n"
                    broadcast_msg = f"{color}{name}: {text}{RESET}"
                else:
                    out = f"{name}: {text}\n"
                    broadcast_msg = f"{name}: {text}"

                print(f"[{channel_name}] {out.strip()}")
                
                # Encrypt and broadcast
                encrypted_out = encrypt_message(broadcast_msg, pin)
                if encrypted_out:
                    broadcast(channel, (encrypted_out + "\n").encode(), conn)
                    
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[{channel_name}] [Error with {name}: {str(e)}]")
                break

    except Exception as e:
        print(f"[Error with client: {str(e)}]")
    finally:
        if channel and conn in channel['clients']:
            print(f"[{channel['name']}] \033[91m{name} left\033[0m")
            release_color(channel, color)
            del channel['clients'][conn]
            broadcast(channel, f"\033[91m{name} left\033[0m\n".encode())
            
            # Remove empty channels after 1 minute of inactivity
            if len(channel['clients']) == 0:
                channel_key = get_channel_key(channel['name'], channel['pin'])
                threading.Timer(60, lambda: cleanup_empty_channel(channel_key)).start()
        
        try:
            conn.close()
        except:
            pass

def cleanup_empty_channel(channel_key):
    """Remove empty channels after timeout"""
    with channels_lock:
        if channel_key in channels and len(channels[channel_key]['clients']) == 0:
            channel_name = channels[channel_key]['name']
            del channels[channel_key]
            print(f"\033[90m[CLEANUP] Channel '{channel_name}' removed (inactive)\033[0m")

def server_commands():
    """Server admin commands"""
    while True:
        cmd = input()
        if cmd == "/channels":
            with channels_lock:
                if not channels:
                    print("\033[90mNo active channels\033[0m")
                else:
                    print(f"\n\033[96m{'='*50}\033[0m")
                    print(f"\033[96mActive Channels: {len(channels)}\033[0m")
                    print(f"\033[96m{'='*50}\033[0m")
                    for ch_key, ch in channels.items():
                        print(f"\n  Channel: \033[93m{ch['name']}\033[0m")
                        print(f"  Users: {len(ch['clients'])}")
                        if ch['clients']:
                            for conn, (uname, ucolor) in ch['clients'].items():
                                print(f"    - {ucolor}{uname}{RESET}")
                    print(f"\033[96m{'='*50}\033[0m\n")
                    
        elif cmd == "/stats":
            with channels_lock:
                total_users = sum(len(ch['clients']) for ch in channels.values())
                print(f"\n\033[96mServer Statistics:\033[0m")
                print(f"  Total Channels: {len(channels)}")
                print(f"  Total Users: {total_users}\n")
                
        elif cmd == "/exit":
            print("\n\033[91m[Shutting down server...]\033[0m")
            shutdown_msg = b"\033[91m[Server is shutting down]\033[0m\n"
            with channels_lock:
                for channel in channels.values():
                    for c in list(channel['clients']):
                        try:
                            c.send(shutdown_msg)
                            c.close()
                        except:
                            pass
            print("\033[91m[Server stopped]\033[0m")
            os._exit(0)
            
        elif cmd == "/help":
            print("\n\033[96mServer Commands:\033[0m")
            print("  /channels - List all active channels and users")
            print("  /stats    - Show server statistics")
            print("  /help     - Show this help")
            print("  /exit     - Shutdown server\n")
            print("\033[96mUser Commands (in chat):\033[0m")
            print("  /ban <username> - Ban a user from the channel\n")

# Start server
s = socket.socket()
try:
    s.bind((HOST, PORT))
    s.listen()
    print(f"\033[92m{'='*50}\033[0m")
    print(f"\033[92mMulti-Channel PyChat Server\033[0m")
    print(f"\033[92mRunning on {HOST}:{PORT}\033[0m")
    print(f"\033[92m{'='*50}\033[0m")
    print("\nType /help for server commands\n")
except Exception as e:
    print(f"\033[91mFailed to start server: {str(e)}\033[0m")
    exit(1)

threading.Thread(target=server_commands, daemon=True).start()

try:
    while True:
        conn, addr = s.accept()
        print(f"[Connection from {addr[0]}:{addr[1]}]")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("\n\033[91m[Server shutting down...]\033[0m")
    s.close()
except Exception as e:
    print(f"\n\033[91m[Server error: {str(e)}]\033[0m")
    s.close()
