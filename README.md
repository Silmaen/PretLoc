# PretLoc

A simple softwrara platform for managing rental.

## Requests

* [ ] afficher la disponibilité d'un article dans une ligne de réservation
    * [ ] (optionnel) déduire de la disponibilité la réservation en cours de création/modification
        * [ ] avoir la même recherche de client dans la réservation et la liste des clients
    * [ ] (optionnel) avoir l'icône de type de client dans la recherche
* [ ] Dans la vue de réservation, afficher le type de client
    * [ ] Afficher si le client bénéficie d'une éxonération de don
    * [ ] Estimer le don suggéré (déduire la cotisation si déjà faite cette année)
        * [ ] Les clients extérieurs ont un don suggéré doublé
* [ ] Dans la vue client, permettre l'affichage des réservations passées
    * [ ] Dans la vue client, permettre l'affichage des réservations à venir/encours
    * [ ] Dans la vue client, permettre l'affichage des dons
* [ ] Ajouter un champ dans les clients pour savoir s'il a déjà fait un don cette année (cotisation)
* [ ] Permettre d'archiver un client (ne plus le proposer dans les recherches)
* [ ] Permettre la génération des pdf de toutes les reservation qui sortent le prochain vendredi ou lundi.
* [ ] Permettre à un client de reconduire sa réservation (mêmes articles, autre date)
* [ ]  Gestion des délais
    * [ ] Pour les ganathains et membre, permettre de réserver 12 mois à l'avance
    * [ ] Pour les extérieurs, permettre de réserver 1 mois à l'avance
        * [ ] Validation impossible si on dépasse cette limite