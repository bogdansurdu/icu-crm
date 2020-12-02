from flask import render_template


def err404(msg):
    return render_template('error.html', code=404, msg=msg)

def err400(msg):
    return render_template('error.html', code=400, msg=msg)