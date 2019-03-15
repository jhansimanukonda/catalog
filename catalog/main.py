from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Data_Setup import Base, ArtCompanyName, ArtName, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///arts.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Arts Store"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tbs_cat = session.query(ArtCompanyName).all()


# login
@app.route('/login')
def showLogin():

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tbs_cat = session.query(ArtCompanyName).all()
    tbes = session.query(ArtName).all()
    return render_template('login.html',
                           STATE=state, tbs_cat=tbs_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # tbs_cat=tbs_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    User1 = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(User1)
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
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#####
# Home


@app.route('/')
@app.route('/home')
def home():
    tbs_cat = session.query(ArtCompanyName).all()
    return render_template('myhome.html', tbs_cat=tbs_cat)

#####
# Art Category for admins


@app.route('/ArtStore')
def ArtStore():
    try:
        if login_session['username']:
            name = login_session['username']
            tbs_cat = session.query(ArtCompanyName).all()
            tbs = session.query(ArtCompanyName).all()
            tbes = session.query(ArtName).all()
            return render_template('myhome.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))

######
# Showing arts based on art category


@app.route('/ArtStore/<int:tbid>/AllCompanys')
def showArts(tbid):
    tbs_cat = session.query(ArtCompanyName).all()
    tbs = session.query(ArtCompanyName).filter_by(id=tbid).one()
    tbes = session.query(ArtName).filter_by(artcompanynameid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showArts.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showArts.html',
                               tbs_cat=tbs_cat, tbs=tbs, tbes=tbes)

#####
# Add New Art


@app.route('/ArtStore/addArtCompany', methods=['POST', 'GET'])
def addArtCompany():
    if "username" not in login_session:
        flash("Please login first")
        return redirect(url_for("showLogin"))
    if request.method == 'POST':
        company = ArtCompanyName(name=request.form['name'],
                                 user_id=login_session['user_id'])
        session.add(company)
        session.commit()
        return redirect(url_for('ArtStore'))
    else:
        return render_template('addArtCompany.html', tbs_cat=tbs_cat)

########
# Edit Art Category


@app.route('/ArtStore/<int:tbid>/edit', methods=['POST', 'GET'])
def editArtCategory(tbid):
    editedArt = session.query(ArtCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(editedArt.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Art Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('ArtStore'))
    if request.method == "POST":
        if request.form['name']:
            editedArt.name = request.form['name']
        session.add(editedArt)
        session.commit()
        flash("Art Category Edited Successfully")
        return redirect(url_for('ArtStore'))
    else:
        # tbs_cat is global variable we can them in entire application
        return render_template('editArtCategory.html',
                               tb=editedArt, tbs_cat=tbs_cat)

######
# Delete Art Category


@app.route('/ArtStore/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteArtCategory(tbid):
    tb = session.query(ArtCompanyName).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Art Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('ArtStore'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("Art Category Deleted Successfully")
        return redirect(url_for('ArtStore'))
    else:
        return render_template('deleteArtCategory.html',
                               tb=tb, tbs_cat=tbs_cat)

######
# Add New Art Name Details


@app.route('/ArtStore/addCompany/addArtDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addArtDetails(tbname):
    tbs = session.query(ArtCompanyName).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tbs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showArts', tbid=tbs.id))
    if request.method == 'POST':
        name = request.form['name']
        year = request.form['year']
        color = request.form['color']
        price = request.form['price']
        artdetails = ArtName(name=name, year=year,
                             color=color,
                             price=price,
                             date=datetime.datetime.now(),
                             artcompanynameid=tbs.id,
                             user_id=login_session['user_id'])
        session.add(artdetails)
        session.commit()
        return redirect(url_for('showArts', tbid=tbs.id))
    else:
        return render_template('addArtDetails.html',
                               tbname=tbs.name, tbs_cat=tbs_cat)

######
# Edit Art details


@app.route('/ArtStore/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editArt(tbid, tbename):
    tb = session.query(ArtCompanyName).filter_by(id=tbid).one()
    artdetails = session.query(ArtName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showArts', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        artdetails.name = request.form['name']
        artdetails.year = request.form['year']
        artdetails.color = request.form['color']
        artdetails.price = request.form['price']
        artdetails.date = datetime.datetime.now()
        session.add(artdetails)
        session.commit()
        flash("Art Edited Successfully")
        return redirect(url_for('showArts', tbid=tbid))
    else:
        return render_template('editArt.html',
                               tbid=tbid, artdetails=artdetails,
                               tbs_cat=tbs_cat)

#####
# Delete Art Edit


@app.route('/ArtStore/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteArt(tbid, tbename):
    tb = session.query(ArtCompanyName).filter_by(id=tbid).one()
    artdetails = session.query(ArtName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this book edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showArts', tbid=tb.id))
    if request.method == "POST":
        session.delete(artdetails)
        session.commit()
        flash("Deleted Art Successfully")
        return redirect(url_for('showArts', tbid=tbid))
    else:
        return render_template('deleteArt.html',
                               tbid=tbid, artdetails=artdetails,
                               tbs_cat=tbs_cat)

####
# Logout from current user


@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected....'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type':
                           'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps
                                 ('Successfully disconnected user..'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('home'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#####
# Json


@app.route('/ArtStore/JSON')
def allArtsJSON():
    artcategories = session.query(ArtCompanyName).all()
    category_dict = [c.serialize for c in artcategories]
    for c in range(len(category_dict)):
        arts = [i.serialize for i in session.query(
                ArtName).filter_by(artcompanynameid=category_dict[c]["id"])
                .all()]
        if arts:
            category_dict[c]["art"] = arts
    return jsonify(ArtCompanyName=category_dict)

####


@app.route('/artStore/artCategories/JSON')
def categoriesJSON():
    arts = session.query(ArtCompanyName).all()
    return jsonify(artCategories=[c.serialize for c in arts])

####


@app.route('/artStore/arts/JSON')
def itemsJSON():
    items = session.query(ArtName).all()
    return jsonify(arts=[i.serialize for i in items])

#####


@app.route('/artStore/<path:art_name>/arts/JSON')
def categoryItemsJSON(art_name):
    artCategory = session.query(ArtCompanyName).filter_by(name=art_name).one()
    arts = session.query(ArtName).filter_by(artcompanyname=artCategory).all()
    return jsonify(artEdtion=[i.serialize for i in arts])

#####


@app.route('/artStore/<path:art_name>/<path:edition_name>/JSON')
def ItemJSON(art_name, edition_name):
    artCategory = session.query(ArtCompanyName).filter_by(name=art_name).one()
    artEdition = session.query(ArtName).filter_by(
           name=edition_name, artcompanyname=artCategory).one()
    return jsonify(artEdition=[artEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
