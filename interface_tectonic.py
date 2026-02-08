"""
Code principal du solveur il sert globalement de Main x IHM je n'ai pas eu le temps de vraiment tout séparer dans un main propre

il contient le cœur de l'application, il relie l'ensemble des modules; 
IA, traitement d'image, solveurs SAT et logiques

Fonctionnalités principales :
- IHM: Gestion de la boucle de jeu, affichage de la grille, 
   des boutons et gestion des événements souris/clavier.
- Fait le lien entre l'utilisateur et les modules techniques :
   - Génération procédurale de niveaux (validés par solveur SAT) (à encore améliorer)
   - Importation de grilles via analyse d'image et reconnaissance de chiffres
   - Résolution assistée coup par coup (solveur 'fait maison') ou résolution complète avec MiniSAT
"""


import pygame
import sys
import random
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
from traitement_image import Traitement_image
from IA_reconnaissance_Chiffres import ChiffreReconnaissance
from Solver_etape_par_etapes import Tectonic, calculer_solution_complete
from TectonicSAT import resoudre_sat
import random


'''-------- Configuration de l'écran des couleurs des boutons, du bg de la grille... ----------'''
HEIGHT = 600
WIDTH = 800
CELL_MAX = 55
OFFSET_Y = 120
FPS = 60

BG = (240, 245, 250)        #couleur du fond
CELL_BG = (255, 255, 255)   #couleur de fond d'une case
GRID_THIN = (200, 210, 230) #couleur trait fin
GRID_THICK = (60, 70, 90)   #couleur trait épais plus sombre
TEXT = (40, 50, 70)         #couleur du texte
SELECT = (180, 230, 255)    #couleur case selectionnée
SUCCESS = (210, 245, 210)   #couleur case validée
ERROR = (255, 200, 200)     #couleur case fausse (bouuh)
LOCKED = (120, 130, 150)    #couleur case locked (validée permanently)
BTN_VERIF = (100, 150, 255)  # couleur bouton de vérify pas activé
BTN_NEUTRAL = (120, 125, 135)    #couleur grise pour "indice" et "effacer"
BTN_GGRID = (255, 160, 100)   #couleur bouton génerer grille
BTN_LOAD = (251, 209, 130)     #couleur bouton importer
BTN_ACTIVE = (100, 220, 150)   #couleur bouton verify activé
BTN_CLEAR = (165, 215, 160)    #couleur bouton clear
BTN_NOTES = (250, 105, 103)    #couleur bouton notes


'''-------- Classe Bouton qui gère les interactions avec les boutons ----------'''

class Button:
    def __init__(self, rect, text, callback, color):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        txt = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

'''------- Classe TectonicGame qui gère tout le coeur du jeu ; interactions, affichage, updates.. ----------'''

class TectonicGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE) #pour pouvoir fullscreen
        pygame.display.set_caption("ANONE SOLVER") #nom de la fenêtre
        self.clock = pygame.time.Clock()    #initalise la tick clock

        #on stock les dimensions actuelles de la fenêtre pour pouvoir les modifier
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()

        #polices d'écriture
        self.font_ui = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_grid = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 48, bold=True) #titre plus gros
        self.font_small = pygame.font.SysFont("Arial", 16)  

        #etat du jeu on commence au menu puis on basculera sur playing
        self.state = "MENU"
        
        #initialisation des boutons du menu principal
        self.init_menu_buttons()
        
        #on initialise les variables du jeu mais on ne charge rien
        self.grid = []
        self.buttons = [] 
        self.message = "Bienvenue ! Choisissez une option."
        
        self.selected = None       # Case sélectionnée
        self.verify = False        # Vérification active
        self.note_mode = False     # Mode notes actif 
        self.solution = None       # La solution complète
        self.locked = []           # Grille des cases verrouillées
        self.notes = []            # Grille des notes

    #si le joueur génere une grille depuis le menu
    def start_generation(self):
        self.generate_level()
        #on passe en mode jeu
        if self.grid:
            self.state = "PLAYING"

    #si le joueur importe depuis le menu
    def start_import(self):
        res = self.load_image()
        #on passe en mode jeu
        if self.grid:
            self.state = "PLAYING"

    

    def load_puzzle(self, puzzle):
        self.zones = puzzle["zones"]            #on récupère les zones dans le dictionnaire
        self.solution = puzzle["solution"]      #ainsi que les solutions
        self.rows = len(self.zones)
        self.cols = len(self.zones[0])
        
        self.grid = [[0]*self.cols for _ in range(self.rows)]       #on crée la grille vide
        self.locked = [[False]*self.cols for _ in range(self.rows)]
        self.notes = [[set() for _ in range(self.cols)] for _ in range(self.rows)]

        for r, c, v in puzzle["givens"]:            #on remplit la grille des chiffres qu'on connait déja
            self.grid[r][c] = v
            self.locked[r][c] = True
            
        self.solver = Tectonic(self.grid, self.zones) # Initialisation du solveur pas-à-pas
        self.cell = min(CELL_MAX, (self.width - 200)//self.cols)     #on ajuste la taille des cellules en fonction de la taille de la grille

    def compute_layout(self):       #pour bien afficher les grilles pas sur les boutons mais quand même sur l'interface ect..
        #on définit une largeur pour le panneau de boutons a droite
        BUTTON_AREA = 220 
        available_width = self.width - BUTTON_AREA
        
        max_w_cell = (available_width - 40) // self.cols  # -40 pour garder une petite marge
        max_h_cell = (self.height - OFFSET_Y - 40) // self.rows
        
        #on prend même la plus petite valeur pour être sûr que tout rentre
        self.cell = min(CELL_MAX, max_w_cell, max_h_cell)
        
        #on calcul la largeur réelle de la grille
        self.grid_width = self.cols * self.cell
        
        #on centre la grille la ou il y a de la place
        self.offset_x = (available_width - self.grid_width) // 2

    def init_buttons(self):
        x = self.offset_x + self.grid_width + 40
        y = OFFSET_Y + 40
        w, h = 150, 45
        
        self.btn_load = Button((x, y, w, h), "Importer Grille", self.load_image, BTN_LOAD)       #init du bouton importer pour bah importer une grille
        self.btn_verify = Button((x, y+60, w, 55), "Vérifier", self.toggle_verify, BTN_VERIF)        #init du bouton vérifier pour vérifier les réponses données jusqu'à présent
        self.btn_notes = Button((x, y+130, w, h), "Notes", self.notes_mode, BTN_NOTES)           #init du switch pour activer/désactiver le mode notes
        self.btn_step = Button((x, y+190, w, h), "Indice", self.solve_step, BTN_NEUTRAL)            #init du bouton Etape pour donner la réponse de l'étape logique suivante
        self.btn_clear = Button((x, y+250, w, h), "Effacer", self.clear_all, BTN_NEUTRAL)            #init du bouton pour effacer toutes les valeurs non-lockées
        self.btn_solve = Button((x, y+310, w, h), "Résoudre", self.solve_all, BTN_CLEAR)           #init du bouton solve pour résoudre totalement la grille
        self.btn_gen = Button((x, y - 60, w, h), "Générer Grille", self.generate_level, BTN_GGRID)          #init du bouton pour générer une grille aléatoire
        
        self.buttons = [self.btn_load, self.btn_verify, self.btn_notes, self.btn_step, self.btn_clear, self.btn_solve,self.btn_gen]  #qu'on met tous dans une liste pour les gérer plus facilement

    #même fonctionnement
    def init_menu_buttons(self):
        #calculs pour centrer les boutons
        btn_w, btn_h = 240, 60
        center_x = (self.width - btn_w) // 2
        center_y = (self.height // 2) - 50
        
        #bouton1 ; générer une grille
        self.btn_menu_gen = Button(
            (center_x, center_y, btn_w, btn_h), 
            "Générer une Grille", 
            self.start_generation, 
            BTN_GGRID
        )
        
        #bouton2 ; importer
        self.btn_menu_imp = Button(
            (center_x, center_y + 80, btn_w, btn_h), 
            "Importer une Image", 
            self.start_import,
            BTN_LOAD
        )
        
        self.buttons_menu = [self.btn_menu_gen, self.btn_menu_imp] #on met dans une liste différente car on différencie les deux etats de jeux



    def open_image(self):
        root = tk.Tk()
        root.withdraw()
        return filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])

    def load_image(self):
        path = self.open_image()
        if not path: return
        
        self.message = "Analyse image et résolution avec minisat..."
        self.draw()
        pygame.event.pump() #garde la fenêtre active pendant le calcul
        
        try:
            #traitement d'image
            images_cases, zones_matrice = Traitement_image(path)
            
            #gestion chemin modèle
            model_path = "./Tectonic/model.ckpt"
            
            #conversion numpy -> list
            if isinstance(zones_matrice, np.ndarray):
                zones_liste = zones_matrice.tolist()
            else:
                zones_liste = zones_matrice
                
            #reconnaissance chiffres
            ia = ChiffreReconnaissance(model_path)
            grille_detectee = ia.predict_grid(images_cases)
        
            #nettoyage et préparation des données
            rows = len(grille_detectee)
            cols = len(grille_detectee[0])
            grille_propre = []
            givens = []
            
            for r in range(rows):
                row_l = []
                for c in range(cols):
                    val = grille_detectee[r][c]
                    if val is None: val = 0
                    val = int(val)
                    row_l.append(val)
                    if val > 0:
                        givens.append((r, c, val))
                grille_propre.append(row_l)

            #résolution avec minisat
            solution_trouvee = resoudre_sat(grille_propre, zones_liste)
            
            if solution_trouvee:
                txt_status = "Grille chargée et résolue !"
            else:
                txt_status = "Grille chargée (Sans solution)."

            # réation du puzzle avec la solution déjà pré-calculée
            new_puzzle = {
                "zones": zones_liste,
                "solution": solution_trouvee,
                "givens": givens
            }
            
            self.load_puzzle(new_puzzle)
            self.compute_layout()
            self.message = txt_status
            
        except Exception as e:
            print(f"Erreur import: {e}")
            self.message = "Erreur lors de l'import (voir console)"


    def create_random_zones(self, rows, cols):
        """
        Pour générer une nouvelle grille, il faut créer des zones a géométrie variable sinon c'est moins fun. On utilise ici un algorithme de remplissage par contagion
        """
        zones = [[-1] * cols for _ in range(rows)]
        zone_id = 0
        
        for r in range(rows):
            for c in range(cols):
                #si la case n'a pas encore de zone
                if zones[r][c] == -1:
                    #on décide de la taille cible de cette nouvelle zone
                    target_size = random.randint(1, 5)
                    
                    #on initialise la zone avec la case actuelle
                    current_zone = [(r, c)]
                    zones[r][c] = zone_id
                    
                    #on essaie de faire grandir la zone
                    attempts = 0
                    while len(current_zone) < target_size and attempts < 10:
                        #on prend une case au hasard déjà dans la zone pour s'étendre depuis elle
                        curr_r, curr_c = random.choice(current_zone)
                        
                        #on cherche les voisins libres
                        voisins = []
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < rows and 0 <= nc < cols and zones[nr][nc] == -1:
                                voisins.append((nr, nc))
                        
                        if voisins:
                            #on choisit un voisin libre et on l'ajoute
                            next_r, next_c = random.choice(voisins)
                            zones[next_r][next_c] = zone_id
                            current_zone.append((next_r, next_c))
                        else:
                            #si on est coincé, on compte un échec
                            attempts += 1
                    
                    #zone finie, on passe à l'ID suivant
                    zone_id += 1
                    
        return zones
        #(c'était atroce)



    """
    Pour améliorer la génération on pourait faire en sorte de générer en continu des grilles et de stocker chaque grille satisfiable
    et ensuite repiocher, pour que le temps passé a rechercher la grille soit un temps ou le joueur joue et n'attends pas
    pour une experience client sans faille
    """

    def generate_level(self):
        attempt = 0
        self.draw()
        
        #on définit les dimensions de la grille (entre 5 et 8) on peut monter plus mais le temps de génération explosr
        target_rows = random.randint(5, 8)
        target_cols = random.randint(5, 8)
        
        #limite de sécurité pour éviter le crash infini lol
        max_total_attempts = 300000 
        
        while attempt < max_total_attempts:
            attempt += 1
            
            self.message = f"Génération en cours (cela peut prendre un moment)... {attempt} grilles insolvables générées."
            self.draw()     
            pygame.display.flip()         #pour que l'interface s'actualise et qu'on voit en direct fin à 60fps le compteur
            
            #garde la fenêtre active
            pygame.event.pump() 
            
            #on crée les zones 
            new_zones = self.create_random_zones(target_rows, target_cols)
            
            #on place chiffres dans la grille 
            grille_vide = [[0]*target_cols for _ in range(target_rows)]
            seed = 0            #'seed' pour faire genre génération procédurale avec perlin noise la classe (non)
            
            for bidule in range(seed):
                #on essaie de placer une seed valide
                for truc in range(10): # 10 essais pour y arriver
                    r, c = random.randint(0, target_rows-1), random.randint(0, target_cols-1)
                    
                    #si la case est déjà prise, on recommence
                    if grille_vide[r][c] != 0: continue

                    zone_id = new_zones[r][c]
                    #on calcule la taille de zone pour pas mettre un 5 dans une zone de 2
                    taille_zone = sum(row.count(zone_id) for row in new_zones)
                    val = random.randint(1, min(taille_zone, 9))
                    
                    #on vérifie les voisins pour aider minisat a pas exploser
                    conflit = False
                    for dr in range(-1, 1):
                        for dc in range(-1, 1):
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < target_rows and 0 <= nc < target_cols:
                                if grille_vide[nr][nc] == val:
                                    conflit = True
                    
                    if not conflit:
                        grille_vide[r][c] = val
                        break

            #on appelle minisat 
            print(f"Essai {attempt}...", end="\r") 
            sol_complete = resoudre_sat(grille_vide, new_zones)
            
            if sol_complete:
                print(f"\n grille valide générée après {attempt} essais !")
                self.rows = target_rows
                self.cols = target_cols
                self.zones = new_zones
                self.solution = sol_complete

                #on met a jour l'affichage taille des cases ect..

                self.cell = min(CELL_MAX, (self.width - 200)//self.cols)
                if self.rows * self.cell > self.height - OFFSET_Y - 50:
                    self.cell = (self.height - OFFSET_Y - 50) // self.rows
                self.compute_layout()
                self.init_buttons() #repositionne les boutons si la grille bouge

                #on reset tout
                self.grid = [[0]*self.cols for _ in range(self.rows)]
                self.locked = [[False]*self.cols for _ in range(self.rows)]
                self.notes = [[set() for _ in range(self.cols)] for _ in range(self.rows)]
                
                #on donne les chiffres de départ
                total_cases = self.rows * self.cols
                nb_indices = int(total_cases * 0.10) # 5% pour le challenge
                
                indices_places = 0
                max_loops = nb_indices * 10
                loops = 0
                while indices_places < nb_indices and loops < max_loops:
                    loops += 1
                    r, c = random.randint(0, self.rows-1), random.randint(0, self.cols-1)
                    if self.grid[r][c] == 0:
                        self.grid[r][c] = self.solution[r][c]
                        self.locked[r][c] = True
                        indices_places += 1
                
                #on initialise le solveur step by step
                self.solver = Tectonic(self.grid, self.zones)
                
                self.message = f"Généré : {self.cols}x{self.rows} après {attempt} grilles générées"
                self.verify = False
                return

    #active ou désactive la vérification si le bouton est pressé et lock un chiffre s'il a été vérifié "bon"
    def toggle_verify(self):
        #si on n'a pas de solution de référence
        if not self.solution:
            self.message = "Calcul de la solution de référence..."
            self.draw()
            pygame.event.pump()
            
            #on solve avec minisat
            sol = resoudre_sat(self.grid, self.zones)
            if sol:
                self.solution = sol
                self.message = "Solution trouvée. Vérification active."
            else:
                self.message = "Impossible de résoudre la grille"
                return

        #bascule l'état de la vérification
        self.verify = not self.verify
        
        #mise à jour visuelle du bouton
        self.btn_verify.text = "ACTIVÉ" if self.verify else "VÉRIFIER"
        self.btn_verify.color = BTN_ACTIVE if self.verify else BTN_VERIF

        if self.btn_verify.text == "ACTIVÉ":
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid[r][c] == self.solution[r][c]:
                        self.locked[r][c] = True


        
        #petit message a l'attention de notre très cher utilisateur
        if self.verify:
            self.message = "Vérification active : Vert = Bon, Rouge = Faux"
        else:
            self.message = "Mode vérification désactivé."

    def notes_mode(self):
        self.note_mode = not self.note_mode
        self.btn_notes.color = BTN_ACTIVE if self.note_mode else BTN_NOTES

    def solve_step(self):       #résouds l'étape d'après si le bouton est pressé
        #utilise le solveur logique pas à pas
        self.solver.carte_nb = [row[:] for row in self.grid]
        self.solver.possi_init() # recalcule les possibilités actuelles
        
        move = self.solver.find_move()
        if move:
            r, c, v = move
            self.grid[r][c] = v
            self.locked[r][c] = True #on lock l'indice
            self.message = f"Indice placé en ({r},{c}) -> {v}"
        else:
            self.message = "Pas de coup logique simple trouvé."

    def solve_all(self):
        #si une solution a été stockée
        if self.solution:
            for r in range(self.rows):
                for c in range(self.cols):
                    self.grid[r][c] = self.solution[r][c]
            self.message = "Affichage de la solution !"
            self.verify = True
        else:                                           #on calcule en urgence (backup)
            self.message = "Calcul de la solution"
            self.draw()
            pygame.event.pump()
        
            sol = resoudre_sat(self.grid, self.zones)
            if sol:
                self.grid = sol
                self.solution = sol
                self.message = "Résolu !"
                self.verify = True
            else:
                self.message = "Impossible à résoudre."
    

    def clear_all(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.locked[r][c]:
                    self.grid[r][c] = 0
                    self.notes[r][c].clear()
        self.message = "Grille nettoyée."

    def run(self):      #boule infinie qui fait tourner le jeu
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):            #gère les interactions HM 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:       #quitter en appuyant sur la croix
                pygame.quit()
                sys.exit()

            elif event.type == pygame.VIDEORESIZE:          #fullscreen avec les carrés la
                self.width, self.height = event.w, event.h
                #on met à jour l'écran
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                
                #on recalcule toutes les positions
                if self.state == "MENU":
                    self.init_menu_buttons() #recentre les boutons du menu
                elif self.state == "PLAYING" or self.state == "LOADING":
                    self.compute_layout()    #recalcule la taille des cases ect
                    self.init_buttons()      #replace la barre latérale à droite

            #on différencie le mode menu du mode playing
            if self.state == "MENU":
                for btn in self.buttons_menu:
                    btn.handle_event(event)

            elif self.state == "PLAYING":
                # Boutons du jeu (ceux à droite)
                for btn in self.buttons: # self.buttons est créé dans init_buttons (le vieux)
                    btn.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:       #selectionne un case si on clique dessus
                        self.select_cell(event.pos)

                if event.type == pygame.KEYDOWN and self.selected:      #permet de saisir ou supprimer un chiffre si rentré dans une case ou 
                    r, c = self.selected
                    if not self.locked[r][c]:
                        if event.unicode.isdigit() and event.unicode != '0':
                            val = int(event.unicode)
                            if self.note_mode:
                                if val in self.notes[r][c]: self.notes[r][c].remove(val)
                                else: self.notes[r][c].add(val)
                            else:
                                self.grid[r][c] = val
                                self.notes[r][c].clear()
                        elif event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                            self.grid[r][c] = 0
                            self.notes[r][c].clear()

    def select_cell(self, pos):     #vérifie si le clic est dans la grille, et si oui, selectionne la case correspondant aux coordonées du clic
        x, y = pos
        if self.offset_x <= x < self.offset_x + self.grid_width and OFFSET_Y <= y < OFFSET_Y + self.rows * self.cell:
            c = int((x - self.offset_x) // self.cell)
            r = int((y - OFFSET_Y) // self.cell)
            self.selected = (r, c)
        else:
            self.selected = None

    #mets a jour l'écran en appelant toutes les fonctions
    def draw(self):
        self.screen.fill(BG)

        #si on est dans le menu 
        if self.state == "MENU":
            
            #on écris le titre centré
            title = self.font_title.render("ANONE SOLVER", True, TEXT)
            rect_title = title.get_rect(center=(self.width//2, self.height//2 - 150))
            self.screen.blit(title, rect_title)
            
            #un sous titre
            sub = self.font_ui.render("Choisissez quoi faire !", True, GRID_THICK)
            rect_sub = sub.get_rect(center=(self.width//2, self.height//2 - 100))
            self.screen.blit(sub, rect_sub)
            
            #les boutons du menu
            for btn in self.buttons_menu:
                btn.draw(self.screen, self.font_ui)
        
        elif self.state == "PLAYING":
            # --- DESSIN DU JEU (Ton code actuel) ---
            
            # Titre en haut à gauche
            title = self.font_grid.render("ANONE SOLVER", True, TEXT) # Font un peu plus petite
            self.screen.blit(title, (self.offset_x, 40))
        
            #déssine les cases, zones ect..
            for r in range(self.rows):
                for c in range(self.cols):
                    rect = pygame.Rect(self.offset_x + c*self.cell, OFFSET_Y + r*self.cell, self.cell, self.cell)
                    
                    #gère quand l'état d'une cell a été modifié, vérif on/ case selectionnée ou vérouillée
                    #fond case
                    color = CELL_BG
                    if self.verify and self.solution:
                        if self.grid[r][c] != 0:
                            color = SUCCESS if self.grid[r][c] == self.solution[r][c] else ERROR
                    elif self.locked[r][c]:
                        color = LOCKED
                    
                    pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=4)
                    
                    #selection
                    if self.selected == (r, c):
                        pygame.draw.rect(self.screen, SELECT, rect.inflate(-2, -2), 3, border_radius=4)

                    #valeur
                    val = self.grid[r][c]
                    if val > 0:
                        txt = self.font_grid.render(str(val), True, TEXT)
                        self.screen.blit(txt, txt.get_rect(center=rect.center))
                    
                    #notes
                    if val == 0 and self.notes[r][c]:
                        # Affichage simplifié des notes
                        note_str = "".join(str(n) for n in sorted(self.notes[r][c]))
                        txt = self.font_small.render(note_str, True, (100, 100, 100))
                        self.screen.blit(txt, (rect.x + 2, rect.y + 2))

            #traits de zones
            for r in range(self.rows):
                for c in range(self.cols):
                    x = self.offset_x + c * self.cell
                    y = OFFSET_Y + r * self.cell
                    
                    #lignes épaisses pour zones 
                    
                    if c < self.cols - 1 and self.zones[r][c] != self.zones[r][c+1]:
                        pygame.draw.line(self.screen, GRID_THICK, (x+self.cell, y), (x+self.cell, y+self.cell), 3)
                    
                    if r < self.rows - 1 and self.zones[r][c] != self.zones[r+1][c]:
                        pygame.draw.line(self.screen, GRID_THICK, (x, y+self.cell), (x+self.cell, y+self.cell), 3)
                    
            #bordure extérieure
            pygame.draw.rect(self.screen, GRID_THICK, (self.offset_x, OFFSET_Y, self.grid_width, self.rows*self.cell), 3)

            #petit coup d'iu
            for btn in self.buttons:
                btn.draw(self.screen, self.font_ui)
            
        #mini barre de status en bas de l'écran pour informer le joueur des events en cours 
        msg = self.font_small.render(self.message, True, TEXT)
        self.screen.blit(msg, (20, self.height - 30))

        pygame.display.flip()

'''Et ENFIN, on lance le run de la classe TectonicGame'''

if __name__ == "__main__":
    TectonicGame().run()