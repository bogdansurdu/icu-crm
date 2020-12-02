from flask import session


def authHeader(json=False):
    if json:
        return {'Authorization': 'Bearer ' + session['token'], 'Content-Type': 'application/json'}
    return {'Authorization': 'Bearer ' + session['token']}


def graphDateTime(time):
    dateString = '%Y-%m-%dT%H:%M:00'
    return {'dateTime': time.strftime(dateString), 'timeZone': 'GMT Standard Time'}
