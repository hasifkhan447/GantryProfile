import pygame
import math
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











# This is an object with mass 
class Object():
    def __init__(self, x_len_real: float, y_len_real : float, mass, pos_x_real = 0.0, pos_y_real = 0.0, name="MW", rotate=True):
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


        self.mass = mass # This is in m 

        self.name = name

    def pos_x_px(self):
        return m2px(self.pos_x_real)

    def pos_y_px(self):
        return m2px(self.pos_y_real)

    def draw(self, screen):
        draw_x = int(self.pos_x_px() - self.x_len_px/2)
        draw_y = int(self.pos_y_px() - self.y_len_px/2)
        rect = pygame.Rect(draw_x, draw_y, int(self.x_len_px), int(self.y_len_px))
        pygame.draw.rect(screen, (60, 60, 80), rect)
        font = pygame.font.SysFont(None, 16)
        label = font.render(self.name, True, (200, 200, 200))
        screen.blit(label, (int(draw_x) + 2, int(draw_y) + int(self.y_len_px) // 2 - 8))


class Structure(): 
    OUTLINE_THICKNESS_REAL = 0.025  # 2.5cm in meters
    def __init__(self, x_len_real, y_len_real, pos_x_real, pos_y_real):
        self.x_len_real = x_len_real
        self.y_len_real = y_len_real
        self.x_len_px = m2px(x_len_real) # This is in px
        self.y_len_px = m2px(y_len_real) # This is in px
        self.outline_px = m2px(self.OUTLINE_THICKNESS_REAL)

        self.pos_x_real = pos_x_real
        self.pos_y_real = pos_y_real


    def pos_x_px(self):
        return m2px(self.pos_x_real)

    def pos_y_px(self):
        return m2px(self.pos_y_real)

    def draw(self, screen):
        color = (180, 180, 180)
        t = self.outline_px
        x, y, w, h = self.pos_x_px() - self.x_len_px/2, self.pos_y_px() - self.y_len_px/2, self.x_len_px, self.y_len_px

        # Top, bottom, left, right bars
        pygame.draw.rect(screen, color, pygame.Rect(x,         y,         w, t))  # top
        pygame.draw.rect(screen, color, pygame.Rect(x,         y + h - t, w, t))  # bottom
        pygame.draw.rect(screen, color, pygame.Rect(x,         y,         t, h))  # left
        pygame.draw.rect(screen, color, pygame.Rect(x + w - t, y,         t, h))  # right


    def contains(self, target_x, target_y):

        half_w = self.x_len_real / 2
        half_h = self.y_len_real / 2
        # Check if the coordinates are within the left/right and top/bottom bounds
        return (self.pos_x_real - half_w <= target_x <= self.pos_x_real + half_w and
                self.pos_y_real - half_h <= target_y <= self.pos_y_real + half_h)





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
                obj.pos_x_real += self.speed_real * dt_s
            # Remove objects that have left the screen
            self.objects = [o for o in self.objects if o.pos_x_px() < dim + 100]

    def toggle(self):
        self.stopped = not self.stopped

    def add(self, obj: Object, start_x_m=0.0): # Start_x is in m 
        obj.pos_x_real = start_x_m
        obj.pos_y_real = self.pos_y_real
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

class EndEffector:
    def __init__(self, x_m, y_m, structure):
        self.x_m = x_m
        self.y_m = y_m 
        self.vx_m = 0
        self.vy_m = 0
        self.objects: list[Object] = []
        self.error_sum_x = 0
        self.error_sum_y = 0

        self.structure = structure;

    def update(self, dt, target_x_m, target_y_m):
        dt_s = dt / 1000.0
        if dt_s <= 0: return
        if ( not self.structure.contains(target_x_m, target_y_m)): return 


        # 1. Calculate current Error
        error_x = target_x_m - self.x_m
        error_y = target_y_m - self.y_m

        # 2. Update Integral (Accumulated Error)
        self.error_sum_x += error_x * dt_s
        self.error_sum_y += error_y * dt_s

        # 3. PI Constants
        # Kp is the "snap" (Proportional)
        # Ki is the "force" to close the final gap (Integral)
        kp = 5.0  
        ki = 1.5  

        # 4. Calculate Velocity Output
        self.vx = (kp * error_x) + (ki * self.error_sum_x)
        self.vy = (kp * error_y) + (ki * self.error_sum_y) 

        # 5. Apply Movement
        self.x_m += self.vx * dt_s 
        self.y_m += self.vy * dt_s

        # 6. Update held objects
        for obj in self.objects:
            obj.pos_x_real = self.x_m
            obj.pos_y_real = self.y_m




    def add(self, obj: Object): # Start_x is in m 
        self.objects.append(obj)


    def pick(self, obj: Object, line: Line):
        if (obj in line.objects):
            line.remove(obj)
        self.add(obj)

    def place(self, obj: Object, reciever : Line | None = None): 
        if reciever == None: 
            obj.pos_x_real = self.x_m
            obj.pos_y_real = self.y_m 
        else: 
            self.objects.remove(obj)
            reciever.add(obj, start_x_m = self.x_m)

    def draw(self, screen):
        for obj in self.objects:
            obj.draw(screen)
        pygame.draw.circle(screen, (100,0,0), (m2px(self.x_m), m2px(self.y_m)), 5)

    def is_close(self, obj: Object):
        if math.sqrt((obj.pos_x_real - self.x_m)**2 + (obj.pos_y_real - self.y_m)**2) < 1e-1:
            return True 
        else:
            return False


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

    ee = EndEffector(gantry.pos_x_real, gantry.pos_y_real, gantry)

    line.add(thermocol, start_x_m=0.05)
    line.add(packaging, start_x_m=thermocol.x_len_real + 0.05)
    line.add(microwave, start_x_m=thermocol.x_len_real + packaging.x_len_real + 0.05)

    # I need my end effector to slave itself to certain positions, and then go not from fixed points but to other points, and it should collect data on its profile
    state = "IDLE"

    while running: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False 

        dt = clock.tick(60)

        screen.fill("purple")



        target_x, target_y = ee.x_m, ee.y_m
        match state:
            case "IDLE":
                if gantry.contains(microwave.pos_x_real, microwave.pos_y_real):
                    state = "PICK_MICROWAVE"

            case "PICK_MICROWAVE":
                target_x, target_y = microwave.pos_x_real, microwave.pos_y_real
                if ee.is_close(microwave):
                    ee.pick(microwave, line)
                    state = "PLACE_MICROWAVE"

            case "PLACE_MICROWAVE":
                target_x, target_y = packaging.pos_x_real, packaging.pos_y_real
                if ee.is_close(packaging):
                    ee.place(microwave)
                    state = "PICK_THERMOCOL"

            case "PICK_THERMOCOL":
                target_x, target_y = thermocol.pos_x_real, thermocol.pos_y_real
                if ee.is_close(thermocol):
                    ee.pick(thermocol, line)
                    state = "PLACE_THERMOCOL"

            case "PLACE_THERMOCOL":
                target_x, target_y = packaging.pos_x_real, packaging.pos_y_real
                if ee.is_close(packaging):
                    ee.place(thermocol)
                    state = "AWAIT_TAPE_ENTRY"

            case "AWAIT_TAPE_ENTRY":
                # The robot waits while the belt moves the package into the taper
                # We can set target to a neutral "home" or the edge of the taper
                target_x, target_y = tape_closing.pos_x_real - 0.5, tape_closing.pos_y_real

                if tape_closing.contains(packaging.pos_x_real, packaging.pos_y_real):
                    state = "AWAIT_TAPE_EXIT"

            case "AWAIT_TAPE_EXIT":
                # The package is currently being taped. Wait for it to clear the structure.
                target_x, target_y = tape_closing.pos_x_real + 0.5, tape_closing.pos_y_real

                if not tape_closing.contains(packaging.pos_x_real, packaging.pos_y_real):
                    # Only proceed if it's still within the gantry's reach
                    if gantry.contains(packaging.pos_x_real, packaging.pos_y_real):
                        state = "PICK_PACKAGED"

            case "PICK_PACKAGED":
                # Assuming the EE needs to pick up the combined package now
                target_x, target_y = packaging.pos_x_real, packaging.pos_y_real
                if ee.is_close(packaging):
                    ee.pick(packaging, line)
                    state = "PLACE_PACKAGED"

            case "PLACE_PACKAGED":
                target_x, target_y = tape_closing.pos_x_real, tape_closing.pos_y_real
                if tape_closing.contains(ee.x_m, ee.y_m):
                    ee.place(packaging, line)
                    state = "IDLE"

        ee.update(dt, target_x, target_y)



        line.draw(screen)
        gantry.draw(screen)
        tape_closing.draw(screen)


        ee.draw(screen)
        line.update(dt)

        font = pygame.font.SysFont('Arial',32)
        text_surface = font.render(state, True, (255,255,255))
        screen.blit(text_surface, (600,600))



        pygame.display.flip()



if __name__ == "__main__":
    main()
