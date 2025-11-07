import hou

INHERIT_PARM_EXPRESSION = '''n = hou.pwd()
n_hasFlag = n.isMaterialFlagSet()
i = n.evalParm('inherit_ctrl')
r = 'none'
if i == 1 or (n_hasFlag and i == 2):
    r = 'inherit'
return r'''

def add_material(matlib, name, basecolor=None, arm=None, et=None, normal=None, useMetallic=False):
	# arm = AO / Roughness / Metallic
	# et = Emission / Transmission
	global INHERIT_PARM_EXPRESSION

	# create subnet template
	destination_node = matlib
	subnetNode = destination_node.createNode("subnet", name)
	subnetNode.moveToGoodPosition()
	subnetNode.setMaterialFlag(True)                  

	parameters = subnetNode.parmTemplateGroup()

	newParm_hidingFolder = hou.FolderParmTemplate("mtlxBuilder","MaterialX Builder",folder_type=hou.folderType.Collapsible)
	control_parm_pt = hou.IntParmTemplate('inherit_ctrl','Inherit from Class', 
	                    num_components=1, default_value=(2,), 
	                    menu_items=(['0','1','2']),
	                    menu_labels=(['Never','Always','Material Flag']))


	newParam_tabMenu = hou.StringParmTemplate("tabmenumask", "Tab Menu Mask", 1, default_value=["MaterialX parameter constant collect null genericshader subnet subnetconnector suboutput subinput"])
	class_path_pt = hou.properties.parmTemplate('vopui', 'shader_referencetype')
	class_path_pt.setLabel('Class Arc')
	class_path_pt.setDefaultExpressionLanguage((hou.scriptLanguage.Python,))
	class_path_pt.setDefaultExpression((INHERIT_PARM_EXPRESSION,))   

	ref_type_pt = hou.properties.parmTemplate('vopui', 'shader_baseprimpath')
	ref_type_pt.setDefaultValue(['/__class_mtl__/`$OS`'])
	ref_type_pt.setLabel('Class Prim Path')               

	newParm_hidingFolder.addParmTemplate(newParam_tabMenu)
	newParm_hidingFolder.addParmTemplate(control_parm_pt)  
	newParm_hidingFolder.addParmTemplate(class_path_pt)    
	newParm_hidingFolder.addParmTemplate(ref_type_pt)             

	parameters.append(newParm_hidingFolder)
	subnetNode.setParmTemplateGroup(parameters)

	# add material to matlib
	mat = subnetNode
	matlib.parm('matnode1').set(mat.name())
	matlib.parm('matpath1').set(mat.name())
	matlib.parm('assign1').set(1)

	# surface shader
	shader_output = mat.node('suboutput1')
	shader_surface = mat.createNode('mtlxstandard_surface')
	shader_output.setInput(0, shader_surface)

	# add maps
	if basecolor:
		shader_basecolor = mat.createNode('mtlximage', 'BASECOLOR')
		shader_basecolor.parm('file').set(basecolor)
		shader_surface.setInput(shader_surface.inputIndex('base_color'), shader_basecolor)

	if arm:
		shader_arm = mat.createNode('mtlximage', 'AMR')
		shader_arm.parm('file').set(arm)
		shader_ao = mat.createNode('mtlxextract', 'AO')
		shader_ao.setInput(shader_ao.inputIndex('in'), shader_arm)
		shader_roughness = mat.createNode('mtlxextract', 'Roughness')		
		shader_roughness.setInput(shader_roughness.inputIndex('in'), shader_arm)
		shader_roughness.parm('index').set(1)
		shader_metallic = mat.createNode('mtlxextract', 'Metallic')
		shader_metallic.parm('index').set(2)
		shader_metallic.setInput(shader_metallic.inputIndex('in'), shader_arm)		
		shader_surface.setInput(shader_surface.inputIndex('specular_roughness'), shader_roughness)
		if useMetallic: shader_surface.setInput(shader_surface.inputIndex('metalness'), shader_metallic)

	if normal:
		shader_normal = mat.createNode('mtlximage', 'NORMAL')
		shader_normal.parm('file').set(normal)
		shader_normal_map = mat.createNode('mtlxnormalmap::2.0')
		shader_normal_map.setInput(shader_normal_map.inputIndex('in'), shader_normal)
		shader_surface.setInput(shader_surface.inputIndex('normal'), shader_normal_map)

	mat.layoutChildren()

	return mat