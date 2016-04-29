# Overview
This is sample code that actually works.

# Requirements
## Credentials file
The code requires a JSON-formatted file in the user's home directory named `.harvest` that contains the user name, password, and account name of a Harvest account. The format is:

```
{
    "app": "SOME APPLICATION NAME",
    "email": "EMAIL ADDRESS",
    "password": "PASSWORD"
}
```

In my case, it looks like:

```
{
    "app": "hughdbrown",
    "email": "hughdbrown@yahoo.com",
    "password": "Un1c0rns s1ng the bluez!!!"
}
```

# Results
When run, this code produces a JSON file for each variety of entity type that Harvest supports.
