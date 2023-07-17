import pygame
pygame.init()
s = pygame.image.load("icon.ico")
s_ = pygame.image.tostring(s, "RGB")

output = open("icon.py", 'wb')

output.write(b'text = ')

output.write(repr(s_).encode('utf-8'))

output.write(b"\n")
output.close()
pygame.quit()
print("Generated icon")
