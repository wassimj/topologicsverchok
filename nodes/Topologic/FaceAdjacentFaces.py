import bpy
from bpy.props import FloatProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(cell):
	returnList = []
	if cell.Type() == topologic.Cell.Type():
		cells = cppyy.gbl.std.list[topologic.Cell.Ptr]()
		_ = cell.AdjacentCells(cells)
		returnList = list(cells)
	return returnList

class SvFaceAdjacentFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs a list of Faces that are adjacent to the input Face
	"""
	bl_idname = 'SvCellAdjacentFaces'
	bl_label = 'Face.AdjacentFaces'
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Face')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		cells = self.inputs['Cell'].sv_get(deepcopy=False)
		cells = flatten(cells)
		outputs = []
		for aCell in cells:
			outputs.append(processItem(aCell))
		self.outputs['Cells'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellAdjacentCells)

def unregister():
	bpy.utils.unregister_class(SvCellAdjacentCells)
