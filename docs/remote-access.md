# Remote access (Fernzugriff)

How to reach the robot's web page from outside the flat, without opening any port on the router.

## Approach

[Tailscale](https://tailscale.com) (WireGuard-based private VPN, free Personal plan) runs in a small LXC container on the home Proxmox server. The container is a **subnet router**: it shares the whole home network with my Tailscale devices.

```
Phone (Tailscale app)
   │  encrypted WireGuard tunnel
   ▼
LXC 100 "tailscale" on Proxmox (192.168.1.102)
   │  IP forwarding (Weiterleitung)
   ▼
Home network 192.168.1.0/24
   ├── Robot (Pi)         http://<pi-ip>:8000
   ├── Proxmox web UI     https://<pve-ip>:8006
   └── Windows PC         (later: Wake-on-LAN)
```

Why Tailscale and not a public tunnel (Cloudflare Tunnel was considered):

- Nothing is public. Only my own logged-in devices can reach the robot.
- No domain and no DNS changes needed.
- No open router ports, no port forwarding (Portweiterleitung).
- Nothing to install on the robot itself. The Pi stays unchanged when it is swapped (Pi 2 → Pi 4/5).

The robot's own safety layer still applies: the connection watchdog (about 1 s) stops the motors if the link drops.

## Setup

### 1. Create the container (Proxmox web UI)

- Template: `debian-12-standard` (local → CT Templates → Templates → Download)
- Create CT: ID `100`, hostname `tailscale`, unprivileged
- 1 core, 512 MB RAM, 512 MB swap, 4 GB disk
- Network: bridge `vmbr0`, IPv4 DHCP
- Options → Start at boot: Yes

### 2. Give the container the TUN device

Tailscale needs the TUN device (virtual network card). An unprivileged container cannot see it by default.

On the Proxmox host shell:

```bash
cat >> /etc/pve/lxc/100.conf << 'EOF'
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
EOF
```

- Line 1: permission (Berechtigung) to use device `10:200` (TUN)
- Line 2: bind-mounts the host's `/dev/net/tun` into the container

### 3. Install Tailscale in the container

```bash
pct start 100
pct enter 100

apt update && apt upgrade -y
apt install -y curl
curl -fsSL https://tailscale.com/install.sh | sh
```

### 4. Enable IP forwarding

```bash
echo 'net.ipv4.ip_forward = 1' > /etc/sysctl.d/99-tailscale.conf
sysctl -p /etc/sysctl.d/99-tailscale.conf
```

The file in `/etc/sysctl.d/` is read at every boot, so the setting stays after a restart.

### 5. Start as subnet router

```bash
tailscale up --advertise-routes=192.168.1.0/24
```

Open the printed login link in a browser. Use the network address (`.0/24`), not the container's own IP.

The warnings about IPv6 forwarding and UDP GRO can be ignored: only IPv4 is used, and GRO only affects throughput.

### 6. Tailscale admin console

In Machines → `tailscale` → `…`:

- Edit route settings → approve `192.168.1.0/24`
- Disable key expiry (otherwise the server logs out after 180 days)

### 7. Clients

Install the Tailscale app on the phone and laptop and log in with the same account.

## Robot requirements

- Fixed IP for the Pi via a DHCP reservation in the router (feste IP)
- uvicorn must listen on `0.0.0.0`, not `127.0.0.1`
- Robot page: `http://<pi-ip>:8000`

## Test

1. Phone: turn WiFi off, use mobile data, turn Tailscale on.
2. Open `https://<pve-ip>:8006` (Proxmox). If it loads, the route works.
3. Later: open the robot page at `http://<pi-ip>:8000` and drive.

## Status

- [x] Tailscale account (Personal plan)
- [x] LXC 100 created, TUN device added
- [x] Tailscale installed, IP forwarding on, subnet route advertised
- [x] Approve subnet route, disable key expiry
- [x] Phone test over mobile data
- [ ] Fixed IP for the Pi, test the robot page remotely
- [ ] Later: Wake-on-LAN for the Windows PC via the container (`wakeonlan <MAC>`)
