from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from Data_Setup import *

engine = create_engine('sqlite:///arts.db')
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

# Delete ArtCompanyName if exisitng.
session.query(ArtCompanyName).delete()
# Delete ArtName if exisitng.
session.query(ArtName).delete()
# Delete User if exisitng.
session.query(User).delete()

# Create sample users data
User1 = User(name="jhansi lakshmi",
             email="manukondajhansilakshmi@gmail.com",
             picture='http://www.enchanting-costarica.com/wp-content/'
                     'uploads/2018/02/jcarvaja17-min.jpg')
session.add(User1)
session.commit()
print ("Successfully Add First User")
# Create sample art companys
Company1 = ArtCompanyName(name="Salvator Mundi",
                          user_id=1)
session.add(Company1)
session.commit()

Company2 = ArtCompanyName(name="The Card Players",
                          user_id=1)
session.add(Company2)
session.commit

Company3 = ArtCompanyName(name="Irises",
                          user_id=1)
session.add(Company3)
session.commit()

Company4 = ArtCompanyName(name="Meule",
                          user_id=1)
session.add(Company4)
session.commit()

# Populare arts with models for testing
# Using different users for arts names year also
Name1 = ArtName(name="Salvator Mundi",
                year="1500",
                color="black",
                price="$450.3",
                date=datetime.datetime.now(),
                artcompanynameid=1,
                user_id=1)
session.add(Name1)
session.commit()

Name2 = ArtName(name="The Card Players",
                year="1892",
                color="blue",
                price="$250",
                date=datetime.datetime.now(),
                artcompanynameid=2,
                user_id=1)
session.add(Name2)
session.commit()

Name3 = ArtName(name="Irises",
                year="1889",
                color="ash",
                price="$53.9",
                date=datetime.datetime.now(),
                artcompanynameid=3,
                user_id=1)
session.add(Name3)
session.commit()

Name4 = ArtName(name="Meule",
                year="1891",
                color="purple",
                price="$81.4",
                date=datetime.datetime.now(),
                artcompanynameid=4,
                user_id=1)
session.add(Name4)
session.commit()
print("Your arts database has been inserted!")
