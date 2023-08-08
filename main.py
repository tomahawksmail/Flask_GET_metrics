from flask import Flask, request, send_file, render_template
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


@app.route('/getcsv', methods=['POST', 'GET'])
def show():
    version = creds.version
    exportlist = []
    if request.method == 'GET':
        SQLrequest = """SELECT * FROM (SELECT * FROM new_events  ORDER BY evid DESC LIMIT 15)Var1
                                ORDER BY evid ASC"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(SQLrequest)
                result = cursor.fetchall()
        except Exception as E:
            exportlist = []
            return render_template('export.html', exportlist=exportlist, version=version)


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
                SQLrequest = """SELECT * FROM new_events WHERE 
                            stamp BETWEEN TIMESTAMP(%s) AND DATE_ADD(TIMESTAMP(%s), INTERVAL 1 DAY)"""
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(SQLrequest, (start, end))
                    result = cursor.fetchall()
                except Exception as E:
                    exportlist = []
                    return render_template('export.html', exportlist=exportlist, version=version)

                for item in result:
                    listval = (list(item.values()))
                    exportlist.append(listval)

                field_names = ['evid', 'host', 'ipaddr', 'user', 'action', 'stamp']
                with open('./csv/Export.csv', 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=field_names)
                    writer.writeheader()
                    writer.writerows(result)
                return render_template('export.html', exportlist=exportlist, version=version)
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

    SQLrequest = """INSERT INTO new_events (host, ipaddr, user, action, stamp) VALUES (%s, %s, %s, %s, %s)"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(SQLrequest, (host, ipaddr, name, event, tm))
        connection.commit()

    except Exception as E:
        with open("Errlog.txt", "w") as file:
            res = host + ' ' + name + ' ' + str(datetime.now()) + ' - ' + str(E)
            file.writelines(res)
    return args


if __name__ == '__main__':
    app.run(debug=False)
