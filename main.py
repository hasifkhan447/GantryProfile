import pygame
# Pixel speed into real speed? How do we convert this?
# I will determine my mapping so that 1m: 100

global dim, onem
dim = 800
onem = 100 #100px/1m 
size = dim/onem


def px2m(quantity_px):
    global onem
    quantity_m = quantity_px/onem 
    return quantity_m

def m2px(quantity_px):
    global onem
    quantity_m = quantity_px*onem 
    return quantity_m


class Structure(): 
    OUTLINE_THICKNESS_REAL = 0.025  # 2.5cm in meters
    def __init__(self, x_len_real, y_len_real, pos_x_real, pos_y_real):
        self.x_len_px = m2px(x_len_real) # This is in px
        self.y_len_px = m2px(y_len_real) # This is in px
        self.outline_px = m2px(self.OUTLINE_THICKNESS_REAL)

        self.pos_x_real = pos_x_real
        self.pos_y_real = pos_y_real
        self.pos_x_px = m2px(self.pos_x_real)
        self.pos_y_px = m2px(self.pos_y_real)

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
    def __init__(self, x_len_real, y_len_real, mass, pos_x_real = 0, pos_y_real = 0, name="MW", rotate=True):
        self.x_len_real = x_len_real # This is in m 
        self.y_len_real = y_len_real # This is in m

        if rotate==True:
            self.x_len_px = m2px(self.y_len_real)
            self.y_len_px = m2px(self.x_len_real)
        else:
            self.x_len_px = m2px(self.x_len_real)
            self.y_len_px = m2px(self.y_len_real)


        self.pos_x_real = pos_x_real
        self.pos_y_real = pos_y_real
        self.pos_x_px = m2px(self.pos_x_real)
        self.pos_y_px = m2px(self.pos_y_real)


        self.mass = mass # This is in m 

        self.name = name

    def draw(self, screen):
        draw_x = int(self.pos_x_px - self.x_len_px/2)
        draw_y = int(self.pos_y_px - self.y_len_px/2)
        rect = pygame.Rect(draw_x, draw_y, int(self.x_len_px), int(self.y_len_px))
        pygame.draw.rect(screen, (60, 60, 80), rect)
        font = pygame.font.SysFont(None, 16)
        label = font.render(self.name, True, (200, 200, 200))
        screen.blit(label, (int(draw_x) + 2, int(draw_y) + int(self.y_len_px) // 2 - 8))



class Line():
    """Assembly line. Owns objects on it and moves them forward each tick."""
    def __init__(self, pos_y_real=8, height_real=80, speed_real=0.30):
        self.height_real = height_real
        self.height_px = m2px(self.height_real)

        self.speed_real = speed_real   # m/s
        self.speed_px = m2px(self.speed_real)  # px/s



        self.pos_y_real = pos_y_real
        self.pos_y_px = m2px(self.pos_y_real)


        self.height_real = height_real
        self.height_px = m2px(self.height_real)

        self.objects: list[Object] = []

        self.stopped = False







    def update(self, dt):
        if not self.stopped:
            dt_s = dt / 1000.0
            for obj in self.objects:
                obj.pos_x_px += self.speed_px * dt_s
            # Remove objects that have left the screen
            self.objects = [o for o in self.objects if o.pos_x_px < dim + 100]

    def toggle(self):
        self.stopped = not self.stopped

    def add(self, obj: Object, start_x_m=0.0): # Start_x is in m 
        obj.pos_x_px = m2px(int(start_x_m))
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

    gantry = Structure(x_len_real=3.5, y_len_real=4, pos_x_real=4, pos_y_real=4)
    tape_closing = Structure(x_len_real=1, y_len_real=1, pos_x_real=4.3, pos_y_real=4)

    microwave = Object(x_len_real=0.67, y_len_real=0.58, mass = 40, name ="MW")
    thermocol = Object(x_len_real=0.67, y_len_real=0.58, mass = 1, name ="thermocol")
    packaging = Object(x_len_real=0.67, y_len_real=0.58, mass = 1, name ="package")
    line = Line(pos_y_real=int(8/2), height_real=1)

    line.add(thermocol, start_x_m=0.05)
    line.add(packaging, start_x_m=thermocol.x_len_real + 0.05)
    line.add(microwave, start_x_m=thermocol.x_len_real + packaging.x_len_real + 0.05)

    # I need my end effector to slave itself to certain positions, and then go not from fixed points but to other points, and it should collect data on its profile


    # TODO: We will phase the collection into a few steps 
    # 1. We will first "move" directly to the position, and calculate the total x,y,z displacement
    # 2. We will secondly "move" according to a specified profile, by anticipating where to move based on the speed of the line (which we know)


    while running: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False 

        dt = clock.tick(60)

        screen.fill("purple")


        line.draw(screen)
        gantry.draw(screen)
        tape_closing.draw(screen)

        line.update(dt)



        pygame.display.flip()



if __name__ == "__main__":
    main()
