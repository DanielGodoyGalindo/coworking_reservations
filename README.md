# coworking_reservations

This is a tutorial to start a Django project.

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

Django Admin -> Create room for testing

Add reservations/api/views.py
Create function availability_view(request) to test api
Go to http://127.0.0.1:8000/api/availability/?room_id=1&date=2026-02-10 to check if it's working properly