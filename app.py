#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from models import Venue, Artist, Show, db
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)


# TODO: connect to a local postgresql database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:presidenT98!@localhost:5432/postgres'
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  current_time = datetime.now().strftime('%Y-%m-%d %H:%S:%M')
  venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
  venue_state_and_city = ''
  data = []

  #loop through venues to check for upcoming shows, city, states and venue information
  for venue in venues:
    #filter upcoming shows given that the show start time is greater than the current time
    print(venue)
    upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
    if venue_state_and_city == venue.city + venue.state:
      data[len(data) - 1]["venues"].append({
        "id": venue.id,
        "name":venue.name,
        "num_upcoming_shows": len(upcoming_shows) # a count of the number of shows
      })
    else:
      venue_state_and_city == venue.city + venue.state
      data.append({
        "city":venue.city,
        "state":venue.state,
        "venues": [{
          "id": venue.id,
          "name":venue.name,
          "num_upcoming_shows": len(upcoming_shows)
        }]
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  venue_query = Venue.query.filter(Venue.name.ilike('%' + request.form['search_term'] + '%'))
  venue_list = list(map({Venue.id, Venue.name}, venue_query)) 
  response = {
    "count":len(venue_list),
    "data": venue_list
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  try:
    if venue:
      venue_data = Venue.data(venue_query)
      current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      new_shows_query = Show.query.options(db.joinedload(Show.Venue)).filter(Show.venue_id == venue_id).filter(Show.start_time > current_time).all()
      new_show = list(map(Show.artist_details, new_shows_query))
      venue_details["upcoming_shows"] = new_show
      venue_details["upcoming_shows_count"] = len(new_show)
      past_shows_query = Show.query.options(db.joinedload(Show.Venue)).filter(Show.venue_id == venue_id).filter(Show.start_time <= current_time).all()
      past_shows = list(map(Show.artist_details, past_shows_query))
      venue_details["past_shows"] = past_shows
      venue_details["past_shows_count"] = len(past_shows)
    
    return render_template('pages/show_venue.html', venue=venue_data)
  except:
    flash(f'The venue {venue.name} does not exit')
    return render_template('pages/home.html')

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:

    new_venue = Venue(
      name=request.form['name'],
      genres=request.form.getlist('genres'),
      address=request.form['address'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      website=request.form.get('website'),
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      seeking_description=request.form['seeking_description'],
      seeking_talent=bool(request.form.get('seeking_talent'))
    )
    #insert new venue records into the db
    Venue.insert_data(new_venue)
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except SQLAlchemyError as e:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    print('Error ',  e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
    flash('Venue number ' + venue_id + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue number' + venue_id + ' could not be deleted.')
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artist_query = Artist.query.filter(Artist.name.ilike('%' + request.form['search_term'] + '%'))
  artist_list = list(map(Artist.short, artist_query)) 
  response = {
    "count":len(artist_list),
    "data": artist_list
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist_search = Artist.query.get(artist_id)
  try:
    if artist_search:
      artist_data = Artist.data(artist_search)
      #get the current system time
      current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      new_shows_query = Show.query.options(db.joinedload(Show.Artist)).filter(Show.artist_id == artist_id).filter(Show.start_time > current_time).all()
      new_shows_list = list(map(Show.venue_details, new_shows_query))
      artist_details["upcoming_shows"] = new_shows_list
      artist_details["upcoming_shows_count"] = len(new_shows_list)
      past_shows_query = Show.query.options(db.joinedload(Show.Artist)).filter(Show.artist_id == artist_id).filter(Show.start_time <= current_time).all()
      past_shows_list = list(map(Show.venue_details, past_shows_query))
      artist_details["past_shows"] = past_shows_list
      artist_details["past_shows_count"] = len(past_shows_list)
      return render_template('pages/show_artist.html', artist=artist_data)
  except:
    flash(f'The artist -> {artist_id} does not exist.')
    return render_template('pages/show_artist.html')


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  
  try:
    artist_data = Artist.query.get(artist_id)
    if artist_data:
      artist_details = Artist.details(artist_data)
      form.name.data = artist_details["name"]
      form.genres.data = artist_details["genres"]
      form.city.data = artist_details["city"]
      form.state.data = artist_details["state"]
      form.phone.data = artist_details["phone"]
      form.website.data = artist_details["website"]
      form.facebook_link.data = artist_details["facebook_link"]
      form.seeking_venue.data = artist_details["seeking_venue"]
      form.seeking_description.data = artist_details["seeking_description"]
      form.image_link.data = artist_details["image_link"]
      return render_template('forms/edit_artist.html', form=form, artist=artist_data)
  except:
    flash(f'The artist -> {artist_id} does not exit.')
  # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html')

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  artist_data = Artist.query.get(artist_id)
  try:
    if artist_data:
        if form.validate():
            seeking_venue = False
            seeking_description = ''
            if 'seeking_venue' in request.form:
                seeking_venue = request.form['seeking_venue'] == 'y'
            if 'seeking_description' in request.form:
                seeking_description = request.form['seeking_description']
            artist_data.name =  request.form['name']
            artist_data.genres = request.form.getlist('genres')
            artist_data.city =  request.form['city']
            artist_data.state = request.form['state']
            artist_data.phone = request.form['phone']
            artist_data.website = request.form['website']
            artist_data.facebook_link = request.form['facebook_link']
            artist_data.image_link = request.form['image_link']
            artist_data.seeking_description = seeking_description
            artist_data.seeking_venue = seeking_venue
            Artist.update_data(artist_data)
            return redirect(url_for('show_artist', artist_id=artist_id))
  except:
    flash(f'The artist -> {artist_id} does not exit.')
    return redirect(url_for('index'))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  try:
    venue_query = Venue.query.get(venue_id)
    if venue_query:
      venue_data = Venue.data(venue_query)
      form.name.data = venue_data["name"]
      form.genres.data = venue_data["genres"]
      form.address.data = venue_data["address"]
      form.city.data = venue_data["city"]
      form.state.data = venue_data["state"]
      form.phone.data = venue_data["phone"]
      form.website.data = venue_data["website"]
      form.facebook_link.data = venue_data["facebook_link"]
      form.seeking_talent.data = venue_data["seeking_talent"]
      form.seeking_description.data = venue_data["seeking_description"]
      form.image_link.data = venue_data["image_link"]
      return render_template('form/edit_venue.html', form=form, Venue=venue_details)
  except:
    flash(f'Venue -> {venue_id} deos not exist')
    return render_template('forms/edit_venue.html')

  # TODO: populate form with values from venue with ID <venue_id>
  #return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  #form = VenueForm(request.form)
  try:
    venue_data = Venue.query.get(venue_id)
    if venue_data:
        if form.validate():
            seeking_talent = False
            seeking_description = ''
            if 'seeking_talent' in request.form:
                seeking_talent = request.form['seeking_talent'] == 'y'
            if 'seeking_description' in request.form:
                seeking_description = request.form['seeking_description']
            venue_data.name = request.form['name']
            venue_data.genres = request.form.getlist('genres')
            venue_data.address = request.form['address']
            venue_data.city = request.form['city']
            venue_data.state = request.form['state']
            venue_data.phone = request.form['phone']
            venue_data.website = request.form['website']
            venue_data.facebook_link = request.form['facebook_link']
            venue_data.image_link = request.form['image_link']
            venue_data.seeking_description = seeking_description
            venue_data.seeking_talent = seeking_talent
            Venue.update_data(venue_data)
            return redirect(url_for('show_venue', venue_id=venue_id))
  except:
    flash(f'The Venue -> {venue_id} does not exist.')
    return redirect(url_for('index'))
  
  #return redirect(url_for('show_venue', venue_id=venue_id))



#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  try:
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    new_artist = Artist(
      name=request.form['name'],
      genres=request.form['genres'],
      city=request.form['city'],
      state= request.form['state'],
      phone=request.form['phone'],
      website=request.form['website'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_venue=seeking_venue,
      seeking_description=seeking_description,
    )
    Artist.insert_data(new_artist)
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except SQLAlchemyError as e:
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    flash('An error occurred. Artist ' + request.form['name'] + 'could not be listed. ')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  show_query = Show.query.options(db.joinedload(Show.Venue), db.joinedload(Show.Artist)).all()
  data = list(map(Show.data, show_query))

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    new_show = Show(
      venue_id=request.form['venue_id'],
      artist_id=request.form['artist_id'],
      start_time=request.form['start_time'],
    )
    Show.insert_data(new_show)

    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except SQLAlchemyError as e:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occured. Show could not be listed.')
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

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
