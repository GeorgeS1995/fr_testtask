FROM python:3.8.3-alpine3.11
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]