# Phase 0: Setup (Einrichtung)

Goal: SSH into the Pi 2 over WiFi and take a photo.

## 1. Flash the SD card

1. Install **Raspberry Pi Imager** on the laptop.
2. Device: **Raspberry Pi 2**. OS: Raspberry Pi OS (other) → **Lite, 32-bit**.
3. Edit settings before writing:
   - Hostname: `patrol-robot`
   - Username and password
   - WiFi: your network, country **CH**
   - Services: enable **SSH** (public key is safer than password)
4. Write the card.

## 2. First boot

1. Plug in the USB WiFi dongle. Connect an **Ethernet cable as backup** (the Pi 2 has a port).
2. Power on, wait 2 to 3 minutes.
3. From the laptop: `ssh <user>@patrol-robot.local`

## 3. WiFi dongle

```bash
lsusb            # dongle listed?
nmcli device     # wlan0 connected?
sudo nmtui       # if not: pick the network here
```

Done when SSH works with the Ethernet cable removed.
If `wlan0` never appears, the dongle has no driver. Buy one listed as Raspberry Pi compatible.

## 4. GitHub repo

On the laptop:

```bash
cd home-patrol-robot
git init && git add . && git commit -m "Project skeleton"
# create an empty public repo "home-patrol-robot" on github.com, then:
git remote add origin git@github.com:<username>/home-patrol-robot.git
git branch -M main && git push -u origin main
```

On the Pi:

```bash
ssh-keygen -t ed25519          # add ~/.ssh/id_ed25519.pub to GitHub → Settings → SSH keys
git clone git@github.com:<username>/home-patrol-robot.git
cd home-patrol-robot
bash setup/install.sh
```

## 5. Camera (Kamera)

1. Pi **off**. Lift the camera connector latch, insert the ribbon cable with the blue side facing the Ethernet port, press the latch down.
2. Boot, then:

```bash
rpicam-hello --list-cameras     # should show imx219 (Camera Module v2)
python3 tools/test_camera.py
```

3. Copy the photo to the laptop:

```bash
scp <user>@patrol-robot.local:~/home-patrol-robot/photo.jpg .
```

## 6. Bonus: live stream

```bash
python3 -m robot.web.app
```

Open `http://patrol-robot.local:8000` on the phone. The stream works now; the drive buttons do nothing until the motors are wired (phase 1).
