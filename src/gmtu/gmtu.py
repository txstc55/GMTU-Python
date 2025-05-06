import socket
import os
import platform
import subprocess
import threading
import requests
import uuid
import datetime
from typing import List, Dict, Any


class gmtu:
  def __get_machine_uuid():
    system = platform.system()
    if system == "Linux":
      try:
        with open('/etc/machine-id', 'r') as f:
          return f.read().strip()
      except FileNotFoundError:
        pass
    elif system == "Darwin":  # macOS
      try:
        output = subprocess.check_output(
          "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
          shell=True
        ).decode()
        return output.split('"')[-2]
      except Exception:
        pass

    elif system == "Windows":
      try:
        output = subprocess.check_output(
          "wmic csproduct get UUID",
          shell=True
        ).decode().split("\n")[1].strip()
        return output
      except Exception:
        return "Unknown_System_ID"
  ####################################################################################
  ## Static variable and methods for if user want to configure things globally
  ####################################################################################
  __default_supabase_url = "https://yhrybsftocoyxlcntlvl.supabase.co/functions/v1/send-push"
  __default_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlocnlic2Z0b2NveXhsY250bHZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU4MTg3MzEsImV4cCI6MjA2MTM5NDczMX0.8NND4xnb4DCs8QVgPfY3nxmHB1Lw4Z3XzZN9utOsMhE"

  @classmethod
  def set_default_supabase_url(cls, url):
    cls.__default_supabase_url = url

  @classmethod
  def set_default_anon_key(cls, key):
    cls.__default_anon_key = key

  __system_name: str = socket.gethostname()
  __system_id: str = __get_machine_uuid()


  def __init__(self, supabase_url = "", supabase_anon_key = "", fcm_token = "", event_name = "Code Progress"):
    ####################################################################################
    ## First we check for supabase anon key and url
    ####################################################################################
    self.__supabase_url = supabase_url
    self.__supabase_anon_key = supabase_anon_key
    if supabase_url == "" and supabase_anon_key == "":
      # we will use the default supabase edge function for sending the push notification
      self.__supabase_url = self.__class__.__default_supabase_url
      self.__supabase_anon_key = self.__class__.__default_anon_key

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
    self.__system_uuid: str = self.__class__.__system_id
    self.__system_name: str = self.__class__.__system_name
    self.__milestones: Dict[float, str] = {}
    self.__event_name: str = event_name
    self.__event_uuid: str = uuid.uuid4()
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
  def event_name(self):
    return self.__event_name

  @property
  def fcm_token(self):
    return self.__fcm_token

  @fcm_token.setter
  def fcm_token(self, token):
    self.__fcm_token = token

  def __get_id(self, event_name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{self.__event_name}_{self.__system_name}_{event_name}_{datetime.datetime.utcnow().isoformat()}_{uuid.uuid4()}"))


  ####################################################################################
  ## the most important function, used to send a push notification
  ####################################################################################
  def __sendPushNotification(self, type, event_name = "", milestones = [], progression: float = 0, eventId: str = "0", silence: bool = False):
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
        "device_id": self.system_uuid,
        "device_name": self.system_name,
        "event_id": eventId,
        "silence": silence
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
  ## function to send a one time event notification
  ## this can be used in cli for like, hey compilation finished etc
  ####################################################################################
  def sendOneTimeEvent(self, content, silence = False) -> None:
    otu_event_id = self.__get_id("otu")
    self.__sendPushNotification(0, content, eventId = otu_event_id, silence = silence) # here the event name field in the send notification function will be the content of the push notification


  ####################################################################################
  ## here we make a class that takes in an iterator
  ####################################################################################
  def setMilestones(self, milestones: Dict[float, str]) -> None:
    if (len(milestones) > 10):
      # send a warning that the number of milestones is too high
      print('''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!  gmtu.setMilestones Warning: The number of milestones is too high  !!!!!!!!!!
!!!!!!!!!!  We recomment reducing the number of milestones                    !!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
''')
    for key in milestones.keys():
      if key <= 0:
        raise ValueError(f'Milestone key {key} must be greater than 0')
      elif key >= 1:
        raise ValueError(f'Milestone key {key} must be less than 1')
    self.__milestones = OrderedDict(sorted(milestones.items()))

  def __call__(self, iterable, event_name = None):
    # When instance is called with an iterable, return a wrapped iterator
    if event_name is not None:
      self.__event_name = event_name
    self.__event_uuid = self.__get_id(self.__event_name) # we make a unique uuid for each event
    return self.Iterator(iterable, self.__event_name, self, self.__milestones)

  class Iterator:
    def __init__(self, iterable, event_name: str, parent, milestones: Dict[float, str]):
      self.__iterable = iterable
      self.__iterator = iter(iterable)
      self.__event_name = event_name
      self.__count = 0
      self.__total = len(iterable) if hasattr(iterable, "__len__") else None
      self.__parent = parent
      self.__started = False
      self.__milestones = milestones

    def __iter__(self):
      return self

    def __next__(self):
      if not self.__started:
        self.__started = True
        # send notification for event starting
        # self.__parent._gmtu__sendPushNotification(1, self.__event_name, milestones = self.__milestones, eventId = self.__parent._gmtu__event_uuid)
        print("Event started")

      try:
        value = next(self.iterator)
        self.count += 1
        if self.total:
          print(f"{self.name}: {self.count}/{self.total}")
        else:
          print(f"{self.name}: {self.count}")
          return value
      except StopIteration:
        # → Loop ended normally here
        # self.__parent._gmtu__sendPushNotification(3, self.__event_name, milestones = self.__milestones, eventId = self.__parent._gmtu__event_uuid)
        print("Event ended")
        raise

    def __del__(self):
      if self.__started and self.count != self.total:
        # self.__parent._gmtu__sendPushNotification(4, self.__event_name, milestones = self.__milestones, eventId = self.__parent._gmtu__event_uuid)
        print("Event cancelled!")

  ####################################################################################
  ## helper functions
  ####################################################################################
