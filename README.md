# Architecture Distribuée : Mixte
Ce projet porte sur des réservation de films dans un cinéma. Il est composé de 4 micro-services. 


|Service | Port |Technologie|
|--|--|--|
|Movies | 3200 |GraphQL|
|User | 3203 |REST|
|Schedule | 50051 |gRPC|
|Booking |3001  |GraphQL|

Chacun de ses services peuvent être individuellement lancé ou lancer tous en même temps via docker. 
(/!\ ne pas certains services comme *Booking* a besoin de se connecter aux autres micro service pour fonctionner)

## Instruction de lancement

### Lancer via docker 
Dans la racine du projet lancer la commande suivante :

    $ docker compose up --build

Cela va lancer la base de donnée mongo ainsi que tous les micro-services de l'application.

### Lancer via pymon :
Pour lancer individuellement les services, allez dans le dossier du service et lancer le grâce à pymon:

    $ cd service
    $ pymon service.py
    
## Fonctionnement de l'application 

### User 
User gère la gestion des utilisateurs, et de leurs droits, il y a des utilisateurs classique et des utilisateurs admin.  Un utilisateur comporte un nom, un id, un boolean représentant si il est admin ou non, et un timestamp représentant la dernière fois qu'il a été actif.

```json
{
	"id": "peter_curley",
	"name": "Peter Curley",
	"last_active": 1360031222,
	"admin": false
},
```

Il est possible de : 
 - Récupérer tout les utilisateurs 
 - Récupérer un utilisateur selon son id
 - Ajouter un utilisateur
 - Supprimer un utilisateur *( admin seulement )*
 - Mettre à jour un utilisateur *( admin ou utilisateur en question seulement )*

### Movie
Movies représente les films disponible dans le cinéma, ils ont chacun un titre,une note , et le nom du directeur ainsi que un id.

```json
{
	"title": "The Good Dinosaur", 
	"rating": 7.4, 
	"director": "Peter Sohn", 
	"id": "720d006c-3a57-4b6a-b18f-9b713b073f3c"
},
```
Il est possible de : 
 - Récupérer tous les films
 - Récupérer un film selon son id
 - Récupérer un film selon son titre
 - Ajouter un film
 - Modifier la note d'un film

### Schedule
Schedule représente les séance de visionnage des films pour une certaine date.

```json
{
	"date": "20151130", 
	"movies": [
		"720d006c-3a57-4b6a-b18f-9b713b073f3c", 
		"a8034f44-aee4-44cf-b32c-74cf452aaaae", 
		"39ab85e5-5e8e-4dc5-afea-65dc368bd7ab"
	]
},
```
 Il est possible de : 
 - Récupérer toutes le séance
 - Récupérer les films à visionner pour une date
 - Récupérer les date des séances d'un film
 - Ajouter une séance
 - Supprimer une séance

### Booking
Booking représente les réservation d'une séance, à une certaine séance d'un utilisateur. 


```json
{
	"userid": "chris_rivers", 
	"dates": [{
		"date": "20151201", 
		"movies": [
			"267eedb8-0f5d-42d5-8f43-72426b9fb3e6",
			 "7daf7208-be4d-4944-a3ae-c1c2f516f3e6"
		]
	}]
}
```
 Il est possible de : 
 - Savoir si une réservation existe déjà
 - Récupérer tous les réservations *( admin seulement )*
 - Récupérer les réservations d'un utilisateur *( admin ou utilisateur en question seulement )*
 - Ajouter une réservation *( admin ou utilisateur en question seulement )*
- Supprimer une réservation *( admin ou utilisateur en question seulement )*

