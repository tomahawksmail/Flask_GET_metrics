from flask import Flask, request, send_file, render_template, redirect, session
from datetime import datetime
import pymysql.cursors
import creds
import csv
from logging import FileHandler, WARNING

app = Flask(__name__, static_folder='csv')
file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)
connection = pymysql.connect(host=creds.host,
                             user=creds.user,
                             password=creds.password,
                             database=creds.database,
                             cursorclass=pymysql.cursors.DictCursor)


@app.route('/', methods=['GET'])
def root():
    return """<!DOCTYPE html>
                <html lang="en">
                <head>
                  <meta charset="UTF-8">
                  <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body>
                  <div class="text-container">
                    <marquee behavior="alternate" direction="left" scrollamount="39">
                      <h1 style="font-size: 72px;">Hello from backend!</h1>
                    </marquee>
                  </div>
                </body>
                </html>"""


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    return """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                      <meta charset="UTF-8">
                      <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    </head>
                    <body>
                      <div class="text-container">
                        <marquee behavior="alternate" direction="left" scrollamount="39">
                          <h1 style="font-size: 72px;">You don't have the rights</h1>
                        </marquee>
                      </div>
                    </body>
                    </html>"""


@app.route('/getcsv', methods=['POST', 'GET'])
def show():
    version = creds.version
    remote_IP = request.environ['REMOTE_ADDR']
    print(remote_IP)
    if remote_IP not in creds.whiteIP:
        return redirect("/logout")

    sql = connection.cursor()
    if request.method == 'GET':
        sql.execute("""SELECT * FROM (SELECT * FROM new_events  ORDER BY evid DESC LIMIT 15)Var1
                        ORDER BY evid ASC""")
        result = sql.fetchall()
        exportlist = []
        for item in result:
            listval = (list(item.values()))
            exportlist.append(listval)

        return render_template('export.html', exportlist=exportlist, version=version)

    elif request.method == 'POST':
        start = request.form['date_start'] if request.form['date_start'] else None
        end = request.form['date_end'] if request.form['date_end'] else None
        if "apply" in request.form:
            if start is None or end is None:
                exportlist = []
                return render_template('export.html', exportlist=exportlist, version=version)
            else:
                sql.execute("""SELECT * FROM new_events WHERE 
                            stamp BETWEEN TIMESTAMP(%s) AND DATE_ADD(TIMESTAMP(%s), INTERVAL 1 DAY)""", (start, end))
                result = sql.fetchall()
                exportlist = []
                for item in result:
                    listval = (list(item.values()))
                    exportlist.append(listval)
                field_names = ['evid', 'host', 'ipaddr', 'user', 'action', 'stamp']
                with open('./csv/Export.csv', 'w') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=field_names)
                    writer.writeheader()
                    writer.writerows(result)
                return render_template('export.html', start=start, exportlist=exportlist, version=version)
        if "getcsv" in request.form:
            return send_file(
                './csv/Export.csv',
                mimetype='text/csv',
                download_name='Export.csv',
                as_attachment=True)


# add event from script to DB
@app.route('/sendmetrics', methods=['GET'])
def search():
    args = request.args.to_dict(flat=False)
    host = args.get("host")[0]
    ipaddr = args.get("public_ip")[0]
    name = args.get("name")[0]
    try:
        tm = datetime.strptime(args.get("tm")[0].split(".")[0], "%m/%d/%Y-%H:%M:%S")
    except Exception as E:
        tm = '1900-01-01 00:00:01'
        with open("Errlog.txt", "w") as file:
            res = host + ' ' + name + ' ' + str(datetime.now()) + ' - ' + str(E)
            file.writelines(res)

    event = args.get("event")[0]
    sql = connection.cursor()
    try:
        sql.execute("""INSERT INTO new_events (host, ipaddr, user, action, stamp) VALUES (%s, %s, %s, %s, %s)""",
                    (host, ipaddr, name, event, tm))
        connection.commit()
    except Exception as E:
        with open("Errlog.txt", "w") as file:
            res = host + ' ' + name + ' ' + str(datetime.now()) + ' - ' + str(E)
            file.writelines(res)
    return args


if __name__ == '__main__':
    app.run(host='0.0.0.0')
