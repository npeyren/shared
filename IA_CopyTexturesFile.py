"""
Situation   : new tree structure and naming system imposed by teachers after one year of production
Problem     : no access to the new server disk yet and big tool pack only available on this new server 
Goal        : rename and copy all the textures in local disk
"""

import os
import shutil
import re

# Paths used by team
propsPath   = r"P:\\IA\\Prod\\0002_Props_Modeling\\"
pArenePath  = r"P:\\IA\\Prod\\0003_Environnement\\ENV_Arene\\"
# Destination
refName     = r"P:\\shows\\IA\\assets\\props\\"
# Temp folder paths
copyFolder  = r"C:\\Users\\npeyren\\Documents\\01_Travail\\00_IA\\copyTextures\\"
laptopFold  = r"C:\\Users\\Nathan\\Documents\\1_Travail\\01_Pole_3D\\01_Productions\\5th_year\\00_IA\\03_Arborescence\\copyTextures\\"
propsName   = []

"""
goal        : convert the current naming system into camelCase and respect the extension file
path        : current path
partName    : name of the props
ext         : current extension file
return      : new name of the props
"""
def camelCaseTx(path, partName, ext):
    childName = partName[5:]
    if childName[:2].isupper() == False:
        lowRnm = childName[0].lower() + childName[1:]
        splChild = lowRnm.split("_")
        count = 0
        for part in splChild:
            if count == 0:
                lowRnm = part
                count += 1
            else:
                lowRnm += part
        
        os.rename(path + partName + ext, path + lowRnm + ext)
        return lowRnm

"""
goal        : convert the current name of the props into camelCase
path        : current path
partName    : name of the props
return      : new name of the props
"""
def camelCase(path, childName):
    if childName[:2].isupper() == False:
        lowRnm = childName[0].lower() + childName[1:]
        splChild = lowRnm.split("_")
        count = 0
        for part in splChild:
            if count == 0:
                lowRnm = part
                count += 1
            else:
                lowRnm += part
        
        os.rename(path + childName, path + lowRnm)
        return lowRnm

"""
goal        : create a list
path        : current path
return      : list of folder or files found
"""
def listMaker(path):
    variantName = []
    for i in os.listdir(path):
        variantName.append(i)
    return variantName

propsName = listMaker(refName) # Lister tous les noms de props de Shows
props = listMaker(propsPath) # Lister tous les noms de props dans propsModeling
count = 130 # Commencer le script a l index X
countTx = 0

# Pour chaque props dans propsModeling
for i in props:
    # Definir sa destination
    texPath = propsPath + i + r"\\0005_Texture\\Publish\\"
    # Compter et lister le nombre de textures
    changeProps = len([ x for x in os.listdir(texPath) if x.endswith(".exr")])
    listVariant = listMaker(texPath)
    print("changeProps has " + str(changeProps) + " exr files")
    # Pour chaque fichier props
    for filesExt in os.listdir(texPath): 
        print(texPath + filesExt)
        noExtFiles = filesExt.split('.')
        # Si il n est pas vide et contient un exr
        if changeProps > 0 and noExtFiles[1] == "exr":
            # Si le dossier avec le nom du props n_existe pas alors le cree
            if not os.path.exists(laptopFold + propsName[count]):
                os.makedirs(laptopFold + propsName[count])
            # Copier les textures actuelles dans mon dossier temp
            shutil.copy(texPath + filesExt, laptopFold + propsName[count] + r"\\" + filesExt)
            # Construction de la nouvelle nomenclature
            underscore = noExtFiles[0].split("_")
            camelCaseFiles = camelCaseTx(laptopFold + propsName[count] + r"\\", noExtFiles[0], "." + noExtFiles[1])
            fileName = "tex_" + propsName[count] + "_full_" + camelCaseFiles + "_v001_" + underscore[0] + "." + noExtFiles[1]
            os.rename(laptopFold + propsName[count] + r"\\" + camelCaseFiles + "." + noExtFiles[1], laptopFold + propsName[count] + r"\\" + fileName)
            # Tracker de l'avancee
            changeProps -= 1
            print("changeProps equal now " + str(changeProps))
            if changeProps == 0:
                count += 1

        # Si il ne contient pas de format exr
        elif len(noExtFiles) == 1:
            # Compte le nombre de variant et le nombre de texture par variant
            changeTx = len([ x for x in os.listdir(texPath) if not x.endswith(".guerilla")])
            changeVariant = len([ x for x in os.listdir(texPath + filesExt + r'\\') if x.endswith(".exr")])
            # Si le dossier du variant n_existe pas alors le cree
            if not os.path.exists(laptopFold + propsName[count] + r"\\" + listVariant[countTx]):
                os.makedirs(laptopFold + propsName[count] + r"\\" + listVariant[countTx])
            # Reitere les manipulations de la condition majeure precedente mais par variant 
            camelCaseFolder = camelCase(laptopFold + propsName[count] + r"\\",  listVariant[countTx])
            for i in os.listdir(texPath + filesExt + r'\\'):
                noExtFiles = i.split('.')
                if noExtFiles[1] == "exr":
                    shutil.copy(texPath + filesExt + r'\\' + i, laptopFold + propsName[count] + r"\\" + camelCaseFolder + r'\\' + i)
                    underscore = noExtFiles[0].split("_")
                    camelCaseFiles = camelCaseTx(laptopFold + propsName[count] + r"\\"+ camelCaseFolder + r'\\', noExtFiles[0], "." + noExtFiles[1])
                    fileName = "tex_" + propsName[count] + "_" + camelCaseFolder + "_" + camelCaseFiles + "_v001_" + underscore[0] + "." + noExtFiles[1]
                    os.rename(laptopFold + propsName[count] + r"\\" + camelCaseFolder + r'\\' + camelCaseFiles + "." + noExtFiles[1], laptopFold + propsName[count] + r"\\" + camelCaseFolder + r'\\' + fileName)
                    # Tracker de l'avancee
                    changeVariant -= 1
                    print("changeVariant equal now " + str(changeVariant))
                    if changeVariant == 0:
                        countTx += 1
                        print("changeTx equal now " + str(changeTx - changeTx + countTx))
                        if changeTx == countTx:
                            count += 1

        # Si le seul fichier trouve se nomme .guerilla alors passe            
        elif noExtFiles[1] == "guerilla":
            pass