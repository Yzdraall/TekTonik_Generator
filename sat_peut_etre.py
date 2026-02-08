from os import system
from pysat.solvers import Glucose3


def Coordinates(G):
    return [[i,j] for j in range(len(G[0])) for i in range(len(G))]

def cases_zones(zones,i,j):
    return [[a,b] for (a,b) in Coordinates(G) if zones[i][j] == zones[a][b] and (a,b)!=(i,j)]

def max_tab(tab):
    max = tab[0][0]
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if max<tab[i][j]:
                max = tab[i][j]
    return max

def compte_cases_zone(zones):
    liste = [0]*(max_tab(zones)+1)
    for i in range(len(zones)):
        for j in range(len(zones[i])):
            liste[zones[i][j]]+=1
    return liste

def ShapeValues(zones,i,j):
    liste = []
    for a in range(1,compte_cases_zone(zones)[zones[i][j]]+1):
        liste.append(a)
    return liste

def UnicityConstraints(G,zones):
    return [ [ (False,i,j,k), (False,i,j,m) ]
            for (i,j) in Coordinates(G)
            for k in ShapeValues(zones,i,j)
            for m in ShapeValues(zones,i,j)
            if k<m ]

def ValueConstraints(G,zones):
    return [ [(True,i,j,k) for k in ShapeValues(zones,i,j)] for (i,j) in Coordinates(G) ]

def Voisins(G,i,j):
    return [(i+di,j+dj) for di in {-1,0,1} for dj in {-1,0,1} if (di,dj) != (0,0) if 0<=i+di<len(G) if 0<=j+dj<len(G[0]) ]

def VoisinsConstraints(G,zones):
    return [ [(False,i,j,k), (False,a,b,k)] for (i,j) in Coordinates(G) for (a,b) in Voisins(G,i,j) for k in ShapeValues(zones,i,j) if k in ShapeValues(zones,a,b)]

def nbr_poss_zones(zones):
    dico = {}
    max = max_tab(zones)
    for i in range(1,max+1):
        dico[i] = []
        for a in range(1,compte_cases_zone(zones)[i-1]+1):
            dico[i].append(a)
    return dico

def ZonesConstraints(G,zones):
    #return [[(False,i,j,k), (False,a,b,k)] for (i,j) in Coordinates(G) for (a,b) in Coordinates(G) for k in ShapeValues(zones,i,j) if (i<a and b<j) if k in ShapeValues(zones,a,b)]
    return  [[(False,i,j,k),(False,a,b,k)] for (i,j) in Coordinates(G) for (a,b) in cases_zones(zones,i,j) for k in ShapeValues(zones,i,j)]

def quasi_etat(G):
    return [[(True,i,j,G[i][j])] for (i,j) in Coordinates(G) if G[i][j] is not None]

def toutes_les_clauses(G,zones):
    return quasi_etat(G) + ValueConstraints(G,zones) + UnicityConstraints(G,zones) + VoisinsConstraints(G,zones) + ZonesConstraints(G,zones)

zones = ((0,0,1,1),
         (0,0,1,1),
         (2,2,1,3),
         (2,2,4,4),
         (2,4,4,4))

G = ((None,None,None,None),
    (None,None,None,5),
    (None,4,None,None),
    (None,None,None,None),
    (3,None,5,None))
"""G = (
    (   1, None,    5,    3, None,    4, None,    5, None),
    (None, None, None, None, None,    7, None, None,    4),
    (   5,    3, None,    7,    4, None, None,    3,    1),
    (None,    1,    5, None, None, None, None,    5, None),
    (   7, None, None, None, None, None, None,    7,    2),
    (   2, None,    1, None,    4,    6,    2,    6, None),
    (None,    5, None,    7, None,    3, None, None,    7),
    (None, None, None, None,    5, None,    2, None,    5),
    (   2, None,    4, None, None,    1, None,    4, None),
)

zones = (
    ( 0,  0,  0,  0,  0,  1,  1,  1,  2, ),
    ( 3,  4,  5,  5,  1,  1,  1,  1,  6, ),
    ( 3,  4,  4,  5,  5,  6,  6,  6,  6, ),
    ( 3,  3,  4,  4,  5,  6,  6,  7,  7, ),
    ( 8,  3,  3,  5,  5,  7,  7,  7,  9, ),
    ( 8,  8, 10, 10, 10,  7,  7,  9,  9, ),
    (11,  8,  8, 12, 10,  9,  9,  9,  9, ),
    (11,  8,  8, 12, 12, 12, 12, 13, 13, ),
    (11, 11, 11, 11, 12, 12, 13, 13, 13, ),
)"""

#print(ZonesConstraints(G,zones))

#print(Coordinates(G))

#for i in range(0,len(quasi_etat(G))):
#    print(quasi_etat(G)[i])

liste_association_case_var = [(i,j,k) for (i,j) in Coordinates(G) for k in ShapeValues(zones,i,j)]
#for i in range(len(liste_association_case_var)):
#    print(i+1,":", liste_association_case_var[i])

#print(ShapeValues(zones,1,0))
#print(Coordinates(G))
#print("\n")
#print(liste_association_case_var)
#print(len(quasi_etat(G)) + len(ValueConstraints(G,zones)) + len(UnicityConstraints(G,zones)) + len(VoisinsConstraints(G,zones)))
#for i in range(45,60):
#    print(ZonesConstraints(G,zones)[i])

def fichier_cnf(G,zones,liste_association_case_var):
    contraintes = toutes_les_clauses(G,zones)
    len_contraintes = len(contraintes)
    cases = quasi_etat(G)
    len_cases = len(cases)
    liste = []
    fichier = open('tectonic.cnf', 'w')
    fichier.write(f"p cnf {len(liste_association_case_var)} {len(contraintes)} ")
    print(len(liste_association_case_var), len(contraintes))
    for i in range(len_contraintes):
        ligne = ""
        for j in range(len(contraintes[i])):
            if contraintes[i][j][0] == True:
                ligne+=f"{liste_association_case_var.index((contraintes[i][j][1],contraintes[i][j][2],contraintes[i][j][3]))+1} "
            else:
                #print(i,j)
                ligne+=f"-{liste_association_case_var.index((contraintes[i][j][1],contraintes[i][j][2],contraintes[i][j][3]))+1} "
        ligne+="0 "
        fichier.writelines(ligne)
    fichier.close()

    system("minisat tectonic.cnf solutions.cnf")
    with open("solutions.cnf","r") as f:
        sol = f.read().split("\n")[1]
    sol_lignes = sol.split(" ")
    solution = []
    for i in range(len(sol_lignes)):
        if sol_lignes[i][0]!="-" and sol_lignes[i] != "0":
            solution.append(liste_association_case_var[int(sol_lignes[i])-1])
    return solution


#fichier_cnf(G,zones,liste_association_case_var)

def cnf_python(G,zones,liste_association_case_var):
    g = Glucose3()
    contraintes = toutes_les_clauses(G,zones)
    len_contraintes = len(contraintes)
    cases = quasi_etat(G)
    len_cases = len(cases)
    liste = []
    #print(contraintes[24:200])
    for i in range(len_contraintes):
        ligne = []
        for j in range(len(contraintes[i])):
            if contraintes[i][j][0] == True:
                ligne.append(liste_association_case_var.index((contraintes[i][j][1],contraintes[i][j][2],contraintes[i][j][3]))+1)
            else:
                ligne.append(-(liste_association_case_var.index((contraintes[i][j][1],contraintes[i][j][2],contraintes[i][j][3]))+1))
        g.add_clause(ligne)
    if g.solve():
        print("cette grille est solvable")
        print(f"la solution est {g.get_model()}")
        for index in g.get_model():
            if index>0:
                print(liste_association_case_var[index-1])
    else:
        print("cette grille n'est pas solvable")

cnf_python(G,zones,liste_association_case_var)
#print(UnicityConstraints(G))
#print(ValueConstraints(G,zones))
#print(Voisins(G,0,0))
#print(VoisinsConstraints(G,zones))
#print(coords_cases_zones(zones))
#print(compte_cases_zone(zones))
#liste = ZonesConstraints(G,zones)
#for a in liste:
#    print(a)
#print(toutes_les_clauses(G,zones)) 
#print(len(toutes_les_clauses(G,zones)))
#print(ValueConstraints(G,zones))
#print(quasi_etat(G))

#liste_infinie = toutes_les_clauses(G,zones)
#print(liste_infinie)
#for i in range(len(VoisinsConstraints(G,zones)),len(ZonesConstraints(G,zones))):
#    print(liste_infinie[i])