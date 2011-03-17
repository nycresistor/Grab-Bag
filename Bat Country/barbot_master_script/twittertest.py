#! /bin/python

import twitter

client = twitter.Api(username="luckyloathing",password="2600Ohms")
client.PostUpdate("Hello World!")