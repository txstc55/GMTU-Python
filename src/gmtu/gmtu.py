import socket
import os
import platform
import subprocess
import uuid
import threading
import requests

class gmtu:
  def __init__(self, supabase_url = "", supabase_anon_key = "", fcm_token = ""):
    ####################################################################################
    ## First we check for supabase anon key and url
    ####################################################################################
    self.__supabase_url = supabase_url
    self.__supabase_anon_key = supabase_anon_key
    if supabase_url == "":
      # we will use the default supabase edge function for sending the push notification
      self.__supabase_url = "https://yhrybsftocoyxlcntlvl.supabase.co/functions/v1/send-push"
      self.__supabase_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlocnlic2Z0b2NveXhsY250bHZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4MTg3MzEsImV4cCI6MjA2MTM5NDczMX0.8NND4xnb4DCs8QVgPfY3nxmHB1Lw4Z3XzZN9utOsMhE"

    if supabase_url == "" and supabase_anon_key != "":
      raise ValueError(f"gmtu.__init__: supabase_url is empty but supabase_anon_key is not empty, anon_key is:{supabase_anon_key}")
    if supabase_url != "" and supabase_anon_key == "":
      raise ValueError(f"gmtu.__init__: supabase_url is not empty but supabase_anon_key is empty, url is:{supabase_url}")

    ####################################################################################
    ## setup fcm token if it is given
    ####################################################################################
    self.__fcm_token = fcm_token

    ####################################################################################
    ## now we set the machine instance
    ####################################################################################
    self.__system_uuid: str = "unknown_system_id"
    self.__system_name: str = socket.gethostname()
    self.__get_machine_uuid()
    self.__events = {}
    # print(f"GMTU initialized with name {self.__system_name} and UUID {self.__system_uuid}")


  ####################################################################################
  ## bunch of properties
  ####################################################################################
  @property
  def system_uuid(self):
    return self.__system_uuid

  @property
  def system_name(self):
    return self.__system_name

  @property
  def events(self):
    return self.__events

  @property
  def fcm_token(self):
    return self.__fcm_token

  @fcm_token.setter
  def fcm_token(self, token):
    self.__fcm_token = token


  ####################################################################################
  ## the most important function, used to send a push notification
  ####################################################################################
  def __sendPushNotification(self, type, event_name = "", milestones = [], progression = "", eventId = 0):
    # let's say
    # type 0 is an one time update, so no progression
    # type 1 is an event starting
    # type 2 is an event progression update
    # type 3 is an event finished
    # type 4 is event cancelled somehow
    if self.__fcm_token == "":
      raise ValueError("gmtu.sendPushNotification: fcm_token is empty")

    def do_send():
      headers = {
        'Authorization': f'Bearer {self.__supabase_anon_key}',
        'Content-Type': 'application/json'
      }
      data = {
        "fcm": self.__fcm_token,
        "type": type,
        "event_name": event_name,
        "milestones": milestones,
        "progression": progression,
        "device_id": self.__system_uuid,
        "device_name": self.__system_name,
        "event_id": eventId
      }
      try:
        response = requests.post(self.__supabase_url, headers=headers, json=data)
        if not response.ok:
          print(f"gmtu.__sendPushNotification failed: {response.status_code} — {response.text}")
      except Exception as e:
        print(f"gmtu.__sendPushNotification error: {e}")
    thread = threading.Thread(target=do_send)
    thread.start()


  ####################################################################################
  ## add event will need an event name and milestones
  ## the milestones are used to determine the progress of the event
  ## by default calling this function will immediately start the event
  ####################################################################################
  def addEvent(self, event_name: str, milestones = [], immediate_start = True) -> None:
    if event_name in self.__events:
      print(f"gmtu.addEvent: {event_name} already exists, this action will override the existing event. This is only a warning, it will not interrupt the existing execution")
    if milestones != []:
      self.__events[event_name] = milestones
    else:
      self.__events[event_name] = list(range(100)) # well this is from 0 to 99 but what can we do
    if immediate_start:
      self.startEvent(event_name)

  ####################################################################################
  ## this is basically for modifying the milestones
  ####################################################################################
  def addMilestones(self, event_name: str, milestones) -> None:
    # this basically modify the existing event with the new milestones
    if event_name in self.__events:
      self.__events[event_name] = milestones

  ####################################################################################
  ## function to start the event
  ####################################################################################
  def startEvent(self, event_name: str) -> None:
    self.__sendPushNotification(1, event_name, milestones = [])


  ####################################################################################
  ## function to send a one time event notification
  ## this can be used in cli for like, hey compilation finished etc
  ####################################################################################
  def sendOneTimeEvent(self, content) -> None:
    self.__sendPushNotification(0, content) # here the event name field in the send notification function will be the content of the push notification


  def updateEvent(self, event_name, milestone = "", single_update = False, title = "", content = "") -> None:
    if self.__fcm_token is None:
      raise ValueError("gmtu.sendEventUpdate: FCM token is not set")
    if not single_update:
      if event_name not in self.__events:
        raise ValueError(f"gmtu.sendEventUpdate: Event {event_name} does not exist")


  def __get_machine_uuid(self):
    system = platform.system()
    if system == "Linux":
      try:
        with open('/etc/machine-id', 'r') as f:
          self.__system_uuid = f.read().strip()
      except FileNotFoundError:
        pass
    elif system == "Darwin":  # macOS
      try:
        output = subprocess.check_output(
          "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
          shell=True
        ).decode()
        self.__system_uuid = output.split('"')[-2]
      except Exception:
        pass

    elif system == "Windows":
      try:
        output = subprocess.check_output(
          "wmic csproduct get UUID",
          shell=True
        ).decode().split("\n")[1].strip()
        self.__system_uuid = output
      except Exception:
        pass
