import pygame
# Pixel speed into real speed? How do we convert this?
# I will determine my mapping so that 1m: 100

global dim, onem
dim = 800
onem = 100 #100px/1m 


def px2m(quantity_px):
    global onem
    quantity_m = quantity_px/onem 
    return quantity_m

def m2px(quantity_px):
    global onem
    quantity_m = quantity_px*onem 
    return quantity_m


#TODO: Need some kind of drawing functionality for each of these
class Gantry(): #TODO: Show a kind of grayed out, dotted line around the line with the dimensions
    OUTLINE_THICKNESS_REAL = 0.025  # 2.5cm in meters
    def __init__(self, x_len_real, y_len_real, pos_x_px, pos_y_px):
        self.x_len_px = m2px(x_len_real) # This is in px
        self.y_len_px = m2px(y_len_real) # This is in px
        self.outline_px = m2px(self.OUTLINE_THICKNESS_REAL)
        self.pos_x_px = pos_x_px
        self.pos_y_px = pos_x_px

    def draw(self, screen):
        color = (180, 180, 180)
        t = self.outline_px
        x, y, w, h = self.pos_x_px - self.x_len_px/2, self.pos_y_px - self.y_len_px/2, self.x_len_px, self.y_len_px

        # Top, bottom, left, right bars
        pygame.draw.rect(screen, color, pygame.Rect(x,         y,         w, t))  # top
        pygame.draw.rect(screen, color, pygame.Rect(x,         y + h - t, w, t))  # bottom
        pygame.draw.rect(screen, color, pygame.Rect(x,         y,         t, h))  # left
        pygame.draw.rect(screen, color, pygame.Rect(x + w - t, y,         t, h))  # right





# This is an object with mass 
class Object():
    def __init__(self, x_len_real, y_len_real, pos_x_px, pos_y_px, mass):
        self.x_len_real = x_len_real # This is in m 
        self.y_len_real = y_len_real # This is in m

        self.x_len_px = m2px(self.x_len_real)
        self.y_len_px = m2px(self.y_len_real)

        self.pos_x_px = pos_x_px
        self.pos_y_px = pos_y_px

        self.mass = mass # This is in m 

    def draw(self, screen):
        draw_x = int(self.pos_x_px - self.x_len_px/2)
        draw_y = int(self.pos_y_px - self.y_len_px/2)
        rect = pygame.Rect(draw_x, draw_y, int(self.x_len_px), int(self.y_len_px))
        pygame.draw.rect(screen, (60, 60, 80), rect)
        font = pygame.font.SysFont(None, 16)
        label = font.render("MW", True, (200, 200, 200))
        screen.blit(label, (int(draw_x) + 2, int(draw_y) + int(self.y_len_px) // 2 - 8))



class Line():
    """Assembly line. Owns objects on it and moves them forward each tick."""
    def __init__(self, pos_y_px=800, height_real=80):
        self.height_real = height_real

        self.height_px = m2px(self.height_real)
        self.speed_real = 1.5   # m/s
        self.speed_px = m2px(self.speed_real)  # px/s
        self.pos_y_px = pos_y_px 

        self.height_real = height_real
        self.height_px = m2px(self.height_real)

        self.objects: list[Object] = []

    def update(self, dt):
        dt_s = dt / 1000.0
        for obj in self.objects:
            obj.pos_x_px += self.speed_px * dt_s
        # Remove objects that have left the screen
        self.objects = [o for o in self.objects if o.pos_x_px < dim + 100]

    def add(self, obj: Object, start_x=0.0):
        obj.pos_x_px = float(start_x)
        obj.pos_y_px = self.pos_y_px # Center object vertically
        self.objects.append(obj)

    def remove(self, obj: Object):
        self.objects.remove(obj)
 
    def draw(self, screen):
        # Belt
        pygame.draw.rect(screen, (40, 120, 40), pygame.Rect(0, self.pos_y_px - self.height_px/2, dim, self.height_px))
        for obj in self.objects:
            obj.draw(screen)
 
        # Speed label
        font = pygame.font.SysFont(None, 20)
        label = font.render(f"Belt: {self.speed_real} m/s", True, (220, 255, 220))
        screen.blit(label, (8, self.pos_y_px + self.height_px/2 + 4))



def main(): 
    pygame.init()
    screen = pygame.display.set_mode((dim, dim))
    clock = pygame.time.Clock()
    running = True 

    gantry = Gantry(x_len_real=3, y_len_real=3, pos_x_px=dim/2, pos_y_px=dim/2)
    microwave = Object(x_len_real=0.67, y_len_real=0.58, pos_x_px = 100, pos_y_px = 100, mass = 40)
    line = Line(pos_y_px=int(dim/2), height_real=1)

    line.add(microwave)

    while running: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False 

        dt = clock.tick(60)

        screen.fill("purple")


        gantry.draw(screen)
        line.draw(screen)

        line.update(dt)



        pygame.display.flip()



if __name__ == "__main__":
    main()
