import socket, threading, time
from collections import defaultdict

# This is the CENTRAL RELAY SERVER
# Run this on a VPS/server with a public IP
# All users connect to THIS server

PORT = 5000
HOST = "0.0.0.0"

print("="*60)
print("  PyChat RELAY SERVER - Centralized Hub")
print("="*60)

# Structure: servers[server_name][pin] = {clients: {conn: name}, ...}
servers = defaultdict(lambda: defaultdict(lambda: {'clients': {}}))
servers_lock = threading.Lock()

def broadcast_in_server(server_name, pin, msg, sender=None):
    """Broadcast to all clients in a specific server+pin"""
    with servers_lock:
        if server_name in servers and pin in servers[server_name]:
            for conn in list(servers[server_name][pin]['clients']):
                if conn != sender:
                    try:
                        conn.send(msg)
                    except:
                        pass

def handle_client(conn, addr):
    server_name = ""
    pin = ""
    username = ""
    
    try:
        # Get Server Name
        conn.send(b"SERVER_NAME\n")
        data = conn.recv(1024)
        if not data:
            conn.close()
            return
        server_name = data.decode().strip()
        
        if not server_name or len(server_name) > 50:
            conn.send(b"INVALID_SERVER\n")
            conn.close()
            return
        
        # Get PIN
        conn.send(b"PIN\n")
        data = conn.recv(1024)
        if not data:
            conn.close()
            return
        pin = data.decode().strip()
        
        if not pin:
            conn.send(b"INVALID_PIN\n")
            conn.close()
            return
        
        # Get Username
        conn.send(b"USERNAME\n")
        data = conn.recv(1024)
        if not data:
            conn.close()
            return
        username = data.decode().strip()
        
        if not username or len(username) > 50:
            conn.send(b"INVALID_USERNAME\n")
            conn.close()
            return
        
        # Check if username already exists in this server
        with servers_lock:
            if username in [name for name in servers[server_name][pin]['clients'].values()]:
                conn.send(b"USERNAME_TAKEN\n")
                conn.close()
                return
            
            # Add to server
            servers[server_name][pin]['clients'][conn] = username
            
            # Check if this is a new server
            is_new = len(servers[server_name][pin]['clients']) == 1
        
        # Send welcome
        welcome = f"\n=== Server: {server_name} ===\n\033[93m---- Messages are encrypted with your PIN ----\033[0m\n"
        conn.send(welcome.encode())
        
        # Broadcast join
        join_msg = f"\033[93m{username} joined\033[0m\n"
        if is_new:
            print(f"\033[92m[NEW SERVER] '{server_name}' created by {username}\033[0m")
        else:
            print(f"[{server_name}] {username} joined")
        broadcast_in_server(server_name, pin, join_msg.encode())
        
        # Handle messages
        while True:
            msg = conn.recv(4096)
            if not msg:
                break
            
            # Relay the encrypted message to all others
            broadcast_in_server(server_name, pin, msg, conn)
            
    except Exception as e:
        print(f"[Error with {username}: {str(e)}]")
    finally:
        with servers_lock:
            if server_name and pin and conn in servers[server_name][pin]['clients']:
                print(f"[{server_name}] \033[91m{username} left\033[0m")
                del servers[server_name][pin]['clients'][conn]
                
                # Clean up empty servers
                if len(servers[server_name][pin]['clients']) == 0:
                    del servers[server_name][pin]
                    if len(servers[server_name]) == 0:
                        del servers[server_name]
                        print(f"\033[90m[CLEANUP] Server '{server_name}' removed\033[0m")
                else:
                    # Notify others
                    leave_msg = f"\033[91m{username} left\033[0m\n"
                    broadcast_in_server(server_name, pin, leave_msg.encode())
        
        try:
            conn.close()
        except:
            pass

def admin_commands():
    """Admin commands"""
    while True:
        cmd = input()
        if cmd == "/servers":
            with servers_lock:
                if not servers:
                    print("\033[90mNo active servers\033[0m")
                else:
                    print(f"\n\033[96m{'='*60}\033[0m")
                    print(f"\033[96mActive Servers: {len(servers)}\033[0m")
                    print(f"\033[96m{'='*60}\033[0m")
                    for srv_name, pins in servers.items():
                        total_users = sum(len(pin_data['clients']) for pin_data in pins.values())
                        print(f"\n  \033[93m{srv_name}\033[0m - {total_users} users")
                    print(f"\033[96m{'='*60}\033[0m\n")
        
        elif cmd == "/stats":
            with servers_lock:
                total_servers = len(servers)
                total_users = sum(
                    len(pin_data['clients']) 
                    for srv in servers.values() 
                    for pin_data in srv.values()
                )
                print(f"\n\033[96mRelay Statistics:\033[0m")
                print(f"  Active Servers: {total_servers}")
                print(f"  Total Users: {total_users}\n")
        
        elif cmd == "/help":
            print("\n\033[96mRelay Commands:\033[0m")
            print("  /servers - List all active servers")
            print("  /stats   - Show statistics")
            print("  /help    - Show this help")
            print("  /exit    - Shutdown relay\n")
        
        elif cmd == "/exit":
            print("\n\033[91m[Shutting down relay...]\033[0m")
            import os
            os._exit(0)

# Start relay server
s = socket.socket()
try:
    s.bind((HOST, PORT))
    s.listen()
    print(f"\n\033[92m{'='*60}\033[0m")
    print(f"\033[92mRelay Server Running on {HOST}:{PORT}\033[0m")
    print(f"\033[92m{'='*60}\033[0m")
    print("\nType /help for commands\n")
except Exception as e:
    print(f"\033[91mFailed to start relay: {str(e)}\033[0m")
    exit(1)

threading.Thread(target=admin_commands, daemon=True).start()

try:
    while True:
        conn, addr = s.accept()
        print(f"[Connection from {addr[0]}:{addr[1]}]")
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
except KeyboardInterrupt:
    print("\n\033[91m[Relay shutting down...]\033[0m")
    s.close()
