from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session

import random
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response



# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

app = Flask(__name__)

# Catalog Section
# Be sure to add some sort of thing so it takes lower case category names.

@app.route('/')
@app.route('/catalog/')
def showCategories():
	categories = session.query(Category).order_by(asc(Category.name))
	category_item = session.query(CategoryItem).order_by(asc(CategoryItem.name))

	return render_template('categories.html', categories=categories, category_item=category_item)

@app.route('/catalog/new/', methods =['GET', 'POST'])
def newCategory():

	# LOGIN VALIDATION 	
	# if 'username' not in login_session:
	# 	return redirect('/login')

	if request.method == 'POST':
		newCategory = Category(name=request.form['name'])
		session.add(newCategory)
		flash('Category \"%s\" has been successfully created' % newCategory.name)
		session.commit()
		return redirect(url_for('showCategories'))
	else:
		return render_template('newCategory.html')


@app.route('/catalog/<category>/edit/', methods = ['GET','POST'])
def editCategory(category):

	# LOGIN VALIDATION
    # if 'username' not in login_session:
    #     return redirect('/login')
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
    # if 'username' not in login_session:
    #     return redirect('/login')	
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
    # if 'username' not in login_session:
    #     return redirect('/login')	
    category = session.query(Category).filter_by(name=category).one()
    items = session.query(CategoryItem).filter_by(category_id=category.id).all()
    return render_template('items.html', items = items, category = category)



# New category item
@app.route('/catalog/<category>/items/new/', methods = ['GET', 'POST'])
def newItem(category):

	# LOGIN VALIDATION
    # if 'username' not in login_session:
    #     return redirect('/login')		
    # Following the way that Udacity does things, the "string" becomes a SqlAlchemy object
    
    category = session.query(Category).filter_by(name=category).one()
    
    # category is now an object and needs to be referred to as such.

    if request.method == 'POST':
    	newItem = CategoryItem(name=request.form['name'], description=request.form['description'],
    		category=category)
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
    # if 'username' not in login_session:
    #     return redirect('/login')     
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
    # if 'username' not in login_session:
    #     return redirect('/login') 
    deleteItemCategory = session.query(Category).filter_by(name=category).one()     
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item successfully deleted.')
        return redirect(url_for('showCategories', category=category))
    else:
        return render_template('deleteCategoryItem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)