import pygame
import math
import numpy as np
from typing import List, Optional

# Global Mapping
dim = 800
onem = 100  # 100px / 1m

def m2px(m_val): return int(m_val * onem)
def px2m(px_val): return px_val / onem

class KinematicsLogger:
    def __init__(self):
        self.data = {
            "time": [],
            "x": [], "y": [], "z": [],
            "vx": [], "vy": [], "vz": [],
            "ax": [], "ay": [], "az": []
        }
        self.total_time = 0.0

    def log(self, pos: np.ndarray, dt_ms: int):
        dt = dt_ms / 1000.0
        if dt <= 0: return

        # Current Position
        cur_x, cur_y = pos[0, 0], pos[1, 0]
        cur_z = 0.0  # Placeholder for Z
        
        # Calculate Velocity (v = dx / dt)
        vx, vy, vz = 0.0, 0.0, 0.0
        if self.data["time"]:
            vx = (cur_x - self.data["x"][-1]) / dt
            vy = (cur_y - self.data["y"][-1]) / dt
            vz = (cur_z - self.data["z"][-1]) / dt

        # Calculate Acceleration (a = dv / dt)
        ax, ay, az = 0.0, 0.0, 0.0
        if len(self.data["vx"]) > 0:
            ax = (vx - self.data["vx"][-1]) / dt
            ay = (vy - self.data["vy"][-1]) / dt
            az = (vz - self.data["vz"][-1]) / dt

        # Append data
        self.total_time += dt
        self.data["time"].append(self.total_time)
        self.data["x"].append(cur_x); self.data["y"].append(cur_y); self.data["z"].append(cur_z)
        self.data["vx"].append(vx); self.data["vy"].append(vy); self.data["vz"].append(vz)
        self.data["ax"].append(ax); self.data["ay"].append(ay); self.data["az"].append(az)

    def save_to_csv(self, filename="kinematics_log.csv"):
        import pandas as pd
        df = pd.DataFrame(self.data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

    def plot_data(self):
            import matplotlib.pyplot as plt
            fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
            axs[0].plot(self.data["time"], self.data["x"], label="X Position")
            axs[1].plot(self.data["time"], self.data["vx"], label="X Velocity", color='orange')
            axs[2].plot(self.data["time"], self.data["ax"], label="X Acceleration", color='red')
            for ax in axs: ax.legend(); ax.grid(True)
            plt.xlabel("Time (s)")
            plt.show()






class Obj:
    """Base class for anything with a physical position in the 2D world."""
    def __init__(self, pos_x: float, pos_y: float, x_len: float, y_len: float):
        # Position stored as a 2x1 Numpy Vector
        self._pos = np.array([[float(pos_x)], [float(pos_y)]])
        self.size_real = np.array([[float(x_len)], [float(y_len)]])
        self.children: List['PhysicsObject'] = []
        self.status = "NONE"

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
        
        # Kinematic State for S-Curve
        self.vel = np.array([[0.0], [0.0]])
        self.accel = np.array([[0.0], [0.0]])
        
        # S-Curve Constraints
        self.max_v = 0.5   # m/s (Your requested clamp)
        self.max_a = 3   # m/s^2
        self.gain_p = 20.0 # How aggressively to snap to target

    def update(self, dt: int, target_vec: np.ndarray):
        dt_s = dt / 1000.0
        if dt_s <= 0: return

        # 1. CLAMP: Keep target within Gantry bounds
        half_limit = self.struct.size_real / 2
        low_limit = self.struct.pos - half_limit
        high_limit = self.struct.pos + half_limit
        clamped_target = np.clip(target_vec, low_limit, high_limit)

        # 2. S-CURVE LOGIC (Simplified via PD-like acceleration control)
        # Calculate desired velocity based on distance to target
        error = clamped_target - self.pos
        desired_vel = error * self.gain_p
        
        # Clamp desired velocity to max_v
        vel_mag = np.linalg.norm(desired_vel)
        if vel_mag > self.max_v:
            desired_vel = (desired_vel / vel_mag) * self.max_v

        # Calculate required acceleration to reach desired velocity
        # This acts as the 'Jerk' limiter effectively
        accel_needed = (desired_vel - self.vel) / 0.1  # 0.1 is a smoothing factor
        
        # Clamp acceleration
        acc_mag = np.linalg.norm(accel_needed)
        if acc_mag > self.max_a:
            accel_needed = (accel_needed / acc_mag) * self.max_a

        # 3. INTEGRATE
        self.vel += accel_needed * dt_s
        
        # Final safety velocity clamp
        final_vel_mag = np.linalg.norm(self.vel)
        if final_vel_mag > self.max_v:
            self.vel = (self.vel / final_vel_mag) * self.max_v

        self.pos = self.pos + (self.vel * dt_s)

        # Sync held objects
        for obj in self.held_objects:
            obj.pos = self.pos.copy()

    # ... keep pick/place/draw methods the same ...

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



        self.objects = [o for o in self.objects if o.x < px2m(dim + 100) and o.x > -5.0]
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
    line_speed = 0.1 # m/s
    spacing_distance = 0.8 # meters between sets

    # Calculate spawn_rate in ms
    spawn_rate = (spacing_distance / line_speed) * 1000 

    # Spawner State Machine variables
    spawn_state = "SPAWN_MW"
    spawn_timer = 0






    
    
    
    line = Line(pos_y=4.0, height=1.0, speed=line_speed)

    state = "IDLE"
    running = True

    home_pos = np.array([[2.5],[4.0]])

    palletized = []

    current_mw: Optional[PhysicsObject] = None
    current_tc: Optional[PhysicsObject] = None 
    current_pk: Optional[PhysicsObject] = None 

    logger = KinematicsLogger()
    time_scale = 10.0  # 2.0 = 2x speed, 5.0 = 5x speed, etc.
    while running:
        real_dt = clock.tick(60)
        sim_dt  = time_scale*real_dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
                logger.save_to_csv()
                logger.plot_data()


        spawn_timer += sim_dt
        if spawn_state == "SPAWN_MW":
                    line.add(PhysicsObject(0.67, 0.58, 40, name="MW"), 0.0)
                    spawn_state = "WAIT_FOR_BOX"
                    spawn_timer = 0

        elif spawn_state == "WAIT_FOR_BOX":
            if spawn_timer >= spawn_rate:
                line.add(PhysicsObject(0.67, 0.58, 1, name="Box"), 0.0)
                spawn_state = "WAIT_FOR_TC"
                spawn_timer = 0

        elif spawn_state == "WAIT_FOR_TC":
            if spawn_timer >= spawn_rate:
                line.add(PhysicsObject(0.67, 0.58, 1, name="TC"), 0.0)
                spawn_state = "WAIT_FOR_NEXT_SET"
                spawn_timer = 0

        elif spawn_state == "WAIT_FOR_NEXT_SET":
            if spawn_timer >= spawn_rate:
                spawn_state = "SPAWN_MW"
                spawn_timer = 0

        # Current Target defaults to EE current pos if no state is active
        target = ee.pos.copy()

# --- 1. PRE-LOGIC: TARGETING FILTERS ---
        all_boxes = [o for o in line.objects if o.name == "Box" and gantry.contains(o.pos)]
        
        # IMPORTANT: Logic to advance box status so ready_to_palletize actually fills up
        for b in all_boxes:
            # If box has 2 items (MW + TC) but status is still NONE, it's packed
            if len(b.children) == 2 and b.status == "NONE":
                b.status = "PACKED"
            # If it's packed and hits the tape machine, it's ready
            if b.status == "PACKED" and tape_machine.contains(b.pos):
                b.status = "TAPING"

            if b.status == "TAPING" and not tape_machine.contains(b.pos):
                b.status = "READY"

        mws_on_belt = [o for o in line.objects if o.name == "MW" and gantry.contains(o.pos) and o.status == "NONE"]
        tcs_on_belt = [o for o in line.objects if o.name == "TC" and gantry.contains(o.pos) and o.status == "NONE"]
        
        empty_boxes = [b for b in all_boxes if len(b.children) == 0]
        boxes_needing_tc = [b for b in all_boxes if len(b.children) == 1]
        # Only palletize if it's READY and within the Gantry reach
        ready_to_palletize = [b for b in all_boxes if b.status == "READY" and gantry.contains(b.pos)]

        # --- 2. THE STATE MACHINE ---
        if state == "IDLE":
            target = home_pos
            
            # HIGHEST PRIORITY: Clear the line of finished goods
            if ready_to_palletize:
                state = "PALLET_PICK"
            
            # SECOND PRIORITY: Complete partially filled boxes
            elif boxes_needing_tc and tcs_on_belt:
                current_pkg = boxes_needing_tc[0]
                state = "TC2PKG_PICK"
            
            # THIRD PRIORITY: Start new boxes
            elif mws_on_belt:
                state = "MW2PKG_PICK"

        # --- PALLET SEQUENCE (TOP PRIORITY) ---
        elif state == "PALLET_PICK":
            # Re-verify the list isn't empty to prevent index errors
            if not ready_to_palletize:
                state = "IDLE"
            else:
                current_pkg = ready_to_palletize[0]
                target = current_pkg.pos
                if ee.is_close(current_pkg):
                    ee.pick(current_pkg, line)
                    state = "PALLET_PLACE"

        elif state == "PALLET_PLACE":
            target = pallet.pos
            if ee.is_close(pallet) and current_pkg is not None:
                obj = ee.place(current_pkg)
                if obj: palletized.append(obj)
                state = "IDLE"

        # --- MICROWAVE SEQUENCE ---
        elif state == "MW2PKG_PICK":
            current_mw = mws_on_belt[0]
            target = current_mw.pos
            if ee.is_close(current_mw):
                ee.pick(current_mw, line)
                state = "MW2PKG_PLACE"

        elif state == "MW2PKG_PLACE":
            if not empty_boxes: 
                target = home_pos # Wait for an empty box to arrive
            else:
                current_pkg = empty_boxes[0]
                target = current_pkg.pos
                if ee.is_close(current_pkg):
                    ee.place_inside(current_mw, current_pkg)
                    state = "IDLE"

        # --- THERMOCOL SEQUENCE ---
        elif state == "TC2PKG_PICK":
            if not tcs_on_belt: state = "IDLE"
            else:
                current_tc = tcs_on_belt[0]
                target = current_tc.pos
                if ee.is_close(current_tc):
                    ee.pick(current_tc, line)
                    state = "TC2PKG_PLACE"

        elif state == "TC2PKG_PLACE":
            # We must target the specific box identified in IDLE
            target = current_pkg.pos
            if ee.is_close(current_pkg):
                ee.place_inside(current_tc, current_pkg)
                state = "IDLE"









        # Logic & Physics
        ee.update(sim_dt, target)
        line.update(sim_dt)

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

        logger.log(ee.pos, sim_dt)

if __name__ == "__main__":
    main()
