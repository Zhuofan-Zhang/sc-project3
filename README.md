Available sensor type:
Device:
temperature,light,humidity,radiation,co2,co,motion,smoke
Washing Machine
washer,lock,load,electricity_usage,water_usage,rpm,temperature,duration

Command type:
heater on/off, light on/off, washer on/off

Example interactions

```markdown
Node /house3/room3/phone - Enter command (interest/data/exit/add_fit): data
Enter destination node for data packet: /house1/room2/washine_machine
Enter sensor name: motor
Enter data content: command/on
```

Start devices separately in different terminals

1. Start Device1

```shell
chmod +x ./scripts/device1.sh
source ./scripts/device1.sh
python NDNNode.py
```

2. Start Device2

```shell
chmod +x ./scripts/device2.sh
source ./scripts/device2.sh
python NDNNode.py
```

3. Start Device3

```shell
chmod +x ./scripts/device3.sh
source ./scripts/device3.sh
python NDNNode.py
```

4. Start Device4

```shell
chmod +x ./scripts/device4.sh
source ./scripts/device4.sh
python NDNNode.py
```

5. Start washing machine

```shell
chmod +x ./scripts/washing_machine.sh
source ./scripts/washing_machine.sh
python NDNNode.py
```

6. Start phone

```shell
chmod +x ./scripts/phone.sh
source ./scripts/phone.sh
python NDNNode.py
```

7. Start auto sender

```shell
python send_data.py
```
