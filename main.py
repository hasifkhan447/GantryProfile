import pygame

# class Rectangle():
#     def __init__(self):
#         # self.image, self.rect = 


def main(): #
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    running = True 

    i = 0

    while running: 
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                running = False 
        screen.fill("purple")
        pygame.draw.rect(screen, (0, 128, 128), pygame.rect.Rect(i, i,100,100))
        pygame.display.flip()

        clock.tick(60)
        i = i + 1



if __name__ == "__main__":
    main()
