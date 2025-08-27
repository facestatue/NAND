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
                        [end_point[0], end_point[1]]])
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
        self.current_uuid = 0

    def add_node(self, pos):
        self.nodes.append(Node([], [], pos, self.current_uuid, False))
        self.current_uuid += 1

    def remove_node(self, uuid: int):
        for node in self.nodes:
            if node.uuid == uuid:
                self.nodes.remove(node)

    def get_node_by_uuid(self, uuid: int):
        for node in self.nodes:
            if node.uuid == uuid:
                return node

    def connect_nodes(self, node_sender: int, node_receiver: int):
        self.get_node_by_uuid(node_sender).out_connections.append(node_receiver)
        self.get_node_by_uuid(node_receiver).in_connections.append(node_sender)

    def disconnect_nodes(self, node_sender: int, node_receiver: int):
        self.get_node_by_uuid(node_sender).out_connections.remove(node_receiver)
        self.get_node_by_uuid(node_receiver).in_connections.remove(node_sender)

    def update_nodes(self):
        next_step = self.nodes
        for node in next_step:
            inputs = []
            for connection in node.in_connections:
                inputs.append(self.get_node_by_uuid(connection).status)
            node.status = not all(inputs) if inputs else node.status
        self.nodes = next_step


world = World()
pygame.init()
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
clock = pygame.time.Clock()
running = True

tool = "modify"
held_node = None
selected_nodes = []
select_rect = None

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    screen.fill("black")

    if tool == "select" and held_node:
        mouse_down, mouse_pos = pygame.mouse.get_pressed(), pygame.mouse.get_pos()
        if mouse_down[0]:
            rect = pygame.Rect(held_node.pos[0],
                               held_node.pos[1],
                               mouse_pos[0] - held_node.pos[0],
                               mouse_pos[1] - held_node.pos[1])
            pygame.draw.rect(screen, "blue", rect, width=3)

    if select_rect:
        pygame.draw.rect(screen, "blue", select_rect, width=3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_s:
                savefile = input("Save to file: ")
                file = open(f"{savefile}.bin", "wb+")
                pickle.dump(world, file)
                file.close()
                running = False

            if event.key == pygame.K_l:
                savefile = input("Load from file: ")
                file = open(f"{savefile}.bin", 'rb')
                world = pickle.load(file)
                file.close()

            if event.key == pygame.K_1:
                tool = "modify"

            if event.key == pygame.K_2:
                held_node = None
                tool = "connection"

            if event.key == pygame.K_3:
                tool = "add"

            if event.key == pygame.K_4:
                held_node = None
                tool = "move"

            if event.key == pygame.K_5:
                held_node = None
                tool = "select"

            if tool == "select":
                if event.key == pygame.K_c:
                    mouse_pos = pygame.mouse.get_pos()
                    cloned_dx = select_rect.center[0] - mouse_pos[0]
                    cloned_dy = select_rect.center[1] - mouse_pos[1]
                    uuid_offset = world.current_uuid + 5
                    node_uuids = [node.uuid for node in selected_nodes]
                    for node in selected_nodes:
                        world.nodes.append(Node(
                            [n + uuid_offset for n in node.out_connections],
                            [n + uuid_offset for n in node.in_connections],
                            (node.pos[0] - cloned_dx, node.pos[1] - cloned_dy),
                            world.current_uuid + 5,
                            node.status
                        ))
                        world.current_uuid += 1

                    select_rect.center = (select_rect.center[0] - cloned_dx, select_rect.center[1] - cloned_dy)
                    selected_nodes = world.nodes[-len(node_uuids):]
                    
            if event.key == pygame.K_r:
                world.nodes = []

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if tool == "move":
                    held_node = None

                if tool == "select":
                    select_rect = pygame.Rect(held_node.pos[0],
                                              held_node.pos[1],
                                              event.pos[0] - held_node.pos[0],
                                              event.pos[1] - held_node.pos[1])
                    for node in world.nodes:
                        if select_rect.left < node.pos[0] < select_rect.right and \
                                select_rect.top < node.pos[1] < select_rect.bottom:
                            selected_nodes.append(node)
                    print(selected_nodes)

                if tool == "select.move":
                    selected_nodes = []
                    select_rect = None
                    tool = "select"

        elif event.type == pygame.MOUSEMOTION:
            if tool == "move" and held_node:
                held_node.pos = event.pos

            if tool == "select.move" and selected_nodes:
                select_rect.center = (select_rect.center[0] + event.rel[0], select_rect.center[1] + event.rel[1])
                for node in selected_nodes:
                    node.pos = (node.pos[0] + event.rel[0], node.pos[1] + event.rel[1])


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

                if tool == "select":
                    if select_rect and event.pos:
                        if select_rect.left < event.pos[0] < select_rect.right and \
                                select_rect.top < event.pos[1] < select_rect.bottom:
                            tool = "select.move"
                        else:
                            held_node = Node([], [], event.pos, None, None)
                            selected_nodes = []
                            select_rect = None
                    else:
                        held_node = Node([], [], event.pos, None, None)
                        selected_nodes = []

                if selected_node:
                    if tool == "connection":
                        if held_node is None:
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
                        if held_node is None:
                            held_node = selected_node

                        else:
                            world.disconnect_nodes(held_node.uuid, selected_node.uuid)
                            held_node = None

    # Draw curves / connections
    for node in world.nodes:
        for connection in node.out_connections:
            curve = generate_curve(start_point=node.pos, end_point=world.get_node_by_uuid(connection).pos)
            lines = rasterize_curve(curve)
            total_length = 0
            for line in lines:
                dx, dy = abs(line[1][0] - line[0][0]), abs(line[1][1] - line[0][1])
                total_length += ((dx**2 + dy**2) ** 0.5)
                if 10 < total_length < 25:
                    color = "green"

                elif curve.length - 25 < total_length < curve.length:
                    color = "red"

                else:
                    color = "yellow" if node.status else "white"
                pygame.draw.line(screen, color, start_pos=line[0], end_pos=line[1], width=2)

    # Draw nodes afterwards
    for node in world.nodes:
        pygame.draw.circle(screen, "yellow" if node.status else "white", center=node.pos, radius=10)

    pygame.display.flip()
    world.update_nodes()

    clock.tick(60)

pygame.quit()
