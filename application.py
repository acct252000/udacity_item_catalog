# application.py created November 22, 2016 by Christine Stoner


__copyright__ = """

    Copyright 2016 Christine Stoner

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
__license__ = "Apache 2.0"
import random
import string
import httplib2
import json
import requests
from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash
from flask import session as login_session
from flask import make_response
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """Generates random state variable and stores in session, returns
       login screen
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Handles google-signin from ajax post from signInCallback on
       Google sign-in.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                 'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    """Creates User and returns user id
    Args:
        login_session: current login session
    """

    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Returns user from user id
    Args:
        user_id : user id - unique identifier
    """

    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """If e-mail is associated with user, returns user id,
       else returns none.
    Args:
        email:  user email
    """

    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    """Handles signout from google
    """

    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API
@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    """Returns item information in JSON form
    Args:
        category_id: id of category
        item_id: id of item
    """

    currentItem = session.query(Item).filter_by(id=item_id).one()
    return jsonify(Item=currentItem.serialize)


# Show all categories and latest added items
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """Shows all categories and last 10 added items, with separate
    displays for public and logged-in versions.
    """

    categories = session.query(Category).order_by(asc(Category.name))
    latest_items = (session.query(Item).join(Item.category)
                    .add_columns(Category.name)
                    .order_by(desc(Item.time_created)).limit(10).all())
    if 'username' not in login_session:
        return render_template('publiccategories.html',
                               categories=categories,
                               latest_items=latest_items)
    else:
        return render_template('category.html', categories=categories,
                               latest_items=latest_items)


# Create a new category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    """Creates a new category
    """

    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')


# Edit a category
@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def editCategory(category_id):
    """Allows user who created category to edit it.
    Args:
        category_id: category id
    """

    editedCategory = session.query(
        Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedCategory.user_id != login_session['user_id']:
        return ("<script>function myFunction() {alert('You are not authorized"
                "to edit this category. Please create your own category in"
                " order to edit.');}</script><body onload='myFunction()''>")
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category=editedCategory)


# Delete a category
@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_id):
    """Allows user who created a category to delete it.  Cascade
       deletes children items using backref relationship established
    """

    categoryToDelete = session.query(
        Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if categoryToDelete.user_id != login_session['user_id']:
        return ("<script>function myFunction() {alert('You are not authorized"
                "to delete this category. Please create your own category in"
                " order to delete.');}</script><body onload='myFunction()''>")
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html',
                               category=categoryToDelete)


# Show a item list
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def showItemList(category_id):
    """Shows list of items for category
    Args:
        category_id: category id
    """

    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    creator = getUserInfo(category.user_id)
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    if (    'username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicitemlist.html', categories=categories,
                               items=items, indcategory=category,
                               creator=creator)
    else:
        return render_template('itemlist.html', categories=categories,
                               items=items, indcategory=category,
                               creator=creator)


# Show item description
@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    """Shows description of current item with links to edit or
       delete if user is signed in
    Args:
        category_id: category id
        item_id: item id
    """
    category = session.query(Category).filter_by(id=category_id).one()
    currentItem = session.query(Item).filter_by(id=item_id).one()
    creator = getUserInfo(category.user_id)
    if (    'username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicitem.html', item=currentItem)
    else:
        return render_template('item.html', item=currentItem,
                               category_id=category_id)


# Create a new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newItem(category_id):
    """Creates a new item to categories created by current user
    Args:
        category_id: category id
    """

    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return ("<script>function myFunction() {alert('You are not authorized"
                " to add items to this category. Please create your own "
                "category in order to add items.');}</script>"
                "<body onload='myFunction()''>")
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category_id, user_id=category.user_id)
        session.add(newItem)
        session.commit()
        flash('New %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)


# Edit a item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    """Edit an item the user previously created
    Args:
        category_id: category id
        item_id: item id
    """

    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if login_session['user_id'] != category.user_id:
        return ("<script>function myFunction() {alert('You are not "
                "authorized to edit items to this category. Please create"
                " your own category in order to edit items.');}"
                "</script><body onload='myFunction()''>")
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
                               item_id=item_id, item=editedItem)


# Delete a item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    """Delete an item the user previously created
    Args:
        category_id: category id
        item_id: item id
    """

    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if login_session['user_id'] != category.user_id:
        return ("<script>function myFunction() {alert('You are not authorized"
                " to delete items to this category. Please create your own "
                "category in order to delete items.');}"
                "</script><body onload='myFunction()''>")
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showItemList', category_id=category_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    """Handles logout process and calls gdisconnect for google signout
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
