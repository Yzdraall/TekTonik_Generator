"""
Reconnaissance de Chiffres par CNN 

Ce fichier implémente le réseau de neurones convolutif pour la reconnaissance de chiffres , spécifiquement optimisée pour
identifier les chiffres d'une grille de tektonik à partir d'images segmentées.

Fonctionnalités principales :
- Architecture du Modèle: définition du CNN avec donc couches de convolution,
   batch normalization, et Global Average Pooling, conçu pour être léger
- traitement : binarisation, redimensionnement (28x28), et centrage 
   des images des cases pour normaliser les entrées avant prédiction.
- Génération de Données Synthétiques (PrintedMNIST) : Création dynamique d'un dataset
   d'entraînement simulant des chiffres imprimés (polices variées, bruit, rotation) donc bien dans la classe MNIST et non dans l'entraînement
Entraînement et Prédiction : Fonctions pour entraîner le modèle train/test
"""


import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data 
from torchvision import datasets, transforms
import matplotlib.pyplot as plt
import cv2
import numpy as np
from skimage.segmentation import clear_border
from scipy import ndimage
from traitement_image import Traitement_image



path = "./Tectonic/avant_tatami.jpg"  # image
path_modele = "./Tectonic/model.ckpt" # poids du modèle ia

class GlobalAveragePooling(nn.Module):
    def __init__(self, in_channels):
        self.s = in_channels
        super(GlobalAveragePooling, self).__init__()

    def forward(self, x):
        shape = x.shape
        x = x.reshape(x.shape[0], x.shape[1], 1, x.shape[2] * x.shape[3])
        x = x.mean(dim = 3, keepdim = True)
        return x

    def __repr__(self):
        return 'GlobalAveragePooling({}, {})'.format(self.s, self.s)

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 30, 3, stride=2)
        self.bn1 = nn.BatchNorm2d(30)
        self.conv2 = nn.Conv2d(30, 30, 3, stride=1)
        self.bn2 = nn.BatchNorm2d(30)
        self.conv3 = nn.Conv2d(30, 30, 3, stride=1)
        self.bn3 = nn.BatchNorm2d(30)
        self.gap = GlobalAveragePooling(30)
        self.conv4 = nn.Conv2d(30, 30, 1, stride=1)
        self.bn4 = nn.BatchNorm2d(30)
        self.conv5 = nn.Conv2d(30, 10, 1, stride=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)

        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)

        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)

        x = self.gap(x)

        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x)

        x = self.conv5(x)
        x = F.relu(x)

        x = x.view(-1, 10)
        return F.log_softmax(x, dim=1)



def train( model, device, train_loader, optimizer,loss_function):
    train_loss = 0
    correct = 0
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()       #on remet à 0 les paramètres du gradient
        output = model(data)        #on passe l'image dans le modele
        loss = loss_function(output, target) #on calcul la function de coût (loss)
        train_loss += loss_function(output, target, reduction="sum").item() #on calcul la loss pour toute l'epoch

        pred = output.argmax(dim=1, keepdim=True)
        correct += pred.eq(target.view_as(pred)).sum().item()

        loss.backward()  #retropropagation du gradient 
        optimizer.step() #descente du gradient 

    train_loss /= len(train_loader.dataset)

    return train_loss, float(correct) / len(train_loader.dataset)


#fonction de validation

def test(model, device, test_loader, loss_function):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += loss_function(output, target, reduction="sum").item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)

    return test_loss, float(correct) / len(test_loader.dataset)


def centrage(im):
    com = ndimage.measurements.center_of_mass(im)




    x_trans = int(im.shape[0]//2-com[0])
    y_trans = int(im.shape[1]//2-com[1])



    if x_trans > 0:
        im2 = np.pad(im, ((x_trans, 0), (0, 0)), mode='constant')
        im2 = im2[:im.shape[0]-x_trans, :]
    else:
        im2 = np.pad(im, ((0, -x_trans), (0, 0)), mode='constant')
        im2 = im2[-x_trans:, :]

    if y_trans > 0:
        im3 = np.pad(im2, ((0, 0), (y_trans, 0)), mode='constant')
        im3 = im3[:, :im.shape[0]-y_trans]

    else:
        im3 = np.pad(im2, ((0, 0), (0, -y_trans)), mode='constant')
        im3 = im3[:, -y_trans:]

    return im3




#--------------Partie génération d'images et entrainement sur données atrifivielles---------------------

import torch

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import glob
import random

class PrintedMNIST(torch.utils.data.Dataset):
    """Génère des chiffres qui ressemblent à ceux d'un Sudoku scanné"""

    def __init__(self, N, random_state, transform=None):
        self.N = N
        self.transform = transform
        
        # Chemins des polices
        fonts_folder = "./Tectonic/fonts"
        self.fonts = glob.glob(fonts_folder + "/*.ttf")
        if not self.fonts:
            print("ATTENTION: Aucune police trouvée ! Utilisation de la police par défaut (risque d'erreur).")
        
        random.seed(random_state)

    def __len__(self):
        return self.N

    def __getitem__(self, idx):

        #on créée l'image
        img = Image.new("L", (40, 40), color=255) # Plus grand que 28 pour permettre rotation/crop
        draw = ImageDraw.Draw(img)
        
        target = random.randint(0, 9)


        if target > 0:
            font_path = random.choice(self.fonts) if self.fonts else None
            #taille variable 
            font_size = random.randint(22, 28)
            
            try:
                font = ImageFont.truetype(font_path, font_size)
            except:
                font = ImageFont.load_default()

           
            text = str(target)
            
            #centrage approximatif
            bbox = draw.textbbox((0, 0), text, font=font)
            w_text, h_text = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (40 - w_text) / 2 + random.randint(-4, 4)
            y = (40 - h_text) / 2 + random.randint(-4, 4)
            
            draw.text((x, y), text, fill=0, font=font)


        else:
            #on ne dessine pas de chiffre case vide
            pass
        
        
        
        angle = random.randint(-15, 15)
        img = img.rotate(angle, fillcolor=255, resample=Image.BILINEAR)


        if random.random() < 0.3:
            d_line = ImageDraw.Draw(img)
            #ligne verticale aléatoire sur un bord
            d_line.line([(0, random.randint(0, 40)), (0, random.randint(0, 40))], fill=0, width=random.randint(1, 3))


        np_img = np.array(img)
        noise = np.random.randint(0, 50, np_img.shape, dtype='uint8')
        
        
        np_img = np.where(np_img > 200, np_img - noise, np_img)
        
        
        np_img = 255 - np_img
        
        
        final_img = Image.fromarray(np_img)
        final_img = final_img.resize((28, 28), resample=Image.BILINEAR)
    
    
        final_np = np.array(final_img)
        
        if self.transform:
            final_np = self.transform(final_np)

        return final_np, target
    


class ChiffreReconnaissance:
    def __init__(self, path_modele):
        self.device = torch.device("cpu")
        self.model = Net().to(self.device)
        #chargement des poids 
        
        self.model.load_state_dict(torch.load(path_modele, map_location=self.device))
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            lambda x: x > 0,
            lambda x: x.float(),
        ])

    def predict_grid(self, image_cases):
        rows = len(image_cases)
        cols = len(image_cases[0])
        resultats = [[0]*cols for _ in range(rows)]
        
        for r in range(rows):
            for c in range(cols):
                img = image_cases[r][c]
                
                if img is None or img.size == 0:
                    resultats[r][c] = 0
                    continue

                
                if len(img.shape) == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                
                
                _, img_thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                
                contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if not contours:
                    resultats[r][c] = 0
                    continue #rien du tout dans la case

                #on prend uniquement le plus gros contour, pour éviter d'essayer de reconnaitre un trait random
                c_max = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(c_max) # x,y,largeur,hauteur
                
                img_h, img_w = img_thresh.shape
                
                
                if cv2.contourArea(c_max) < 30: 
                    resultats[r][c] = 0
                    continue


                #si la hauteur fait moins de 25% de la case on estime que c'est du bruit un truc dans le genre
                if h < img_h * 0.25:
                    resultats[r][c] = 0
                    continue

                if x <= 1 or y <= 1 or (x+w) >= img_w-1 or (y+h) >= img_h-1:
                    resultats[r][c] = 0
                    continue


                #on redimensionne en 28x28
                img_resized = cv2.resize(img_thresh, (28, 28), interpolation=cv2.INTER_AREA)
                
                #on centre proprement
                img_final = centrage(img_resized)
                
                #on fait notre prédiction
                tensor = self.transform(img_final.astype(np.float32) / 255.0)
                tensor = tensor.unsqueeze(0)
                
                with torch.no_grad():
                    output = self.model(tensor.to(self.device))
                    
                    probs = torch.exp(output)
                    prob_max = probs.max().item()
                    pred = output.argmax(dim=1).item()
                    

                if prob_max < 0.5:
                    resultats[r][c] = 0
                else:
                    resultats[r][c] = pred
                
        return resultats







#------ TRAIN EVENTUEL NE PAS TOUCHER ! (ne se lance que si c'est ce programme qu'on lance direct, pour relancer l'entrainement mettez 'oui' a l'input-----

if __name__ == "__main__":

    image_cases, zones = Traitement_image(path)

    preds_import = ChiffreReconnaissance(path_modele)
    print(f"Predictions ; {preds_import.predict_grid(image_cases)}") 
    print(zones) 

    plt.figure()
    for i in range(len(image_cases)):
        for j in range(len(image_cases[0])):
            plt.subplot(len(image_cases),len(image_cases[0]),i*len(image_cases[0]) + j+1)
            plt.imshow(image_cases[i][j])
    '''print(f"zones ;{zones_matrice} image_cases ; {image_cases}")'''
    plt.show()



    if str(input("voulez-vous lancer l'entrainement?")) == "oui":   #on lance pas l'entrainement a chaque fois, que si désiré

        print("--- DÉMARRAGE DE L'ENTRAÎNEMENT SYNTHÉTIQUE ---")
        
        #paramètres
        device = torch.device("cpu")
        model = Net().to(device)
        optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.5)
        
        
        #note: La binarisation se fait déjà dans PrintedMNIST
        transform_base = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
            lambda x: x > 0,
            lambda x: x.float(),
        ])
        
        #création du Dataset
        train_set = PrintedMNIST(100000, 42, transform=transform_base)      # 100000 images
        train_loader = torch.utils.data.DataLoader(train_set, batch_size=64, shuffle=True)
        

        model.train()
        for epoch in range(1, 6):
            total_loss = 0
            for batch_idx, (data, target) in enumerate(train_loader):
                optimizer.zero_grad()
                output = model(data)
                loss = F.nll_loss(output, target)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                
            print(f"Epoch {epoch} terminée. Loss moyenne: {total_loss / len(train_loader):.4f}")

        #sauvegarde du modèle
        path_save = "./Tectonic/model.ckpt"
        torch.save(model.state_dict(), path_save)
        print(f"Modèle sauvegardé sous : {path_save}")