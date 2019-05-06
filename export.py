#!/usr/bin/python3 -W ignore
"""
This script exports all transactions from all accounts into a csv file.
It removes duplicates comming from transactions between Bunq accounts.
Hopefully it is usefull as an example as well.

"""
import warnings
warnings.filterwarnings("ignore")

from bunq.sdk.client import Pagination
from bunq.sdk.exception import BunqException
from bunq.sdk.context import ApiEnvironmentType, ApiContext, BunqContext
from bunq.sdk.model.generated import endpoint
import csv
from dateutil import parser as dateparse
import datetime
import pickle
from os.path import isfile

epoch = datetime.datetime.utcfromtimestamp(0)
def unix_time(dt):
    return (dt - epoch).total_seconds()

def unique_float(f):
    res = round(f)
    if res - f > 0.25:
        return frozenset([res,res-1])
    if res - f < -0.25:
        return frozenset([res,res+1])
    else:
        return res

def iter_payments(account):
    # # This is probably the best example
    last_result = None

    # Loop until end of account
    while last_result == None or last_result.value != []:
        if last_result == None:
            # We will loop over the payments in baches of 20
            pagination = Pagination()
            pagination.count = 100
            params = pagination.url_params_count_only
        else:
            # When there is already a paged request, you can get the next page from it, no need to create it ourselfs:
            try:
                params = last_result.pagination.url_params_previous_page
            except BunqException:
                break

        last_result = endpoint.Payment.list(
            params=params,
            monetary_account_id=account)

        if len(last_result.value) == 0:
            # We reached the end
            break

        # The data is in the '.value' field.
        for payment in last_result.value:
            yield payment


def all_transactions(dt = None):
    # This should be enough to ensure the whole account is included.
    if dt == None:
        dt = epoch

    env = ApiEnvironmentType.PRODUCTION

    if not isfile('bunq-production.conf'):
        raise Exception("No config file found, run start.py first.")

    # Reload the API context
    api_context = ApiContext.restore('bunq-production.conf')
    api_context.ensure_session_active()
    api_context.save('bunq-production.conf')

    BunqContext.load_api_context(api_context)

    # User info
    user = endpoint.User.get().value.get_referenced_object()

    # To get a list we want a pagination object.
    # When making a pagination object yourself you normally only set the 'count'
    # Then you get the url params from it using 'url_params_count_only'
    pagination = Pagination()
    pagination.count = 100

    accounts = []

    all_monetary_account_bank = endpoint.MonetaryAccountBank.list(
        pagination.url_params_count_only).value

    for monetary_account_bank in all_monetary_account_bank:
        if monetary_account_bank.status == "ACTIVE":
            accounts.append(monetary_account_bank)

    all_monetary_account_savings = endpoint.MonetaryAccountSavings.list(
    pagination.url_params_count_only).value

    for monetary_account_savings in all_monetary_account_savings:
        if monetary_account_savings.status == "ACTIVE":
            accounts.append(monetary_account_savings)

    # Reload where we where last time.
    try:
        with open("seen.pickle","rb") as fp:
            seen = pickle.load(fp)
    except Exception:
        seen = set()
    # We will keep a list of transactions that are already processed in this set.
    # The transactions will contain:
    #  - A set of the two possible roundings of the datestamp
    #  - The ammount of money in absolute value
    #  - The description
    #  - A set containing the two accounts involved
    # The goal here is that this representation is the same for two accounts when shifting money arround.

    for a in accounts:
        aid = a.id_
        # keep track of where we are
        print(a.description)


        for p in iter_payments(aid):
            # python can handle the dates we get back
            date = dateparse.parse(p.created)

            #round to the second to get a (sort of) unique, but not to precise timestamp
            since_epoch = int(unix_time(date))

            row = [p.created,
                   p.amount.value,
                   p.description.replace("\r","").replace("\n"," "),
                   p.alias.label_monetary_account.iban,
                   p.counterparty_alias.label_monetary_account.iban]

            # frozenset can be used to hash a set, so the order does not matter.
            summary = (unique_float(since_epoch), #take both so there is norounding problem
                       abs(float(p.amount.value)),
                       p.description,
                       frozenset([p.alias.label_monetary_account.iban,
                            p.counterparty_alias.label_monetary_account.iban]))

            # Still in range
            if date >= dt:
                if summary in seen:
                    continue
                else:
                    seen.add(summary)
                    yield(row)
            else:
                break



    with open("seen.pickle","wb") as fp:
        pickle.dump(seen, fp)


def main():
    from dateutil import parser

    last_week = datetime.datetime.now() - datetime.timedelta(7)
    # Save in a file with the current timestamp
    with open('export/bunq-%s.csv' % (str(datetime.datetime.now())), 'w') as csvfile:
        spamwriter = csv.writer(csvfile)
        for row in all_transactions(last_week):
            spamwriter.writerow(map(str,row))


if __name__ == '__main__':
    main()
