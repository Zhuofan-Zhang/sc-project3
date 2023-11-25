# Scalable Computing Group Project - Smart Home

Our use case was a smart home that would have devices monitoring 'stats' in a room (eg temperature, light, CO2 levels, etc.), could control 'apparatus' in the room (machines that could affect the rooms stats) and could communicate with each other if needed.

## Executables

1. `SmartHome` have rooms and devices in the rooms. They are the network.
   You can run one with the command below, and can then use the terminal to interact with devices.
   (To satisfy project requirements, start with 5 rooms per SmartHome, which will create 5 devices on the network. You can start a network on any Pi)

```shell
python3 SmartHome.py --home_id=1 --rooms=5
```

2. Once `SmartHome` is running, you can monitor device logs like this:

```shell
tail -f device_logs/room_0_device.log
```

3. You can also monitor room stats and apparatus like this:

```shell
python3 RoomMonitor.py
```

4. You can run the untrusted device using the command below.
   This will create a device that doesn't join the network officially like the other nodes, therefore it will have its packets ingnored.

```shell
python3 UntrustedDevice.py
```

## Recommended Marking Steps

1. Make sure requirements are installed (just `pandas`)

```shell
pip install -r requirements.txt
```

2. Open seven terminals on the same Pi

   - One to run `SmartHome`
   - One to tail `Room_0` logs
   - One to tail `Room_1` logs
   - One to monitor `Room_0`
   - One to monitor `Room_1`
   - One to run `UntrustedDevice`
   - One to tail `UntrustedDevice` logs

3. Run the scripts/commands (one per terminal created in step above):
   - `SmartHome` first to create missing directories and log/stat files
   ```shell
   python3 SmartHome.py --home_id=1 --rooms=5
   ```
   - Open `Room_0` logs
   ```shell
   tail -f device_logs/room_0_device.log
   ```
   - Open `Room_1` logs
   ```shell
   tail -f device_logs/room_1_device.log
   ```
   - Monitor `Room_0` (enter command below then type in `0` when prompted)
   ```shell
   python3 RoomMonitor.py
   ```
   - Monitor `Room_1` (enter command below then type in `1` when prompted)
   ```shell
   python3 RoomMonitor.py
   ```
   - Run `UntrustedDevice` (don't interact with it right now, open logs first)
   ```shell
   python3 UntrustedDevice.py
   ```
   - One to tail `UntrustedDevice` logs
   ```shell
   tail -f device_logs/untrusted_device.log
   ```
4. Interact with devices via `SmartHome` terminal prompts
   EG:

   - Select a device to interact with, eg. enter `0` to choose the device in Room_0
     - Type `turn off` to turn off
     - See device logs
     - Type `turn on` to turn back on
     - See device logs
     - Type `actuate` to bring up actuation options
       - Type the name of one of the apparatus listed, eg, `heater`
       - This will toggle the apparatus on/off
       - Notice change in the RoomMonitor terminal of Room_0
     - Type `send interest` to bring up destination options
       - Type in number of destination room, eg, `1`
       - Type in data name (something 'correct' from the listlike `temp` or 'wrong' to see what happens)
       - Notice activity in logs of Room_0 and Room_1
       - Correct data name will result in the interest being received by R1, and data sent to R0
       - Incorrect data name will result in the interest being received by R1, and a NACK sent to R0 (ie, "I don't have this")
     - Type `back` to leave this device and select a new one or quit
   - Type `quit` to turn off devices and the simulation
     - Notice change in the device logs
     - (`Ctrl+C` in the other terminals to end their processes)

5. Interact with `UntrustedDevice` (if `SmartHome` is still running)
   EG:

   - Choose a destination device, eg `0`
     - Choose data name, eg `CO`
     - Notice logs of selected room warn that an unkown packet was received, so it discarded it
     - Notice logs of `UntrustedDevice` show it sent an interest packet but never received anything back
   - Type `quit` when you want to exit

6. Close up terminals when finished, and give us a good grade!
