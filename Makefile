stop:
	sudo docker compose stop

build:
	sudo docker compose build

up:
	sudo docker compose up -d

all: stop build up
