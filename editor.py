import sys
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

# Define the rendering scale (used to upscale the game view)
RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up the window title and display dimensions
        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((640, 480))  # Main window
        self.display = pygame.Surface((320, 240))  # Scaled-down surface for rendering

        # Initialize the game clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Load tile assets into categorized groups
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'spawners': load_images('tiles/spawners'),
        }
        
        # Movement state: [left, right, up, down]
        self.movement = [False, False, False, False]
        
        # Initialize the tilemap object with a tile size of 16 pixels
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Try loading an existing map file, if it exists
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass
        
        # Initial camera scroll (viewport offset)
        self.scroll = [0, 0]
        
        # List of tile categories and selected tile states
        self.tile_list = list(self.assets)  # ['decor', 'grass', ...]
        self.tile_group = 0  # Index of selected tile group
        self.tile_variant = 0  # Index of selected tile variant
        
        # Interaction flags
        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True  # Whether tiles are placed on a grid or freely
        
    def run(self):
        # Main game loop
        while True:
            # Clear the display with a black background
            self.display.fill((0, 0, 0))
            
            # Adjust the scroll based on movement inputs
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))  # Integer offset
            
            # Render the tilemap with the current scroll offset
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Get the current tile image and make it semi-transparent for preview
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)
            
            # Get the mouse position, scaled to the rendering surface
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            
            # Calculate the tile grid position under the mouse
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size)
            )
            
            # Render the preview tile at the correct position
            if self.ongrid:  # Snap to grid
                self.display.blit(
                    current_tile_img,
                    (tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                     tile_pos[1] * self.tilemap.tile_size - self.scroll[1])
                )
            else:  # Free placement
                self.display.blit(current_tile_img, mpos)
            
            # Handle left-click (place tiles)
            if self.clicking and self.ongrid:
                self.tilemap.tilemap[f"{tile_pos[0]};{tile_pos[1]}"] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': tile_pos
                }
            
            # Handle right-click (remove tiles)
            if self.right_clicking:
                # Remove grid-aligned tiles
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                
                # Remove free-placed tiles
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(
                        tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1],
                        tile_img.get_width(), tile_img.get_height()
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            
            # Display the currently selected tile in the top-left corner
            self.display.blit(current_tile_img, (5, 5))
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Quit the editor
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.clicking = True
                        if not self.ongrid:  # Free placement mode
                            self.tilemap.offgrid_tiles.append({
                                'type': self.tile_list[self.tile_group],
                                'variant': self.tile_variant,
                                'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])
                            })
                    if event.button == 3:  # Right mouse button
                        self.right_clicking = True
                    if self.shift:  # Shift + scroll to change variants
                        if event.button == 4:  # Scroll up
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:  # Scroll down
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:  # Scroll to change tile groups
                        if event.button == 4:  # Scroll up
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:  # Scroll down
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button released
                        self.clicking = False
                    if event.button == 3:  # Right mouse button released
                        self.right_clicking = False
                        
                if event.type == pygame.KEYDOWN:
                    # Movement keys
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:  # Toggle grid snapping
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:  # Apply autotile
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:  # Save the map
                        self.tilemap.save('map.json')
                    if event.key == pygame.K_LSHIFT:  # Hold shift
                        self.shift = True
                if event.type == pygame.KEYUP:
                    # Release movement keys
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:  # Release shift
                        self.shift = False
            
            # Scale the display surface to the main screen and update
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            
            # Maintain 60 frames per second
            self.clock.tick(60)

# Run the editor
Editor().run()
