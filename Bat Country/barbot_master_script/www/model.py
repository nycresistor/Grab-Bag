import web

db = web.database(dbn='sqlite', db='/var/www/barbot.sqlite')

def get_logs():
    results = db.query("SELECT id, text, datetime(time, 'unixepoch') as time from logs order by id desc limit 10");
    return results
    
def get_drinklist():
	results = db.query("SELECT id, name from drinks order by id")
	return results
	
def get_custom():
	results = db.query("select custom.id, name from custom, drinks where custom.drinknum = drinks.id and custom.done is not 'True'")
	return results

def order_drink(id):
	sequence_id = db.insert('custom', id=None, drinknum=id, done=None, time=None)
	return sequence_id
	
def new_log(text):
    db.insert('logs', title=text)

def del_log(id):
    db.delete('logs', where="id=$id", vars=locals())

def get_time(time):
    return asctime(time)
