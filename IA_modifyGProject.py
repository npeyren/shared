"""
Situation	: Generated Guerilla scenes, props paths and texture paths moved on a new tree structure
Problem		: All the paths inside Guerilla became wrong
Goal		: Relink all the paths
"""

from guerilla import Document, Modifier
from guerilla import pynode, Node
import os
import shutil

source = r"C:/Users/Nathan/Documents/1_Travail/01_Pole_3D/01_Productions/5th_year/00_IA/03_Arborescence/copyLookDev/"
globalPath = r"P:/shows/IA/assets/"
abcPath = r"/publishs/modeling/"
texPath = r"/publishs/texturing/"
savePath = r"/tasks/shading/"
libraryPathM = r"P:/shows/IA/library/lookDev/publishs/modeling/v001/"
libraryPathT = r"P:/shows/IA/library/lookDev/publishs/texturing/v001/"
categories = {"CHR":r"characters/", "PRP":r"props/", "ARN":r"propsArene/", "TNL":r"propsTunnel/"}

# Load a new scene
doc = Document()

for gproject in os.listdir(source):
    scene = doc.load(source + gproject, warn=False)

	# Split the file name into different parts
    fullPath = doc.getfilename()
    splFullPathS = fullPath.split(r"/")
    fileName = splFullPathS[-1]
    splFileName = fileName.split("_")
    propsName = splFileName[2]

    with Modifier() as mod:

		categoryPath = categories.get(splFileName[0], "none")

		# REFERENCES
		# For each archReference Node found
		for ref in doc.children(type='ArchReference',recursive=True):
			refName = ref.name
			print(str(refName) + " is a new ArchReference")
			# Relink the hero archReference with the last version number and rename his node
			versions = [x for x in os.listdir(globalPath + categoryPath + propsName + abcPath) if os.path.exists(globalPath + categoryPath + propsName + abcPath)]
			if str(ref.name) != "PRP_CAM_LookDev_abc" and str(ref.name) != "PRP_Obj_LookDev_abc" and str(ref.name) != "PRP_Skylight_LookDev_abc":
				ref.ReferenceFileName.set(globalPath + categoryPath + propsName + abcPath + versions[-1] + r"/mod_" + propsName + "_" + versions[-1] + ".abc")
				mod.renamenode(ref, "mod_" + propsName)
			# Relink the recurrent props and rename them
			elif str(ref.name) == "PRP_CAM_LookDev_abc":
				ref.ReferenceFileName.set(libraryPathM + "mod_camera_v001.abc")
				mod.renamenode(ref, "mod_camera_001")
			elif str(ref.name) == "PRP_Obj_LookDev_abc":
				ref.ReferenceFileName.set(libraryPathM + "mod_objet_v001.abc")
				mod.renamenode(ref, "mod_objet_001")
			elif str(ref.name) == "PRP_Skylight_LookDev_abc":
				ref.ReferenceFileName.set(libraryPathM + "mod_skyLight_v001.abc")
				mod.renamenode(ref, "mod_skyLight_001")

		# RENDERGRAPH NODE
		# For each rendergraph node
		for render in doc.children(type='RenderGraph',recursive=True):
			rGraph = render.name
			print(str(rGraph) + " is a new RenderGraphNode")
			# Rename the rendergraph
			mod.renamenode(render, "rGraph_" + propsName + "_001")
			# Check the last version number
			versions = [x for x in os.listdir(globalPath + categoryPath + propsName + texPath) if os.path.exists(globalPath + categoryPath + propsName + texPath)]
			# Check if there is variant texture
			variantCheck = len([x for x in os.listdir(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/") if x.endswith(".exr")])
			
			# HERO SHADER NODE SET
			for c in render.children('RenderGraphNodeShader'):
				print(str(c.name) + " is a new NodeSurface")
				# For each texture attribute with no variant, relink it with the new path
				for attr in c.children('AttributeShader'):
					if variantCheck != 0:
						if attr.Shader.get() != 'TextureSwitch':
							if attr.File.get().endswith("Base_Color.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_baseColor_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Metallic.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_metallic_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Height.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_height_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Normal_OpenGL.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_normalOpenGL_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Normal_DirectX.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_normalDirectX_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Roughness.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_roughness_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Opacity.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_opacity_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Glass.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_glass_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("300x208.jpg"):
								attr.File.set(libraryPathT + r"tex_planeCouleurs_full_baseColor_v001.%d.jpg")
							elif attr.File.get().endswith("Mixed_AO.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/tex_" + propsName + "_full_mixedAO_" + versions[-1] + ".%d.exr")
					# For each texture attribute with a specific variant, relink it with the new path
					if variantCheck == 0:
						variants = [x for x in os.listdir(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/")]
						if attr.Shader.get() != 'TextureSwitch':
							if attr.File.get().endswith("Base_Color.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_baseColor_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Metallic.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_metallic_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Height.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_height_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Normal_OpenGL.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_normalOpenGL_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Normal_DirectX.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_normalDirectX_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Roughness.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_roughness_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Opacity.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_opacity_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Glass.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_glass_" + versions[-1] + ".%d.exr")
							elif attr.File.get().endswith("Mixed_AO.exr"):
								attr.File.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variants[0] + r"/tex_" + propsName + "_" + variants[0] + "_mixedAO_" + versions[-1] + ".%d.exr")
						# For each texture attribute with variants and textureSwitch, relink it with the new path
						elif attr.Shader.get() == 'TextureSwitch':
							if attr.File.get().endswith("Base_Color.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_baseColor_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_baseColor_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Metallic.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_metallic_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_metallic_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Height.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_height_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_height_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Normal_OpenGL.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_normalOpenGL_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_normalOpenGL_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Normal_DirectX.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_normalDirectX_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_normalDirectX_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Roughness.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_roughness_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_roughness_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Opacity.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_opacity_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_opacity_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Glass.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_glass_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_glass_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
							elif attr.File.get().endswith("Mixed_AO.exr"):
								count = 0
								for variant in variants:
									if count == 0:
										attr.Files.set(globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_mixedAO_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
										count += 1
									elif count != 0:
										attr.Files.set(newName + "\n" + globalPath + categoryPath + propsName + texPath + versions[-1] + r"/" + variant + r"/tex_" + propsName + "_" + variant + "_mixedAO_" + versions[-1] + ".%d.exr")
										newName = attr.Files.get()
			# SHADER NODE
			for c in render.children('RenderGraphNodeShader'):
				print(str(c.name) + " is a new NodeSurface")
				# HERO PROPS SHADER
				if str(c.name) != "Ball_Chrome_Shader" and str(c.name) != "Ball_Gray_Shader" and str(c.name) != "Plane_Colors_Shader" and str(c.name).startswith("PRP_"):
					mod.renamenode(c, "shd_" + propsName)
				# OTHERS
				elif str(c.name) == "Displacement":
					mod.renamenode(c, "shd_displacement")
				elif str(c.name) == "Ball_Chrome_Shader":
					mod.renamenode(c, "shd_ballChrome")
				elif str(c.name) == "Ball_Gray_Shader":
					mod.renamenode(c, "shd_ballGray")
				elif str(c.name) == "Plane_Colors_Shader":
					mod.renamenode(c, "shd_planeCouleurs")
				elif str(c.name) == "Glass":
					mod.renamenode(c, "shd_glass")

			# LIGHT NODE
			for c in render.children('RenderGraphNodeLight'):
				print(str(c.name) + " is a new NodeLight")
				for envMap in c.children('EnvironmentLocator'):
					if envMap.EnvironmentMap.get().endswith("07_2k.exr"):
						envMap.EnvironmentMap.set(libraryPathT + r"tex_skyLight_studioSmall2k_v001.exr")
					elif envMap.EnvironmentMap.get().endswith("fireplace_2k.exr"):
						envMap.EnvironmentMap.set(libraryPathT + r"tex_skyLight_fireplace2k_v001.exr")

			for c in render.children('RenderGraphNodeLight'):
				if str(c.name) == "EnvLight":
					mod.renamenode(c, "envLight01")
				elif str(c.name) == "EnvLight1":
					mod.renamenode(c, "envLight02")

			# TAG NODE
			for c in render.children('RenderGraphNodeTag'):
				print(str(c.name) + " is a new NodeTag")
				# HERO PROPS TAG
				if str(c.name) != "Ball_Chrome_Tag" and str(c.name) != "Ball_Gray_Tag" and str(c.name) != "Plane_Colors_Tag" and str(c.name).startswith("PRP_"):
					c.Tag.set(propsName)
					mod.renamenode(c, "tag_" + propsName)
				# OTHERS
				elif str(c.name) == "Ball_Chrome_Tag":
					c.Tag.set("ballChrome")
					mod.renamenode(c, "tag_ballChrome")
				elif str(c.name) == "Ball_Gray_Tag":
					c.Tag.set("ballGray")
					mod.renamenode(c, "tag_ballGray")
				elif str(c.name) == "Plane_Colors_Tag":
					c.Tag.set("planeCouleurs")
					mod.renamenode(c, "tag_planeCouleurs")

			# PATH NODE
			for c in render.children('RenderGraphNodePath'):
				print(str(c.name) + " is a new NodePath")
				if str(c.name) == "aiSkyDomeLightShape1":
					mod.renamenode(c, "skyLight_001")
				else:
					mod.renamenode(c, str(c.name)[0].lower() + str(c.name)[1:])

	# Save the file at the new path with the new naming system
    categoryPath = categories.get(splFileName[0], "none")
    doc.save(filename = globalPath + categoryPath + propsName + savePath + "shd_" + propsName + "_full_v001.gproject")