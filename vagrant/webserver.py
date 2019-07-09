from http.server import BaseHTTPRequestHandler, HTTPServer
import cgi
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


engine = create_engine('sqlite:///restaurant_menu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


class WebServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Show all restaurants in the list
            if self.path.endswith('/restaurant'):
                restaurants = session.query(Restaurant).all()

                output = '<html><head><title>Find our restaurants!</title></head><body>'
                output += '<a href="/restaurant/new">Click here to add a new restaurant!</a>'

                for restaurant in restaurants:
                    line = '<h2 style="margin-block-start: 4px; margin-block-end: 0px">' + \
                           str(restaurant.id) + '&nbsp&nbsp&nbsp&nbsp' + restaurant.name + '</h2>'
                    output += line
                    output += '<a href="/{}/edit">Edit</a>'.format(str(restaurant.id))
                    output += '<br>'
                    output += '<a href="/{}/delete">Delete</a>'.format(str(restaurant.id))

                output += '</body></html>'

            # Add a new restaurant to the list
            if self.path.endswith('/restaurant/new'):
                output = '<html><head><title>Add a new restaurant</title></head><body>'
                output += '<form method="POST" enctype="multipart/form-data" action="/restaurant/new">' \
                          '<h2>Add A New Restaurant</h2>'\
                          '<input name="restaurant-name" type="text" placeholder="New Restaurant Name">'\
                          '<input type="submit" value="Create">'\
                          '</form>'
                output += '</body></html>'

            # Edit a current restaurant in the list
            if self.path.endswith('/edit'):
                restaurant_id_to_edit = int(self.path.split('/')[-2])
                restaurant_to_edit = session.query(Restaurant).filter_by(id=restaurant_id_to_edit).one()
                old_name = restaurant_to_edit.name

                output = '<html><head><title>Edit a current restaurant name</title></head><body>'
                output += '<form method="POST" enctype="multipart/form-data" action="/restaurant/{}/edit">'.format(
                    str(restaurant_id_to_edit)
                )
                output += '<p>{}</p>'.format(old_name)
                output += '<input name="new-restaurant-name" type="text" placeholder="{}">'.format(old_name)
                output += '<input type="submit" value="Create">'\
                          '</form>'
                output += '</body></html>'

            # Delete a current restaurant in the list
            if self.path.endswith('/delete'):
                restaurant_id_to_delete = int(self.path.split('/')[-2])
                restaurant_to_delete = session.query(Restaurant).filter_by(id=restaurant_id_to_delete).one()

                output = '<html><head><title>Delete a current restaurant</title></head><body>'
                output += '<h2>Are you sure you want to delete: {} ?</h2><br>'.format(restaurant_to_delete.name)
                output += '<form method="POST" enctype="multipart/form-data" action="/restaurant/{}/delete">'.format(
                    str(restaurant_id_to_delete)
                )
                output += '<input type="submit" value="Delete"></form></body></html>'

            self.wfile.write(output.encode())

        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))

    def do_POST(self):
        try:
            # Handle Adding post request
            if self.path.endswith('/restaurant/new'):
                ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
                if ctype == 'multipart/form-data':
                    pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
                    pdict['CONTENT-LENGTH'] = self.headers.get('Content-Length')
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    restaurant_name_added = fields.get('restaurant-name')[0].decode()
                    new_restaurant = Restaurant(name=restaurant_name_added)
                    session.add(new_restaurant)
                    session.commit()

            # Handle Editing post request
            if self.path.endswith('/edit'):
                restaurant_id_to_edit = int(self.path.split('/')[-2])
                restaurant_to_edit = session.query(Restaurant).filter_by(id=restaurant_id_to_edit).one()

                ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
                if ctype == 'multipart/form-data':
                    pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
                    pdict['CONTENT-LENGTH'] = self.headers.get('Content-Length')
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    new_restaurant_name = fields.get('new-restaurant-name')[0].decode()

                    restaurant_to_edit.name = new_restaurant_name
                    session.add(restaurant_to_edit)
                    session.commit()

            # Handle Editing post request
            if self.path.endswith('/delete'):
                restaurant_id_to_delete = int(self.path.split('/')[-2])
                restaurant_to_delete = session.query(Restaurant).filter_by(id=restaurant_id_to_delete).one()
                session.delete(restaurant_to_delete)
                session.commit()

            self.send_response(301)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Location', '/restaurant')
            self.end_headers()

        except IOError as e:
            print(e)


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print("Web server running on port {}".format(str(port)))
        server.serve_forever()

    except KeyboardInterrupt:
        print("^C entered, stopping web server...")
        server.socket.close()


if __name__ == '__main__':
    main()