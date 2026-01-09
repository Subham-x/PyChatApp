# PyChat - Centralized Relay System

## 🎯 New Architecture

Instead of needing to know IP addresses, all users connect to ONE central relay server!

```
         Central Relay (VPS)
              xxx.xxx.018
                   ↓
    ┌──────────────┼──────────────┐
    ↓              ↓              ↓
Server: "Gaming"  Server: "Work"  Server: "Family"
 User1, User2     User3, User4    User5, User6
```

## 🚀 Quick Start

### Step 1: Deploy Relay Server (ONE TIME)

**Option A: Free VPS (Recommended)**
1. Get free Oracle Cloud VM
2. Upload `relay_server.py`
3. Run: `python relay_server.py`
4. Note the public IP (e.g., 103.182.10.147)

**Option B: Test Locally**
1. Run `start_relay.bat`
2. Keep it running

### Step 2: Connect as User (EVERYONE)

1. Run `start_client_relay.bat`
2. Enter relay IP (or press Enter for localhost)
3. Enter **Server Name** (e.g., "MyGaming")
4. Enter **PIN** (e.g., "secret123")
5. Enter **Username** (e.g., "Alice")
6. Start chatting!

## 🎮 How It Works

### Server Name
- Acts as your "virtual server"
- Anyone with same name + PIN joins same chat room
- Example: "FriendGroup", "WorkTeam", "Gaming"

### PIN
- Access key to your server
- Encrypts all messages (AES-128)
- Only people with correct PIN can decrypt
- **Keep it secret!**

### Username
- Your display name in the server
- Must be unique within each server
- Can be same across different servers

## 📝 Example Usage

**User 1 (Alice):**
```
Relay IP: 103.182.10.147
Server Name: MyFriends
PIN: secret123
Username: Alice
```

**User 2 (Bob):**
```
Relay IP: 103.182.10.147
Server Name: MyFriends
PIN: secret123
Username: Bob
```

✅ Alice and Bob can now chat!

**User 3 (Charlie):**
```
Relay IP: 103.182.10.147
Server Name: WorkTeam
PIN: work456
Username: Charlie
```

❌ Charlie is in a different server - cannot see Alice/Bob's messages

## 🔒 Security

- **End-to-End Encryption**: Messages encrypted with PIN
- **Relay cannot read**: Server just forwards encrypted data
- **Wrong PIN**: Cannot decrypt messages (see garbage text)
- **Unique PIN**: Use different PINs for different servers

## ⚙️ Files

### New Relay System:
- `relay_server.py` - Central relay (run on VPS)
- `client_relay.py` - Client for relay system
- `start_relay.bat` - Start relay server
- `start_client_relay.bat` - Start client

### Old P2P System (still works):
- `server_multichannel.py` - Direct server
- `client_multichannel.py` - Direct client
- `start_server.bat` - Start direct server
- `start_client.bat` - Start direct client

## 🎯 Advantages

✅ **No IP hassle**: Just enter server name
✅ **No port forwarding**: Relay handles everything
✅ **Easy sharing**: Just share server name + PIN
✅ **Multiple servers**: Create unlimited virtual servers
✅ **Same interface**: All users use same relay IP

## 🌐 Deployment Options

### Free Hosting for Relay:
1. **Oracle Cloud** - Forever free tier
2. **AWS EC2** - 12 months free
3. **Google Cloud** - Free tier
4. **Railway.app** - Free tier with credit

### Domain (Optional):
Instead of `103.182.10.147`, use `chat.yourdomain.com`

## 🔧 Relay Server Commands

Type in relay terminal:
- `/servers` - List active servers
- `/stats` - Show statistics
- `/help` - Show help
- `/exit` - Shutdown relay

## ❓ FAQ

**Q: Do I need to run server.py?**
A: No! With relay system, only the relay server runs. Users just connect with client.

**Q: Can two people create same Server Name?**
A: Yes, but if PINs are different, they're in separate rooms.

**Q: What if someone guesses my Server Name?**
A: They still need your PIN to decrypt messages.

**Q: How many users per server?**
A: Unlimited (depends on relay server capacity).

**Q: Can I run relay on my PC?**
A: Yes for testing, but need port forwarding for others to connect.

## 🎨 Next Features (TODO)

- [ ] Add /ban command to relay
- [ ] Server owner permissions
- [ ] Server description/MOTD
- [ ] User list command
- [ ] Private messages
- [ ] File sharing
