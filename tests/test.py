from gmtu import gmtu
import time
f = open('../src/fcm_token', 'r')
fcm_token = f.read().strip()

gmtu_instance = gmtu(fcm_token)

for i in gmtu_instance(range(10038), event_name = "python for loop testing"):
  if i == 3:
    time.sleep(0.1)
    gmtu_instance.sendOTU("Message in between")
    time.sleep(1)
  time.sleep(0.2)
  print(i)
