# SeelkCoinAPI

API that enables users to be alerted by email of currencies exchange movement

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Not included in this project requirements but needed are:
```
PostgreSQL
Python3
And a celery message broker
```

### Installing

After cloning this repo move to SeelkCoinAPI and create a virtual environment there:

```
python3 -m venv env
source env/bin/activate
```

Then install requirements:

```
pip install -r requirements.txt
```

Last step before using the API is creating a super user:

```
python manage.py createsuperuser
```

I advise you to create the following one for perfect compatibility with shared Postman workspace:

```
username:         admin
email:            admin@host.com
password:         password
confirm_password: password
```

You can then run the project by typing:

```
python manage.py runserver
```

and the celery worker (in a different window):

```
celery -A api worker -l info -E
```

## API Content

This API allows:
* REGULAR USERS to:
  * Register, LogIn, LogOut
  * See, update and/or delete their own account (on /me route)
  * Create, retrieve, update and delete their own alerts (on /alerts route)
* STAFF USERS to:
  * Do same the thing than regular users, plus:
  * Create, retrieve, update and delete account of other users (on /users route)
  * Create, retrieve, update and delete alerts of other users (on /users/<id>/alerts route)

Alerts can be of two type:
   * A threshold is set => The user is alerted when the desired exchange rate climbs above or falls under this threshold.
   * An evolution rate and a period are set => The user is alerted if the exchange rate evolves from this percentage in the given timeframe.

The provided parameters for alert creation must follow these rules:
* The threshold argument must be a positive number
* The evolution rate (percentage of variation) cannot be lower than -100 (%) but can be greater than 100...
* The period is expressed in seconds
* The list of available currencies is available [here](https://0bin.net/paste/w5dV4dhVme6SQY2P#6luDL+gQHZELTFxwj6H+1e2u348RBR1R30brH6yAEHi)

Note: To be able to use this API you must also register and get a free API Key from [coinapi.io](https://docs.coinapi.io/)

## WIP and ideas for improvement

Eventhough the list of accepted currencies by my API is quite long, there are more available on coinapi.io, but in order to exploit them, it is better to get a paid key. Indeed, my API only makes requests on a restricted part of coinapi.io because of the limitation of 100API calls/day.

Ideas for improvement include:
  * Make requests on ohclv route for assets that dont't have a usd_price
  * In order to consume less bandwidth, connect to websocket stream instead of REST API
  * Implement a better management of the Celery task queue ^^
 
 ## Author
 * **Adrien Serguier** - Ecole 42 @Paris
 
