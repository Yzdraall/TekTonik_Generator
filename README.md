# ANONE Solver - Groupe Anone

Bienvenue sur le dépôt officiel du projet ANONE Solver réalisé par le groupe Anone (original).

Ce projet est une application complète développée par nos soins permettant d'importer, générer et résoudre des grilles de Tectonic.

Voici l'équipe ;

Killian     ->  Reconnassance de chiffe/IHM/Compilation gobale
Louna       ->  IHM
Titouan     ->  Traitement d'image
Pierre      ->  Solveur sat et HADOC
Néo         ->  Solveur sat et HADOC

----------

## Fonctionnalités principales ;

### Interface de jeu complète

- Menu interactif ; au lancement choisissez si vous voulez importer votre propre grille ou en générer une aléatoirement
- iteractive avec le clavier et la souris : selectionnez et remplissez les cases.
- mode notes (brouillon); permet d'inscrire des petits chiffres dans le coin pour tester des hypothèses.
- affichage adaptatif; La fenêtre est redimensionnable et l'interface s'adapte à la taille de l'écran et de la grille (dans la limite du raisonnable).

### Générateur de niveaux

- Création aléatoire de grilles de tailles variables (AxB avec A et B dans [5,9]²) avec zones variables.
puis utilise un solveur SAT pour garantir que chaque grille générée possède une solution.
la génération n'étant pas réellement optimisée, elle peut prendre un certain temps (3min max)

### Importation de grille personelle

- Prenez une photo d'une grille de Tectonic et importez-la.
L'application pourra reconnaître la grille et les chiffres et ainsi reconstruire la grille complète dans l'interface.
En parrallèle la grille sera tranférée a Minisat pour qu'il nous fournisse la grille résolue

### Outils d'Assistance

- Vérifier : Compare votre grille à la solution en temps réel (vert/rouge).
- Indice : Un solveur logique vous donne le prochain coup à jouer à un moment donné.
- Résoudre : Remplissage instantané de la grille grâce à MiniSAT.


--------


Pour lancer l'application, il faut run 'interface_tectonic.py', la fenêtre se lancera et le reste devrait être assez intuitif.