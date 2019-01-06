#!/usr/bin/env python

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, CategoryItem, User

engine = create_engine('sqlite:///itemcatalog.db')
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

# Create user
User1 = User(name="Pepito Grillo", email="pepito@grillo.com",
             picture="https://pbs.twimg.com/profile_images/2671170543/"
             "18debd694829ed78203a5a36dd364160_400x400.png")
session.add(User1)
session.commit()

# Create Categories
category1 = Category(name="Athletic")
category2 = Category(name="Ballet")
category3 = Category(name="Boots")
category4 = Category(name="Dress shoe")
category5 = Category(name="Flip Flops")
category6 = Category(name="High-heeled")
category7 = Category(name="Mary Jane")
category8 = Category(name="Moccasin")
category9 = Category(name="Platform")
category10 = Category(name="Sandals")
category11 = Category(name="Slipper")
category12 = Category(name="Sneakers")
category13 = Category(name="Snow boot")

session.add(category1)
session.commit()

session.add(category2)
session.commit()

session.add(category3)
session.commit()

session.add(category4)
session.commit()

session.add(category5)
session.commit()

session.add(category6)
session.commit()

session.add(category7)
session.commit()

session.add(category8)
session.commit()

session.add(category9)
session.commit()

session.add(category10)
session.commit()

session.add(category11)
session.commit()

session.add(category12)
session.commit()

session.add(category13)
session.commit()

# Create items
item1 = CategoryItem(user_id=1, name="Hamaianas Unisex",
                     description="Brasilian Flip Flops in black color."
                     " Perfect for the summer.",
                     category=category5)
item2 = CategoryItem(user_id=1, name="Gladiator strappy wedge sandal",
                     description="Ladies' sandal. Perfect for summer evening"
                     " dress party.",
                     category=category10)
item3 = CategoryItem(user_id=1, name="Tennis trainers",
                     description="Adidas Men White & Black Net Nuts Printed"
                     " Tennis Shoes.",
                     category=category1)
item4 = CategoryItem(user_id=1, name="Basketball shoes",
                     description="First release on 1988, these are the best"
                     " shoes you will ever find.",
                     category=category1)
item5 = CategoryItem(user_id=1, name="Fotball trainers",
                     description="Top Rated 10 Best Tennis Shoes For Men.",
                     category=category1)

session.add(item1)
session.commit()

session.add(item2)
session.commit()

session.add(item3)
session.commit()

session.add(item4)
session.commit()

session.add(item5)
session.commit()

print "added user, categories and items!"
