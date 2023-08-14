#!/bin/bash

systemctl stop camera.service && \
systemctl disable camera.service && \
rm -f /lib/systemd/system/camera.service && \
echo "pi camera stream service disabled and unistalled."

systemctl daemon-reload

