from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, CategoryItem, User
from flask import session as login_session

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
    items = session.query(CategoryItem).filter_by(name=category).all()
    return render_template('items.html', items = items, category = category)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)