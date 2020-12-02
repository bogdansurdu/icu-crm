import msal
from flask import session, request, Blueprint, jsonify, render_template, url_for, redirect, jsonify
from datetime import datetime

conv = Blueprint('conv', __name__, url_prefix='/conv')

class Staff():
    # TODO: Create db which links staff to working hours, and get this data from the db
    name = "Ovidiu Badea"
    email = "ob@ic.ac.uk"

def add_new_conversation():
    staff = Staff()

    db_fields = ['student_name', 'student_email', 'staff_name', 'staff_email', 'seen_by_staff', 'seen_by_student']
    keys = ["\'"+session["user"]+"\'", "\'"+session["email"]+"\'", "\'"+staff.name+"\'", "\'"+staff.email+"\'", '0', '0']

    fields = []
    values = []
    for i in range(len(keys)):
        fields.append(db_fields[i])
        values.append(keys[i])
        
    from .db import get_db
    db = get_db()
    query = 'insert into conversation ({}) values({})'.format(', '.join(db_fields), ', '.join(values))
    db.execute(query)
    db.commit()

@conv.route('/', methods=('GET', 'POST'))
def data():
    if request.method == 'POST':
        from .db import get_db
        db = get_db()
        result = db.execute('select staff_name from conversation where student_name = "{0}" and staff_name = "{1}"'.format(session["user"], Staff().name)).fetchone() 
        print(result)
        if result is None:
            add_new_conversation()
    return render_template("all_chats.html", user=session["user"], active='conv')
        
    

@conv.route('/data', methods=('GET', 'POST'))
def return_data():
    from .db import get_db
    db = get_db()
    result = db.execute('select staff_name as Name, seen_by_student as Seen from conversation where student_name = "{0}" union select student_name as Name, seen_by_staff as Seen from conversation where staff_name = "{0}"'.format(session["user"])).fetchall() 
    if result is None:
        return jsonify('No entries')
    else:
        k = []
        for row in result:
            k.append({'name': row[0], 'seen': row[1]})
        return jsonify(k)

@conv.route('/conv_id_for', methods = ['POST'])
def get_id():
    from .db import get_db
    db = get_db()

    data = request.get_json()

    name1 = data['name1']
    name2 = data['name2']

    query = 'select id from conversation where (student_name = "{0}" and staff_name = "{1}") or (student_name = "{1}" and staff_name = "{0}")'.format(name1, name2)

    result = db.execute(query).fetchone()

    if result is None:
        return jsonify('No entries')
    else:
        temp = list(result)
        return jsonify({'result' : temp[0]})

        