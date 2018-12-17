# bunq-example-export
An example project for Bunq banking &amp; Python, the script exports all transactions from all accounts to .csv

## How to use

Install the bunq sdk:
```
pip3 install bunq_sdk --upgrade
```
Or, install as a user:
```
pip3 install bunq_sdk --upgrade --user
```

Get an api key from the Bunq app under `Settings -> Developers`.
Then, run `start.py --api-key <YOUR API KEY>` to generate a config file.
*Be carefull with this file, it gives access to your bunq accounts!*
You only need to run this ones.

Now we are setup, you can run `export.py` to export the last weeks worth of transactions from all your accounts, excluding transactions seen before.

## How to read the example

The `start.py` file is taken from the Bunq examples. 
As for the `export.py`, most should be clear from the comments. 
A general point that took me a while to figure out is that the Python SDK for bunq is not really a SDK.
It is a set of automatically generated functions that correspond with the API endpoints.
This means you will need to do a lot of coding yourself, there is no nice `all_accounts()` function. 
