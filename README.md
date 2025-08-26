# NAND v0.1.1
A short pygame demo (that will be expanded upon) that showcases the power of NAND in a graph theory inspired format.

## Instructions for use
### Keybinds
Press `1` for "modify" mode. Click on a node to reverse its status.

Press `2` for "connection" mode. Left click on a node to mark it for connection, and click another to connect the marked node to the clicked node.
To disconnect two nodes, perform the same procedure with right click.

Press `3` for "create" mode. Click anywhere to add another node. Right click to delete a node.

Press `4` for "move" mode. Click and hold to move a node.

Press `R` to clear the entire board.

Press `S` to save the current board to the directory the `main.py` file is located in. When pressed, a default python input prompt will appear in your terminal.

Press `L` to load a file from the directory the `main.py` file is located in. When pressed, a default python input prompt will appear in your terminal.

### Instructions
A node's color is its "status". When an update happens, every node will take the statuses of the nodes that are connected to it 
(connections are one-way- the red side is the "status out" side, the green side is the "status in" side) and perform a check. 

If all the node's inputs are True, the node will output False. In all other circumstances, it will output True. In other words, the boolean NAND operation.

## Packages/Installation
Fairly simple- just run "main.py". As for packages:
- `numpy 2.3.2`
- `bezier 2024.6.20`
- `pygame 2.6.1`
This also uses `pickle` and `dataclasses`.
