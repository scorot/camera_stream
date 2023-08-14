#!/bin/bash

WD=$(pwd)

test -e /lib/systemd/system/camera.service && \
echo "Pi camera stream service is already installed." && \
exit 0

cp ./camera.service camera.service.install
sed -i "s|install_dir|$PWD|" camera.service.install

cp ./camera.service.install /lib/systemd/system/camera.service
#rm ./camera.service.install
chown root:root /lib/systemd/system/camera.service
chmod 0644 /lib/systemd/system/camera.service

systemctl daemon-reload
sleep 1
systemctl enable camera.service
systemctl start camera.service
if [ $? -eq 0 ]; then
echo "Install finished. You can connect to your pi camera stream at:"
echo "$(hostname):8000/index.html"
fi
