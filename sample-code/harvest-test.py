#!/usr/bin/env python3
from __future__ import print_function

import sys
import os.path
from glob import glob
from csv import DictWriter, QUOTE_ALL

from harvest import Harvest
import simplejson

HARVEST_CREDENTIALS = "~/.harvest"


def get_credentials():
    """
    Harvest credentials are stored as a JSON file on the file system
    """
    full_path = os.path.expanduser(HARVEST_CREDENTIALS)
    with open(full_path) as f:
        return simplejson.loads(f.read())


def get_client():
    print("get_credentials", file=sys.stderr)
    credentials = get_credentials()
    app, email, password = (credentials[key] for key in ("app", "email", "password"))
    url = "https://{0}.harvestapp.com".format(app)
    return Harvest(url, email, password)


def main(client):
    """
    Read Harvest credentials and pull down Harvest data
    """
    # Primary objects
    print("main", file=sys.stderr)
    mapping_fns = [
        ("clients.json", client.clients),
        ("projects.json", client.projects),
        ("contacts.json", client.contacts),
        ("people.json", client.people),
        ("tasks.json", client.tasks),
        ("invoices.json", client.invoices),
    ]
    for filename, fn in mapping_fns:
        print(filename, file=sys.stderr)
        json = fn()
        with open(filename, "w") as handle:
            handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))

    # Lists of data
    mapping_lists = [
        ("expense_categories.json", client.expense_categories),
    ]
    for filename, list_attr in mapping_lists:
        print(filename, file=sys.stderr)
        json = list_attr
        with open(filename, "w") as handle:
            handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))

    with open("projects.json", "r") as handle:
        projects = simplejson.loads(handle.read())
        project_ids = [d["project"]["id"] for d in projects]

    with open("clients.json", "r") as handle:
        clients = simplejson.loads(handle.read())
        client_ids = [d["client"]["id"] for d in clients]

    # Projects and clients (APIs that take IDs as arguments)
    ALL_2016 = {"start_date": "2016-01-01", "end_date": "2016-12-31"}
    mapping_ids = [
        # expenses_for_project(self, project_id, start_date, end_date
        ("expenses_for_project.json", client.expenses_for_project, ALL_2016, project_ids),

        # get_all_tasks_from_project(self, project_id)
        ("tasks_for_project.json", client.get_all_tasks_from_project, {}, project_ids),

        # timesheets_for_project(self, project_id, start_date, end_date)
        ("timesheets_for_project.json", client.timesheets_for_project, ALL_2016, project_ids),

        # projects_for_client(self, client_id)
        ("projects_for_client.json", client.projects_for_client, {}, client_ids),
    ]

    for filename, fn, kwargs, ids in mapping_ids:
        print(filename, file=sys.stderr)
        json = []
        for id in ids:
            print("\t", id, file=sys.stderr)
            d = fn(id, **kwargs)
            if d:
                json += d
        with open(filename, "w") as handle:
            handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))


def json_to_csv():
    print("json_to_csv", file=sys.stderr)
    for json_filename in glob("*.json"):
        csv_filename = os.path.splitext(json_filename)[0] + ".csv"
        print("{0} {1} -> {2}".format("-" * 30, json_filename, csv_filename), file=sys.stderr)

        # Read the JSON
        with open(json_filename, "r") as handle:
            data = simplejson.loads(handle.read())
        print("{0} JSON records".format(len(data)), file=sys.stderr)

        # Write the CSV
        with open(csv_filename, "w") as handle:
            try:
                # Get the first item in the list of dicts,
                # get the first key (the only key)
                d1 = data[0]
                key = d1.keys()[0]

                # Sort the keys in the dict: they will be the headers for the CSV
                fields = sorted(d1[key].keys())
                dw = DictWriter(handle, fieldnames=fields, quoting=QUOTE_ALL)
                dw.writeheader()

                i = 0
                for row in data:
                    d0 = row[key]
                    d = {field: d0.get(field) for field in fields}
                    dw.writerow(d)
                    i += 1
                print("{0} CSV rows".format(i), file=sys.stderr)
            except IndexError:
                # No rows in JSON
                print("No data in '{0}'".format(json_filename), file=sys.stderr)


if __name__ == '__main__':
    try:
        client = get_client()
        main(client)
        json_to_csv()
    except Exception as exc:
        print(exc)
