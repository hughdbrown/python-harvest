#!/usr/bin/env python3
from __future__ import print_function

import sys
import os
import os.path as op
from glob import glob
from csv import DictWriter, QUOTE_ALL

from harvest import Harvest
import simplejson
import logging


logger = logging.getLogger(__name__)

HARVEST_CREDENTIALS = "~/.harvest"
LOG_PATH = op.expanduser(op.join("~", "logs"))
LOG_FILE = op.join(LOG_PATH, "harvest.log")


def get_credentials():
    """
    Harvest credentials are stored as a JSON file on the file system
    """
    full_path = op.expanduser(HARVEST_CREDENTIALS)
    with open(full_path) as f:
        return simplejson.loads(f.read())


def get_client():
    credentials = get_credentials()
    app, email, password = (credentials[key] for key in ("app", "email", "password"))
    url = "https://{0}.harvestapp.com".format(app)
    logger.info(msg="url is {0}".format(url))
    return Harvest(url, email, password)


def test_json(json):
    """
    Test for a failed authentication request
    """
    return not (type(json) is dict and json.get("message") == "Authentication failed for API request.")


def main(client):
    """
    Read Harvest credentials and pull down Harvest data
    """
    errors = 0
    # Primary objects
    mapping_fns = [
        ("clients.json", client.clients),
        ("projects.json", client.projects),
        ("contacts.json", client.contacts),
        ("people.json", client.people),
        ("tasks.json", client.tasks),
        ("invoices.json", client.invoices),
    ]
    for filename, fn in mapping_fns:
        json = fn()
        if test_json(json):
            logger.info(filename)
            with open(filename, "w") as handle:
                handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))
        else:
            logger.error(msg="{0}: Authentication failed".format(filename))
            errors += 1

    # Lists of data
    mapping_lists = [
        # ("expense_categories.json", client.expense_categories),
    ]
    for filename, list_attr in mapping_lists:
        json = list_attr
        if test_json(json):
            logger.info(filename)
            with open(filename, "w") as handle:
                handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))
        else:
            logger.error(msg="{0}: Authentication failed".format(filename))
            errors += 1

    if errors:
        return errors

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
        logger.info(filename)
        json = []
        for id in ids:
            logger.info(msg="{0}".format(id))
            d = fn(id, **kwargs)
            if d:
                json += d
        with open(filename, "w") as handle:
            handle.write(simplejson.dumps(json, sort_keys=True, indent="    "))
    return 0

def json_to_csv():
    for json_filename in glob("*.json"):
        csv_filename = op.splitext(json_filename)[0] + ".csv"
        logger.info("{0} -> {1}".format(json_filename, csv_filename))

        # Read the JSON
        with open(json_filename, "r") as handle:
            data = simplejson.loads(handle.read())
        logger.info("{0} JSON records".format(len(data)))

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
                logger.info("{0} CSV rows".format(i))
            except IndexError:
                # No rows in JSON
                logger.error(msg="No data in '{0}'".format(json_filename))


def setup_logger():
    """
    Set up the logger to write out system actions
    """
    logger.setLevel(logging.INFO)
    if not op.exists(LOG_PATH):
        os.makedirs(LOG_PATH)
    formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s")
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


if __name__ == '__main__':
    setup_logger()
    try:
        client = get_client()
        errors = main(client)
        if not errors:
            json_to_csv()
        sys.exit(errors)
    except Exception as exc:
        logger.exception(exc)
    finally:
        print("See log at: {0}".format(LOG_FILE), file=sys.stderr)
