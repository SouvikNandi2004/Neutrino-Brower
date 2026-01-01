# MIT License
#
# Copyright (c) 2021 Souvik Nandi, DisunicX
#
# Permission is granted to use, copy, modify, and distribute this software for any purpose with or without fee, provided the copyright notice appears in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.


if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root. Use sudo."
  exit 1
fi

# 2. Add Tor repository & GPG key
echo "Adding Tor repository and GPG key..."

# Import GPG key for the Tor repository
curl -fsSL https://deb.torproject.org/torproject.org/gpgkey | gpg --dearmor | tee /usr/share/keyrings/tor-archive-keyring.gpg > /dev/null

# Check the Ubuntu codename (e.g., "plucky", "jammy", "focal", etc.)
CODENAME=$(lsb_release -cs)

# If on 'plucky' (Ubuntu 24.04), use 'jammy' (Ubuntu 22.04 LTS) for compatibility
if [ "$CODENAME" == "plucky" ]; then
  echo "Detected Ubuntu codename: $CODENAME. Replacing with 'jammy' for compatibility."
  CODENAME="jammy"
fi

# Add the Tor repository (update for jammy if on plucky)
echo "deb [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org $CODENAME main" | tee /etc/apt/sources.list.d/tor.list

# 3. Update and install Tor
echo "Updating system and installing Tor..."

apt update
apt install -y tor

# 4. Start and enable Tor service
echo "Starting Tor service..."
systemctl start tor
systemctl enable tor

# 5. Verify Tor installation
echo "Verifying Tor installation..."
systemctl status tor

echo "Tor installation completed successfully!"

# 6. Check if Tor is running
echo "Testing if Tor is running on the default SOCKS proxy port (9050)..."
netstat -tulpen | grep 9050

echo "Tor should now be running. You can use it through SOCKS5 on port 9050."
