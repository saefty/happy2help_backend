**Happy 2 Help Django Backend**
-

Django backend with graphql

**How to run:**
```
# install virtualenv
pip install virtualenv
```
```
# create virtualenv
# (make sure to use python3)
virtualenv env
```
```
# activate virtualenv
source env/Scripts/activate # linux
env/Scripts/activate # windows
```
```
# install requirements
pip install -r requirements.txt
```
```
# create database
python manage.py makemigrations
python manage.py migrate
```
```
# create superuser
python manage.py createsuperuser
```
```
# run development server
python manage.py runserver
```
```
# save data to file
python manage.py dumpdata Happy2Help auth.user --indent=2 > sample_data.json
```
```
# load data from file
python manage.py loaddata sample_data.json
```
```python
import this
import antigravity
```