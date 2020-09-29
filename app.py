# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import create_app, Artist, Venue, Show
from collections import defaultdict
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy()
migrate = Migrate(app, db)

with app.app_context():
    db.init_app(app)


# TODO: connect to a local postgresql database
# Project Complete
# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    ''' Show all the venues '''
    # Getting the areas
    areas = db.session.query(Venue.city, Venue.state).distinct()

    data = []
    for area in areas:
        state = Venue.query.filter_by(state=area.state)
        state_city = state.filter_by(city=area.city)
        venues = state_city.all()

        venue_list = []

        for venue in venues:
            shows = db.session.query(Show)
            query2 = shows.filter(Show.venue_id == 1)
            upcoming = query2.filter(Show.start_time > datetime.now())
            UpcomingShowsCount = len(upcoming.all())

            venues_data = {
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': UpcomingShowsCount
            }
            venue_list.append(venues_data)

        data.append({
            "city": area.city,
            "state": area.state,
            "venues": venue_list
        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    '''search for a venue'''
    results = defaultdict()
    search_term = request.form.get('search_term')
    search_venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
    results['count'] = len(search_venues)
    results['data'] = search_venues

    return render_template('pages/search_venues.html', results=results,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    ''' Getting a venue '''
    try:
        venue_result = Venue.query.get(venue_id)
        if not venue_result:
            return render_template('errors/404.html')

        shows = db.session.query(Show)
        join_artist = shows.join(Artist)
        show_for_venue = join_artist.filter(Show.venue_id == venue_id)
        upcoming = show_for_venue.filter(Show.start_time > datetime.now())
        shows_upcoming = upcoming.all()

        upcoming_shows = []
        for show in shows_upcoming:
            upcoming_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        past = show_for_venue.filter(Show.start_time < datetime.now())
        shows_past = past.all()

        past_shows = []
        for show in shows_past:
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        data = {
            "id": venue_result.id,
            "name": venue_result.name,
            "genres": venue_result.genres,
            "address": venue_result.address,
            "city": venue_result.city,
            "state": venue_result.state,
            "phone": venue_result.phone,
            "website": venue_result.website,
            "facebook_link": venue_result.facebook_link,
            "image_link": venue_result.image_link,
            "seeking_talent": venue_result.seeking_talent,
            "seeking_description": venue_result.seeking_description,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }

        return render_template('pages/show_venue.html', venue=data)
    except:
        flash('Record not found')
        return render_template('errors/404.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    ''' create a new venue '''
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """ create a new venue submission """
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        genres = request.form.getlist("genres[]")
        facebook_link = request.form.get("facebook_link")
        website = request.form.get("website_link")
        image_link = request.form.get("image_link")

        venue = Venue(name=name, city=city, state=state, genres=genres, address=address, phone=phone,
                      facebook_link=facebook_link, website=website, image_link=image_link)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except Exception as e:
        flash('Venue ' + request.form['name'] + ' could not be listed due to error:- ' + str(e))
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """ delete a venue """
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue_id + ' is deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash('Something went wrong. Venue ' + venue_id + ' could not be deleted.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    ''' Getting artists '''
    data = db.session.query(Artist).all()

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    ''' search artists '''
    results = defaultdict()
    search_term = request.form.get('search_term')
    search_results = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
    results['count'] = len(search_results)
    results['data'] = search_results

    return render_template('pages/search_artists.html',
                           results=results,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    ''' show artist '''
    try:
        artist = db.session.query(Artist)
        artist_query_result = artist.get(artist_id)

        if not artist_query_result:
            return render_template('errors/404.html')

        shows = db.session.query(Show)
        venue_join = shows.join(Venue)
        show_venue = venue_join.filter(Show.artist_id == artist_id)
        past = show_venue.filter(Show.start_time < datetime.now())

        shows_past = past.all()

        past_shows = []

        for show in shows_past:
            past_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "artist_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        upcoming = show_venue.filter(Show.start_time > datetime.now())
        shows_upcoming = upcoming.all()
        upcoming_shows = []

        for show in shows_upcoming:
            upcoming_shows.append({
                "venue_id": show.venue_id,
                "venue_name": show.venue.name,
                "artist_image_link": show.venue.image_link,
                "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
            })

        data = {
            "id": artist_query_result.id,
            "name": artist_query_result.name,
            "genres": artist_query_result.genres,
            "city": artist_query_result.city,
            "state": artist_query_result.state,
            "phone": artist_query_result.phone,
            "website": artist_query_result.website,
            "facebook_link": artist_query_result.facebook_link,
            "image_link": artist_query_result.image_link,
            "seeking_venue": artist_query_result.seeking_venue,
            "seeking_description": artist_query_result.seeking_description,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
        }

        return render_template('pages/show_artist.html', artist=data)
    except:
        flash('Record not found')
        return render_template('errors/404.html')



#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    ''' edit artist '''
    form = ArtistForm()
    artist_result = Artist.query.get(artist_id)
    if (artist_result):
        form.name.data = artist_result.name
        form.city.data = artist_result.city
        form.state.data = artist_result.state
        form.phone.data = artist_result.phone
        form.genres.data = artist_result.genres
        form.facebook_link.data = artist_result.facebook_link
        form.image_link.data = artist_result.image_link
        form.website.data = artist_result.website
        form.seeking_venue.data = artist_result.seeking_venue
        form.seeking_description.data = artist_result.seeking_description

    return render_template('forms/edit_artist.html', form=form, artist=artist_result)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    ''' edit artist submission '''
    artist_result = Artist.query.get(artist_id)
    try:
        artist_result.name = request.form['name']
        artist_result.city = request.form['city']
        artist_result.state = request.form['state']
        artist_result.phone = request.form['phone']
        artist_result.genres = request.form.getlist('genres')
        artist_result.image_link = request.form['image_link']
        artist_result.facebook_link = request.form['facebook_link']
        artist_result.website = request.form['website']
        artist_result.seeking_venue = True if 'seeking_venue' in request.form else False
        artist_result.seeking_description = request.form['seeking_description']
        db.session.commit()
        flash('Artist detail is successfully updated!')

    except Exception as e:
        db.session.rollback()
        flash('Error %s occured. Artist could not be changed.' % str(e))
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    ''' edit venue '''
    form = VenueForm()
    venue_result = Venue.query.get(venue_id)

    if venue_result:
        form.name.data = venue_result.name
        form.city.data = venue_result.city
        form.state.data = venue_result.state
        form.phone.data = venue_result.phone
        form.address.data = venue_result.address
        form.genres.data = venue_result.genres
        form.facebook_link.data = venue_result.facebook_link
        form.image_link.data = venue_result.image_link
        form.website.data = venue_result.website
        form.seeking_talent.data = venue_result.seeking_talent
        form.seeking_description.data = venue_result.seeking_description

        return render_template('forms/edit_venue.html', form=form, venue=venue_result)
    else:
        flash('Error while editing')


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    ''' edit venue submission '''
    venue_result = Venue.query.get(venue_id)

    try:
        venue_result.name = request.form['name']
        venue_result.city = request.form['city']
        venue_result.state = request.form['state']
        venue_result.address = request.form['address']
        venue_result.phone = request.form['phone']
        venue_result.genres = request.form.getlist('genres')
        venue_result.image_link = request.form['image_link']
        venue_result.facebook_link = request.form['facebook_link']
        venue_result.website = request.form['website']
        venue_result.seeking_talent = True if 'seeking_talent' in request.form else False
        venue_result.seeking_description = request.form['seeking_description']
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash('Error occured!Venue details could not be changed.')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    """ create artists """
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """ create artists submission """
    try:
        name = request.form.get("name")
        genres = request.form.getlist("genres[]")
        city = request.form.get("city")
        state = request.form.get("state")
        phone = request.form.get("phone")
        website = request.form.get("website_link")
        image_link = request.form.get("image_link")
        facebook_link = request.form.get("facebook_link")
        seeking_venue = True if 'seeking_venue' in request.form else False
        seeking_description = request.form.get("seeking_description")

        artist = Artist(name=name, genres=genres, city=city, state=state, phone=phone, website=website,
                        facebook_link=facebook_link,
                        image_link=image_link, seeking_venue=seeking_venue, seeking_description=seeking_description, )
        db.session.add(artist)
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        flash('Artist ' + request.form['name'] + ' could not be listed due to error:- ' + str(e))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    ''' Getting shows '''
    shows = Show.query.all()

    shows_list = []
    for show in shows:
        venue_id = show.venue_id
        artist_id = show.artist_id
        start_time = str(show.start_time)
        venue_name = db.session.query(Venue.name).filter(Venue.id==show.venue_id).first()
        artist_name = db.session.query(Artist.name).filter(Artist.id==show.artist_id).first()
        artist_image_link = db.session.query(Artist.image_link).filter(Artist.id==show.artist_id).first()
        data = {
            "venue_id": venue_id,
            "artist_id": artist_id,
            "start_time": start_time,
            "venue_name": venue_name[0],
            "artist_name": artist_name[0],
            "artist_image_link": artist_image_link[0]
        }
        shows_list.append(data)
        return render_template('pages/shows.html', shows=shows_list)

@app.route('/shows/create')
def create_shows():
    ''' create new show '''
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    ''' create new show submission '''
    try:
        venue_id = request.form.get('venue_id'),
        artist_id = request.form.get('artist_id'),
        start_time = request.form.get('start_time')

        show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was listed successfuly!')
    except Exception as e:
        flash('Show could not be listed due to error:- ' + str(e))
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:

if __name__ == '__main__':
    #    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=5000, debug=True)

