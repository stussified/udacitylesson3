import random
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import string
from flask import make_response
import requests


# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

# loading client ID

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']


# Login section - only using GConnect

@app.route('/login')
def showLogin():
    print 'state should be: '
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

    print state

    login_session['state'] = state

    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Compare the state token to see if they match
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # obtain authorization code

    code = request.data

    try:
        # upgrade the auth code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade auth code.'), 401) 
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check the token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' 
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    print "this is result", result

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify access token is for the right user

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("User's token doesn't match Id"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    #verify access token is valid for the app

    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't match app's"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id


    # get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

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
    output += '" style = "width: 100px; height: 100px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print login_session
    return output

# disconnect/logout from Gconnect

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    # no access token means no user is logged in
    if access_token is None:
        response = make_response(json.dumps('No user is logged in'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
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
        # return response
        return redirect(url_for('showCategories'))
    else:

        response = make_response(json.dumps('Failed to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# Catalog Section

@app.route('/')
@app.route('/catalog/')
def showCategories():
	categories = session.query(Category).order_by(asc(Category.name))
	category_item = session.query(CategoryItem).order_by(asc(CategoryItem.name))

	return render_template('categories.html', categories=categories, category_item=category_item)

@app.route('/catalog/new/', methods =['GET', 'POST'])
def newCategory():

	# LOGIN VALIDATION 	
	if 'username' not in login_session:
		return redirect('/login')

	if request.method == 'POST': 
		newCategory = Category(name=request.form['name'], user_id = getUserID(login_session['email']))
		session.add(newCategory)
		flash('Category \"%s\" has been successfully created' % newCategory.name)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('newCategory.html')


@app.route('/catalog/<category>/edit/', methods = ['GET','POST'])
def editCategory(category):

	# LOGIN VALIDATION
    if 'username' not in login_session:
        return redirect('/login')
    editedCategory = session.query(Category).filter_by(name=category).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name)
            return redirect(url_for('showCategories'))
    else:
        return render_template('editCategory.html', category=editedCategory)	

@app.route('/catalog/<category>/delete/', methods = ['GET', 'POST'])
def deleteCategory(category):

	# LOGIN VALIDATION
    if 'username' not in login_session:
        return redirect('/login')	
    categoryToDelete = session.query(Category).filter_by(name=category).one()
    print "category",category	

    if request.method == 'POST':
    	session.delete(categoryToDelete)
    	flash('%s has been successfully deleted' % categoryToDelete.name)
    	session.commit()
    	return redirect(url_for('showCategories'))
    else:
    	return render_template('deleteCategory.html', category = categoryToDelete)

# Category Item routings

@app.route('/catalog/<category>/')
@app.route('/catalog/<category>/items/')
def showItems(category):

	# LOGIN VALIDATION
    category = session.query(Category).filter_by(name=category).one()
    items = session.query(CategoryItem).filter_by(category_id=category.id).all()
    return render_template('items.html', items = items, category = category)



# New category item
@app.route('/catalog/<category>/items/new/', methods = ['GET', 'POST'])
def newItem(category):

	# LOGIN VALIDATION
    if 'username' not in login_session:
        return redirect('/login')		
    # Following the way that Udacity does things, the "string" becomes a SqlAlchemy object
    
    category = session.query(Category).filter_by(name=category).one()
    
    # category is now an object and needs to be referred to as such.
    if request.method == 'POST':
    	newItem = CategoryItem(name=request.form['name'], description=request.form['description'],
    		category=category, user_id = getUserID(login_session['email']))
    	session.add(newItem)
    	session.commit()
    	flash('New Item %s has been added' % (newItem.name))
    	return redirect(url_for('showItems', category=category.name))
    else:
        # at this point, category is still a string from the URL rather than the object.
        print "Request method was not POST"
        return render_template('newItem.html', category=category)


# Edit category item
@app.route('/catalog/<category>/items/<int:item_id>/edit/', methods = ['GET', 'POST'])
def editItem(category, item_id):

    # LOGIN VALIDATION
    if 'username' not in login_session:
        return redirect('/login')     
    editedCategory = session.query(Category).filter_by(name=category).one()
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        # if request.form['category']:
        #     editedItem.category = request.form['category']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showItems', category=category))
    else:
        return render_template('editCategoryItem.html', category=category, item=editedItem)


# Delete category item
@app.route('/catalog/<category>/items/<int:item_id>/delete', methods =['POST', 'GET'])
def deleteItem(category, item_id):

    # LOGIN VALIDATION


    deleteItemCategory = session.query(Category).filter_by(name=category).one()     
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item successfully deleted.')
        return redirect(url_for('showCategories', category=category))
    else:
        return render_template('deleteCategoryItem.html', item=itemToDelete)


# User functions 
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)