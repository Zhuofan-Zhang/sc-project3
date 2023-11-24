Lorem Ipsum

1. Make sure requirements are installed

```shell
pip install -r requirements.txt
```

2. Start a SmartHome instance with desired number of rooms.
   This will start all the room/device pairs, and the devices will begin to broadcast to each other for discovery.
   You can then use the terminal to manually turn on/off devices and send interest packets.
   To satisfy project requirements, start with 5 rooms per SmartHome, and only one SmartHome per Pi.

```shell
python3 SmartHome.py --home_id=1 --rooms=5
```

3. (Opt) Open log files of rooms in seperate, to monitor a devices activity (needed to see when a device sends/receives interest packet)

```shell
tail -f device_logs/room_0_device.log
```

4. (Opt) Monitor Room stats in seperate terminal, to monitor apparatus activity and room stats

```shell
python3 RoomMonitor.py
```

5. (TODO) Run UntrustedDevice to see what happens when an unsecure device joins the network.

```shell
python3 UntrustedDevice.py
```

6. Give us a good grade!
