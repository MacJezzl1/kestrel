# ====================================================================
# Kestrel Trading Platform — MetaTrader 5 Container Service
# Based on gmag11/MetaTrader5-Docker with Wine & Python RPC Server
# ====================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV WINEARCH=win64
ENV WINEDEBUG=-all
ENV WINEPREFIX=/root/.wine

# Install Wine, Python 3, and prerequisites
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wine64 wine32 wine \
        xvfb x11vnc fluxbox \
        python3 python3-pip python3-setuptools \
        curl wget ca-certificates supervisor && \
    rm -rf /var/lib/apt/lists/*

# Install Python requirements for Bridge server
RUN pip3 install --no-cache-dir \
    fastapi uvicorn pydantic requests

# Create application directory
WORKDIR /app
COPY bridge_server.py /app/bridge_server.py

# Expose RPC bridge port & VNC port (for manual terminal debugging)
EXPOSE 5001 5900

# Start RPC server and headless Xvfb
CMD ["python3", "/app/bridge_server.py"]
