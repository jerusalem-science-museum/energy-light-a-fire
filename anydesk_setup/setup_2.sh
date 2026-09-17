#!/bin/bash

echo "=== 🚀 Lancement AnyDesk si non actif ==="
anydesk &

sleep 2

echo "=== 🆔 Identifiant AnyDesk de la machine ==="
anydesk --get-id

echo "=== 🔐 Définition du mot de passe pour accès distant ==="
echo "yourpassword" | sudo anydesk --set-password

echo "=== 🛡️ Écriture du fichier de configuration ~/.anydesk/service.conf ==="
mkdir -p ~/.anydesk
cat > ~/.anydesk/service.conf <<EOF
[permission]
accept_incoming_connections=1
unattended_access=1
allow_unattended_access=1
always_accept=1
EOF

echo "=== 🔁 Redémarrage du service AnyDesk ==="
sudo systemctl restart anydesk

echo "✅ AnyDesk configuré pour accès automatique avec mot de passe 'yourpassword'"
