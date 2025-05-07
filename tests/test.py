from gmtu import gmtu
f = open('../src/fcm_token', 'r')
fcm_token = f.read().strip()

gmtu_instance = gmtu(fcm_token)

for i in gmtu_instance(range(10)):
  print(i)
