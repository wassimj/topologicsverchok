import bpy
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def matchLengths(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

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
	v = item[0]
	t = item[1]
	dist = None
	try:
		dist = topologic.VertexUtility.Distance(v, t)
	except:
		dist = None
	return dist

class SvVertexDistance(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Outputs the distance between the input Vertex and the input Topology
	"""
	bl_idname = 'SvVertexDistance'
	bl_label = 'Vertex.Distance'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertex')
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Distance')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Edge'].sv_set([])
			return
		vertexList = self.inputs['Vertex'].sv_get(deepcopy=False)
		topologyList = self.inputs['Topology'].sv_get(deepcopy=False)

		vertexList = flatten(vertexList)
		topologyList = flatten(topologyList)
		matchLengths([vertexList, topologyList])
		inputs = zip(vertexList, topologyList)
		outputs = []
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Distance'].sv_set(outputs)

def register():
    bpy.utils.register_class(SvVertexDistance)

def unregister():
    bpy.utils.unregister_class(SvVertexDistance)
