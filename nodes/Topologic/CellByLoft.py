import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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

def classByType(argument):
	switcher = {
		1: Vertex,
		2: Edge,
		4: Wire,
		8: Face,
		16: Shell,
		32: Cell,
		64: CellComplex,
		128: Cluster }
	return switcher.get(argument, Topology)

def fixTopologyClass(topology):
  topology.__class__ = classByType(topology.GetType())
  return topology

def processItem(item):
	finalCell = None
	for i in range(len(item)-1):
		wires = cppyy.gbl.std.list[topologic.Wire.Ptr]()
		w1 = item[i]
		w2 = item[i+1]
		wires.push_back(w1)
		wires.push_back(w2)
		cell = topologic.CellUtility.ByLoft(wires)
		if finalCell == None:
			finalCell = cell
		else:
			finalCell = finalCell.Union(cell, False)
	return fixTopologyClass(finalCell)

class SvCellByLoft(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Cell by lofting through the input Wires. The Wires must be closed and ordered
	"""
	bl_idname = 'SvCellByLoft'
	bl_label = 'Cell.ByLoft'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wires')
		self.outputs.new('SvStringsSocket', 'Cell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		wiresList = self.inputs['Wires'].sv_get(deepcopy=False)
		if isinstance(wiresList[0], list) == False:
			wiresList = [wiresList]
		outputs = []
		for wireList in wiresList:
			outputs.append(processItem(wireList))
		self.outputs['Cell'].sv_set(outputs)

def register():
	bpy.utils.register_class(SvCellByLoft)

def unregister():
	bpy.utils.unregister_class(SvCellByLoft)
