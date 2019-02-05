#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify, make_response
from database_setup import Base, Category, CategoryItem, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Shoeify!"

# Create session and connect to DB
engine = create_engine('sqlite:///itemcatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# API Endpoint (GET Request)
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[c.serialize for c in categories])


@app.route('/category/<int:category_id>/item/JSON')
def categoryItemsJSON(category_id):
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return jsonify(CategoryItem=[i.serialize for i in items])


@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def menuJSON(category_id, item_id):
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    return jsonify(item.serialize)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
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
        logger.info("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                 'Current user is already connected.'), 200)
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

    # See if users exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = '<div id="welcomeMessage">'
    output += '<p>Welcome, '
    output += login_session['username']
    output += '!</p>'
    output += '<img src="'
    output += login_session['picture']
    output += '></div>'
    logger.info("Done!")
    return output


# Log out user from the google account
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
                                 'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    token = login_session['access_token']
    logger.debug('Token: %s', token)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
                                 'Failed to revoke token for given user.',
                                 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Log out and redirect to main page
@app.route('/disconnect')
def disconnect():
    if 'username' in login_session:
        gdisconnect()
        flash("You have successfully been logged out")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


# Renders main page
@app.route('/')
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).all()
    return render_template('categories.html', categories=categories)


# Shows all items once a category has been chosen
@app.route('/category/<int:category_id>')
@app.route('/category/<int:category_id>/item/')
def showItems(category_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    return render_template('items.html', category=category, items=items,
                           categories=categories)


# Renders the detail page of an item
@app.route('/category/<int:category_id>/item/<int:item_id>')
def itemDetails(category_id, item_id):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).all()
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    creator = getUserInfo(item.user_id)
    user_id = login_session['user_id']
    if 'username' not in login_session or creator.id != user_id:
        return render_template('publicitem.html', category=category,
                               items=items, categories=categories, item=item)
    else:
        return render_template('item.html', category=category,
                               items=items, categories=categories, item=item)


# Renders the page that allows users to create a new item
@app.route('/category/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newCategoryItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name'] and request.form['description']:
            new_item = CategoryItem(name=request.form['name'],
                                    description=request.form['description'],
                                    category_id=category_id,
                                    user_id=login_session['user_id'])
            session.add(new_item)
            session.commit()
            flash("A new item %s has been added" %
                  new_item.name)
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newcategoryitem.html', category_id=category_id)


# Renders the page that allows users to edit an item
@app.route('/category/<int:category_id>/item/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editCategoryItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item_to_edit = session.query(CategoryItem).filter_by(id=item_id).one()
    if login_session['user_id'] != item_to_edit.user_id:
        return "<script>function myFunction() {alert('You are not authorized "
        "to edit this item.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if (request.form['name'] or request.form['description'] or
                request.form['price'] or request.form['course']):
            if request.form['name'] != "":
                item_to_edit.name = request.form['name']
            if request.form['description'] != "":
                item_to_edit.description = request.form['description']
            session.add(item_to_edit)
            session.commit()
            flash("The shoe %s has been changed" % item_to_edit.name)
        return redirect(url_for('itemDetails', category_id=category_id,
                        item_id=item_to_edit.id))
    else:
        return render_template('editcategoryitem.html',
                               category_id=category_id, item=item_to_edit)


# Renders the page that allows users to delete an item
@app.route('/category/<int:category_id>/item/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteCategoryItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item_to_delete = session.query(CategoryItem).filter_by(id=item_id).one()
    if login_session['user_id'] != item_to_delete.user_id:
        return "<script>function myFunction() {alert('You are not authorized "
        "to delete this item.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(item_to_delete)
        session.commit()
        flash("The item %s has been deleted" % item_to_delete.name)
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deletecategoryitem.html',
                               category_id=category_id, item=item_to_delete)


# Returns the user ID
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            return user.id
        else:
            return None
    except ImportError:
        return None


# Returns all the info from a user stored in the database
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Every time a new user enters the app the user is stored in the database
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
