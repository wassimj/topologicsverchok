import bpy
from bpy.props import IntProperty, StringProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph
import cppyy
import time

import importlib
importlib.import_module('topologicsverchok.nodes.Topologic.Replication')
from topologicsverchok.nodes.Topologic.Replication import flatten, repeat, onestep, iterate, trim, interlace, transposeList
replication = [("Default", "Default", "", 1),("Trim", "Trim", "", 2),("Iterate", "Iterate", "", 3),("Repeat", "Repeat", "", 4),("Interlace", "Interlace", "", 5)]

def processItem(item):
	topology = None
	graph = item[0]
	vertexA = item[1]
	vertexB = item[2]
	vertexKey = item[3]
	edgeKey = item[4]
	timeLimit = item[5]
	print("Graph Shortest Paths - Time Limit: "+str(timeLimit))
	paths = cppyy.gbl.std.list[topologic.Wire.Ptr]()
	_ = graph.ShortestPaths(vertexA, vertexB, vertexKey, edgeKey, True, timeLimit, paths)
	return list(paths)


class SvGraphShortestPaths(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a list of Wires that represents the shortest paths between the two input Graph Vertices found within the time limit in seconds
	"""
	bl_idname = 'SvGraphShortestPaths'
	bl_label = 'Graph.ShortestPaths'
	VertexKey: StringProperty(name='VertexKey', update=updateNode)
	EdgeKey: StringProperty(name='EdgeKey', update=updateNode)
	Replication: EnumProperty(name="Replication", description="Replication", default="Default", items=replication, update=updateNode)
	TimeLimit: IntProperty(name="Time Limit", default=10, min=1, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Graph')
		self.inputs.new('SvStringsSocket', 'Vertex A')
		self.inputs.new('SvStringsSocket', 'Vertex B')
		self.inputs.new('SvStringsSocket', 'Vertex Key').prop_name='VertexKey'
		self.inputs.new('SvStringsSocket', 'Edge Key').prop_name='EdgeKey'
		self.inputs.new('SvStringsSocket', 'Time Limit').prop_name="TimeLimit"
		self.outputs.new('SvStringsSocket', 'Wires')

	def draw_buttons(self, context, layout):
		layout.prop(self, "Replication",text="")

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			self.outputs['Topology'].sv_set([])
			return
		graphList = self.inputs['Graph'].sv_get(deepcopy=True)
		vertexAList = self.inputs['Vertex A'].sv_get(deepcopy=True)
		vertexBList = self.inputs['Vertex B'].sv_get(deepcopy=True)
		vertexKeyList = self.inputs['Vertex Key'].sv_get(deepcopy=True)
		edgeKeyList = self.inputs['Edge Key'].sv_get(deepcopy=True)
		timeLimitList = self.inputs['Time Limit'].sv_get(deepcopy=True)
		graphList = flatten(graphList)
		vertexAList = flatten(vertexAList)
		vertexBList = flatten(vertexBList)
		vertexKeyList = flatten(vertexKeyList)
		edgeKeyList = flatten(edgeKeyList)
		timeLimitList = flatten(timeLimitList)
		inputs = [graphList, vertexAList, vertexBList, vertexKeyList, edgeKeyList, timeLimitList]
		outputs = []
		if ((self.Replication) == "Default"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Trim"):
			inputs = trim(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Iterate"):
			inputs = iterate(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Repeat"):
			inputs = repeat(inputs)
			inputs = transposeList(inputs)
		elif ((self.Replication) == "Interlace"):
			inputs = list(interlace(inputs))
		for anInput in inputs:
			outputs.append(processItem(anInput))
		self.outputs['Wires'].sv_set(outputs)
		end = time.time()
		print("Graph ShortestPaths Operation consumed "+str(round(end - start,2))+" seconds")

def register():
    bpy.utils.register_class(SvGraphShortestPaths)

def unregister():
    bpy.utils.unregister_class(SvGraphShortestPaths)
