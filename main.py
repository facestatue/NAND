import bezier
import numpy as np
import pygame
import pickle
from dataclasses import dataclass

# Bezier curve helper functions
def generate_curve(start_point: tuple[int, int], end_point: tuple[int, int]):
    y_avg = (start_point[1] + end_point[1]) // 2
    nodes = np.asarray([[start_point[0], start_point[1]],
                        [start_point[0], y_avg],
                        [end_point[0], y_avg],
                        [end_point[0], end_point[1]]
                       ])
    return bezier.Curve(nodes.T, degree=3)

def rasterize_curve(p_curve: bezier.Curve, subdivisions: int = 7):
    curves = [p_curve]
    new_curves = []
    for i in range(subdivisions):
        for j in range(2**i):
            curve = curves[j]
            new_curves.extend(curve.subdivide())
        curves = new_curves
        new_curves = []
    return [(c.nodes.T[0], c.nodes.T[-1]) for c in curves]


"""out_connections and in_connections is a list of node UUIDs."""
@dataclass
class Node:
    out_connections: list[int]
    in_connections: list[int]
    pos: tuple[float, float]
    uuid: int
    status: bool


class World(object):
    def __init__(self):
        self.nodes = []

    def add_node(self, pos):
        self.nodes.append(Node([], [], pos, len(self.nodes), False))

    def remove_node(self, uuid: int):
        self.nodes.pop(uuid)

    def connect_nodes(self, node_sender: int, node_receiver: int):
        self.nodes[node_sender].out_connections.append(node_receiver)
        self.nodes[node_receiver].in_connections.append(node_sender)

    def disconnect_nodes(self, node_sender: int, node_receiver: int):
        self.nodes[node_sender].out_connections.remove(node_receiver)
        self.nodes[node_receiver].in_connections.remove(node_sender)

    def update_nodes(self):
        next_step = self.nodes
        for node in next_step:
            inputs = []
            for connection in node.in_connections:
                inputs.append(self.nodes[connection].status)
            node.status = not all(inputs) if inputs else node.status
        self.nodes = next_step

world = World()
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
clock = pygame.time.Clock()
running = True

tool = "modify"
held_node = None

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            held_node = None
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_s:
                savefile = input("Save to file: ")
                file = open(f"{savefile}.bin", "wb+")
                pickle.dump(world.nodes, file)
                file.close()
                running = False

            if event.key == pygame.K_l:
                savefile = input("Load from file: ")
                file = open(f"{savefile}.bin", 'rb')
                world.nodes = pickle.load(file)
                file.close()

            if event.key == pygame.K_1:
                tool = "modify"

            if event.key == pygame.K_2:
                tool = "connection"

            if event.key == pygame.K_3:
                tool = "add"

            if event.key == pygame.K_4:
                tool = "move"

            if event.key == pygame.K_r:
                world.nodes = []

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                world.update_nodes()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if tool == "move":
                    held_node = None

        elif event.type == pygame.MOUSEMOTION:
            if tool == "move" and held_node:
                held_node.pos = event.pos

        elif event.type == pygame.MOUSEBUTTONDOWN:
            selected_node = None
            for node in world.nodes:
                dx = abs(event.pos[0] - node.pos[0])
                dy = abs(event.pos[1] - node.pos[1])
                distance = round((dx ** 2 + dy ** 2) ** 0.5)
                if distance < 10:
                    selected_node = node
                    break

            if event.button == 1:
                if tool == "add":
                    world.add_node(event.pos)

                if tool == "move" and held_node:
                    held_node.pos = event.pos

                if selected_node:
                    if tool == "connection":
                        if held_node == None:
                            held_node = selected_node

                        else:
                            world.connect_nodes(held_node.uuid, selected_node.uuid)
                            held_node = None

                    if tool == "modify":
                        selected_node.status = not selected_node.status

                    if tool == "move":
                        held_node = selected_node
                        held_node.pos = event.pos

            elif event.button == 3:
                if selected_node:
                    if tool == "add":
                        world.remove_node(selected_node.uuid)

                    if tool == "connection":
                        if held_node == None:
                            held_node = selected_node

                        else:
                            world.disconnect_nodes(held_node.uuid, selected_node.uuid)
                            held_node = None


    screen.fill("black")

    # Draw curves / connections
    for node in world.nodes:
        for connection in node.out_connections:
            curve = generate_curve(start_point=node.pos, end_point=world.nodes[connection].pos)
            lines = rasterize_curve(curve)
            total_length = 0
            for line in lines:
                dx = abs(line[1][0] - line[0][0])
                dy = abs(line[1][1] - line[0][1])
                total_length += ((dx**2 + dy**2) ** 0.5)
                if total_length > 10 and total_length < 25:
                    color = "green"

                elif total_length > curve.length - 25 and total_length < curve.length:
                    color = "red"

                else: color = "yellow" if node.status else "white"
                pygame.draw.line(screen, color, start_pos=line[0], end_pos=line[1], width=2)

    # Draw nodes afterwards
    for node in world.nodes:
        pygame.draw.circle(screen, "yellow" if node.status else "white", center=node.pos, radius=10)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
