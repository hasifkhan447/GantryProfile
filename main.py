import pygame
import math
import numpy as np
from typing import List, Optional

# Global Mapping
dim = 800
onem = 100  # 100px / 1m

def m2px(m_val): return int(m_val * onem)
def px2m(px_val): return px_val / onem

class Obj:
    """Base class for anything with a physical position in the 2D world."""
    def __init__(self, pos_x: float, pos_y: float, x_len: float, y_len: float):
        # Position stored as a 2x1 Numpy Vector
        self._pos = np.array([[float(pos_x)], [float(pos_y)]])
        self.size_real = np.array([[float(x_len)], [float(y_len)]])
        self.children: List['PhysicsObject'] = []

    @property 
    def pos(self):
        return self._pos 

    @pos.setter 
    def pos(self, new_pos):
        self._pos = new_pos 
        for child in self.children:
            child.pos = new_pos.copy()
    
    @property
    def x(self): return self._pos[0, 0]

    @property
    def y(self): return self._pos[1, 0]

    def is_close(self, other: 'Obj', threshold=0.1) -> bool:
        """Euclidean distance check between two Obj instances."""
        self.pos 
        other.pos
        if np.linalg.norm(self.pos - other.pos) < threshold:
            return True
        else: 
            return False

    def contains(self, other_pos: np.ndarray) -> bool:
        """Checks if a 2x1 position vector is within this object's rectangular bounds."""
        half_size = self.size_real / 2
        low = self.pos - half_size
        high = self.pos + half_size
        if np.all((other_pos >= low) & (other_pos <= high)):
            return True 
        else: return False


class Structure(Obj):
    OUTLINE_THICKNESS = 0.025
    def __init__(self, x_len, y_len, pos_x, pos_y):
        super().__init__(pos_x, pos_y, x_len, y_len)

    def draw(self, screen):
        color = (180, 180, 180)
        t = m2px(self.OUTLINE_THICKNESS)
        w, h = m2px(self.size_real[0,0]), m2px(self.size_real[1,0])
        x = m2px(self.x) - w//2
        y = m2px(self.y) - h//2
        pygame.draw.rect(screen, color, (x, y, w, h), t)

class PhysicsObject(Obj):
    def __init__(self, x_len, y_len, mass, pos_x=0.0, pos_y=0.0, name="Item", rotate=True):
        if rotate:
            super().__init__(pos_x, pos_y, y_len, x_len)
        else:
            super().__init__(pos_x, pos_y, x_len, y_len)
        self.mass = mass
        self.name = name

    def draw(self, screen):
        w, h = m2px(self.size_real[0,0]), m2px(self.size_real[1,0])
        x, y = m2px(self.x) - w//2, m2px(self.y) - h//2
        pygame.draw.rect(screen, (60, 60, 80), (x, y, w, h))
        label = pygame.font.SysFont(None, 16).render(self.name, True, (200, 200, 200))
        screen.blit(label, (x + 2, y + h//2 - 8))

        for child in self.children:
            child.draw(screen)

class EndEffector(Obj):
    def __init__(self, pos_x, pos_y, bound_structure: Structure):
        super().__init__(pos_x, pos_y, 0.1, 0.1)
        self.struct = bound_structure
        self.held_objects: List[PhysicsObject] = []
        
        # PI Control
        self.error_sum = np.array([[0.0], [0.0]])
        self.last_target = np.array([[0.0], [0.0]])
        self.kp = 5.0
        self.ki = 1.5

    def update(self, dt: int, target_vec: np.ndarray):
        dt_s = dt / 1000.0
        if dt_s <= 0: return

        # AUTO-RESET: If target vector has changed significantly, clear integral memory
        if not np.allclose(target_vec, self.last_target, atol=1e-4):
            self.error_sum = np.array([[0.0], [0.0]])
            self.last_target = target_vec.copy()

        # CLAMP: Keep target within Gantry bounds
        half_limit = self.struct.size_real / 2
        low_limit = self.struct.pos - half_limit
        high_limit = self.struct.pos + half_limit
        clamped_target = np.clip(target_vec, low_limit, high_limit)

        # PI Calculation
        error = clamped_target - self.pos
        self.error_sum += error * dt_s
        
        velocity = (self.kp * error) + (self.ki * self.error_sum)
        self.pos = self.pos + (velocity * dt_s)
        # Sync held objects
        for obj in self.held_objects:
            obj.pos = self.pos.copy()



    def pick(self, obj: PhysicsObject, line: 'Line'):
        if obj in line.objects:
            line.objects.remove(obj)
            self.held_objects.append(obj)

    def place_inside(self, item: PhysicsObject, container: PhysicsObject):
        if item in self.held_objects:
            self.held_objects.remove(item)
            container.children.append(item)

    def place(self, obj: PhysicsObject, receiver: Optional['Line'] = None):
        if obj in self.held_objects:
            self.held_objects.remove(obj)
            if receiver:
                receiver.add(obj, obj.x)
            else:
                # If no receiver, the object stays exactly where it was placed
                # We return it so the main loop can track it if needed
                return obj
            return None



    def draw(self, screen):
        for obj in self.held_objects: obj.draw(screen)
        pygame.draw.circle(screen, (100, 0, 0), (m2px(self.x), m2px(self.y)), 5)

class Line:
    def __init__(self, pos_y, height, speed=0.30):
        self.pos_y = pos_y
        self.height = height
        self.speed = speed
        self.objects: List[PhysicsObject] = []

    def add(self, obj: PhysicsObject, start_x):
        obj.pos = np.array([[float(start_x)], [float(self.pos_y)]])
        self.objects.append(obj)

    def update(self, dt):
        dt_s = dt / 1000.0
        for obj in self.objects:
            new_pos = obj.pos.copy()
            new_pos[0, 0] += self.speed * dt_s
            obj.pos = new_pos



        self.objects = [o for o in self.objects if m2px(o.x) < dim + 100]

    def draw(self, screen):
        py = m2px(self.pos_y)
        ph = m2px(self.height)
        pygame.draw.rect(screen, (40, 120, 40), (0, py - ph//2, dim, ph))
        for obj in self.objects: obj.draw(screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((dim, dim))
    clock = pygame.time.Clock()
    
    gantry = Structure(3.5, 4.0, 4.0, 4.0)
    tape_machine = Structure(1.0, 1.0, 4.3, 4.0)
    pallet = Structure(1, 1, 5, 2.7)




    ee = EndEffector(4.0, 4.0, gantry)
    
    mw = PhysicsObject(0.67, 0.58, 40, name="MW")
    tc = PhysicsObject(0.67, 0.58, 1, name="TC")
    pk = PhysicsObject(0.67, 0.58, 1, name="Box")
    
    line = Line(pos_y=4.0, height=1.0)
    line.add(tc, 0.05)
    line.add(pk, 0.8)
    line.add(mw, 1.6)

    state = "IDLE"
    running = True

    home_pos = np.array([[4.0],[4.0]])

    palletized = []

    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # Current Target defaults to EE current pos if no state is active
        target = ee.pos.copy()

        # State Machine Logic
        if state == "IDLE":
            target=home_pos
            if gantry.contains(mw.pos) and not pallet.contains(mw.pos): 
                print("I'm in idle right now")
                print("Microwave is at:", mw.pos[0], mw.pos[1])
                print("EE is at: ", ee.pos[0], ee.pos[1])
                state = "PICK_MW"

        elif state == "PICK_MW":
            target = mw.pos
            if ee.is_close(mw):
                ee.pick(mw, line); state = "PLACE_MW"

        elif state == "PLACE_MW":
            target = pk.pos
            if ee.is_close(pk):
                ee.place_inside(mw,pk); state = "PICK_TC"

        elif state == "PICK_TC":
            target = tc.pos
            if ee.is_close(tc):
                ee.pick(tc, line); state = "PLACE_TC"

        elif state == "PLACE_TC":
            target = pk.pos
            if ee.is_close(pk):
                ee.place_inside(tc, pk); state = "AWAIT_TAPE_IN"

        elif state == "AWAIT_TAPE_IN":
            target = tape_machine.pos - np.array([[0.8], [0.0]])
            if tape_machine.contains(pk.pos): state = "AWAIT_TAPE_OUT"

        elif state == "AWAIT_TAPE_OUT":
            target = tape_machine.pos + np.array([[0.8], [0.0]])
            if not tape_machine.contains(pk.pos) and gantry.contains(pk.pos):
                state = "PICK_PACKAGED"

        elif state == "PICK_PACKAGED":
            target = pk.pos
            if ee.is_close(pk):
                ee.pick(pk, line); state = "PLACE_PACKAGED"

        elif state == "PLACE_PACKAGED":
            target = pallet.pos
            if pallet.is_close(ee, threshold=0.15):
                obj = ee.place(pk)
                if obj: 
                    palletized.append(obj)
                print("Successfully palletized!")
                state = "IDLE"

        # Logic & Physics
        ee.update(dt, target)
        line.update(dt)

        # Rendering
        screen.fill((50, 20, 70))
        line.draw(screen)
        gantry.draw(screen)
        tape_machine.draw(screen)
        ee.draw(screen)
        pallet.draw(screen)

        for obj in palletized:
            obj.draw(screen)
        
        img = pygame.font.SysFont('Arial', 24).render(f"STATE: {state}", True, (255,255,255))
        screen.blit(img, (20, 20))
        pygame.display.flip()

if __name__ == "__main__":
    main()
