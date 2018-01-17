from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify)
from flask import session as login_session
import random
import string
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

# Imports for oauth
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

engine = create_engine('sqlite:///items.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']


# Main Page
@app.route('/')
@app.route('/catalog')
def home():
    categories = session.query(Categories).all()
    items = session.query(Items).limit(10).all()
    return render_template("home.html",
                           categories=categories,
                           items=items,
                           login_session=login_session)


# Login Page
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" %login_session['state']
    return render_template("login.html",
                           STATE=state,
                           login_session=login_session)


# Handler for using Google to log in
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Make sure of token to prevent man in the middle attack
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade auth code'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Get a token from google
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    gplus_id = credentials.id_token['sub']
    # Make sure userid matches google token
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user id"
                                            "does not match given user id"),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client id"
                                            "does not match app id"),
                                 401)
        print "Token's client id does not match apps id"
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user'
                                            'is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Authorized so now set session parameters
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width:300px; height:300px;border-radius:150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    return output


# For when a user logs out. Destroy session variables.
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user is not connect'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']

        response = make_response(json.dumps(
            'User successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Add a new item to the catalog.
@app.route('/catalog/newitem/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        flash("You must be logged in to add an item!")
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category']
        item = session.query(Items).filter_by(name=name,
                                              category_id=category_id).first()
        if item is None:
            newItem = Items(name=request.form['name'],
                            description=request.form['description'],
                            category_id=request.form['category'],
                            user_name=login_session['username'])
            session.add(newItem)
            session.commit()
            flash("New item has been added")
            return redirect(url_for('home'))
        else:
            flash("An item with that same name"
                  "already exists in that category!")
            categories = session.query(Categories).all()
            return render_template("newitem.html",
                                   categories=categories,
                                   login_session=login_session)
    else:
        categories = session.query(Categories).all()
        return render_template("newitem.html",
                               categories=categories,
                               login_session=login_session)


# Add a category to the catalog
@app.route('/catalog/newcategory', methods=['GET', 'POST'])
def newCat():
    if 'username' not in login_session:
        flash("You must be logged in to add a category!")
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        name = request.form['name']
        catDupe = session.query(Categories).filter_by(name=name).first()
        if catDupe is None:
            newCat = Categories(name=name,
                                user_name=login_session['username'])
            session.add(newCat)
            session.commit()
            flash("New item has been added")
            return redirect(url_for('home'))
        else:
            flash("A category of the same name already exists!")
            return render_template("newcategory.html",
                                   login_session=login_session)
    else:
        return render_template("newcategory.html",
                               login_session=login_session)


# This page allows you to view all the items for a user-selected category
@app.route('/catalog/<category_name>', methods=['GET', 'POST'])
def categoryDisplay(category_name):
    category = session.query(Categories).filter_by(name=category_name).one()
    categories = session.query(Categories).all()
    items = session.query(Items).filter_by(category_id=category.id)
    return render_template("categorydisplay.html",
                           categories=categories,
                           category=category,
                           items=items,
                           login_session=login_session)


# This page lets you view the details for a given item.
# If you are the items creator
# you may edit or delete the item from this page
@app.route('/catalog/<category_name>/<item_name>', methods=['GET', 'POST'])
def itemDisplay(category_name, item_name):
    item = session.query(Items).filter_by(name=item_name).one()
    return render_template("itemdisplay.html",
                           item=item,
                           login_session=login_session)


# Delete an item. Checks to make sure
# user is logged in and matches creator first
@app.route('/catalog/<category_name>/<item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        flash("You must be logged in to delete an item!")
        return redirect(url_for('showLogin'))
    item = session.query(Items).filter_by(name=item_name).one()
    if login_session['username'] != item.user_name:
        flash("You must be this item's creator to delete it!")
        return redirect(url_for('home'))
    session.delete(item)
    session.commit()
    flash("item successfully deleted")
    return redirect(url_for('home'))


# Edit an item. Again, checks to ensure user is logged in and is the creator
@app.route('/catalog/<category_name>/<item_name>/edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    if 'username' not in login_session:
        flash("You must be logged in to edit an item!")
        return redirect(url_for('showLogin'))
    item = session.query(Items).filter_by(name=item_name).one()
    if login_session['username'] != item.user_name:
        flash("You must be this item's creator to edit it!")
        return redirect(url_for('home'))
    categories = session.query(Categories).all()

    if request.method == 'POST':
        dupeItem = session.query(Items)\
            .filter(Items.name == request.form['name'])\
            .filter(Items.id != item.id).first()
        if dupeItem is None:
            item.name = request.form['name']
            item.category_id = request.form['category']
            item.description = request.form['description']
            session.add(item)
            session.commit()
            flash("Item successfully saved!")
            return redirect(url_for('itemDisplay',
                            category_name=item.getCatName,
                            item_name=item.name))
        else:
            flash("An item with that same name"
                  "already exists in this category!")
            return render_template("edititem.html",
                                   categories=categories,
                                   item=item,
                                   login_session=login_session)
    else:
        return render_template("edititem.html",
                               categories=categories,
                               item=item,
                               login_session=login_session)


# JSON endpoint for all categories
@app.route('/catalog/categories/json')
def catalogJSON():
    categories = session.query(Categories).all()
    return jsonify(categories=[c.serialize for c in categories])


# JSON endpoint for all items
@app.route('/catalog/items/json')
def itemsJSON():
    items = session.query(Items).all()
    return jsonify(items=[item.serialize for item in items])


# JSON endpoint for all items of a certain category
@app.route('/catalog/<category_name>/json')
def catItemJSON(category_name):
    try:
        category = session.query(Categories)\
            .filter_by(name=category_name).one()
    except:
        return "That category name does not exist"

    items = session.query(Items).filter_by(category_id=category.id).all()
    return jsonify(items=[item.serialize for item in items])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
