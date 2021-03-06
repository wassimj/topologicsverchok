import bpy
from bpy.props import BoolProperty, FloatProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, repeat_last
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.utils.handle_blender_data import correct_collection_length
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
import sverchok.utils.meshes as me

from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology, Graph, Dictionary, Attribute, AttributeManager, VertexUtility, EdgeUtility, WireUtility, ShellUtility, CellUtility, TopologyUtility
import cppyy
from itertools import cycle

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
	if topology == None:
		return None
	else:
		topology.__class__ = classByType(topology.GetType())
	return topology

def edgesByVertices(vertices, topVerts):
    edges = cppyy.gbl.std.list[Edge.Ptr]()
    for i in range(len(vertices)-1):
        v1 = vertices[i]
        v2 = vertices[i+1]
        e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
        edges.push_back(e1)
    # connect the last vertex to the first one
    v1 = vertices[-1]
    v2 = vertices[0]
    e1 = Edge.ByStartVertexEndVertex(topVerts[v1], topVerts[v2])
    edges.push_back(e1)
    return edges


def vertexIndex(v, vertices, tolerance):
    index = None
    v._class__ = Vertex
    i = 0
    for aVertex in vertices:
        aVertex.__class__ = Vertex
        d = VertexUtility.Distance(v, aVertex)
        if d <= tolerance:
            index = i
            break
        i = i+1
    return index


def topologyByFaces(faces, tolerance):
	output = None
	if len(faces) == 1:
		return fixTopologyClass(faces.front())
	try:
		output = Cell.ByFaces(faces)
	except:
		try:
			output = CellComplex.ByFaces(faces, tolerance)
		except:
			try:
				output = Shell.ByFaces(faces)
			except:
				try:
					output = Cluster.ByTopologies(faces)
				except:
					print("ERROR: Could not create any topology from the input faces!")
					output = None
	return fixTopologyClass(output)

def topologyByEdges(edges):
	output = None
	if len(edges) == 1:
		return fixTopologyClass(edges.front())
	try:
		output = Wire.ByEdges(edges)
	except:
		try:
			output = Cluster.ByTopologies(edges)
		except:
			print("ERROR: Could not create any topology from the input edges!")
			output = None
	return fixTopologyClass(output)

class SvTopologyByGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Topology from the input geometry
	"""
	bl_idname = 'SvTopologyByGeometry'
	bl_label = 'Topology.ByGeometry'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)
	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Vertices')
		self.inputs.new('SvStringsSocket', 'Edges')
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvStringsSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Faces')


	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		vertices = []
		edges = []
		faces = []
		if (self.inputs['Vertices'].is_linked):
			vertices = self.inputs['Vertices'].sv_get(deepcopy=False, default=[])[0]
		if (self.inputs['Edges'].is_linked):
			edges = self.inputs['Edges'].sv_get(deepcopy=False, default=[])[0]
		if (self.inputs['Faces'].is_linked):
			faces = self.inputs['Faces'].sv_get(deepcopy=False, default=[])[0]
		tol = self.inputs['Tol'].sv_get(deepcopy=False, default=0.0001)[0]

		if len(vertices) > 0:
			topVerts = cppyy.gbl.std.vector[Vertex.Ptr]()
			for aVertex in vertices:
				v = Vertex.ByCoordinates(aVertex[0], aVertex[1], aVertex[2])
				topVerts.push_back(v)
			self.outputs['Vertices'].sv_set(list(topVerts))
		else:
			self.outputs['Topology'].sv_set([])
			return

		if len(faces) > 0:
			topFaces = cppyy.gbl.std.list[Face.Ptr]()
			for aFace in faces:
				faceEdges = edgesByVertices(aFace, topVerts)
				faceWire = Wire.ByEdges(faceEdges)
				topFace = Face.ByExternalBoundary(faceWire)
				topFaces.push_back(topFace)
			output = topologyByFaces(topFaces, tol)
			self.outputs['Faces'].sv_set(list(topFaces))
			self.outputs['Topology'].sv_set([output])
			return

		if len(edges) > 0:
			topEdges = cppyy.gbl.std.list[Edge.Ptr]()
			for anEdge in edges:
				topEdge = Edge.ByStartVertexEndVertex(topVerts[anEdge[0]], topVerts[anEdge[1]])
				topEdges.push_back(topEdge)
			output = topologyByEdges(topEdges)
			self.outputs['Edges'].sv_set(list(topEdges))
			self.outputs['Topology'].sv_set([output])
			return
		topologies = cppyy.gbl.std.list[Topology.Ptr]()
		for aVert in topVerts:
			topologies.push_back(aVert)
		output = Cluster.ByTopologies(topologies)
		self.outputs['Topology'].sv_set([output])


def register():
	bpy.utils.register_class(SvTopologyByGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyByGeometry)

