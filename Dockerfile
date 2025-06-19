FROM ghcr.io/home-assistant/home-assistant:stable

# Copy the custom component into the Home Assistant config directory
COPY custom_components/ /config/custom_components/

# Set default config (optional, can be overridden by mounting a volume)
# COPY configuration.yaml /config/ 