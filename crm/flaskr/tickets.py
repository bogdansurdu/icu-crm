from flask import request, Blueprint, jsonify, render_template, url_for, redirect, session
from datetime import datetime, timedelta
from .responseTemplates import err404
from .db import get_db

bp = Blueprint('tickets', __name__, url_prefix='/tickets')


def timeWaiting(diff, delta=False):
    if not delta:
        diff = datetime.now() - diff
    hours = int(diff.seconds / 3600)
    if diff.days > 2:
        return '{} days'.format(diff.days)
    elif diff.days > 1:
        return '1 day {} hours'.format(hours)
    else:
        minutes = int((diff.seconds % 3600) / 60)
        if hours > 0:
            return '{} hours {} minutes'.format(hours, minutes)
        else:
            if minutes < 2:
                return 'Just now'
            return '{} minutes'.format(minutes)


def averageWaitTime(department=None, default='No closed tickets'):
    query = "select created, response_time from ticket where response_time is not null"
    if department:
        query += " and department = '{}'".format(department)
    from .db import get_db
    times = list(get_db().execute(query).fetchall())
    if len(times) == 0:
        return default
    total = timedelta()
    for row in times:
        total += row[1] - row[0]
    avg = total / len(times)
    s = timeWaiting(avg, delta=True)
    if s == 'Just now':
        return default
    else:
        return s


def addResponse(response, id):
    keys = ['response', 'responder', 'responder_email', 'response_meeting']
    values = ["response_time = '" + str(datetime.now()) + "'"]
    for i in range(len(keys)):
        if keys[i] in response:
            values.append(keys[i] + ' = ' + "'" + response.get(keys[i]).replace("'", "''") + "'")
    from .db import get_db
    query = 'update ticket set {} where id = {}'.format(', '.join(values), id)
    print('\n\n' + query + '\n\n')
    db = get_db()
    db.execute(query)
    db.commit()


def addNewTicket(ticket):
    keys = ['department', 'name', 'email', 'group', 'claim', 'created', 'title', 'body']
    db_fields = ['department', 'author_name', 'author_email', 'author_group', 'claim_number', 'created', 'title',
                 'body']
    fields = []
    values = []
    for i in range(len(keys)):
        if keys[i] in ticket:
            fields.append(db_fields[i])
            values.append("'" + ticket.get(keys[i]).replace("'", "''") + "'")
        elif keys[i] == 'created':
            fields.append('created')
            values.append("'" + str(datetime.now()) + "'")
    from .db import get_db
    db = get_db()
    query = 'insert into ticket ({}) values({})'.format(', '.join(fields), ', '.join(values))
    db.execute(query)
    db.commit()


@bp.route('')
def personal():
    if request.method == 'GET':
        from .db import get_db
        db = get_db()
        filter = request.args.get('filter', '')
        if filter != '':
            if filter == 'open':
                filter = ' and response is null'
            elif filter == 'closed':
                filter = ' and response is not null'
        if request.args.get('order') == 'old':
            order = ' order by created asc'
        else:
            order = ' order by created desc'

        email = session.get('email')
        result = db.execute("select * from ticket where author_email = '{}'{}".format(email, filter + order)).fetchall()
        if result is not None:
            result = list(result)
        for i in range(len(result)):
            result[i] = list(result[i])
            result[i][6] = timeWaiting(result[i][6])
            for j in range(len(result[i])):
                if result[i][j] == '':
                    result[i][j] = 'N/A'
        open = db.execute(
            "select count(*) from ticket where author_email = '{}' and response is null".format(email)).fetchone()[0]
        closed = db.execute(
            "select count(*) from ticket where author_email = '{}' and response is not null".format(email)).fetchone()[
            0]
        return render_template('personal_tickets.html', tickets=result, active='my_tickets', open=open, closed=closed,
                               filter=request.args.get('filter'), order=request.args.get('order'))


@bp.route('/all', methods=('GET', 'POST'))
def data():
    if request.method == 'GET':
        from .db import get_db
        db = get_db()
        filter = request.args.get('filter', '')
        if filter != '':
            if filter == 'open':
                filter = ' where response is null'
            elif filter == 'closed':
                filter = ' where response is not null'
        dept = str(request.args.get('dept', ''))
        if dept != '':
            depts = {
            '0' : 'Commercial Services',
            '1' : 'Membership Services',
            '2' : 'Student Representation',
            '3' : 'Marketing',
            '4' : 'Opportunities & Development'
            }
            dept = depts.get(dept)
            if dept is None:
                dept = ''
            else:
                if filter == '':
                    dept = " where department = '{}'".format(dept)
                else:
                    dept = " and department = '{}'".format(dept)
        if request.args.get('order') == 'old':
            order = ' order by created asc'
        else:
            order = ' order by created desc'
        result = db.execute('select * from ticket {}'.format(filter + dept + order)).fetchall()
        if result is not None:
            result = list(result)
        for i in range(len(result)):
            result[i] = list(result[i])
            result[i][6] = timeWaiting(result[i][6])
            for j in range(len(result[i])):
                if result[i][j] == '':
                    result[i][j] = 'N/A'
        open = db.execute("select count(*) from ticket where response is null").fetchone()[0]
        closed = db.execute("select count(*) from ticket where response is not null").fetchone()[0]
        return render_template('tickets.html', tickets=result, active='tickets', open=open, closed=closed,
                               filter=request.args.get('filter'), order=request.args.get('order'),
                               dept=request.args.get('dept'), avg=averageWaitTime())
    elif request.method == 'POST':
        args = []
        order = request.form['order']
        if order != 'None':
            args.append('order={}'.format(order))
        filter = request.form['filter']
        if filter != 'None':
            args.append('filter={}'.format(filter))
        depts = [
            'Commercial Services',
            'Membership Services',
            'Student Representation',
            'Marketing',
            'Opportunities & Development'
        ]
        dept = request.form.get('department')
        if dept != 'All':
            args.append('dept={}'.format(depts.index(dept)))
        if len(args) > 0:
            args = '?' + '&'.join(args)
        else:
            args = ''
        return redirect(url_for('tickets.data')+args)

@bp.route('/submit', methods=('GET', 'POST'))
def submit():
    if request.method == 'GET':
        return render_template('submit.html', active='submit')
    if request.method == 'POST':
        ticket = {}
        for key in request.form:
            ticket[key] = request.form.get(key)
        ticket['name'] = session.get('user')
        ticket['email'] = session.get('email')
        topics = [
            ['Bars', 'Shop'],
            ['Club budgets', 'Clubs and Societies', 'Projects'],
            ['Academic Representation', 'Wellbeing Representation'],
            ['Social Media', 'Takeovers'],
            ['Emerging Leaders']
        ]
        redirects = {
            0 : 'Commercial Services',
            1 : 'Membership Services',
            2 : 'Student Representation',
            3 : 'Marketing',
            4 : 'Opportunities & Development'
        }
        dept = ticket.get('department')
        if dept == 'Other':
            ticket.pop('department')
        else:
            for i in range(len(topics)):
                if dept in topics[i]:
                    ticket['department'] = redirects[i]
        addNewTicket(ticket)
        return redirect(url_for('tickets.personal'))


@bp.route('/<id>')
def base_ticket(id):
    from .db import get_db
    result = get_db().execute(
        "select * from ticket where id = {} and author_email = '{}'".format(id, session.get('email'))).fetchone()
    if result is None:
        return err404('No tickets with id #{} exist, or you cannot view them'.format(id))
    ticket = []
    for i in result:
        if i is None or i=='':
            i = 'N/A'
        ticket.append(i)
    ticket[6] = ticket[6].strftime('%h %d, %H:%M')
    if ticket[13] != 'N/A':
        ticket[13] = ticket[13].strftime('%h %d, %H:%M')
    print(ticket[14])
    return render_template('simple_ticket.html', ticket=ticket, active='my_tickets')


@bp.route('/staff/<id>', methods=['GET', 'POST'])
def ticket(id):
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'comment':
            comment = {
                'ticket_id': id,
                'name': session['user'],
                'email': session['email'],
                'comment': request.form.get('message').replace("'", "''")
            }
            from .comment import addNewComment
            addNewComment(comment)
        elif action == 'response':
            print('submitting a response')
            response = {
                'response': request.form.get('message'),
                'responder': session.get('user'),
                'responder_email': session.get('email')
            }
            if 'date' in request.form:
                try:
                    parts = request.form.get('date').split('-')
                    response['response_meeting'] = parts[2] + '.' + parts[1] + '.' + parts[0]
                except IndexError:
                    pass
                # print('date is {}'.format(response['response_meeting']))
            addResponse(response, id)
        return redirect(url_for('tickets.ticket', id=id))

    from .db import get_db
    result = get_db().execute('select * from ticket where id = {}'.format(id)).fetchone()
    if result is None:
        return err404('No ticket with id of {} was found'.format(id))
    ticket = []
    for i in result:
        if i is None or i=='':
            i = 'N/A'
        ticket.append(i)
    ticket[6] = ticket[6].strftime('%h %d, %H:%M')
    if ticket[13] != 'N/A':
        ticket[13] = ticket[13].strftime('%h %d, %H:%M')
    comments = get_db().execute(
        "select * from comments where ticket_id = {} order by created".format(id)).fetchall() or []
    for i in range(len(comments)):
        comment = list(comments[i])
        comment[5] = comment[5].strftime('%h %d, %H:%M')
        comments[i] = comment
    print(ticket)
    return render_template('ticket.html', ticket=ticket, comments=comments, active='tickets')
