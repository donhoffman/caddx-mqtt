FROM python:3.11

EXPOSE 5007

# Install

# OPTION A - Published version
#RUN pip3 install --no-cache-dir caddx_mqtt

# OPTION B - DEV version
WORKDIR /app/s
COPY . .
WORKDIR /app/caddx-mqtt
RUN pip3 install . --use-feature=in-tree-build
RUN chmod a+x /usr/bin/caddx_server
RUN chmod a+x /usr/bin/caddx_client

# Environment variables supported by this compose file
ENV LOG_LEVEL=WARNING
ENV API_ADDR="0.0.0.0"
ENV API_PORT=5007
ENV MQTT_BROKER="127.0.0.1"
ENV MQTT_PORT=1883
ENV MQTT_TLS=False
ENV MQTT_TLS_INSECURE=False
ENV MQTT_USER=""
ENV MQTT_PASSWORD=""
ENV MQTT_STATE_TOPIC_ROOT="home/alarm"
ENV MQTT_COMMAND_TOPIC="home/alarm"
ENV MQTT_TIMEOUT=10
ENV SOL_ADDR=""
ENV SERIAL_PORT=""
ENV SERIAL_BAUD=38400
ENV CONFIG_FILE="/config/config.ini"

ENTRYPOINT  python3 /usr/bin/caddx_server \
    --logLevel $LOG_LEVEL \
    --apiAdddr $API_ADDR --apiPort $API_ADDR \
    --mqttBroker $MQTT_BROKER \
    --mqttPort $MQTT_PORT \
    --mqttStateTopicRoot $MQTT_STATE_TOPIC_ROOT \
    --mqttCommandTopic $MQTT_COMMAND_TOPIC \
    --mqttTimeout $MQTT_TIMEOUT \
    --mqttUser $MQTT_USER \
    --mqttPassword $MQTT_PASSWORD \
    --serial $SERIAL_PORT --baud $SERIAL_BAUD \
    --config $CONFIG_FILE
