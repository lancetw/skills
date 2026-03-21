#!/bin/bash
# FortiClient VPN status checker via openfortivpn
# Output: JSON with connection status

if pgrep -x openfortivpn > /dev/null 2>&1; then
    VPN_IP=$(ifconfig ppp0 2>/dev/null | grep "inet " | awk '{print $2}')
    REMOTE_IP=$(ifconfig ppp0 2>/dev/null | grep "inet " | awk '{print $4}')
    if [ -n "$VPN_IP" ]; then
        echo "{\"connected\":true,\"ip\":\"$VPN_IP\",\"remote\":\"$REMOTE_IP\",\"interface\":\"ppp0\"}"
    else
        echo "{\"connected\":true,\"ip\":null,\"note\":\"process running but no ppp0 interface yet\"}"
    fi
else
    echo "{\"connected\":false}"
fi
