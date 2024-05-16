
# NX584/NX8E Interface to MQTT client and HTTP server

This is a tool to let you interact with your NetworX alarm panel via
the NX584 module (which is built into NX8E panels). You must enable it
in the configuration of the control panel. 

This package is designed to be a direct replacement for pynx584.
Connection services allow for MQTT client (paho-mqtt) and/or legacy HTTP server (flask).

MQTT provides considerable improvements in zone change latency. Also, since flask is really designed only for development 
and is considered unstable, HTTP usage is not suggested, but only is provided for backwards-compatibility.

Typical use case is for a NX/Caddx alarm connected to MQTT mosquitto broker, possibly then to Home Assistant.
 
# Install

Package installation:

 `pip3 install caddx_mqtt`

 
The server must be run on a machine with connectivity to the panel,
which can be a local serial port, or a Serial-over-LAN device (i.e. a
TCP socket). For example:

`caddx_server --serial /dev/ttyS0 --baud 38400 [...]`

or

`caddx_server --solAddr 192.168.1.101:23 [...]`


# Usage

`caddx_server --mqtt 192.168.1.102 [...]`


# Command Line Parameters

## HTTP (legacy)
'--listen' - 'HTTP Server address (defaults to disabled)'
'--port' - 'HTTP Server port (defaults to 5007)'

## MQTT

Command line parameters for MQTT are as follows:

'--mqtt' - 'MQTT Client Host to connect'
'--mqttPort' - 'MQTT client port (defaults to 1883)'
'--username' - 'MQTT Client Username'
'--password' - 'MQTT Client Password')
'--stateTopicRoot' - 'Root topic for MQTT Client publishing (defaults to 'home/alarm')'
'--commandTopic', - 'Command topic for MQTT Client subscription/monitoring (defaults to 'home/alarm/set')'
'--mqttTlsActive' - 'Enable MQTT TLS (default= to false)'
'--mqttTlsInsecure' - 'Ignore MQTT TLS Insecurities (Not Recommended) (defaults to false)'
'--timeout' - 'MQTT Timeout in seconds (default is 10)'
'--logLevel' - 'Verbosity of logs written to console [WARNING|INFO|DEBUG] (defaults to WARNING)'

- Publish to mqtt <command topic> with value:

'disarm,<part>,<code>' - Disarms partition <part> using code <code>
'arm_home,<part>' - Arms home partition <part>
'arm_away,<part>' - Arms away partition <part>
'bypass_toggle,<zone>' - Toggle bypass of zone (be sure zone is bypassable!!)
'time' - Update alarm time from local time of caddx_mqtt server
'status' - Update mqtt status of all fields (dev only)
'nop' - No action, clears command after arm/disarm to reduce code visibility



# Client Usage (if enabled/installed)

Once the server is is running, you should be able to do something like this:

 $ nx584_client summary
 +------+-----------------+--------+--------+
 | Zone |       Name      | Bypass | Status |
 +------+-----------------+--------+--------+
 |  1   |    FRONT DOOR   |   -    | False  |
 |  2   |   GARAGE DOOR   |   -    | False  |
 |  3   |     SLIDING     |   -    | False  |
 |  4   | MOTION DETECTOR |   -    | False  |
 +------+-----------------+--------+--------+
 Partition 1 armed

 # Arm for stay with auto-bypass
 $ nx584_client arm-stay

 # Arm for exit (requires tripping an entry zone)
 $ nx584_client arm-exit

 # Auto-arm (no bypass, no entry zone trip required)
 $ nx584_client arm-auto

 # Disarm
 $ nx584_client disarm --master 1234



 
Install via Docker Compose
Before creating the Docker container, you need to define how you connect to the panel (local serial port, or a 
Serial-over-LAN device (i.e. a TCP socket)) in the :`docker-compose.yml` file. 
Uncomment and edit the `environment` section to fit your needs:

'''
 version: "3.2"

 services:
   caddx_mqtt:
     container_name: caddx_mqtt
     build:
       context: .docker
       dockerfile: Dockerfile
     restart: unless-stopped
     ports:
       - 5007:5007
     environment:
       # Uncomment these as needed, depending on how you connect to the panel (via Serial or TCP Socket)
       # - SERIAL=/dev/ttyS0
       # - BAUD=38400
       # - CONNECT=192.168.1.101:23
'''

To build the image, create the Docker container and then run it, make sure you're at the root of the checked out repo and run::

 # docker-compose up -d

You should now be able to connect to the caddx_mqtt Docker container via its exposed port (default :code:`5007`).

Config
------

The `config.ini` should be generated once the controller reports the first
zone name. However, here is a full `config.ini` if you want to pre-populate
it with zone names::

 [config]
 # max_zone is the highest numbered zone you have populated
 max_zone = 5

 # Set to true if your unit sends DD/MM dates instead of MM/DD
 euro_date_format = False
 
 [email]
 fromaddr = security@foo.com
 smtphost = imap.foo.com
 
 [zones]
 # Zone names
 1 = Front Door
 2 = Garage Entry
 3 = Garage Side
 4 = Garage Back
 5 = Kitchen
 
 
 
# Optional Home Assistant MQTT Integration
 ************************************************************
 
>> Binary Sensors
Note: Previous binary sensors were auto-named from zones, and now would require additional effort to reproduce. 
Zone names and details are all published to the mqtt server.
I would suggest using a mqtt explorer to examine your published names and zones numbers to recreate, if desired
```
  - platform: mqtt
    state_topic: "tele/nx584/zones/1/faulted"
    name: "Z1 Front Door"
    device_class: opening
    payload_off: "false"
    payload_on: "true"
    availability:
      - topic: "tele/nx584/system/avail"
        payload_available: "online"
        payload_not_available: "offline"
```
>> Alarm Control Panel
```
alarm_control_panel:
  - platform: mqtt
    state_topic: "tele/nx584/partitions/1/state"
    command_topic: "cmnd/nx584/action"
#    command_template: "{{action}},{partition_int_hardcode_REPLACE_ME},{{code}}"
    command_template: "{{action}},1,{{code}}"
    code_arm_required: false
    code_disarm_required: true
    code_format: "number"
    name: "nx584"
    retain: true
```
