"""
Situation	: New features to add inside the project. New tree structure and naming system imposed by teachers after one year of production.
Problem		: Non zero attributes. Need to add GuerillaTags and variant. No access to the new server disk yet.
Goal		: Clean props attributes, add features and reexport them in the new path.
"""

import os
import sys
import shutil

#====================================================================#
#THESE ARE THE MISSING STUFF WHEN RUNNING python.exe compared with mayapy.exe
#====================================================================#

os.environ["MAYA_LOCATION"] = r"C:\\Program Files\\Autodesk\\Maya2020"
os.environ["PYTHONHOME"]    = r"C:\\Program Files\\Autodesk\\Maya2020\\Python"
os.environ["PATH"]          = r"C:\\Program Files\\Autodesk\\Maya2020\\bin;" + os.environ["PATH"]

sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\Python\\Lib\\site-packages\\maya")                     
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\bin\\python27.zip")
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\Python\\DLLs")
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\Python\\lib")
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\bin")
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\Python")
sys.path.append("C:\\Program Files\\Autodesk\\Maya2020\\Python\\lib\\site-packages")

myLocalDirIA = r"C:\\Users\\npeyren\\Documents\\01_Travail\\02_personal\\tmp\\modeling\\"
myDirIA = r"C:\\Users\\Nathan\\Documents\\1_Travail\\\\02_personal\\tmp\\publishs\\"
categories = {"CHR":r"characters\\", "CLT":r"cloth\\", "PRP":r"props\\", "TNL":r"propsTunnel\\", "ARN":r"propsArene\\"}
tagConvert = {"CHR":"ch", "CLT":"cl", "PRP":"p", "TNL":"pt", "ARN":"pa", "ENV":"en"}
sceneDir = r"\\tasks\\modeling\\"
exportDir = r"\\publishs\\modeling\\v001\\"
objTransformed = r"C:\\Users\\Nathan\\Documents\\1_Travail\\\\02_personal\\tmp\\"
missingFiles = []

import maya.standalone as standalone
import maya.cmds as cmds
import re

def getNumericTail(str):
    tail = re.split('[^\d]', str)[-1]
    if len(tail) > 1:
        finder = str[:-len(tail)-1] + "_" + tail
        if finder != str:
            tail = ""
            return tail
        else:
            return tail
    else:
        return tail

def endsWithNumber(str):
    return bool(getNumericTail(str))

def camelCase(childName):
    if childName[:2].isupper() == False:
        lowRnm = cmds.rename(childName, childName[0].lower() + childName[1:])
        splChild = lowRnm.split("_")
        count = 0
        for part in splChild:
            if count == 0:
                addPart = cmds.rename(lowRnm, part)
                lowRnm = addPart
                count += 1
            else:
                addPart = cmds.rename(lowRnm, lowRnm + part)
                lowRnm = addPart

def meshCleaner(trans):
    cmds.setAttr(trans + ".visibility", 1)
    cmds.select(trans)
    cmds.file(objTransformed + trans + ".obj", f=True, pr=1, typ="OBJexport", es=1, op="groups=0; ptgroups=0; materials=0; smoothing=0; normals=0")
    cmds.delete(trans)
    cmds.file(objTransformed + trans + ".obj", f=True, i = True)
    cleanedMesh = cmds.select("Mesh")
    renamedMesh = cmds.rename(cleanedMesh, trans)
    return renamedMesh

def exportCmd(expPath, objFile, objName):
    cmds.file(expPath + "mod_" + objFile + "_v001.obj", f=True, pr=1, typ="OBJexport", es=1, op="groups=1; ptgroups=0; materials=0; smoothing=0; normals=1")
    finder = cmds.getFileList(folder = expPath, filespec = "*.mtl")
    for mtl in finder:
        os.remove(expPath + mtl)
    root = "-root " + objName
    cmds.AbcExport(j = "-frameRange 0 0 -attr typeTag -attr GuerillaTags -uvWrite -worldSpace -dataFormat ogawa " + root + " -file " + expPath + "mod_" + objFile + "_v001.abc")

def saver(path, objName):
    cmds.file(rename = str(path + "mod_" + objName) + "_v001" + ".ma")
    cmds.file(save=True, f = True, type = "mayaAscii")

# Reset translate /rotate, freeze scales, rename geo as fileName, delete history, add GuerillaTags attribute, export OBJ
def SceneCleaner(abcPath, abcFile):
    # Open a file and get the file name.
    cmds.AbcImport(abcPath, mode = "open", fitTimeRange = True)
    # Get the file name with no extension.
    dotSplitName = abcFile.split('.')
    objectName = dotSplitName[0]
    # Split the file name.
    tagName = objectName.split('_')
    axis = ['x', 'y', 'z']
    attrs = ['t', 'r', 's']

    # WHEN THE FILE IS OPENED #
    # Make geometry visible and delete history with objExport and rename mesh or group meshes.
    list = cmds.ls(g=True)

    for i in list:
        if (cmds.objExists(i) == True):
            transform = cmds.listRelatives(i, ap=True)
            if len(list) > 1:
                parentGrp = cmds.listRelatives(transform, ap=True)
                cmds.parent(meshCleaner(transform[0]), parentGrp)
                cmds.rename(parentGrp, tagName[1] + "_001")
            else:
                cmds.rename(meshCleaner(transform[0]), tagName[1] + "_001")
        else:
            pass

    # Rename children.
    list = cmds.ls(g=True)
    if len(list) > 1:
        transform = cmds.listRelatives(list[0], ap=True, f = True)
        splTransform = transform[0].split("|")
        neutralGrp = splTransform[1]
        children = cmds.listRelatives(neutralGrp, c=True)
            
        for child in children:
            nbDigits = len(str(getNumericTail(child)))
            if endsWithNumber(child) == True:
                baseRnm = cmds.rename(child, child[4:-nbDigits - 1])
                camelCase(baseRnm)
            else:
                baseRnm = cmds.rename(child, child[4:])
                camelCase(baseRnm)

    # Get the new list of primitives.
    list = cmds.ls(g=True)
    for k in list:
        # Delete namespaces.
        namespaces = cmds.namespaceInfo(lon=True)
        namespaces.remove('UI')
        namespaces.remove('shared')
        if namespaces >= 1:
            cmds.namespace(set = ':')
            for i in namespaces:
                cmds.namespace(f = True, removeNamespace = i, deleteNamespaceContent = True)
        else:
            pass
        
    # Create the attribute GuerillaTags or refresh it by the object name without padding.
    list = cmds.ls(g=True)
    for shape in list:
        existTags = cmds.attributeQuery('GuerillaTags', node = shape, exists = True)
        transform = cmds.listRelatives(shape, ap=True)
        if not existTags:
            cmds.select(shape)
            cmds.addAttr(shortName = 'GuerillaTags', longName = 'GuerillaTags', dataType = 'string')

        if len(list) > 1:
            renamedTransform = transform[0].split("_")
            cmds.setAttr(shape + '.GuerillaTags', transform[0], type = 'string')
        else:
            cmds.setAttr(shape + '.GuerillaTags', tagName[1], type = 'string')

    transform = cmds.listRelatives(list[0], ap=True)
    if len(list) > 1:
        grpTransform = cmds.listRelatives(transform, ap=True)
        cmds.select(grpTransform)
        cmds.addAttr(shortName = 'typeTag', longName = 'typeTag', dataType = 'string')
        category = tagConvert.get(tagName[0], "none")
        cmds.setAttr(grpTransform[0] + '.typeTag', category, type = 'string')
        transform = grpTransform
        cmds.delete(ch=True)
    else:
        cmds.select(transform[0])
        cmds.addAttr(shortName = 'typeTag', longName = 'typeTag', dataType = 'string')
        category = tagConvert.get(tagName[0], "none")
        cmds.setAttr(transform[0] + '.typeTag', category, type = 'string')
        cmds.delete(ch=True)
        
    # Find the category of the propFile.
    categoryPath = categories.get(tagName[0], "none")
    
    exportPath  = myDirIA + categoryPath + tagName[1] + exportDir
    savePath    = myDirIA + categoryPath + tagName[1] + sceneDir
    
    if not os.path.exists(exportPath):
        os.makedirs(exportPath)
        # Export in obj.
        exportCmd(exportPath, tagName[1], transform[0])

        if not os.path.exists(savePath):
            os.makedirs(savePath)
            # Save as mayaAscii file.
            saver(savePath, tagName[1])
        else:
            saver(savePath, tagName[1])
    else:
        exportCmd(exportPath, tagName[1], transform[0])

        if not os.path.exists(savePath):
            os.makedirs(savePath)
            saver(savePath, tagName[1])
        else:
            saver(savePath, tagName[1])

standalone.initialize(name='python')
cmds.loadPlugin("C:\\Program Files\\Autodesk\\Maya2020\\bin\\plug-ins\\objExport")
cmds.loadPlugin("C:\\Program Files\\Autodesk\\Arnold\\Maya2020\\plug-ins\\mtoa")
cmds.loadPlugin("C:\\Program Files\\Autodesk\\Maya2020\\bin\\plug-ins\\abcImport")
cmds.loadPlugin("C:\\Program Files\\Autodesk\\Maya2020\\bin\\plug-ins\\abcExport")

# Liste les chemins de scenes Maya.
finder = cmds.getFileList(folder = myLocalDirIA, filespec = "*.abc")

for i in finder:
    print("Compute " + i)
    SceneCleaner(myLocalDirIA + i, i)

standalone.uninitialize()