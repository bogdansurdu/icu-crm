from flask import request, Blueprint, jsonify, render_template, url_for, redirect
from datetime import datetime

comm = Blueprint('comment', __name__, url_prefix='/comment')


def addNewComment(comment):
    keys = ['ticket_id', 'name', 'email', 'comment', 'created']
    db_fields = ['ticket_id', 'author_name', 'author_email', 'comment', 'created']
    fields = []
    values = []
    for i in range(len(keys)):
        if keys[i] in comment:
            fields.append(db_fields[i])
            values.append("'" + comment.get(keys[i]) + "'")
        elif keys[i] == 'created':
            fields.append('created')
            values.append("'" + str(datetime.now()) + "'")
    print(values)
    from .db import get_db
    db = get_db()
    query = 'insert into comments ({}) values ({})'.format(', '.join(fields), ', '.join(values))
    print(query)
    db.execute(query)
    db.commit()


# This is used to submit a comment and if submitted properly, redirects to the comments for that specific ticket.
@comm.route('/submit', methods=('GET', 'POST'))
def submit_comment():
    if request.method == 'GET':
        return render_template('comments/submit_comments.html')
    # Redirects to the comments for the specific ticket where the comment was posted (may need some rewiring).
    if request.method == 'POST':
        addNewComment(request.form)
        tid = request.form.get("ticket_id", "")
        return redirect(url_for('comment.return_ticket_comments', ticket_id=tid))


# Displays the comments for a specific ticket by rendenring a template taking the ticket as a parameter and the comment
# list as another parameter.
@comm.route('<ticket_id>/comments', methods=('GET', 'POST'))
def return_ticket_comments(ticket_id):
    if request.method == 'GET':
        from .db import get_db
        db = get_db()
        result = db.execute(
            'select author_name, comment from comments where ticket_id = {}'.format(ticket_id)).fetchall()
        result_ticket = db.execute('select * from ticket where id = {}'.format(id)).fetchone()
        if result_ticket is None:
            return jsonify('Invalid ticket')
        elif result is None:
            return jsonify('No entries')
        else:
            print(list(result))
            return render_template('comments/comments.html', ticket=result_ticket, comments=list(result))
    elif request.method == 'POST':
        if 'Content-Type' in request.headers and request.headers['Content-Type'] == 'application/json':
            try:
                body = request.json
            except:
                return jsonify({'error_msg': 'Failed to decode JSON body'}), 400
            addNewComment(body)
            return 'You sent a post request!'
        else:
            return jsonify({'error_msg': '"Content-Type" header is required for post method'}), 400


@comm.route('<ticket_id>/comments/<comment_id>', methods=['GET'])
def comment(ticket_id, comment_id):
    from .db import get_db
    result = get_db().execute(
        'select * from comments where id = {}, ticket_id = {}'.format(comment_id, ticket_id)).fetchone()
    if result is None:
        return jsonify({'error_msg': 'No comment with that id or ticket id was found'}), 404
    else:
        print(list(result))
        k = []
        for i in result:
            l = []
            for j in i:
                if j is None:
                    j = 'N/A'
                l.append(str(j))
            k.append(': '.join(l))
        return jsonify('\n'.join(k))
