from pysat.solvers import Solver

class TectonicSAT:
    def __init__(self, grille, zones):
        self.grille = grille
        self.carte_zones = zones
        self.lignes = len(grille)
        self.cols = len(grille[0])
        
        #on utilise MiniSat via pysat
        self.solveur = Solver(name='m22') 
        
        #dictionnaire pour mapper (ligne, col, valeur) -> ID
        self.map_vars = {}
        self.map_inv = {}
        self.compteur_var = 1

    def id_var(self, l, c, v):
        """Retourne l'ID unique pour la variable 'Case(l,c) = v'"""
        if (l, c, v) not in self.map_vars:
            self.map_vars[(l, c, v)] = self.compteur_var
            self.map_inv[self.compteur_var] = (l, c, v)
            self.compteur_var += 1
        return self.map_vars[(l, c, v)]

    def pos_zone(self):
        """Récupère les coordonnées par zone (comme dans votre code original)"""
        nb_zone = 0
        for ligne in self.carte_zones:
            for nb in ligne:
                if nb > nb_zone: nb_zone = nb
        
        res = [[] for _ in range(nb_zone + 1)]
        for i in range(self.lignes):
            for j in range(self.cols):
                res[self.carte_zones[i][j]].append((i, j))
        return [z for z in res if z] # Filtre les zones vides

    def contrainte_possibilite(self, zones_coords):
        """Chaque case doit avoir au moins une valeur valide"""
        # Pour les cases déjà remplies
        for i in range(self.lignes):
            for j in range(self.cols):
                val = self.grille[i][j]
                if val != 0:
                    self.solveur.add_clause([self.id_var(i, j, val)])

        # Pour toutes les cases : doit valoir entre 1 et taille_zone
        for zone in zones_coords:
            taille = len(zone)
            for (i, j) in zone:
                clause = [self.id_var(i, j, v) for v in range(1, taille + 1)]
                self.solveur.add_clause(clause)

    def contrainte_unicite(self, zones_coords):
        """Une case ne peut pas avoir deux valeurs en même temps"""
        for zone in zones_coords:
            taille = len(zone)
            for (i, j) in zone:
                for v1 in range(1, taille + 1):
                    for v2 in range(v1 + 1, taille + 1):
                        self.solveur.add_clause([-self.id_var(i, j, v1), -self.id_var(i, j, v2)])

    def contrainte_voisinage(self, zones_coords):
        """Deux cases voisines ne peuvent pas avoir la même valeur"""
        for i in range(self.lignes):
            for j in range(self.cols):
                #voisins
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        if di == 0 and dj == 0: continue
                        ni, nj = i + di, j + dj
                        
                        if 0 <= ni < self.lignes and 0 <= nj < self.cols:
                            for v in range(1, 10): 
                                id1 = self.id_var(i, j, v)
                                id2 = self.id_var(ni, nj, v)
                                self.solveur.add_clause([-id1, -id2])

    def contrainte_zone(self, zones_coords):
        """Dans une zone, chaque chiffre est unique"""
        for zone in zones_coords:
            taille = len(zone)
            for v in range(1, taille + 1):
                # Pour chaque paire de cases dans la zone, elles ne peuvent pas valoir v toutes les deux
                for k in range(len(zone)):
                    for m in range(k + 1, len(zone)):
                        pos1 = zone[k]
                        pos2 = zone[m]
                        self.solveur.add_clause([
                            -self.id_var(pos1[0], pos1[1], v),
                            -self.id_var(pos2[0], pos2[1], v)
                        ])

    def resoudre(self):
        zones_coords = self.pos_zone()
        
        # Application des contraintes 
        self.contrainte_possibilite(zones_coords)
        self.contrainte_unicite(zones_coords)
        self.contrainte_voisinage(zones_coords)
        self.contrainte_zone(zones_coords)
        
        # Résolution avec MiniSat
        if self.solveur.solve():
            modele = self.solveur.get_model()
            grille_res = [row[:] for row in self.grille]
            
            # Reconstruction de la grille
            for val_id in modele:
                if val_id > 0 and val_id in self.map_inv:
                    l, c, v = self.map_inv[val_id]
                    grille_res[l][c] = v
            
            self.solveur.delete()
            return grille_res
        else:
            self.solveur.delete()
            return None

def resoudre_sat(grille, zones):
    # Fonction wrapper pour garder l'appel simple dans l'interface
    solveur = TectonicSAT(grille, zones)
    return solveur.resoudre()