# Scalable Computing Project 3 Group 21- Smart Home

Our use case was a smart home that would have devices monitoring 'stats' in a room (eg temperature, light, CO2 levels, etc.), could control 'apparatus' in the room (machines that could affect the rooms stats) and could communicate with each other if needed.

## Overview

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

## Demo Instructions

### 1. Check requirements

1. Make sure requirements are installed (just `pandas`)

```shell
pip install -r requirements.txt
```

### 2. Set Up the Demo

1. Open a terminal on the Pi and run the following script/command to create a `SmartHome` instance and to create missing directories and log/stat files:
   ```shell
   python3 SmartHome.py --home_id=1 --rooms=5
   ```

2. Open a new terminal on the same Pi and run the following script/command to view the logs of `Room_0`:
   ```shell
   tail -f device_logs/room_0_device.log
   ```

3. Open a new terminal on the same Pi and run the following script/command to view the logs of `Room_1`:
   ```shell
   tail -f device_logs/room_1_device.log
   ```

4. Open a new terminal on the same Pi and run the following script/command to create an `UntrustedDevice` instance:
   ```shell
   tail -f device_logs/untrusted_device.log
   ```

5. Open a new terminal on the same Pi and run the following script/command to view the logs of `UntrustedDevice`:
   ```shell
   tail -f device_logs/untrusted_device.log
   ```

### 3. Demo Scenarios

#### Scenario 1: A node leaves and re-enters the network.

1. In the first terminal that is running the `SmartHome` instance, enter `0` to choose the device in `Room_0`.
2. Enter `turn off` to turn the device off.
3. Notice activity in logs of `Room_0` and `Room_1`.
3. Enter `turn on` to turn the device on.
5. Notice activity in logs of `Room_0` and `Room_1`.

#### Scenario 2: A node sends an interest packet for a data name that exists.

After the steps of scenario 1, the first terminal that is running the `SmartHome` instance should still be in the menu for `Room_0`.

1. Enter `send interest` to bring up destination options
3. Enter `1` to select `Room_1` as the destination of the interest packet.
4. Enter `temp` to send the interest packet for data `room_1_device/temp`.
5. Notice activity in logs of `Room_0` and `Room_1`. `Room_0` sends the interest packet, which `Room_1` receives. Then `Room_1` sends a data packet with the requested data, which `Room_0` receives.

#### Scenario 3: A node sends an interest packet for a data name that does not exist.

After the steps of scenario 2, the first terminal that is running the `SmartHome` instance should still be in the menu for `Room_0`.

1. Enter `send interest` to bring up destination options
3. Enter `1` to select `Room_1` as the destination of the interest packet.
4. Enter `foobar` to send the interest packet for data `room_1_device/foobar` that doesn't exist.
5. Notice activity in logs of `Room_0` and `Room_1`. `Room_0` sends the interest packet, which `Room_1` receives. Then `Room_1` sends a data packet saying `room_1_device/foobar` doesn't exist, which `Room_0` receives.
 
#### Scenario 4: A node receives a packet with unknown encryption.

1. In the terminal that is running the `UntrustedDevice` instance (the 4th one opened), enter `0` to choose the device in `Room_0`.
4. Enter `temp` to send the interest packet for data `room_0_device/temp`.
5. Notice activity in logs of `Room_0` and `UntrustedDevice`. `UntrustedDevice` sends the interest packet, which `Room_0` receives. `Room_1` outputs that a packet with unknown encryption was received and discards the packet. Note that `UntrustedDevice` never receives anything back.

### 3. Close up terminals when finished, and give us a good grade!
