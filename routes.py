from flask import g, Flask, request, render_template, flash, redirect, url_for, abort, session, jsonify
from functools import wraps
from forms import LoginForm, PurchaseRequestForm, Cart, VendorOffer, RequestForQuoteForm, VendorQuoteForm
from models import db, Users
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from models import db, PurchaseRequests, Catalog, Orders, Catalog_Pr, Catalog_Order_Vendor
from datetime import date, datetime
from status import Pr_Status, Order_Status
import json
import numpy as np

app = Flask(__name__)

# Connect to DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:only4db@localhost/dbrev3'
app.config['DATABASE_URI'] = 'postgres://cjjyrqrvmpblze:fe2c6cc420ebf6b0c0f54ad4f3d5dd7f9d0b06cf61801cbdd84ed014f95a6b2b@ec2-35-170-146-54.compute-1.amazonaws.com:5432/den733lrttecjf'

# Initialize database class from models.py
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# For security
app.secret_key = "procure-rev3"


# Decorators
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


def restricted(access_level):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            access_level.append('admin')
            if current_user.role not in access_level:
                abort(403)
                # flash('Access Restricted!')
                # redirect(url_for('index'))
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Functions
def convertItemDbToCart(itemDb):
    cart = Cart()
    for item in itemDb:
        cart.addItem(item.catalog_id, item.quantity)
    return cart


def addItemsToCart(itemList):
    cart = Cart()
    for itemCode in itemList:
        item_qty = itemCode.split('_')
        cart.addItem(int(item_qty[0]), int(item_qty[1]))
    return cart


def convertOrderCartToJson(dictOrderCart):
    jsonobj = {}
    for oid, ordercart in dictOrderCart.items():
        jsonobj[oid] = [item.__dict__ for item in ordercart]
    jsonobj = json.dumps(jsonobj, sort_keys=True, default=int)
    return jsonobj


def getCartDetailsForOrderId(list_oids):
    dict_order_card = {}
    allPrs = PurchaseRequests.query.all()
    catalogPrs = Catalog_Pr.query.all()
    for oid in list_oids:
        pridList = [pr.id for pr in allPrs if pr.order_id == oid]
        selectCatalogPrs = [item for item in catalogPrs if item.pr_id in pridList]
        uniqItemIds = np.unique([item.catalog_id for item in selectCatalogPrs])
        cart = Cart()
        for uniqItemId in uniqItemIds:
            total_qty = np.sum([item.quantity for item in selectCatalogPrs if item.catalog_id == uniqItemId])
            cart.addItem(uniqItemId, total_qty)
        dict_order_card[oid] = cart.itemList
    return dict_order_card


def buildJsonForComparison(uniq_oids, allCOVs):
    dictOrderCart = getCartDetailsForOrderId(uniq_oids.tolist())
    dict_comparison = buildDictForComparison(dictOrderCart, allCOVs)
    json_comparison = json.dumps(dict_comparison, sort_keys=True, default=str)
    json_ordercart = convertOrderCartToJson(dictOrderCart)
    return json_ordercart, json_comparison


def buildDictForComparison(dictOrderCart, allCOVs):
    # Output is a nested Dictionart: order_id -> vendor_id -> catalog_id -> Item offer details
    dict_comp = {}
    for cov in allCOVs:
        cartList = dictOrderCart.get(cov.order_id)
        list_cid = [item.item_id for item in cartList]
        if cov.catalog_id in list_cid:
            dict_item_offer = {
                cov.catalog_id: VendorOffer(cost_per_unit=cov.cost, available_date=cov.available_date).__dict__}
        dict_comp.setdefault(cov.order_id, {}).setdefault(cov.vendor_id, {}).update(dict_item_offer)
    return dict_comp


def buildJsonForOrderInfo(uniq_oids):
    di = {}
    list_oids = uniq_oids.tolist()
    for oid in list_oids:
        di[oid] = Orders.query.filter_by(id=oid).first().__dict__
    return json.dumps(di, sort_keys=True, default=str)


def createDictItemWithCost(catalog_ov):
    dict_item_cost = {}
    if catalog_ov:
        for item in catalog_ov:
            dict_item_cost[item.catalog_id] = item.cost
    else:
        dict_item_cost = None
    return dict_item_cost


def getPurchaseRequestsFromDb():
    if current_user.role is 'admin':
        return PurchaseRequests.query.all()
    else:
        return PurchaseRequests.query.filter_by(poc_id=current_user.id).all()


def buildDictOfUser():
    users = Users.query.all()
    di = {}
    for user in users:
        di[user.id] = user.name
    return di


def buildDictOfCatalog():
    catalog = Catalog.query.all()
    di = {}
    for item in catalog:
        di[item.id] = item.name + ' | ' + item.maker + ' | ' + item.model
    return di


# Routes
@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', user=current_user)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        form = LoginForm()
        return render_template("login.html", form=form)
    else:
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email, password=password).first()
        if user:
            print(user.name)
            login_user(user, remember=False)
            return redirect(url_for('profile'))
        else:
            form = LoginForm()
            flash("Incorrect login credentials!")
            return render_template("login.html", form=form)


@app.route("/profile", methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route("/populatedb", methods=['GET', 'POST'])
def populatedb():
    # Place holder to create users and items
    db.session.add(Catalog(name='Test', maker='Test', model='Test'))
    # db.session.add(Catalog(name='Laptop', maker='Dell', model='XPZ'))
    # db.session.add(Catalog(name='Printer', maker='Brother', model='PX100'))
    # db.session.add(Catalog(name='Keyboard', maker='Anker', model='QZ12'))
    # db.session.add(Catalog(name='Paper', maker='Forest', model='A4'))
    # db.session.add(Users(name='Admin', email='admin@xyz.com', password='admin', phone='8888', role='admin'))
    # db.session.add(Users(name='Chetan', email='chetan@xyz.com', password='qwerty', phone='8888', role='admin'))
    # db.session.add(Users(name='Arun', email='arun@xyz.com', password='qwerty', phone='8888', role='admin'))
    db.session.commit()
    return redirect(url_for("login"))


@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/poc", methods=['GET'])
@login_required
@restricted(access_level=['poc'])
def poc():
    allPrs = getPurchaseRequestsFromDb()
    return render_template("poc_landing.html", allPrs=allPrs, dictUser=buildDictOfUser())


@app.route("/show-purchase-request", methods=['POST'])
@login_required
@restricted(access_level=['poc'])
def show_purchase_request():
    prid = int(request.form.get('prid'))
    pr = PurchaseRequests.query.filter_by(id=prid).first()
    items_qty = Catalog_Pr.query.filter_by(pr_id=prid).all()
    cart = convertItemDbToCart(items_qty)
    form = PurchaseRequestForm(contact=pr.name, required_date=pr.required_date)
    allItems = Catalog.query.all()
    return render_template("show_purchase_request.html", form=form, allItems=allItems,
                           cart=cart.itemList, dictCatalog=buildDictOfCatalog())


@app.route("/edit-purchase-request", methods=['POST'])
@login_required
@restricted(access_level=['poc'])
def edit_purchase_request():
    prid = int(request.form.get('prid'))
    pr = PurchaseRequests.query.filter_by(id=prid).first()
    items_qty = Catalog_Pr.query.filter_by(pr_id=prid).all()
    cart = convertItemDbToCart(items_qty)
    form = PurchaseRequestForm(contact=pr.name, required_date=pr.required_date)
    allItems = Catalog.query.all()
    return render_template("create_purchase_request.html", form=form, allItems=allItems, cart=cart.itemList,
                           prid=prid, dictCatalog=buildDictOfCatalog())


@app.route("/create-purchase-request", methods=['GET', 'POST'])
@login_required
@restricted(access_level=['poc'])
def create_purchase_request():
    form = PurchaseRequestForm()
    allItems = Catalog.query.all()
    if request.method == 'GET':
        return render_template("create_purchase_request.html", form=form, allItems=allItems, cart=[], prid=0)
    else:
        if form.validate_on_submit:
            prid = int(request.form.get("prid"))
            isNewPR = False
            if prid == 0:
                isNewPR = True
            # Refresh page while populating cart
            if request.form['submit'] == 'Add':
                quantity = int(request.form['quantity'])
                itemId = int(request.form.get('itemList'))
                # Cart
                try:
                    itemList = request.form.getlist('cart')
                except:
                    itemList = []
                cart = addItemsToCart(itemList)
                cart.addItem(itemId, quantity)
                return render_template("create_purchase_request.html", form=form, allItems=allItems, cart=cart.itemList,
                                       prid=prid, dictCatalog=buildDictOfCatalog())
            else:
                # Submit action
                contact = request.form['contact']
                created_date = datetime.now()
                required_date = request.form['required_date']
                status = 1  # Create Purchase Request
                if isNewPR:  # Prid is zero, it is a new PR
                    pr = PurchaseRequests(name=contact, poc_id=current_user.id, created_date=created_date,
                                          required_date=required_date,
                                          status=status)
                else:
                    pr = PurchaseRequests.query.filter_by(id=prid).first()
                    pr.name = contact
                    pr.required_date = required_date
                    pr.status = status
                    created_date = pr.created_date
                db.session.add(pr)
                db.session.commit()

                # Item List
                itemList = request.form.getlist('cart')
                cart = addItemsToCart(itemList)
                pr = PurchaseRequests.query.filter_by(name=contact, created_date=created_date).first()
                prid = pr.id
                if ~isNewPR:  # If old PR, clear previous items in PR
                    Catalog_Pr.query.filter_by(pr_id=prid).delete()
                    db.session.commit()
                for item in cart.itemList:
                    catalog_pr = Catalog_Pr(catalog_id=item.item_id, pr_id=prid, quantity=item.quantity)
                    db.session.add(catalog_pr)
                db.session.commit()
            return redirect(url_for('poc'))


@app.route("/submit-purchase-request", methods=['POST'])
@login_required
@restricted(access_level=['poc'])
def submit_purchase_request():
    prid = int(request.form.get('prid'))
    pr = PurchaseRequests.query.filter_by(id=prid).first()
    pr.status = 2
    db.session.add(pr)
    db.session.commit()
    return redirect(url_for('poc'))


@app.route("/approver", methods=['GET'])
@login_required
@restricted(access_level=['approver'])
def approver():
    allPrs = PurchaseRequests.query.all()
    selectPrs = [pr for pr in allPrs if pr.status >= 2]  # Pr_Status.approval_requested
    catalogPrs = Catalog_Pr.query.all()
    cart_dict = {}
    for pr in selectPrs:
        cart = convertItemDbToCart([cr for cr in catalogPrs if cr.pr_id == pr.id])
        cart_dict[pr.id] = cart.itemList
    # print(cart_dict)
    return render_template("approver_landing.html", allPrs=selectPrs, cartDict=cart_dict,
                           dictUser=buildDictOfUser(), dictCatalog=buildDictOfCatalog())


@app.route("/approve-purchase-request", methods=['POST'])
@login_required
@restricted(access_level=['approver'])
def approve_purchase_request():
    prid = request.form.get('prid')
    pr = PurchaseRequests.query.filter_by(id=prid).first()
    pr.status = 4
    pr.approver_id = current_user.id
    db.session.add(pr)
    db.session.commit()
    return redirect(url_for('approver'))


@app.route("/reject-purchase-request", methods=['POST'])
@login_required
@restricted(access_level=['approver'])
def reject_purchase_request():
    prid = request.form.get('prid')
    pr = PurchaseRequests.query.filter_by(id=prid).first()
    pr.status = 1
    db.session.add(pr)
    db.session.commit()
    return redirect(url_for('approver'))


@app.route("/procurer", methods=['GET', 'POST'])
@login_required
@restricted(access_level=['procurer'])
def procurer():
    if request.method == 'GET':
        return render_template("procurer_landing.html")
    else:
        if request.form['form'] == 'Show PR':
            return redirect(url_for('procurer_show_pr'))
        elif request.form['form'] == 'Show RFQ':
            return redirect(url_for('procurer_show_rfq'))


@app.route("/procurer/show-pr", methods=['GET', 'POST'])
@login_required
@restricted(access_level=['procurer'])
def procurer_show_pr():
    allPrs = PurchaseRequests.query.all()
    selectPrs = [pr for pr in allPrs if pr.status >= 4]
    catalogPrs = Catalog_Pr.query.all()
    cart_dict = {}
    for pr in selectPrs:
        cart = convertItemDbToCart([cr for cr in catalogPrs if cr.pr_id == pr.id])
        cart_dict[pr.id] = cart.itemList
    return render_template("procurer_show_pr.html", allPrs=selectPrs, cartDict=cart_dict,
                           dictUser=buildDictOfUser(), dictCatalog=buildDictOfCatalog())


@app.route("/procurer/show-rfq", methods=['GET', 'POST'])
@login_required
@restricted(access_level=['procurer'])
def procurer_show_rfq():
    # Order summary & comparison table
    allCOVs = Catalog_Order_Vendor.query.all()
    uniq_oids = np.unique([cov.order_id for cov in allCOVs])
    jsonOrderCart, jsonComparison = buildJsonForComparison(uniq_oids, allCOVs)
    jsonOrderInfo = buildJsonForOrderInfo(uniq_oids)
    return render_template("procurer_show_rfq.html", jsonOrderCart=jsonOrderCart, jsonComparison=jsonComparison,
                           jsonOrderInfo=jsonOrderInfo, uniq_oids=uniq_oids,
                           jsonUser=json.dumps(buildDictOfUser()), jsonCatalog=json.dumps(buildDictOfCatalog()))


@app.route("/procurer/create-rfq", methods=['POST'])
@login_required
@restricted(access_level=['procurer'])
def procurer_create_rfq():
    form = RequestForQuoteForm()
    pridList = [int(prid) for prid in request.form.getlist('prs')]
    session['pridList'] = pridList
    allPrs = PurchaseRequests.query.all()
    catalogPrs = Catalog_Pr.query.all()
    selectPrs = [pr for pr in allPrs if pr.id in pridList]
    selectCatalogPrs = [item for item in catalogPrs if item.pr_id in pridList]
    uniqItemIds = np.unique([item.catalog_id for item in selectCatalogPrs])
    cart = Cart()
    for uniqItemId in uniqItemIds:
        total_qty = np.sum([item.quantity for item in selectCatalogPrs if item.catalog_id == uniqItemId])
        cart.addItem(uniqItemId, total_qty)
    return render_template("create_rfq.html", form=form, cart=cart.itemList, dictCatalog=buildDictOfCatalog())


@app.route("/submit-rfq", methods=['POST'])
@login_required
@restricted(access_level=['procurer'])
def submit_rfq():
    contact = request.form['contact']
    created_date = datetime.now()
    required_date = request.form['required_date']
    status = 1
    order = Orders(name=contact, procurer_id=current_user.id, created_date=created_date, required_date=required_date,
                   status=status)
    db.session.add(order)
    db.session.commit()

    # PR Update
    order = Orders.query.filter_by(name=contact, created_date=created_date).first()
    pridList = session['pridList']
    allPrs = PurchaseRequests.query.all()
    for pr in allPrs:
        if pr.id in pridList:
            pr.order_id = order.id
            pr.status = 5
            db.session.add(pr)
    db.session.commit()
    return redirect(url_for('procurer'))


@app.route("/procurer/confirm-order-vendor/<int:order_id>/<int:vendor_id>")
@login_required
@restricted(access_level=['procurer'])
def procurer_confirm_order_vendor(order_id, vendor_id):
    order = Orders.query.filter_by(id=order_id).first()
    order.vendor_id = vendor_id
    order.status = 2
    db.session.add(order)

    # Update PR Status
    list_pr = PurchaseRequests.query.filter_by(order_id=order.id).all()
    for pr in list_pr:
        pr.status = 6
        db.session.add(pr)

    db.session.commit()
    return redirect(url_for('procurer'))


@app.route("/vendor", methods=['GET'])
@login_required
@restricted(access_level=['vendor'])
def vendor():
    allOrders = Orders.query.all()
    # Order are open or are submitted by vendor (rejected or accepted)
    allAvailOrders = []
    for order in allOrders:
        if not order.vendor_id or \
                Catalog_Order_Vendor.query.filter_by(order_id=order.id, vendor_id=current_user.id).first():
            allAvailOrders.append(order)

    list_oids = [order.id for order in allAvailOrders]
    dictOrderCart = getCartDetailsForOrderId(list_oids)
    return render_template("vendor_landing.html", allOrders=allAvailOrders, cartDict=dictOrderCart,
                           dictUser=buildDictOfUser(), dictCatalog=buildDictOfCatalog())


@app.route("/vendor/order/<int:order_id>", methods=['POST'])
@login_required
@restricted(access_level=['vendor'])
def vendor_quote(order_id):
    cartItemList = getCartDetailsForOrderId([order_id]).get(order_id)
    order = Orders.query.filter_by(id=order_id).first()
    catalog_ov = Catalog_Order_Vendor.query.filter_by(order_id=order_id, vendor_id=current_user.id)
    dictItemCost = createDictItemWithCost(catalog_ov)
    form = VendorQuoteForm()
    if dictItemCost:
        total_value = np.sum([item.cost * item.quantity for item in catalog_ov])
        form = VendorQuoteForm(available_date=catalog_ov[1].available_date, total=total_value)
    return render_template('vendor_quote.html', cart=cartItemList, order=order, form=form,
                           itemDict=dictItemCost, current_user_id=current_user.id,
                           dictCatalog=buildDictOfCatalog())


@app.route("/submit-vendor-quote", methods=['POST'])
@login_required
@restricted(access_level=['vendor'])
def submit_vendor_quote():
    oid = int(request.form.get('order_id'))
    vendor_id = current_user.id
    avail_date = request.form['available_date']
    item_id = request.form.getlist('item_id')
    item_quantity = request.form.getlist('item_quantity')
    cost_per_unit = request.form.getlist('costPerUnitList')
    total = 0
    for i in range(len(item_id)):
        i_id = int(item_id[i])
        i_qty = int(item_quantity[i])
        i_cpu = int(cost_per_unit[i])
        total += i_qty * i_cpu
        cov = Catalog_Order_Vendor(catalog_id=i_id, order_id=oid, vendor_id=vendor_id, quantity=i_qty, cost=i_cpu,
                                   available_date=avail_date)
        db.session.add(cov)
    db.session.commit()
    return redirect(url_for('vendor'))


@app.route("/success", methods=['GET'])
def success():
    return render_template("success.html")


@app.route("/fail", methods=['GET'])
def fail():
    return render_template("fail.html")


if __name__ == "__main__":
    app.run(debug=True)
