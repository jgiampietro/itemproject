import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

engine = create_engine('sqlite:///items.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create Categories Table


class Categories(Base):
    __tablename__ = 'categories'

    name = Column(
        String(80), nullable=False)
    id = Column(
        Integer, primary_key=True)
    user_name = Column(String(250))

# Method to serialize data, can be used with JSONIFY
# to create JSON for each object
    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'user_name': self.user_name
        }

# Count of items for each Category row
    @property
    def getNumItems(self):
        numItems = session.query(Items).filter_by(category_id=self.id).count()
        return numItems


# Create items table
class Items(Base):
    __tablename__ = 'items'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)
    user_name = Column(String(250))

# Method to serialize data, can be used with JSONIFY
# to create JSON for each object
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id,
            'user_name': self.user_name
        }

# Method to allow front end dev get each items parent category from template
    @property
    def getCatName(self):
        category = session.query(Categories)\
            .filter_by(id=self.category_id).one()
        catname = category.name
        return catname

engine = create_engine('sqlite:///items.db')
Base.metadata.create_all(engine)
