<center>
    <h1>Coworking Reservations - Django project</h1>
</center>

<p align="center">
    <img src="https://i0.wp.com/www.opengis.ch/wp-content/uploads/2020/04/django-python-logo.png?fit=500%2C500&ssl=1" width=200px/>
</p>
<br><br>

This is the tutorial to create my project.
I will write every step that I do, so my future self can see how I did it :p
<br/>

 First create the project:
> python -m django startproject coworking_reservations

Then start the project with:
> python manage.py runserver

Now it's time to create the apps:
> python manage.py startapp rooms
python manage.py startapp reservations

Add new apps to coworking_reservations\settings.py:
INSTALLED_APPS = [..., rooms, reservations]

Create models:
Edit rooms/models.py and and classes

Create migrations:
https://docs.djangoproject.com/en/6.0/intro/tutorial02/
> python manage.py makemigrations
python manage.py migrate

Create tests in /reservations/tests.py
Use TDD (Test Driven Development) to test before writing more code
> python manage.py test reservations
For more info:
> python manage.py test reservations -v 2

Django Admin -> Create room for testing

Add reservations/api/views.py
Create function availability_view(request) to test api
Go to http://127.0.0.1:8000/api/availability/?room_id=1&date=2026-02-10 to check if it's working properly

Create function create_reservation in reservation/services.py
Test with POSTMAN
> POST http://127.0.0.1:8000/api/reservations/
> header -> Content-Type: application/json
> body raw JSON ->
{
  "room_id": 1,
  "date": "2026-02-10",
  "start_time": "09:00",
  "end_time": "10:00"
}

Create new tests file: tests_api.py
To execute the tests use:
> python manage.py test reservations.tests_api -v 2

Add authentication check: Just check in views if request.user is authenticated.
If not, return 401