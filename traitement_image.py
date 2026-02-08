import numpy as np
import cv2
import matplotlib.pyplot as plt
from math import *
from statistics import mean,median
import random

path = "./Tectonic/avant_tatami.jpg"

def RGB2GRAY(image):
    gris = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    kernel = np.ones((7, 7), np.uint8)
    background = cv2.morphologyEx(gris, cv2.MORPH_DILATE, kernel)
    background = cv2.GaussianBlur(background, (21, 21), 0)

    diff = cv2.divide(gris, background, scale=255)
    return diff

def GRAY2BINARY(image_gris):
    thresh = cv2.adaptiveThreshold(image_gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    return thresh

def RGB2HSV(image):
    return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

def mask(imageHSV, lower, upper):
    kernel = np.ones((3,3))
    image_mask = cv2.inRange(imageHSV, lower, upper)
    return cv2.dilate(image_mask,kernel,iterations = 1)

def ftncontour(image_mask,palier, valeur_haute):
    _,tresh = cv2.threshold(image_mask, palier, valeur_haute,0)
    contours_image, _ = cv2.findContours(tresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours_image

def contours_pertinents(contours, aire_basse = 0, aire_haute = inf, grille = True):
    liste = []
    for contour in contours:
        if aire_haute > cv2.contourArea(contour) > aire_basse:
            if grille:
                peri = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
                if 4 <= len(approx) <= 6:
                    liste.append(contour)
            else:
                liste.append(contour)
    return liste

def coin_HG_HD_BD_BG(contour):
    rect = cv2.minAreaRect(contour)

    box = cv2.boxPoints(rect)
    box = np.array(box, dtype="float32")

    coins = np.zeros((4, 2), dtype="float32")

    s = box.sum(axis=1)
    coins[0] = box[np.argmin(s)]      # Top-Left (Somme min)
    coins[2] = box[np.argmax(s)]      # Bottom-Right (Somme max)

    diff = np.diff(box, axis=1)
    coins[1] = box[np.argmin(diff)]   # Top-Right (Diff min)
    coins[3] = box[np.argmax(diff)]   # Bottom-Left (Diff max)

    return coins


def Traitement_image(path):

    image = cv2.imread(path)
    dimensions = (len(image[0]),len(image))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) #passage en RGB
    image_gris = RGB2GRAY(image) #passage de RGB à niveaux de gris
    image_binaire = GRAY2BINARY(image_gris) #passage de niveaux de gris à binaire/noir et blanc (au sens strict du terme)

    image_HSV = RGB2HSV(image)
    lower_blue = np.array([80,80,70])
    
    upper_blue = np.array([130,255,255])
    mask_blue = mask(image_HSV, lower_blue, upper_blue) #traitement de l'image de manière à faire apparaître les bords des grilles
    contours_image = ftncontour(mask_blue, 127, 255) #on trouve TOUS les contours (donc pas juste ceux qui nous intéressent)

    liste_contours_pertinents_grilles = contours_pertinents(contours_image, aire_basse = 100000) #ici on ne garde que les contours qui nous intéressent : ceux des grilles qui ont une surface importante par rapport aux autres

    liste_contours_grille = liste_contours_pertinents_grilles[1::2] #normalement, dans la liste des contours, on le contour extérieur puis intérieur des grilles à la suite donc on ne garde que l'un des deux (on prie oui)

    coins_grilles = []
    for contour in liste_contours_grille:
        coins_grilles.append(coin_HG_HD_BD_BG(contour)) #on trouve le coin supérieur gauche et le coin inférieur droit de chaque grille

    liste_images_grilles = []
    liste_grilles_hsv = []
    liste_grilles_mask = []
    liste_grilles_contours = []
    for i in range(len(coins_grilles)):
        largeur_a = np.sqrt((coins_grilles[i][2][0] - coins_grilles[i][3][0])**2 + (coins_grilles[i][2][1] - coins_grilles[i][3][1])**2)
        largeur_b = np.sqrt((coins_grilles[i][0][0] - coins_grilles[i][1][0])**2 + (coins_grilles[i][0][1] - coins_grilles[i][1][1])**2)
        largeur_max = max(int(largeur_a),int(largeur_b))

        hauteur_a = np.sqrt((coins_grilles[i][0][0] - coins_grilles[i][3][0])**2 + (coins_grilles[i][0][1] - coins_grilles[i][3][1])**2)
        hauteur_b = np.sqrt((coins_grilles[i][2][0] - coins_grilles[i][1][0])**2 + (coins_grilles[i][2][1] - coins_grilles[i][1][1])**2)
        hauteur_max = max(int(hauteur_a),int(hauteur_b))

        destination = np.array([[0, 0],[largeur_max - 1, 0],[largeur_max - 1, hauteur_max - 1],[0, hauteur_max - 1]], dtype="float32")

        M = cv2.getPerspectiveTransform(coins_grilles[i], destination)
        grille_redressee = cv2.warpPerspective(image,M, (largeur_max,hauteur_max))

        """
        la partie ci-dessus trouve les quatre coins de la grille sur l'image, ce qui ne forme pas forcément un rectangle, ça dépend de comment la photo a été prise
        destination est un rectangle sur lequel on va projeter la grille, c'est à dire qu'on va essayer de redresser les coins pour que la grille devienne un rectangle
        """

        liste_images_grilles.append(grille_redressee)
        
        liste_grilles_hsv.append(RGB2HSV(liste_images_grilles[i]))
        lower_black = np.array([0,0,0])
        upper_black = np.array([130,130,130])
        liste_grilles_mask.append(mask(liste_grilles_hsv[i], lower_black, upper_black))

        liste_grilles_contours.append(ftncontour(liste_grilles_mask[i], 127, 255)) #on trouve les contours de chaque case

    liste_contours_pertinents_grilles = []
    for contour_grille in liste_grilles_contours:
        liste_contours_pertinents_grilles.append(contours_pertinents(contour_grille, aire_basse= 7000, aire_haute= 40000, grille = False)) #on isole les contours intéressants

    liste_min_max_cases = []
    for j in range(len(liste_contours_pertinents_grilles)):
        dimensions_grille = (len(liste_images_grilles[j][0]),len(liste_images_grilles[j]))
        liste = []
        for contour in liste_contours_pertinents_grilles[j]:
            liste.append(coin_HG_HD_BD_BG(contour))
        liste_min_max_cases.append(liste)

    liste_contour_cases = []
    for i in range(len(liste_contours_pertinents_grilles)):
        liste_cases_grille = []
        for j in range(len(liste_contours_pertinents_grilles[i])):
            liste_cases_grille.append(liste_images_grilles[i][int(liste_min_max_cases[i][j][0][1]):int(liste_min_max_cases[i][j][2][1]),int(liste_min_max_cases[i][j][0][0]):int(liste_min_max_cases[i][j][2][0])])
        liste_contour_cases.append(liste_cases_grille)

    liste_dimensions_grille = []
    grilles = []
    liste_centre_case = []
    liste_zones_grille = []
    liste_grilles_inversees = []
    for a in range(len(liste_contour_cases)):
        largeurs = []
        hauteurs = []

        for coords in liste_min_max_cases[a]:
            largeurs.append(coords[2][0] - coords[0][0])
            hauteurs.append(coords[2][1] - coords[0][1])
        
        largeur_case = max(largeurs)
        hauteur_case = max(hauteurs)

        h,w,_ = liste_images_grilles[a].shape
        nbr_col = int(w//largeur_case)
        nbr_row = int(h//hauteur_case)

        grille = []
        centre_cases = []
        for i in range(nbr_row):
            ligne = []
            ligne2 = []
            for j in range(nbr_col):
                ligne.append(0)
                ligne2.append(0)
            grille.append(ligne)
            centre_cases.append(ligne2)
        for i in range(len(liste_contour_cases[a])):
            centre_cases[int(abs(((liste_min_max_cases[a][i][0][1]+liste_min_max_cases[a][i][2][1])/2)//hauteur_case))][int(abs(((liste_min_max_cases[a][i][0][0]+liste_min_max_cases[a][i][2][0])/2)//largeur_case))] = [int((liste_min_max_cases[a][i][0][0]+liste_min_max_cases[a][i][2][0])/2),int((liste_min_max_cases[a][i][0][1]+liste_min_max_cases[a][i][2][1])/2)]
            grille[int(abs(((liste_min_max_cases[a][i][0][1]+liste_min_max_cases[a][i][2][1])/2)//hauteur_case))][int(abs(((liste_min_max_cases[a][i][0][0]+liste_min_max_cases[a][i][2][0])/2)//largeur_case))] = liste_contour_cases[a][i]
        liste_dimensions_grille.append([nbr_row,nbr_col])
        grilles.append(grille)
        liste_centre_case.append(centre_cases)

        kernel = np.ones((9,9),np.uint8)
        grille_erodee = cv2.erode(liste_grilles_mask[a],kernel,iterations=1)
        grille_ouverte = cv2.dilate(grille_erodee,kernel,iterations=3)
        for i in range(len(liste_contour_cases[a])):
            cv2.circle(grille_ouverte,(int((liste_min_max_cases[a][i][0][0]+liste_min_max_cases[a][i][2][0])/2),int((liste_min_max_cases[a][i][0][1]+liste_min_max_cases[a][i][2][1])/2)),int(0.33*min(hauteur_case,largeur_case)), 0, -1)
        grille_inversee = cv2.bitwise_not(grille_ouverte)
        liste_grilles_inversees.append(grille_inversee)
        num_labels, labels = cv2.connectedComponents(grille_inversee)

        zones = np.zeros(liste_dimensions_grille[a],dtype = int)

        for r in range(liste_dimensions_grille[a][0]):
            for c in range(liste_dimensions_grille[a][1]):
                x = liste_centre_case[a][r][c][0]
                y = liste_centre_case[a][r][c][1]

                zone_id = labels[y,x]
                zones[r,c] = zone_id
        u, inv = np.unique(zones, return_inverse=True)
        zones = inv.reshape(zones.shape)
        liste_zones_grille.append(zones)

    images_cases = grilles[0]         # Liste 2D des images rognées
    zones_matrice = liste_zones_grille[0] # Matrice numpy des ID de zones
    

    
    return images_cases, zones_matrice

    
"""
les données qui nous intéressent pour la partie IA sont dans les listes "grilles" et "liste_zones_grilles".
pour utiliser le code l'idéal est de n'avoir qu'une seule grille sur l'image et à peu près la même luminosité sur toute l'image
les listes qui nous intéressent sont de la forme suivante : ce sont des listes de listes (il y a encore des listes après mais j'y viens), les premières sous-listes, celles auxquelles on accède par grilles[i], nous donnent des informations pour une seule grille de l'image
c'est à dire que s'il y a une seule grille sur l'image, "grilles" et "liste_zones_grilles" seront de longueur 1.
ensuite, grilles[0] (même chose pour la liste des zones) est un tableau de la forme [[]*nombre colonnes]*nombre lignes, ainsi grilles[0][2][1] nous donne une information sur la case à la troisième ligne et deuxième colonne
dans grilles[0][i][j], on trouve l'image de la case, normalement rognée correctement
dans liste_zones_grilles[0][i][j], on trouve l'identifiant de la zone à laquelle appartient la case, ce qui (je crois) correspond bien à la forme de donnée que l'on avait utilisé pour les solveurs.
si c'est toujours incompréhensible demandez moi sur insta ou autre.
"""