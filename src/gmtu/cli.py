import argparse
from gmtu import gmtu

def main():
  parser = argparse.ArgumentParser(description="Greet with gmtu class.")
  parser.add_argument("--content", type = str, default="There's an update", help="the push notification content")
  parser.add_argument("--fcm-token", type = str, default="unknown", help="the fcm token of the device you want to send to")
  args = parser.parse_args()
  instance = gmtu(fcm_token = args.fcm_token)
  instance.sendOneTimeEvent(args.content)

if __name__ == "__main__":
  main()
