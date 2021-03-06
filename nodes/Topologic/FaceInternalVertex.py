import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(item):
	vert = None
	try:
		vert = topologic.FaceUtility.InternalVertex(item)
	except:
		vert = None
	return vert

class SvFaceInternalVertex(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Vertex guaranteed to be inside the input Face
	"""
	bl_idname = 'SvFaceInternalVertex'
	bl_label = 'Face.InternalVertex'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Vertex')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		inputs = self.inputs['Face'].sv_get(deepcopy=False)
		inputs = flatten(inputs)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Vertex'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvFaceInternalVertex)

def unregister():
	bpy.utils.unregister_class(SvFaceInternalVertex)
