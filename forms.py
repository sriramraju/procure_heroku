from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PurchaseRequestForm(FlaskForm):
    contact = StringField('Name', validators=[DataRequired()])
    required_date = DateField('Required by', validators=[DataRequired()])
    quantity = IntegerField('Quantity')
    submit = SubmitField('Submit')


class RequestForQuoteForm(FlaskForm):
    contact = StringField('Name', validators=[DataRequired()])
    required_date = DateField('Required by', validators=[DataRequired()])
    submit = SubmitField('Submit')


class VendorQuoteForm(FlaskForm):
    available_date = DateField('Available by', validators=[DataRequired()])
    total = IntegerField('Total')
    submit = SubmitField('Submit')


class Cart():
    def __init__(self):
        self.itemList = []

    def addItem(self, item_id, quantity):
        self.removeItem(item_id, quantity)
        cartItem = CartItem(item_id, quantity)
        self.itemList.append(cartItem)

    def removeItem(self, item_id, quantity):
        itemList = [cartItem for cartItem in self.itemList if cartItem.item_id != item_id]
        self.itemList = itemList

    def print(self):
        for item in self.itemList:
            print(item.item_id, ' -> ', item.quantity)

class CartItem:
    def __init__(self, item_id, quantity):
        self.item_id = item_id
        self.quantity = quantity

class VendorOffer:
    def __init__(self, cost_per_unit, available_date):
        self.cost_per_unit = cost_per_unit
        self.available_date = available_date