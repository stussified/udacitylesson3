from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Category, CategoryItem, Base

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Tony Mercielago", email="acwacw11@gmail.com",
             picture='http://d4f1ndlb0hkjb.cloudfront.net/wp-content/uploads/2014/01/camronB-e1330270328587.jpg')
session.add(User1)
session.commit()

# Create dummy category 1
category1 = Category(user_id=1, name="Adidas")

session.add(category1)
session.commit()

category_item1 = CategoryItem(user_id=1, name="PureBoost 1", description="Pureboost shoes", category=category1)

session.add(category_item1)
session.commit()

category_item2 = CategoryItem(user_id=1, name="Ultraboost", description="Ultraboost shoes", category=category1)

session.add(category_item2)
session.commit()

# Create dummy category 2

category2 = Category(user_id=1, name="Nike")

session.add(category1)
session.commit()

category_item1 = CategoryItem(user_id=1, name="Dunk SB", description="Dunk SB shoes", category=category2)

session.add(category_item1)
session.commit()

category_item2 = CategoryItem(user_id=1, name="Jordan 1", description="Jordan 1s", category=category2)

session.add(category_item2)
session.commit()


print "added menu items!"
