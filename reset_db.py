import MySQLdb

conn = MySQLdb.connect(host='localhost', user='add', passwd='123456')
cursor = conn.cursor()
cursor.execute('DROP DATABASE IF EXISTS `django6`')
cursor.execute('CREATE DATABASE `django6` CHARACTER SET utf8mb3 COLLATE utf8mb3_unicode_ci')
cursor.close()
conn.commit()
conn.close()
print('✓ Veritabanı sıfırlandı, migrasyona hazır')
