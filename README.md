# GMTU

### What is this project

It sends notification to your phone (assuming you have your GMTU app installed) so that you know when to get the fuck back to work.

### Who is it for

If you ever doubt that you have ADHD and when you are waiting for code to finish you will open up a youtube video and slack off while your code finished 2 hours ago, this is for you.


## How to install it

```bash
pip install gmtu
```

## How to use it

### In terminal

On the GMTU app, you will see your fcm token. This token is used to send push notification to your phone through firebase's push notification system. Whenever you send your push notification, you will need this string.

Assuming you have this string now, in terminal do:
```bash
gmtu --fcm-token MY_FCM_TOKEN --content "A message"
```

This will send in what I call an OTU(one time update), and it will be shown on the app as an OTU.


### In Python

The gmtu library is mainly used for python interface. Right now the interface is quite simple.

You first initialize a gmtu instance:

```python
MY_FCM_TOKEN = "..."
gmtu_instance = gmtu(MY_FCM_TOKEN)
```

You then can use this instance to send an OTU:
```python
gmtu_instance.sendOTU("OTU Message")
```

You can also use the instance like tqdm:
```python
for i in gmtu_instance(range(123), event_name = "for loop test 2")
  pass
```

The instance will then decide when to send an update to the phone. As default(currently not configurable), it will send a progress update ever 10% or it has been 2 seconds since the last update. This is to avoid spamming updates and other issues with how messages are handled/delivered, which we will detail soon.


## Technical Details and Privacy Concerns

### Database

If you inspect the GMTU project you will notice that it uses supabase as backend. All messages are sent using a supabase edge function. Which may concern some people as in are we collecting any data in the backend.

The short answer is **No**. But we maybe doing it in the future, let me explain it one by one.

The existance of the edge function is to facilitate sending the message using firebase's fcm service. To use this service, you will need to regiseter the app with firebase, and also get a bearer token. This token doesn't have infinite lifetime so we have to refresh this token and store it in the database. The edge function will have direct access to this token by using a service role key to access the database. Without exposing this bearer token, we need to use the edge function as a middle stop.

This design also means that on the app side, it never tries to contact supabase to check for progress. As a matter of fact, the app will only update when it receives a notification. The data carried alongside the notification will update the frontend.


## But why we maybe collecting your data in the future?

The sentence itself sounds evil. But in reality if we collect any data, it will be just the progress information. And here comes the question why.

As we use push notification to send informations, both firebase and Apple itself has limitations to prevent spamming.

For example, you may think sending a silent push notification with only data and no message(hence no banner, no nothing) is the best for updating a progress. But in reality, silent notifications are 1. not guaranteed to deliver, and 2. has a long cooldown on Apple's side to prevent app being waken up too often.

This means, without the app trying to contact supabase for any updates, we will need a way to send the data to the phone. Luckily, we can group the notification with an ID. This way, we can send progress as grouped notifications, and only the latest will be shown on your notification center.

This again, is not the perfect solution as Firebase doesn't let you send too many grouped messages.

So while spamming messages seems to be the perfect way to avoid database collecting any information, in reality I can't seem to find a way that guarantees the message to be delivered with only the notification system.

Hence, in the future, we may consider adding support for sending heartbeats to database server, and allowing the app to check for updates in real time.

So yes, to ensure that the updates are up to date without relying too much on a notification system, we may collect your data in the future.

## App download

ios: [link](https://apps.apple.com/us/app/gmtu/id6745209414)

android: N/A
