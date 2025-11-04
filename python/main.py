import oracledb

connection = oracledb.connect(
    user="system",
    password="oracle",
    dsn="localhost/XE"
)

cursor = connection.cursor()
cursor.execute("SELECT 'Hello Oracle!' FROM dual")
for row in cursor:
    print(row)

connection.close()
