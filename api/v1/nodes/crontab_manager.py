#!/usr/bin/python3

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from crontab import CronTab
import getpass
import json
import os

def updateCronTab(node, sync=None):
    """
    Uses crontab to manage the service triggers
    Found the job by Comment
    and update the values
    cal:
        - the date from the client
    sync:
        - the actual time from the client
    
    """
    cal = json.loads(node.analisis_params)['date']
    params = json.loads(node.analisis_params)
    if sync:
        sys_time = datetime.now()
        print('14: ', *cal, sync, sys_time)
        # check if the time to save is before the actual
        if datetime(*cal) < sys_time:
            print('You are saving a date before the actual')
        month_diff = sys_time.month - sync[1]
        day_diff = sys_time.day - sync[2]
        hour_diff = sys_time.hour - sync[3]
        def_time = datetime(*cal) + \
                   timedelta(days=day_diff, hours=hour_diff) + \
                   relativedelta(months=month_diff)
    else:
        def_time = datetime(*cal)
    cmd = '/usr/bin/python3 {}/api/v1/nodes/job.py {} > /usr/src/app/date_test.txt 2>&1'
    cmd = cmd.format(os.getcwd(), node.id)
    cron = CronTab(user='root')
    exists = False
    print('Parameters for the Cron Job')
    print(json.dumps(params, indent=2))
    print('Definitive Time', def_time)
    for job in cron:
        if job.comment == node.id:
            if 'active' not in params or params['active'] == False:
                print('desactive this cron job')
                cron.remove(job)
            else:
                job.setall(def_time)
                if 'frequency' in params:
                    print(params['frequency'])
                    if params['frequency'] == 'hourly':
                        job.hour.every(1)
                        job.day.every(1)
                    elif params['frequency'] == 'daily':
                        job.day.every(1)
                        job.month.every(1)
                    elif params['frequency'] == 'weekly':
                        job.day.every(7)
                        job.month.every(1)
                    elif params['frequency'] == 'monthly':
                        job.month.every(1)
            exists = True
    if not exists and 'active' in params:
        job = cron.new(command=cmd, comment=node.id)
        job.setall(def_time)
        if 'frequency' in params:
            print(params['frequency'])
            if params['frequency'] == 'hourly':
                job.hour.every(1)
                job.day.every(1)
            elif params['frequency'] == 'daily':
                job.day.every(1)
                job.month.every(1)
            elif params['frequency'] == 'weekly':
                job.day.every(7)
                job.month.every(1)
            elif params['frequency'] == 'monthly':
                job.month.every(1)
    cron.write()
    os.system('/etc/init.d/cron start')
    print(def_time)
    return node.id

def deleteCronTab(node, sync=None):
    """
    update crontab to remove the node services
    """
    return True