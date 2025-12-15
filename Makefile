up : 
	docker compose up -d
build : 
	docker compose build
build-up : build up
down : 
	docker compose down
down-volumes : 
	docker compose down -v