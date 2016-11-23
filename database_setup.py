# database_setup.py created November 22, 2016 by Christine Stoner

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

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.sql import func
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """Lists id, name, email, and picture url of user
    Attributes:
        id: integer primary key
        name: string name
        email: string email
        picture string picture url
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    """Lists id, name, userid of creator of category
    Attributes:
        id: integer primary key
        name: string name
        user_id: integer user id of user who created, foreign key
                 with user.id
        user: relationship with User table
    """
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Item(Base):
    """Lists name, id, time_created, description, category id of related
       category, userid of creator
    Attributes:
        name:  string item name
        id: integer primary key
        time_created:  DateTime time created
        description: string description of item
        category_id: integer id of related category, foreign key with
                     category.id
        category: relationship with Category table
        user_id: integer user id of user who created, foreign key
                 with user.id
        user: relationship with User table
    """
    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    time_created = Column(DateTime, server_default=func.now())
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category,
                            backref=backref("item", 
                                            cascade="all, delete-orphan"))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }


engine = create_engine('sqlite:///itemcatalogwithusers.db')


Base.metadata.create_all(engine)
