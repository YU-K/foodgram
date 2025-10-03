stop:
	sudo docker compose stop

build:
	sudo docker compose build

up:
	sudo docker compose up -d

logs:
	sudo docker compose logs -f

all: stop build up
