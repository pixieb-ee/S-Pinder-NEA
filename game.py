##Samantha Pinder AQA Non-Exam Assessment 2024

import pygame
from pygame.locals import *
import csv
import sys
import os
import time
from math import sqrt
import random

# Define the window dimensions, title and game speed (frames per second)
WINDOW_WIDTH = 816
WINDOW_HEIGHT = 528
WINDOW_TITLE = "Hero Adventure"
GAME_FPS = 30

# Size of each map tile in pixels
TILE_WIDTH = 48
TILE_HEIGHT = 48

# Maximum size the map can be in tiles
MAP_WIDTH = 300
MAP_HEIGHT = 300

# Maximum size of the collision layer
COLLISION_LAYER_WIDTH = MAP_WIDTH*3
COLLISION_LAYER_HEIGHT = MAP_HEIGHT*3

# Size of the maze in tiles
MAZE_WIDTH = 23
MAZE_HEIGHT = 21

# Start co-ordinates for the player
PLAYER_START_X = 71 * TILE_WIDTH
PLAYER_START_Y = 87 * TILE_HEIGHT

# Define the different Person NPC movement types
PERSON_MOVE_NONE = 0
PERSON_MOVE_WANDER = 1
PERSON_MOVE_FOLLOW = 2

# Define the different Monster NPC movement types
MONSTER_MOVE_NONE = 0
MONSTER_MOVE_RAILS = 1
MONSTER_MOVE_ATTACK = 2

# Constants used for the different directions the player can face
FACING_UP = 0
FACING_LEFT = 1
FACING_DOWN = 2
FACING_RIGHT = 3

# Constants for the different way rails can point
RAIL_LEFT = 1
RAIL_RIGHT = 2
RAIL_UP = 3
RAIL_DOWN = 4

# Set to TRUE to show Player, NPC, and Item hit boxes. Used for debugging
DRAW_HIT_BOXES = False

# The map is made up of three visible layers called base, detail and top
base_layer = [[0]*MAP_WIDTH for i in range(MAP_HEIGHT)]
detail_layer = [[0]*MAP_WIDTH for i in range(MAP_HEIGHT)]
top_layer = [[0]*MAP_WIDTH for i in range(MAP_HEIGHT)]

# Two invsisible layers are used for collision detection and movement on rails
rail_layer = [[0]*MAP_WIDTH for i in range(MAP_HEIGHT)]
collision_layer = [[0]*COLLISION_LAYER_WIDTH for i in range(COLLISION_LAYER_HEIGHT)]

# Variables used to keep track of scrolling through the map as the player moves
scroll_x_offset = 60
scroll_y_offset = 84
scroll_x_counter = 0
scroll_y_counter = 0

#########################################################################################
# Display class. Used for displaying images and text on the screen
#########################################################################################

class Display():
    def __init__ (self, width, height, title="", fps=60):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()

        # Work around a bug in pygame. First window created isn't centred.
        # So it creates a window and the immediately remove it.
        pygame.display.set_mode((100, 100), flags=pygame.HIDDEN)
        pygame.display.quit()

        # Now create the actual game window which will be centred correctly.
        self.__screen = pygame.display.set_mode((width, height))

        self.__fps = fps
        self.__last_time = time.time()
        self.__title = title
        if title != "":
            pygame.display.set_caption (title)
        pygame.font.init()
        self.__font =pygame.font.Font(None,30)
        self.__big_font =pygame.font.SysFont("Arial",50)

    def clear(self, colour=(0,0,0)):
        self.__screen.fill(colour)

    def blit(self, source, dest, area=None, special_flags=0):
        self.__screen.blit (source, dest, area, special_flags)

    def draw_text (self, text, position, colour=(255,255,255), alpha=255):
        textimg=self.__font.render(text, True, colour)
        textimg.set_alpha(alpha)
        self.__screen.blit (textimg, position)

    def draw_text_centred (self, text, position_y, colour=(255,255,255), alpha=255):
        textimg=self.__font.render(text, True, colour)
        position_x = (WINDOW_WIDTH - textimg.get_width())//2
        textimg.set_alpha(alpha)
        self.__screen.blit (textimg, (position_x, position_y))

    def draw_big_text_centred (self, text, position_y, colour=(255,255,255), alpha=255):
        textimg=self.__big_font.render(text, True, colour)
        position_x = (WINDOW_WIDTH - textimg.get_width())//2
        textimg.set_alpha(alpha)
        self.__screen.blit (textimg, (position_x, position_y))

    def draw_line (self, start_pos, end_pos, colour, width=1):
        pygame.draw.line (self.__screen, colour, start_pos, end_pos, width)

    def draw_filled_rect (self, rect, colour):
        pygame.draw.rect (self.__screen, colour, rect)

    def draw_rect (self, rect, colour, line_width=1):
        pygame.draw.rect (self.__screen, colour, rect, line_width)

    def set_clip (self, rect):
        self.__screen.set_clip (rect)

    def get_clip (self):
        return self.__screen.get_clip()

    def update(self):
        pygame.display.update()

        # Limit the game speed to our desired FPS
        current_time = time.time()
        delta = current_time - self.__last_time
        self.__last_time = current_time
        delay = max(1.0/self.__fps - delta, 0)
        time.sleep(delay)

        # Update the window caption to include actual FPS
        fps = 1.0/(delay + delta)
        pygame.display.set_caption("{0}: {1:.2f}".format(self.__title, fps))

#########################################################################################
# GUIManager class. Handles GUI elements such as displaying in game messages
#########################################################################################

class GUIManager():
    def __init__(self):
        self.__message = ""
        self.__message_timer = 0
        self.__alpha = 255
        self.__fade_length = 0

    def display_message(self, message, timer):
        self.__message = message
        self.__message_timer = timer
        self.__alpha = 255
        self.__fade_length = timer//2

    def draw(self):
        if self.__message_timer != 0:
            if self.__message_timer <= self.__fade_length:
                self.__alpha -= (255//self.__fade_length)
            screen.draw_text_centred(self.__message, 250, (255, 255, 255), self.__alpha)
            self.__message_timer -= 1


#########################################################################################
# SpriteSheet class. Used for loading sprite sheet images and displaying sprites
#########################################################################################

class SpriteSheet():
    def __init__(self, image_file, tile_width, tile_height, tiles_across, tiles_down):
        self.__image_file = image_file
        self.__tile_width = tile_width
        self.__tile_height = tile_height
        self.__tiles_across = tiles_across
        self.__tiles_down = tiles_down
        self.__spritesheet_image = pygame.image.load("images/"+image_file)

    def draw(self, screen_x, screen_y, tile_num):
        row = tile_num // self.__tiles_across
        col = tile_num % self.__tiles_down
        px = col * self.__tile_width
        py = row * self.__tile_height
        screen.blit(self.__spritesheet_image, (screen_x, screen_y), Rect(px, py, self.__tile_width, self.__tile_height))

#########################################################################################
# Scene class. Used to ensure moving objects (player, items, NPCs) are drawn in the
#              correct order so they appear in front of or behind each other
#              Uses a binary tree to keep objects in the correct Y order
#########################################################################################

class Scene():
    def __init__(self):
        #The scene is stored in a binary tree which uses 4 empty lists
        self.__object_to_draw = []  #Object to be drawn
        self.__object_y = []        #The object's Y position
        self.__object_left = []     #Index oof the left-hand node
        self.__object_right = []    #Index of the right-hand node

    # Function to add an object to the scene tree
    # Takes the object to be drawn and its Y position on the map
    def add_to_scene(self, leaf_object, leaf_y):
        # ****
        self.__object_to_draw.append(leaf_object)
        self.__object_y.append(leaf_y)
        self.__object_left.append(-1)
        self.__object_right.append(-1)
        new_index = len(self.__object_to_draw)-1
        #If the object is not the first to be added to the tree
        #then add the object to the correct position
        if new_index != 0:
            self.tree(leaf_object, leaf_y, new_index, 0)

    # Recursive function to create the scene tree based on the y-coordinates  of objects
    def tree(self, leaf_object, leaf_y, new_index, node_index):
        if leaf_y <= self.__object_y[node_index]:
            if self.__object_left[node_index] == -1:
                self.__object_left[node_index] = new_index
            else:
                node_index = self.__object_left[node_index]
                self.tree(leaf_object, leaf_y, new_index, node_index)
        else:
            if self.__object_right[node_index] == -1:
                self.__object_right[node_index] = new_index
            else:
                node_index = self.__object_right[node_index]
                self.tree(leaf_object, leaf_y, new_index, node_index)

    # Draws the objects from the tree using in order tree traversal
    # this draws objects from lowest y-coordinate to highest (top of the screen down)
    #****************
    def draw_tree(self, node_index):
        if node_index == -1:
            return
        self.draw_tree(self.__object_left[node_index])
        self.__object_to_draw[node_index].draw()
        self.draw_tree(self.__object_right[node_index])

    def draw(self):
        self.draw_tree(0)
        self.__object_to_draw = []
        self.__object_y = []
        self.__object_left = []
        self.__object_right = []

#########################################################################################
# Item class. Defines an item that the player can pick up, drop or use
#########################################################################################

class Item():
    def __init__(self, item_name, global_x, global_y, base_box, is_getable, item_sheet, sprite_num):
        self.__item_name = item_name
        self.__global_x = global_x
        self.__global_y = global_y
        self.__base_box = base_box
        self.__is_getable = is_getable
        self.__item_sheet = item_sheet
        self.__sprite_num = sprite_num
        self.__ani_count = 1

    def get_x(self):
        return self.__global_x

    def set_x(self, new_x):
        self.__global_x = new_x

    def get_y(self):
        return self.__global_y

    def set_y(self, new_y):
        self.__global_y = new_y

    def get_is_getable(self):
        return self.__is_getable

    def set_is_getable(self, getable_flag):
        self.__is_getable = getable_flag

    def get_name(self):
        return self.__item_name

    def distance_to(self, x, y):
        dx = x - self.__global_x
        dy = y - self.__global_y
        return sqrt(dx*dx + dy*dy)

    def get_base_box(self):
        box = self.__base_box.move(self.__global_x, self.__global_y)
        return box

    def draw(self):
        global frame_count
        if frame_count%7 == 0:
            self.__ani_count = (self.__ani_count + 1)%4
        screen_x = self.__global_x - (scroll_x_offset*TILE_WIDTH)
        screen_y = self.__global_y - (scroll_y_offset*TILE_HEIGHT)
        self.__item_sheet.draw(screen_x-23, screen_y-47, self.__sprite_num + self.__ani_count+1)
        if DRAW_HIT_BOXES:
            show_base_box = self.__base_box.move(screen_x, screen_y)
            screen.draw_rect(show_base_box, (0,255,255))

    def draw_icon(self, screen_x, screen_y):
        self.__item_sheet.draw(screen_x, screen_y, self.__sprite_num)

#########################################################################################
# ItemManager class. Keeps track of all the items in the game and what the player is holding
#                    Handles picking up, dropping and using an item
#########################################################################################

class ItemManager():
    def __init__(self, image_file):
        self.__itemsheet_image = SpriteSheet(image_file, 48, 48, 10, 10)
        self.__items = {}
        self.__ani_count = 0  ##animation frame counter
        self.__inventory = ["Nothing", "Nothing"]
        self.__selected_slot = 0

    def add_item(self, item_name, global_x, global_y, base_box, is_getable, sprite_num):
        self.__items[item_name] = Item(item_name, global_x, global_y, base_box, is_getable, self.__itemsheet_image, sprite_num)

    def get_selected_slot(self):
        return self.__selected_slot

    def set_selected_slot(self, new_selected):
        self.__selected_slot = new_selected

    def distance_to(self, item_name, x, y):
        return self.__items[item_name].distance_to(x, y)

    def get_selected_item(self):
        name = ""
        if self.__selected_slot == 1:
            name = self.__inventory[0]
        elif self.__selected_slot == 2:
            name = self.__inventory[1]
        else:
            name = "Nothing"
        return name

    def get_inventory(self):
        return self.__inventory

    def collide_with_base_box(self, main_box):
        for item in self.__items.values():
            if item.get_base_box().colliderect(main_box):
                return item.get_name()
        return ""

    def pickup(self, player_x, player_y):
        nearest_item_name = "Nothing"
        got_item = "Nothing"
        nearest_item_distance = 99999999
        for item in self.__items.values():  ##for loop to find the item which is closest to the player
            item_name = item.get_name()
            item_x = item.get_x()
            item_y = item.get_y()
            dx = player_x - item_x
            dy = player_y - item_y
            distance = sqrt(dx*dx + dy*dy)  ##Pythagoras theorum to calculate the distance of the current item
            if distance < nearest_item_distance:  ## works out the closest item to the player
                nearest_item_distance = distance
                nearest_item_name = item_name

        if self.__items[nearest_item_name].get_is_getable() == True:
            if nearest_item_distance < 50:
                if self.__inventory[0] == "Nothing":
                    self.__inventory[0] = nearest_item_name
                    self.__items[nearest_item_name].set_x(-100000)
                    got_item = nearest_item_name
                elif self.__inventory[1] == "Nothing":
                    self.__inventory[1] = nearest_item_name
                    self.__items[nearest_item_name].set_x(-100000)
                    got_item = nearest_item_name
            return got_item
        else:
            return "Nothing"

    def use_item(self, player_x, player_y):
        if self.__selected_slot == 0:
            return
        if self.__inventory[self.__selected_slot-1] == "Nothing":
            return
        if self.__inventory[self.__selected_slot-1] == "Empty_Bucket":
            cx = player_x // 16
            cy = player_y // 16
            if collision_layer[cy][cx] == 4:
                self.__inventory[self.__selected_slot-1] = "Filled_Bucket"
                GUI.display_message("You have filled the bucket", 90)
        elif self.__inventory[self.__selected_slot-1] == "Filled_Bucket":
            self.__inventory[self.__selected_slot-1] = "Empty_Bucket"
            fires_put_out = 0
            for item in self.__items.values():  ##for loop to find fire items
                item_name = item.get_name()
                if item_name[0:4] == "Fire":
                    if items.distance_to(item_name, player_x, player_y) < 50:
                        fires_put_out += 1
                        self.__items[item_name].set_x(-100000)
            if fires_put_out == 0:
                GUI.display_message("Water splashes everywhere!", 90)
            elif fires_put_out == 1:
                GUI.display_message("You put out the fire!", 90)
            else:
                GUI.display_message("You put out the fires!", 90)

    def drop(self, player_x, player_y):
        if self.__selected_slot == 0:
            return "Nothing"
        if self.__inventory[self.__selected_slot-1] == "Nothing":
            return "Nothing"
        dropped = self.__inventory[self.__selected_slot-1]
        self.__items[self.__inventory[self.__selected_slot-1]].set_x(player_x)
        self.__items[self.__inventory[self.__selected_slot-1]].set_y(player_y+20)
        self.__inventory[self.__selected_slot-1] = "Nothing"
        return dropped

    def draw(self):
        for item in self.__items.values():
            scene.add_to_scene(item, item.get_y())
            ##item.draw(self.__ani_count + 1)

    def draw_inventory(self):
        if self.__selected_slot == 2:
            screen.draw_filled_rect(Rect(756, 8, 52, 52), (255,0,0))
        screen.draw_filled_rect(Rect(758, 10, 48, 48), (100,100,100))
        if self.__selected_slot == 1:
            screen.draw_filled_rect(Rect(698, 8, 52, 52), (255,0,0))
        screen.draw_filled_rect(Rect(700, 10, 48, 48), (100,100,100))
        if self.__inventory[0] != "Nothing":
            self.__items[self.__inventory[0]].draw_icon(700, 10)
        if self.__inventory[1] != "Nothing":
            self.__items[self.__inventory[1]].draw_icon(758, 10)

#########################################################################################
# NPC class. The parent class for NPCs. Each NPC type inherits and expands this class
#########################################################################################

class NPC():
    def __init__(self, npc_x, npc_y, foot_box, direction, image_file, move_type):
        self.__npc_world_x = npc_x
        self.__npc_world_y = npc_y
        self.__foot_box = foot_box
        self.__npc_screen_x = self.__npc_world_x - (scroll_x_offset*TILE_WIDTH)
        self.__npc_screen_y = self.__npc_world_y - (scroll_y_offset*TILE_HEIGHT)
        self.__direction = direction
        self.__weapon_offset = 0  ##determines what set of sprites are shown (walking/ walking with sword)
        self.__has_sword = False
        self.__ani_count = 0  #animation frame counter
        self.__herosheet_image = SpriteSheet(image_file, 96, 96, 8, 8)
        self._move_type = move_type

    def get_screen_x(self):
        return self.__npc_screen_x

    def get_screen_y(self):
        return self.__npc_screen_y

    def get_world_x(self):
        return self.__npc_world_x

    def get_world_y(self):
        return self.__npc_world_y

    def set_move_type(self, move_type):
        self._move_type = move_type

    def get_move_type(self):
        return self._move_type

    def draw(self):
        self.__npc_screen_x = self.__npc_world_x - (scroll_x_offset*TILE_WIDTH)
        self.__npc_screen_y = self.__npc_world_y - (scroll_y_offset*TILE_HEIGHT)
        self.__herosheet_image.draw(self.__npc_screen_x-47, self.__npc_screen_y-90, self.__direction*8+self.__ani_count + self.__weapon_offset)
        if DRAW_HIT_BOXES:
            show_foot_box = self.__foot_box.move(self.__npc_screen_x, self.__npc_screen_y)
            screen.draw_rect(show_foot_box, (0,255,255))

    def move(self, x, y):
        global frame_count, scroll_x_offset, scroll_y_offset
        if frame_count%3 == 0:
            self.__ani_count = (self.__ani_count + 1)%8
        new_x = self.__npc_world_x
        new_y = self.__npc_world_y

        if x == 1:
            if new_x <= MAP_WIDTH*TILE_WIDTH - 16:
                new_x +=2
            self.__direction = 3
        elif x == -1:
            if new_x >= 16:
                new_x -=2
            self.__direction = 1

        if y == 1:
            if new_y <= MAP_HEIGHT*TILE_HEIGHT - 6:
                new_y +=2
            self.__direction = 2
        elif y == -1:
            if new_y >= 78:
                new_y -=2
            self.__direction = 0

        box = self.__foot_box.move(new_x, new_y)
        if items.collide_with_base_box(box) == "":
            cx = new_x // 16
            cy = new_y // 16
            if collision_layer[cy][cx] == 0 or collision_layer[cy][cx] == 4:
                self.__npc_world_x = new_x
                self.__npc_world_y = new_y
            else:
                self.__ani_count = 7

    # moves the NPC towards the target x and y position
    def move_towards_target(self, target_x, target_y):
        #calculate difference between target position and npc position
        dx = target_x - self.__npc_world_x
        dy = target_y - self.__npc_world_y
        x = 0
        y = 0

        # calculates the direction that the NPC should move
        # the value 8 stops the NPC within 8 pixels from the target
        if dx > 8:
            x = 1
        elif dx < -8:
            x = -1

        if dy > 8:
            y = 1
        elif dy < -8:
            y = -1

        # prevents NPC from walking diagonally
        if x != 0 and y != 0:
            if frame_count % 100 < 50:
                x = 0
            else:
                y = 0
        # move the NPC in the calculated direction
        if x != 0 or y != 0:
            self.move(x, y)

#########################################################################################
# NPCManager class. Parent class for NPC managers which each NPC manager inherits
#                   Uses a dictionary to keep track of the NPCs
#########################################################################################

class NPCManager():
    def __init__(self):
        self._npcs = {}

    def draw(self):
        for npc in self._npcs.values():
            scene.add_to_scene(npc, npc.get_world_y())

    def set_move_type(self, name, move_type):
        self._npcs[name].set_move_type(move_type)

    def update(self):
        for npc in self._npcs.values():
            npc.update()


#########################################################################################
# Person class. Inherits the NPC class and adds movement for villager NPCs.
#########################################################################################

class Person(NPC):
    def __init__(self, npc_x, npc_y, foot_box, direction, image_file, move_type):
        super().__init__(npc_x, npc_y, foot_box, direction, image_file, move_type)
        self.__move_x = 0
        self.__move_y = 0
        self.__timer = 60

    def update(self):
        # Code to make the person wander about the island
        # Makes them either walk in a direction for a random amount of time
        # or stand still for a random amout of time
        if self._move_type == PERSON_MOVE_WANDER:
            self.__timer -= 1
            if self.__timer == 0:
                self.__timer = random.randint(60, 90)
                direction = random.randint(0, 4)
                if direction == 0:
                    self.__move_x = 0
                    self.__move_y = 0
                elif direction == 1:
                    self.__move_x = 0
                    self.__move_y = -1
                elif direction == 2:
                    self.__move_x = -1
                    self.__move_y = 0
                elif direction == 3:
                    self.__move_x = 0
                    self.__move_y = 1
                else:
                    self.__move_x = 1
                    self.__move_y = 0
            if self.__move_x != 0 or self.__move_y != 0:
                super().move(self.__move_x, self.__move_y)
        # Code for getting an NPC to follow the player
        # The player walks towards the square that is behind the player
        elif self._move_type == PERSON_MOVE_FOLLOW:
            facing = player.get_direction()
            dx = 0
            dy = 0
            if facing == FACING_LEFT:
                dx = 1
            elif facing == FACING_RIGHT:
                dx = -1
            elif facing == FACING_UP:
                dy = 1
            elif facing == FACING_DOWN:
                dy = -1
            # target for NPC to move towards is 1 tile behind the player
            target_x = player.get_world_x()+dx*TILE_WIDTH
            target_y = player.get_world_y()+dy*TILE_HEIGHT
            self.move_towards_target(target_x, target_y)


#########################################################################################
# PersonManager class. Class to manage all of the Person NPCs
#                      Inherits the NPCManager class
#########################################################################################

class PersonManager(NPCManager):
    def __init__(self):
        super().__init__()

    def add_person(self, name, x, y, foot_box, direction, image_file, move_type=PERSON_MOVE_NONE):
        self._npcs[name] = Person(x, y, foot_box, direction, image_file, move_type)

#########################################################################################
# Monster class. Inherits the NPC class and adds movement for monster NPCs.
#########################################################################################

class Monster(NPC):
    def __init__(self, npc_x, npc_y, foot_box, direction, image_file, move_type):
        super().__init__(npc_x, npc_y, foot_box, direction, image_file, move_type)

    def update(self):
        # Code for getting an NPC to attack the player
        # The monster tries to get in front of the player
        if self._move_type == MONSTER_MOVE_ATTACK:
            facing = player.get_direction()
            dx = 0
            dy = 0
            if facing == FACING_LEFT:
                dx = -1
            elif facing == FACING_RIGHT:
                dx = 1
            elif facing == FACING_UP:
                dy = -1
            elif facing == FACING_DOWN:
                dy = 1
            # target for monster to move towards is 1 tile in front the player
            target_x = player.get_world_x()+dx*TILE_WIDTH
            target_y = player.get_world_y()+dy*TILE_HEIGHT
            self.move_towards_target(target_x, target_y)
        # Code for moving an NPC along rails
        elif self._move_type == MONSTER_MOVE_RAILS:
            x = self.get_world_x() // TILE_WIDTH
            y = self.get_world_y() // TILE_HEIGHT
            rail = rail_layer[y][x]
            dx = 0
            dy = 0
            if rail == RAIL_LEFT:
                dx = -1
            elif rail == RAIL_RIGHT:
                dx = 1
            elif rail == RAIL_UP:
                dy = -1
            elif rail == RAIL_DOWN:
                dy = 1
            # works out the tile that the current rail is pointing to
            target_x = (x + dx) * TILE_WIDTH + (TILE_WIDTH // 2)
            target_y = (y + dy) * TILE_HEIGHT + (TILE_HEIGHT // 2)
            self.move_towards_target(target_x, target_y)

#########################################################################################
# MonsterManager class. Class to manage all of the Monster NPCs
#                      Inherits the NPCManager class
#########################################################################################

class MonsterManager(NPCManager):
    def __init__(self):
        super().__init__()

    def add_monster(self, name, x, y, foot_box, direction, image_file, move_type=MONSTER_MOVE_NONE):
        self._npcs[name] = Monster(x, y, foot_box, direction, image_file, move_type)

#########################################################################################
# Player class. Functions for drawing the player and moving them about the map
#########################################################################################

class Player():
    def __init__(self, player_x, player_y, foot_box, direction, image_file):
        self.__player_world_x = player_x
        self.__player_world_y = player_y
        self.__foot_box = foot_box
        self.__player_screen_x = self.__player_world_x - (scroll_x_offset*TILE_WIDTH)
        self.__player_screen_y = self.__player_world_y - (scroll_y_offset*TILE_HEIGHT)
        self.__direction = direction
        self.__weapon_offset = 0  ##determines what set of sprites are shown (walking/ walking with sword)
        self.__has_sword = False
        self.__ani_count = 0  #animation frame counter
        self.__herosheet_image = SpriteSheet(image_file, 96, 96, 8, 8)

    def get_screen_x(self):
        return self.__player_screen_x

    def get_screen_y(self):
        return self.__player_screen_y

    def get_world_x(self):
        return self.__player_world_x

    def get_world_y(self):
        return self.__player_world_y

    def set_has_sword(self, has_sword):
        self.__has_sword = has_sword
        if self.__has_sword == True:
            self.__weapon_offset = 32
        else:
            self.__weapon_offset = 0

    def get_direction(self):
        return self.__direction

    def draw(self):
        self.__player_screen_x = self.__player_world_x - (scroll_x_offset*TILE_WIDTH)
        self.__player_screen_y = self.__player_world_y - (scroll_y_offset*TILE_HEIGHT)
        self.__herosheet_image.draw(self.__player_screen_x-47, self.__player_screen_y-90, self.__direction*8+self.__ani_count + self.__weapon_offset)
        if DRAW_HIT_BOXES:
            show_foot_box = self.__foot_box.move(self.__player_screen_x, self.__player_screen_y)
            screen.draw_rect(show_foot_box, (0,255,255))

    def move(self, x, y):
        global frame_count, scroll_x_offset, scroll_y_offset

        if frame_count % 3 == 0:
            self.__ani_count = (self.__ani_count + 1) % 8

        new_x = self.__player_world_x
        new_y = self.__player_world_y

        if x == 1:
            if new_x <= MAP_WIDTH*TILE_WIDTH - 16:
                new_x += 3
            self.__direction = 3
        elif x == -1:
            if new_x >= 16:
                new_x -= 3
            self.__direction = 1

        if y == 1:
            if new_y <= MAP_HEIGHT*TILE_HEIGHT - 6:
                new_y += 3
            self.__direction = 2
        elif y == -1:
            if new_y >= 78:
                new_y -= 3
            self.__direction = 0

        # Check the collision map to see if the player can move to the new position
        # Also used to see if the player has stepped on a teleport square and move
        # them the new location if they have.

        box = self.__foot_box.move(new_x, new_y)
        if items.collide_with_base_box(box) == "":
            cx = new_x // 16
            cy = new_y // 16
            if collision_layer[cy][cx] == 0 or collision_layer[cy][cx] == 4:
                self.__player_world_x = new_x
                self.__player_world_y = new_y
            elif collision_layer[cy][cx] == 2:              # Teleport Yellow 1
                self.__player_world_x = 5232
                self.__player_world_y = 470
                scroll_x_offset = 98
                scroll_y_offset = 0
            elif collision_layer[cy][cx] == 3:              # Teleport Purple 1
                self.__player_world_x = 1080
                self.__player_world_y = 1752
                scroll_x_offset = 12
                scroll_y_offset = 28
            elif collision_layer[cy][cx] == 5:              # Teleport Yellow 2
                self.__player_world_x = 108*48
                self.__player_world_y = 100*48+20
                scroll_x_offset = 104
                scroll_y_offset = 97
            elif collision_layer[cy][cx] == 6:              # Teleport Purple 2
                self.__player_world_x = 1080
                self.__player_world_y = 1752
                scroll_x_offset = 12
                scroll_y_offset = 28
            else:
                self.__ani_count = 7

#########################################################################################
# Map class. Used for loading the map layers, generating the maze and drawing the map
#########################################################################################

class Map():
    def __init__(self, map_top_x, map_top_y, view_height, view_width, image_file):
        self.__map_view_height = view_height
        self.__map_view_width = view_width
        self.__map_top_x = map_top_x
        self.__map_top_y = map_top_y
        self.__tiles_image = SpriteSheet(image_file, TILE_WIDTH, TILE_HEIGHT, 15, 15)
        self.__maze = [[0]*MAZE_WIDTH for i in range(MAZE_HEIGHT)]

    def get_screen_height(self):
        return self.__map_view_height

    def get_screen_width(self):
        return self.__map_view_width

    def get_top_x(self):
        return self.__map_top_x

    def get_top_y(self):
        return self.__map_top_y

    # Generate a random maze. Uses a stack to keep track of visited cells.
    def generate_maze(self):
        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                self.__maze[y][x] = False

        mx = 1
        my = 5
        stack = []
        self.__maze[my][mx]=0
        stack.append((mx,my))

        while len(stack) != 0:
            (mx,my) = stack.pop()

            neighbours=[]
            # check if any of the current cell neighbours are unvisited
            if mx > 1 and self.__maze[my][mx-2] == False:
                neighbours.append((-1,0))
            if mx < (MAZE_WIDTH-2) and self.__maze[my][mx+2] == False:
                neighbours.append((1,0))
            if my > 1 and self.__maze[my-2][mx] == False:
                neighbours.append((0,-1))
            if my < (MAZE_HEIGHT-2) and self.__maze[my+2][mx] == False:
                neighbours.append((0,1))

            if len(neighbours) != 0:
                (dx,dy) = random.choice (neighbours)
                stack.append((mx,my))
                self.__maze[my+dy][mx+dx] = True
                self.__maze[my+dy+dy][mx+dx+dx] = True
                stack.append((mx+dx+dx,my+dy+dy))

        # Add in an entrance and exit to the maze
        self.__maze[15][0] = True
        self.__maze[15][1] = True
        self.__maze[1][15] = True
        self.__maze[0][15] = True

        # Now add the generated maze into the map layers
        maze_position_x = 107
        maze_position_y = 85

        for y in range(MAZE_HEIGHT):
            for x in range(MAZE_WIDTH):
                if self.__maze[y][x] == True:
                    base_layer[y+maze_position_y][x+maze_position_x] = 1
                else:
                    base_layer[y+maze_position_y][x+maze_position_x] = 1
                    detail_layer[y+maze_position_y][x+maze_position_x] = 80
                    for i in range(3):
                        for j in range(5):
                            collision_layer[(y+maze_position_y)*3+i][(x+maze_position_x)*3+j-1] = 1

    # Load the map from a CSV file
    def load(self):
        csv_file = open("map.txt", "r")
        csv_reader = csv.reader(csv_file)
        dimensions = next(csv_reader)
        width = int(dimensions[0])
        height = int(dimensions[1])
        #print("width: {}, height: {}".format(width, height))
        for y in range(height):
            row = next(csv_reader)
            #print(row)
            for x in range(width):
               base_layer[y][x] = int(row[x])
        for y in range(height):
            row = next(csv_reader)
            #print(row)
            for x in range(width):
               detail_layer[y][x] = int(row[x])
        for y in range(height):
            row = next(csv_reader)
            #print(row)
            for x in range(width):
               top_layer[y][x] = int(row[x])
        for y in range(height*3):
            row = next(csv_reader)
            #print(row)
            for x in range(width*3):
               collision_layer[y][x] = int(row[x])
        for y in range(height):
            row = next(csv_reader)
            #print(row)
            for x in range(width):
               rail_layer[y][x] = int(row[x])
        csv_file.close()

    def draw_tile(self, tile_num, screen_x, screen_y):
        self.__tiles_image.draw(screen_x, screen_y, tile_num)

    def draw(self, draw_top):
        for y in range(self.__map_view_height):
            for x in range(self.__map_view_width):
                if draw_top == False:
                    tile_num = base_layer[y+scroll_y_offset][x+scroll_x_offset]
                    self.draw_tile(tile_num, self.__map_top_x + x*TILE_WIDTH, self.__map_top_x+ y*TILE_HEIGHT)
                    tile_num = detail_layer[y+scroll_y_offset][x+scroll_x_offset]
                    if tile_num != 0 :
                        self.draw_tile(tile_num, self.__map_top_x + x*TILE_WIDTH, self.__map_top_x+ y*TILE_HEIGHT)
                else:
                    tile_num = top_layer[y+scroll_y_offset][x+scroll_x_offset]
                    if tile_num != 0 :
                        self.draw_tile(tile_num, self.__map_top_x + x*TILE_WIDTH, self.__map_top_x+ y*TILE_HEIGHT)

#########################################################################################
# MenuButton class. Handles buttons on the opening menu screen
#########################################################################################

class MenuButton():
    def __init__(self, label, box):
        self.__label = label
        self.__box = box

    def draw(self):
        screen.draw_filled_rect(self.__box, (255, 255, 255))
        screen.draw_big_text_centred(self.__label, self.__box.y + 10, (0,0,0))
        mouse_pos = pygame.mouse.get_pos()
        if self.__box.collidepoint(mouse_pos):
            screen.draw_rect(self.__box, (255,0,0), 2)

    def is_pressed(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.__box.collidepoint(mouse_pos):
            return True
        else:
            return False

#########################################################################################
# MenuScreen class. Draws the opening menu and handles the selection made
#########################################################################################

class MenuScreen():
    def __init__(self):
        self.__in_menu = True
        self.__logo_image = SpriteSheet("logo.png", 558, 100, 1, 1)
        self.__start_button = MenuButton("Start Game", Rect(138, 165, 540, 80))
        self.__options_button = MenuButton("Options", Rect(138, 265, 540, 80))
        self.__credits_button = MenuButton("Credits", Rect(138, 365, 540, 80))

    def menu_main(self):
        screen.clear((143,210,255))
        self.__logo_image.draw(129, 30, 0)
        while self.__in_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__in_menu = False
                elif event.type == pygame.KEYDOWN:
                    self.menu_key_down(event.key, event.mod)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.menu_mouse_down(event.pos, event.button)

            self.__start_button.draw()
            self.__options_button.draw()
            self.__credits_button.draw()
            screen.update()

    def menu_key_down(self, key, mod):
        if key == keys.SPACE:
            self.__in_menu = False

    def menu_mouse_down(self, pos, button):
        if button == mouse.LEFT:
            if self.__start_button.is_pressed():
                self.__in_menu = False

#########################################################################################
# Function to handle key presses
#########################################################################################

def on_key_down(key, mod):

    if key == keys.E:
        item_got = items.pickup(player.get_world_x(), player.get_world_y())  ##calls pickup function
        print(item_got)
        print(items.get_inventory())
        ##if item_got == "Sword":   ##checks if the picked up item was a sword
            ##player.set_has_sword(True)

    if key == keys.Q:
        item_dropped = items.drop(player.get_world_x(), player.get_world_y())
        print(items.get_inventory())
        if item_dropped == "Sword":
            player.set_has_sword(False)

    if key == keys.K_1:
        if items.get_selected_slot() == 1:
            items.set_selected_slot(0)
        else:
            items.set_selected_slot(1)

    if key == keys.K_2:
        if items.get_selected_slot() == 2:
            items.set_selected_slot(0)
        else:
            items.set_selected_slot(2)

    if items.get_selected_item() == "Sword":
        player.set_has_sword(True)
    else:
        player.set_has_sword(False)

#########################################################################################
# Function to handle mouse button presses
#########################################################################################

def on_mouse_down(pos, button):
    if button == mouse.RIGHT:
        items.use_item(player.get_world_x(), player.get_world_y())


#########################################################################################
# Function to handle mouse button up events.
#########################################################################################

def on_mouse_up(pos, button):
    pass


#########################################################################################
# The game draw function that draws everything in the running game
#########################################################################################

def draw():
    screen.clear()
    game_map.draw(False)
    items.draw()
    scene.add_to_scene(player, player.get_world_y())
    people_npcs.draw()
    monster_npcs.draw()
    scene.draw()
    game_map.draw(True)
    items.draw_inventory()
    GUI.draw()

#########################################################################################
# Function to update everything when the game is playing
#########################################################################################

def update():
    global scroll_x_offset, scroll_y_offset, scroll_x_counter, scroll_y_counter
    keys=pygame.key.get_pressed()

    # If the screen needs scrolling then keep scrolling it
    if scroll_x_counter > 0:
        scroll_x_counter -= 1
        if scroll_x_offset < MAP_WIDTH-game_map.get_screen_width():
            scroll_x_offset += 1
        return

    if scroll_x_counter < 0:
        scroll_x_counter += 1
        if scroll_x_offset > 0:
            scroll_x_offset -= 1
        return

    if scroll_y_counter > 0:
        scroll_y_counter -= 1
        if scroll_y_offset<MAP_HEIGHT-game_map.get_screen_height():
            scroll_y_offset += 1
        return

    if scroll_y_counter < 0:
        scroll_y_counter += 1
        if scroll_y_offset > 0:
            scroll_y_offset -= 1
        return

    # Check for the WSAD movment keys
    if keys[K_w]:
        player.move(0, -1)
    elif keys[K_s]:
        player.move(0, 1)
    elif keys[K_a]:
        player.move(-1, 0)
    elif keys[K_d]:
        player.move(1, 0)

    # If the player reaches the edge of the screen then
    # set the screen to be scrolled.

    player_sx = player.get_screen_x()
    player_sy = player.get_screen_y()
    if player_sx >= 720:
        scroll_x_counter += min(12, (MAP_WIDTH-game_map.get_screen_width())-scroll_x_offset)

    if player_sx <= 96:
        scroll_x_counter -= min(12, scroll_x_offset)

    if player_sy >= 480:
        scroll_y_counter += min(7, (MAP_HEIGHT-game_map.get_screen_height())-scroll_y_offset)

    if player_sy <= 96:
        scroll_y_counter -= min(7, scroll_y_offset)

    # Update all the NPCs
    people_npcs.update()
    monster_npcs.update()

#########################################################################################
# Startup function to create all the game objects
#########################################################################################

def startup():
    global game_map, player, people_npcs, monster_npcs, items, scene, GUI

    # Load the map and generate the maze
    game_map = Map(0, 0, 11, 17, "tilesheet.png")
    game_map.load()
    game_map.generate_maze()

    # Create a Player object
    player = Player(PLAYER_START_X, PLAYER_START_Y, Rect(-15, -10, 33, 15), 2, "herosheet.png")

    # Create a PersonManager object and add the villagers to the game
    people_npcs = PersonManager()
    people_npcs.add_person("old_man", 1396, 1876, Rect(-15, -10, 33, 15), 2, "oldman.png")
    people_npcs.add_person("lady", 50*TILE_WIDTH+24, 83*TILE_HEIGHT+24, Rect(-15, -10, 33, 15), 2, "lady.png", PERSON_MOVE_WANDER)
    people_npcs.add_person("kid", 68*TILE_WIDTH, 83*TILE_HEIGHT, Rect(-15, -10, 33, 15), 2, "kid.png", PERSON_MOVE_FOLLOW)
    people_npcs.add_person("blacksmith", 70*TILE_WIDTH, 86*TILE_HEIGHT, Rect(-15, -10, 33, 15), 2, "blacksmith.png")
    people_npcs.set_move_type("blacksmith", PERSON_MOVE_WANDER)

    # Create a MonsterManager object and add the monsters to the game
    monster_npcs = MonsterManager()
    monster_npcs.add_monster("orc", 55*TILE_WIDTH+24, 83*TILE_HEIGHT+24, Rect(-15, -10, 33, 15), 2, "orc.png", MONSTER_MOVE_RAILS)

    # Create an object for the GUI
    GUI = GUIManager()

    # Create an object for the scene tree
    scene = Scene()

    # Create an ItemManager object and add all the items to the game
    items = ItemManager("items.png")
    items.add_item("Sword", 1296, 1600, Rect(-15, -13, 16, 8), True, 0)
    items.add_item("Empty_Bucket", 1344, 1625, Rect(-15, -13, 31, 15), True, 10)
    items.add_item("Filled_Bucket", -100000, -100000, Rect(-15, -13, 31, 15), True, 15)
    items.add_item("Axe", 1296, 1650, Rect(-15, -11, 12, 8), True, 5)
    items.add_item("Fire1", 1400 , 1700, Rect(-20, -44, 43, 47), False, 20)
    items.add_item("Fire2", 1400 , 1735, Rect(-20, -44, 43, 47), False, 20)


#########################################################################################
# Main game function
#########################################################################################

def game_main():
    global frame_count, screen

    screen = Display(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, GAME_FPS)
    startup()
    menu = MenuScreen()
    menu.menu_main()

    frame_count = 0
    playing = True
    while playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                on_mouse_down(event.pos, event.button)
            elif event.type == pygame.MOUSEBUTTONUP:
                on_mouse_up(event.pos, event.button)
            elif event.type == pygame.KEYDOWN:
                on_key_down(event.key, event.mod)

        update()
        draw()
        screen.update()
        frame_count += 1


game_main()
pygame.quit()
sys.exit()
