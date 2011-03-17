import web
import model
import time

### Url mappings

urls = (
    '/logs', 'Logs',
    '/drinks', 'Drinks',
    '/order', 'Order',
)


### Templates

render = web.template.render('/var/www/templates', base='base')


class Logs:

    def GET(self):
        """ Show Logs """
        logs = model.get_logs()
        return render.index(logs)
        
class Drinks:
    
    def GET(self):
        """ Show Drink List """
        drinks = model.get_drinklist()
        custom = model.get_custom()
        
        return render.drinks(drinks, custom)
    
    def POST(self, id):
        id = int(id)
        model.order_drink(id)
        raise web.seeother('/drinks')
        
class Order:
    
    def GET(self):
    	input = web.input()
        id = int(input.order)
        model.order_drink(id)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
