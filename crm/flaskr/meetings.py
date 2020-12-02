from flask import session, Blueprint, request, url_for, render_template, redirect
import requests
from requests_oauthlib import OAuth2Session
import sys
from . import app_config
from .responseTemplates import err400, err404
from datetime import datetime, timedelta
from .utils import authHeader, graphDateTime
from json import dumps, dump
from .ad import tokenExpired
from .db import get_db

bp = Blueprint('calendar', __name__, url_prefix='/calendar')
sys.path.append('/usr/local/lib/python3.8/site-packages/')

def updateMeeting(start, id):
    start = 'set ' + start.strftime('%h %d, %H:%M')
    query = "update ticket set response_meeting = '{}' where id={}".format(start, id)
    db = get_db()
    db.execute(query)
    db.commit()



@bp.route('/availability', methods=('GET', 'POST'))
def availability():
    # if tokenExpired():
    #     return redirect(url_for('ad.expired'))
    auth = False
    if 'user' in request.args and 'id' in request.args:
        id = request.args.get('id')
        ticket = get_db().execute('select * from ticket where id={}'.format(id)).fetchone()
        if ticket is None:
            return err404('An invalid ticket id #{} was in your url'.format(id))
        if session.get('email') == ticket[3] and request.args.get('user') == ticket[12]:
            meeting = ticket[14]
            if 'set' not in meeting and meeting != None and meeting != '':
                auth = True
    if not auth:
        return err400("This isn't allowed")
    if request.method == 'GET':
        if 'user' in request.args:
            user = request.args.get('user')
        else:
            return err400('The user parameter is required in the query string')
        duration = str(request.args.get('duration', 9))
        if duration.isdigit():
            duration = int(duration)
        else:
            return err400('Duration must be a valid integer')
        if 'start' in request.args:
            time = datetime.strptime(request.args.get('start'), '%d.%m.%Y')
        else:
            time = datetime.now()
        startTime = datetime(year=time.year, month=time.month, day=time.day, hour=9)
        print(startTime)

        dateString = '%Y-%m-%dT%H:%M:00'
        start = graphDateTime(startTime)
        endTime = (startTime + timedelta(hours=duration))
        end = graphDateTime(endTime)
        body = {'schedules': [user], 'startTime': start, 'endTime': end}
        headers = authHeader(json=True)
        headers['Prefer'] = 'outlook.timezone="GMT Standard Time"'
        prettyString = '%h %d %Y, %H:%M'
        r = requests.post(url='https://graph.microsoft.com/v1.0/me/calendar/getSchedule', headers=headers, data=dumps(body))
        # TODO: Handle cases where response is bad (due to token expiry)
        dump(r.json(), open('schedule.json', 'w'), indent=2)
        schedule = r.json()['value'][0]['scheduleItems']
        page_data = []
        timeString = '%d %h, %H:%M'
        availability = {
            'free': 'Free'
        }
        # TODO: Join consecutive busy sessions
        for item in schedule:
            print(item['start']['dateTime'][:-8])
            item_start = datetime.strptime(item['start']['dateTime'][:-8], dateString)
            item_end = datetime.strptime(item['end']['dateTime'][:-8], dateString)
            if not item_start < startTime:
                page_data.append([availability.get(item['status'], 'Busy'), item_start.strftime(timeString),
                                  item_end.strftime(timeString)])

        return render_template('schedule.html', name=user, start=startTime.strftime(prettyString),
                               end=endTime.strftime(prettyString), schedule=page_data, day=startTime.strftime('%Y-%m-%dT'))
    elif request.method == 'POST':
        dateString = '%Y-%m-%dT%H:%M'
        day = request.form.get('day')
        start = graphDateTime(datetime.strptime(day+request.form.get('start'), dateString))
        end = graphDateTime(datetime.strptime(day+request.form.get('end'), dateString))
        body = {
            'subject': request.form.get('title', 'CRM Request Meeting'),
            'start': start,
            'end': end,
            'attendees': [
                {
                    'emailAddress': {
                        'address': request.form.get('user')
                    },
                    'type': 'required'
                }
            ]
        }
        if 'description' in request.form:
            body['body'] = {
                'contentType': 'Text',
                'content': request.form.get('description')
            }
        r = requests.post(url='https://graph.microsoft.com/v1.0/me/events', data=dumps(body), headers=authHeader(json=True))
        id = request.args.get('id')
        updateMeeting(datetime.strptime(day+request.form.get('start'), dateString), request.args.get('id'))
        return redirect(url_for('tickets.base_ticket', id=id))


@bp.route('/book')
def bookMeeting():
    return session.get('token', 'No token found')


graph_url = 'https://graph.microsoft.com/v1.0'


@bp.route('/')
def get_user():
    graph_client = OAuth2Session(state=session['state'], scopes=app_config.SCOPE, redirect_uri=url_for('meetings'
                                                                                                       '.bookMeeting'))
    # Send GET to /me
    token = graph_client.fetch_token()
    user = graph_client.get('{0}/me'.format(graph_url))
    # Return the JSON result
    return str(user.json())
