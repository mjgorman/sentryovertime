#!/usr/bin/env python3
import os
import logging
import requests
from time import sleep
from requests.auth import HTTPBasicAuth
from influxdb import InfluxDBClient
from datetime import datetime


class SentryOverTime(object):
    def __init__(self):
        self.sentry_api_key = os.getenv('SENTRY_API_KEY')
        self.sentry_base_url = 'https://sentry.io/api/0/projects/'
        self.sentry_account = os.getenv('SENTRY_ACCOUNT')
        self.sentry_query = '/issues/?statsPeriod=24h&query=is:unresolved'
        self.sentry_projects = str(os.getenv('SENTRY_PROJECTS')).split(',')
        self.influx_host = os.getenv('INFLUXDB_HOST', 'influxdb')
        self.influx_port = os.getenv('INFLUXDB_PORT', 8086)
        self.influx_user = os.getenv('INFLUXDB_USER', 'bob')
        self.influx_password = os.getenv('INFLUXDB_PASSWORD', 'bob')

    def count_issues(self, project):
        issues = requests.get('{0}{1}/{2}{3}'.format(self.sentry_base_url,
                                                     self.sentry_account,
                                                     project,
                                                     self.sentry_query),
                              auth=HTTPBasicAuth('{0}'.format(self.sentry_api_key), ''))
        return len(issues.json())

    def write_influxdb(self, json_body):
        client = InfluxDBClient(self.influx_host,
                                self.influx_port,
                                self.influx_user,
                                self.influx_password,
                                'sentry')
        client.create_database('sentry')
        client.write_points(json_body)

    def update(self):
        for project in self.sentry_projects:
            num_issues = self.count_issues(project)
            json_body = [{"measurement": "open_issues_{0}".format(project),
                          "fields": {"value": num_issues},
                          "time": "{0}".format(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                          }]
            self.write_influxdb(json_body)
            logger.info("Updated {0}".format(project))


if __name__ == "__main__":
    logger = logging.getLogger('SentryOverTime')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    logger.debug('Logging Started')
    over_time = SentryOverTime()
    while True:
        over_time.update()
        sleep(60)
