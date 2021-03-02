# app.py
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

import datetime as dt

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Hawaii Climate API database<br/>"
        f"-------------------------------------<br/><br/>"
        f"Available Routes:<br/>"
        f"-----------------------<br/>"
        f"1. Last 12 months of precipitation data -<br>"
        f"  /api/v1.0/precipitation<br/><br/>"
        f"2. List of Hawaii weather stations -<br>"
        f"  /api/v1.0/stations<br/><br/>"
        f"3. Temperature observations of the most active station for the last year -<br>"
        f"  /api/v1.0/tobs<br/><br/>"
        f"4. Minimum temperature, the average temperature,"
        f"and the max temperature of a given date range -<br>"
        f"  /api/v1.0/(start date 'YYYY-MM-DD')<br>  or<br>"
        f"  /api/v1.0/(start date 'YYYY-MM-DD')/(end date 'YYYY-MM-DD')"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    query_date = one_year_ago(session)

    # Perform a query to retrieve the data and precipitation scores
    results = session.query(Measurement.date, Measurement.prcp).\
    filter(Measurement.date >= query_date).all()

    session.close()

    # Convert list of tuples into normal list
    all_dates = list(np.ravel(results))

    return jsonify(all_dates)


@app.route("/api/v1.0/stations")
def stations():
     # Create our session (link) from Python to the DB
     session = Session(engine)

     """Return a list of station data including the station name, latitude, and longitude"""
     # Query all stationss
     results = session.query(Station.station, Station.name, Station.latitude, Station.longitude).all()

     session.close()

     # Convert list of tuples into normal list
     all_stations = list(np.ravel(results))

     return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    query_date = one_year_ago(session)

    # Find the most active station for the last year in the database
    active_station = session.query(Station.station, Station.name, func.count(Measurement.id)).\
        group_by(Measurement.station).filter(Measurement.station == Station.station).\
        filter(Measurement.date >= query_date).\
        order_by(func.count(Measurement.id).desc()).first()

    # get the temperture results for the most active station in the last year
    results = session.query(Station.station, Station.name, Measurement.date, Measurement.tobs).\
        filter(Measurement.station == Station.station).\
        filter(Measurement.date >= query_date).filter(Measurement.station == active_station[0])
    
    session.close()

    all_temps = []
    for station, name, date, tobs in results:
        temp_dict = {}
        temp_dict["station"] = station
        temp_dict["name"] = name
        temp_dict["date"] = date
        temp_dict["tobs"] = tobs
        all_temps.append(temp_dict)

    return jsonify(all_temps)

@app.route("/api/v1.0/<start_date>")
def start_date(start_date):
     # Create our session (link) from Python to the DB
     session = Session(engine)

     # Perform a query to retrieve temperature greater than requested date
     try:
        query_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs)\
        , func.max(Measurement.tobs)).filter(Measurement.date >= query_date).all()
     except ValueError:
        return jsonify({"error": f"Date must be in 'YYYY-MM-DD' format."}), 404
     
     session.close()

     # Convert list of tuples into normal list
     statistics = list(np.ravel(results))

     return jsonify(statistics)

@app.route("/api/v1.0/<start_date>/<end_date>")
def start_end_date(start_date, end_date):
     # Create our session (link) from Python to the DB
     session = Session(engine)

     # Perform a query to retrieve temperature greater than requested date
     try:
        q_start_date = dt.datetime.strptime(start_date, '%Y-%m-%d')
        q_end_date = dt.datetime.strptime(end_date, '%Y-%m-%d')
        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs)\
        , func.max(Measurement.tobs)).filter(Measurement.date >= q_start_date).\
            filter(Measurement.date <= q_end_date).all()
     except ValueError:
        return jsonify({"error": f"Date must be in 'YYYY-MM-DD' format."}), 404
     
     session.close()

     # Convert list of tuples into normal list
     statistics = list(np.ravel(results))

     return jsonify(statistics)

#################################################
# Main code and Sub Routines
#################################################

# Calculate the date 1 year ago from the last data point in the database
def one_year_ago(session):
    lastdate = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    lastdatedt = dt.datetime.strptime(lastdate[0], '%Y-%m-%d')
    query_date = lastdatedt - dt.timedelta(days=365)
    return query_date

# Main
if __name__ == '__main__':
    app.run(debug=True)