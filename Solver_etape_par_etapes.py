
class Tectonic:

    def __init__(self, Carte_nb, Carte_zone):
        self.carte_zone=Carte_zone
        self.carte_nb=Carte_nb
        self.zones=self.pos_zone()
        self.possi_init()
        self.equal()


    def pos_zone(self):
        """
        Renvoie un tableau associant chaque zone aux coordonnées de ses cases
        """
        nb_zone=1
        for ligne in self.carte_zone:
            for nb in ligne:
                if nb>=nb_zone:
                    nb_zone=nb+1
        #on crée une liste contenant un tableau pour représenter chaque zone
        res=[[]for i in range(nb_zone)]
        for i in range(len(self.carte_zone)):
            for j in range(len(self.carte_zone[0])):
                res[self.carte_zone[i][j]].append((i,j))
        return res
    
    def upd_adj(self,nb,pos):
        """
        Met à jour les possibilités des cases adjacentes à la case à la position "pos" en fonction de son nombre
        """
        del(self.possi[pos])
        for i in range(pos[0]-1,pos[0]+2):
            for j in range(pos[1]-1,pos[1]+2):
                if (i,j) in self.possi:
                    k=0
                    while k<len(self.possi[(i,j)]):
                        if self.possi[(i,j)][k]==nb:
                            del(self.possi[(i,j)][k])
                            k-=1
                        k+=1
        return

    def upd_zone(self,nb,pos):
        """
        Met à jour les possibilités des cases de la même zone que la case à la position "pos" en fonction de son nombre
        """
        for zone in self.zones:
            if pos in zone:
                for posi in zone:
                    if posi in self.possi:
                        k=0
                        while k<len(self.possi[posi]):
                            if self.possi[(posi)][k]==nb:
                                del(self.possi[(posi)][k])
                                k-=1
                            k+=1
        return

    def possi_init(self):
        """
        Initialise le dico de possibilités associant chaque coordonées du tableau avec ses possibilités
        """
        self.possi={}
        for i in range(len(self.zones)):
            for j in range(len(self.zones[i])):
                self.possi[self.zones[i][j]]=[i+1 for i in range(len(self.zones[i]))]
        for i in range(len(self.carte_nb)):
            for j in range(len(self.carte_nb[0])):
                if self.carte_nb[i][j]!=0:
                    self.upd_adj(self.carte_nb[i][j],(i,j))
                    self.upd_zone(self.carte_nb[i][j],(i,j))
        return
    
    def equal(self):
        """
        renvoi un dictionaire associant chaque case aux cases qui prendront forcément la même valeur
        """
        self.equals={}
        undef_zones=[[]for i in range(len(self.zones))]
        for i in range(len(self.zones)):
            for j in range(len(self.zones[i])):
                undef_zones[i].append(self.zones[i][j])
        for i in range(len(undef_zones)):
            j=0
            while j<len(undef_zones[i]):
                if undef_zones[i][j] not in self.possi:
                    del undef_zones[i][j]
                    j-=1
                j+=1
        for i in range(len(self.zones)):
            for pos1 in self.zones[i]:
                if pos1 in self.possi:
                    for x in range(pos1[0]-1,pos1[0]+2):
                        for y in range(pos1[1]-1,pos1[1]+2):
                            for zone in undef_zones:
                                if (x,y) in zone and pos1 not in zone:
                                    compt=0
                                    for pos2 in zone:
                                        if self.is_neigh(pos1,pos2):
                                            compt+=1
                                        else:
                                            add=pos2
                                    if compt==len(zone)-1:
                                        possible=True
                                        for possibilite in self.possi[pos1]:
                                            if possibilite not in self.possi[pos2]:
                                                possible=False
                                        if possible:
                                            if pos1 not in self.equals:
                                                self.equals[pos1]=[]
                                            if add not in self.equals[pos1]:
                                                self.equals[pos1].append(add)
        return

    def possi_uni(self):
        """
        Si une case n'a qu'une possibilité, renvoi le tableau avec cette case modifiée, sinon, renvoi le tableau d'origine
        """
        res=[[n for n in l]for l in self.carte_nb]
        for i in range(len(self.carte_nb[0])):
            for j in range(len(self.carte_nb)):
                if (i,j) in self.possi and len(self.possi[(i,j)])==1:
                    res[i][j]=self.possi[(i,j)][0]
                    return (res,self.possi[(i,j)][0],(i,j))
        return (res,None,None)
    
    def possi_zone(self,zone):
        """
        Associe à chaque nombre possible dans une zone les coordonées ou il est possible
        """
        res=[[]for i in range(len(zone))]
        for i in range(1,len(zone)+1):
            for pos in zone:
                if pos in self.possi and i in self.possi[pos]:
                    res[i-1].append(pos)
        return res
    
    def possi_uni_zones(self):
        """
        Si une zone à une possibilité qui n'est présente que dans une case, renvoi le tableau avec cette case modifiée, sinon, renvoi le tableau d'origine
        """
        res=[[n for n in l]for l in self.carte_nb]
        for zone in self.zones:
            pos_possi = self.possi_zone(zone)
            for i in range(len(pos_possi)):
                if len(pos_possi[i])==1:
                    pos=pos_possi[i][0]
                    res[pos[0]][pos[1]]=i+1
                    return (res,i+1,pos)        
        return (res,None,None)
    
    def is_neigh(self,pos1,pos2):
        if pos1==pos2:
            return False
        for i in range(pos1[0]-1,pos1[0]+2):
            for j in range(pos1[1]-1,pos1[1]+2):
                if (i,j)==pos2:
                    return True
        return False
    
    def parity(self):
        res={}
        for key in self.possi.keys():
            res[key]=[n for n in self.possi[key]]
        for zone in self.zones:
            pos_possi = self.possi_zone(zone)
            for i in range(len(pos_possi)):
                for j in range(len(pos_possi[i])):
                    for x in range(pos_possi[i][j][0]-1,pos_possi[i][j][0]+2):
                        for y in range(pos_possi[i][j][1]-1,pos_possi[i][j][1]+2):
                            overlap=True
                            for pos in pos_possi[i]:
                                if not self.is_neigh((x,y),pos):
                                    overlap=False
                                    if pos in self.equals:
                                        for pos2 in self.equals[pos]:
                                            if self.is_neigh((x,y),pos2):
                                                overlap=True
                            if overlap and (x,y) in res:
                                k=0
                                while k<len(res[(x,y)]):
                                    if res[(x,y)][k]==i+1:
                                        del(res[(x,y)][k])
                                        k-=1
                                    k+=1
                                return res
        return res
    """
    def hint(self):
        
        Renvoi un indice indiquant quel type de résolution est possible

        if self.possi_uni()[0] != self.carte_nb:
            #Highlight zone
            print("Une case n'a qu'une seule possibilité")
        elif self.possi_uni_zones()[0] != self.carte_nb:
            #Highlight zone
            print("Dans une zone, un nombre n'est possible que dans une seule case")
        elif self.parity() != self.possi:
            print("Il y a une parité")
        else:
            print("Résolution par étape impossible ou trop complexe")
            return
        #pour tests
        print("")
        print("position nombres :")
        for l in self.carte_nb:
            print(l)
        print("")
        print("position zones :")
        for l in self.carte_zone:
            print(l)
        #
        return
    """

    def find_move(self):
        """
        Cherche le prochain coup logique et le renvoie sous forme (ligne, col, valeur).
        Renvoie None si rien n'est trouvé.
        """
        #test si une case n'a qu'une seule possibilité
        res, val, pos = self.possi_uni()
        if pos is not None:
            return pos[0], pos[1], val
        
        # test si dans une zone, un nombre n'a qu'une place possible
        res, val, pos = self.possi_uni_zones()
        if pos is not None:
            return pos[0], pos[1], val
            
        #réduction par parité
        new_possi = self.parity()
        if new_possi != self.possi:
            self.possi = new_possi
            self.equal()
            return self.find_move() #récursion pour voir si cela a débloqué un coup
            
        return None
    

    def help(self):
        """
        Place un nombre dans la case la plus "simple" à résoudre
        """
        if self.possi_uni()[0] != self.carte_nb:
            res=self.possi_uni()
            self.carte_nb=res[0]
            self.upd_adj(res[1],res[2])
            self.upd_zone(res[1],res[2])
            self.equal()
        elif self.possi_uni_zones()[0] != self.carte_nb:
            res=self.possi_uni_zones()
            self.carte_nb=res[0]
            self.upd_adj(res[1],res[2])
            self.upd_zone(res[1],res[2])
            self.equal()
        elif self.parity() != self.possi:
            self.possi=self.parity()
            self.equal()
            self.help()
        else:
            print("Résolution par étape impossible ou trop complexe")
            return
        #pour tests
        print("position nombres :")
        for l in self.carte_nb:
            print(l)
        print("")
        print("position zones :")
        for l in self.carte_zone:
            print(l)
        #
        return



def calculer_solution_complete(grille_depart, zones):
    """
    Crée une instance du solveur et boucle tant qu'il trouve des coups logiques.
    Renvoie la grille remplie (ou partiellement remplie si bloqué).
    """
    
    grille_temp = [row[:] for row in grille_depart]
    
    solveur = Tectonic(zones, grille_temp)
    
    en_progres = True
    while en_progres:
        en_progres = False
        
        #test Case Unique
        res = solveur.possi_uni()
        if res[1] is not None:
            # On applique le changement
            solveur.carte_nb = res[0]
            solveur.upd_adj(res[1], res[2])
            solveur.upd_zone(res[1], res[2])
            solveur.equal()
            en_progres = True
            continue # On recommence la boucle pour voir si ça a débloqué un truc simple
            
        # test Zone Unique (seulement si case unique n'a rien donné)
        res = solveur.possi_uni_zones()
        if res[1] is not None:
            solveur.carte_nb = res[0]
            solveur.upd_adj(res[1], res[2])
            solveur.upd_zone(res[1], res[2])
            solveur.equal()
            en_progres = True
            continue

    return solveur.carte_nb






#Tests :

if __name__ == "__main__":

    Grille_1 = Tectonic([[5, 0, 0, 0, 0, 0, 0, 3, 0], [0, 4, 0, 0, 5, 0, 0, 0, 0], [0, 0, 0, 0, 0, 3, 0, 0, 0], [1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 2, 0]], 

[[ 0,  0,  0,  1,  2, 2, 3, 4, 4],
 [0, 0, 1, 1, 2, 2, 5, 4, 4],
 [7, 1, 1, 8, 2, 5, 5, 5, 6],
 [7, 7, 7, 8, 8, 8, 5, 6, 6],
 [7, 10, 10, 10, 10, 8, 11, 6, 9,]])
    

    print(Grille_1.equals)
    for i in range(16):
        print("")
        print("Appel n°"+str(i+1))
        print("")

        """Grille_1.hint()"""

        """ print("")"""
        Grille_1.help()

