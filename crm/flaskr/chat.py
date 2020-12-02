import msal
from flask import session, request, Blueprint, jsonify, render_template, url_for, redirect, jsonify
from datetime import datetime

chat = Blueprint('chat', __name__, url_prefix='/chat')

def add_new_message(message):
    keys = ['conv_id', 'msg', 'date_time', 'sender']
    db_fields = ['conversation_id', 'message', 'created', 'author']
    fields = []
    values = []
    for i in range(len(keys)):
        if keys[i] in message:
            fields.append(db_fields[i])
            values.append("'" + message.get(keys[i]) + "'")
        elif keys[i] == 'created':
            fields.append('created')
            values.append("'" + str(datetime.now()) + "'")
    from .db import get_db
    db = get_db()

    db.execute('insert into messages ({}) values({})'.format(', '.join(fields), ', '.join(values)))

    db.execute("update conversation set seen_by_student = 1 where id = {0} and not student_name = '{1}'".format(message.get(keys[0]), session["user"]))
    db.execute("update conversation set seen_by_staff = 1 where id = {0} and not staff_name = '{1}'".format(message.get(keys[0]), session["user"]))
        
    db.commit()

@chat.route('/<conv_id>', methods=('GET', 'POST'))
def data(conv_id):
    if request.method == 'POST':
        try:
            body = request.json
        except:
            return jsonify({'error_msg': 'Failed to decode JSON body'}), 400
        add_new_message(request.form)
    return render_template("chat_window.html", id = conv_id, user=session["user"], version=msal.__version__)
        
    

@chat.route('/<id>/data', methods=('GET', 'POST'))
def return_data(id):
    from .db import get_db
    db = get_db()
    result = db.execute('select author, message from messages where conversation_id = {}'.format(id)).fetchall()
    if result is None:
        return jsonify('No entries')
    else:
        result1 = db.execute("update conversation set seen_by_student = 0 where id = {0} and student_name = '{1}'".format(id, session["user"]))
        print(result1.rowcount, "record(s) affected")
        result1 = db.execute("update conversation set seen_by_staff = 0 where id = {0} and staff_name = '{1}'".format(id, session["user"]))
        print(result1.rowcount, "record(s) affected")
        db.commit()
        k = []
        for i in result:
            l = []
            for j in i:
                if j is None:
                    j = 'N/A'
                l.append(str(j))
            k.append(': '.join(l))
        return jsonify('<br>'.join(k))
    