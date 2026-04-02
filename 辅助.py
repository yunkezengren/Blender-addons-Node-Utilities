import bpy

for tree in bpy.data.node_groups:
    for old_node in tree.nodes:
        if old_node.bl_idname != "NodeUndefined": continue
        if old_node.name.startswith("List"): 
            new_node = tree.nodes.new("GeometryNodeFieldToList")
        if old_node.name.startswith("Get List Item"): 
            old_type = old_node.inputs[0].type
            new_node = tree.nodes.new("GeometryNodeListGetItem")
            new_node.socket_type = old_type if old_type != "VALUE" else "FLOAT"
        for i, socket in enumerate(old_node.inputs):
            for link in socket.links:
                tree.links.new(link.from_socket, new_node.inputs[i], handle_dynamic_sockets=True)
        for socket in old_node.outputs:
            for link in socket.links:
                tree.links.new(new_node.outputs[0], link.to_socket, handle_dynamic_sockets=True)
        new_node.location = old_node.location
        new_node.parent = old_node.parent
        tree.nodes.remove(old_node)
        