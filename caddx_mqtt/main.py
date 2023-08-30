import argparse
import logging
import logging.handlers
import os
import sys
import threading

from caddx_mqtt import api_alt
from caddx_mqtt import controller

# This fork uses SemVer
VERSION = '0.1.0'
DEFAULT_MQTT_PORT = 1883

LOG_FORMAT = '%(asctime)-15s %(module)s %(levelname)s %(message)s'


class NoFlaskInfoFilter(logging.Filter):
    # Matches Flask log lines for filtering
    def filter(self, record: logging.LogRecord) -> bool:
        return not (record.levelname in 'INFO'
                    and record.module in '_internal'
                    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', default=False, action='store_true',
                        help='Display version')

    parser.add_argument('--config', default='config.ini',
                        metavar='FILE',
                        help='Path to config file')
    # Logging
    parser.add_argument('--debug', default=False, action='store_true',
                        help='Enable debug')
    parser.add_argument('--log', default=None,
                        metavar='FILE',
                        help='Path to log file')
    levels = ('DEBUG', 'INFO', 'WARNING')
    parser.add_argument('--logLevel', default='INFO', choices=levels,
                        metavar='LOG_LEVEL_CONSOLE',
                        help='Level of log displayed to console')

    # Alarm connection
    parser.add_argument('--solAddr', default=None,
                        metavar='HOST:PORT',
                        help='Host and port to connect for serial stream')
    parser.add_argument('--serial', default=None,
                        metavar='DEVICE',
                        help='Serial port to open for stream')
    parser.add_argument('--baudrate', default=38400, type=int,
                        metavar='BAUD',
                        help='Serial baudrate')

    # Web / SSE
    parser.add_argument('--apiAddress', default='127.0.0.1',
                        metavar='API_ADDRESS',
                        help='API Listen address (defaults to localhost)')
    parser.add_argument('--apiPort', default=5007, type=int,
                        help='API Listen port (defaults to 5007)')

    # MQTT (Required for activation)
    parser.add_argument('--mqttBroker', default='127.0.0.1',
                        metavar='MQTT_BROKER',
                        help='MQTT Broker  (defaults to localhost)')
    # Optional
    parser.add_argument('--mqttPort', default=DEFAULT_MQTT_PORT,
                        metavar='MQTT_PORT',
                        help='MQTT Broker Port (default: %s)' % DEFAULT_MQTT_PORT)
    parser.add_argument('--mqttUser', default=None,
                        metavar='MQTT_USERNAME',
                        help='MQTT Client Username')
    parser.add_argument('--mqttPassword', default=None,
                        metavar='MQTT_PASSWORD',
                        help='MQTT Client Password')
    parser.add_argument('--mqttStateTopicRoot', default='home/alarm',
                        metavar='STATE_TOPIC_ROOT',
                        help='Root topic for MQTT Client publishing')
    parser.add_argument('--mqttCommandTopic', default='home/alarm/set',
                        metavar='COMMAND_TOPIC',
                        help='Command topic for MQTT Client subscription/monitoring')
    parser.add_argument('--mqttTlsActive', default=False, action='store_true',
                        help='Enable MQTT TLS')
    parser.add_argument('--mqttTlsInsecure', default=False, action='store_true',
                        help='Ignore MQTT TLS Insecurities (Not Recommended)')
    parser.add_argument('--mqttTimeout', default=10, type=int,
                        metavar='MQTT_TIMEOUT',
                        help='MQTT Timeout in seconds')

    LOG = logging.getLogger()
    formatter = logging.Formatter(LOG_FORMAT)
    istty = os.isatty(0)

    LOG.debug("Parsing args...")
    args = parser.parse_args()

    if args.version:
        LOG.info('%s' % VERSION)
        sys.exit()

    if args.debug and not istty:
        debug_handler = logging.handlers.RotatingFileHandler(
            'debug.log',
            maxBytes=1024 * 1024 * 10,
            backupCount=3)
        debug_handler.setFormatter(formatter)
        debug_handler.setLevel(logging.DEBUG)
        LOG.addHandler(debug_handler)

    if istty:
        verbose_handler = logging.StreamHandler()
        verbose_handler.setFormatter(formatter)
        verbose_handler.setLevel(logging.DEBUG)
        LOG.addHandler(verbose_handler)

    if args.log:
        log_handler = logging.handlers.RotatingFileHandler(
            args.log,
            maxBytes=1024 * 1024 * 10,
            backupCount=3)
        log_handler.setFormatter(formatter)
        log_handler.setLevel(logging.INFO)
        LOG.addHandler(log_handler)

    if args.logLevel == 'DEBUG':
        LOG.setLevel(logging.DEBUG)
    elif args.logLevel == 'INFO':
        LOG.setLevel(logging.INFO)
    elif args.logLevel == 'WARNING':
        LOG.setLevel(logging.WARNING)
        logger = logging.getLogger()
        for handler in logger.handlers:
            handler.addFilter(NoFlaskInfoFilter())
    else:
        LOG.error('Input Log level INVALID. Try: "INFO|DEBUG|WARNING"')
        LOG.setLevel(logging.WARNING)

    LOG.debug(f"Broker: {args.mqttBroker}")
    if args.mqttBroker:
        # TBD: just use the args namespace instead of copying to local vars
        mqtt_broker = args.mqttBroker
        mqtt_port = args.mqttPort
        mqtt_username = args.mqttUser
        mqtt_password = args.mqttPassword
        mqtt_state_topic_root = args.mqttStateTopicRoot
        mqtt_command_topic = args.mqttCommandTopic
        mqtt_tls_active = args.mqttTlsActive
        mqtt_tls_insecure = args.mqttTlsInsecure
        mqtt_timeout = args.mqttTimeout

    else:
        LOG.error('Missing MQTT server address.')
        sys.exit()

    LOG.info('Starting caddx_mqtt %s' % VERSION)

    # Activate controller
    LOG.debug('Activating controller')
    # TBD Figuring out what type of connection is being used by checking if the first part of the port spec starts with a /dev/ or not
    #      is a hack. Fix this.

    LOG.debug(f"Serial: {args.serial}")
    if args.solAddr:
        host, port = args.solAddr.split(':')
        ctrl = controller.NXController((host, int(port)),
                                       args.config, mqtt_broker, mqtt_port, mqtt_username,
                                       mqtt_password, mqtt_state_topic_root, mqtt_command_topic,
                                       mqtt_tls_active, mqtt_tls_insecure, mqtt_timeout)
    elif args.serial:
        ctrl = controller.NXController((args.serial, args.baudrate),
                                       args.config, mqtt_broker, mqtt_port, mqtt_username,
                                       mqtt_password, mqtt_state_topic_root, mqtt_command_topic,
                                       mqtt_tls_active, mqtt_tls_insecure, mqtt_timeout)
    else:
        LOG.error('Either host:port or serial and baudrate are required')
        sys.exit()

    LOG.debug('Activating mqtt controller')
    api_alt.CONTROLLER = ctrl
    t = threading.Thread(target=ctrl.controller_loop)
    t.daemon = True
    t.start()

    # Activate web api
    LOG.debug('Activating web api')
    try:
        if args.apiAddress:
            from caddx_mqtt import api
            api.CONTROLLER = ctrl
            api.app.run(debug=False, host=args.apiAddress, port=args.apiPort, threaded=True)  # Blocking to run
        else:
            LOG.error('Missing API address.')
            sys.exit()
    except Exception as ex:
        print('Fatal exception in activation: %s' % str(ex))
    finally:
        # Mark system and zones as offline
        # TBD: Manual LWT not necessary as LWT can be sent by broker
        #      if we tell it what to send on connect.
        # try:
        #     if args.mqtt is not None:
        #         topic = mqtt_state_topic_root + "/system/avail"
        #         api_alt.CONTROLLER.mqtt_client.publish(topic, "offline", retain=True)
        # except Exception as ex:
        #     LOG.error('Unable to send MQTT Last Will message: %s' % str(ex))
        sys.exit()
