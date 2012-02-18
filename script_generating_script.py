import pygame
pygame.init()
s = pygame.image.load("icon.ico")
s_ = pygame.image.tostring(s, "RGB")

output = open("icon.py", 'w')

output.write('# -*- coding: utf-8 -*-\ntext = """')

output.write(s_)

output.write('"""')
output.write("\n")
output.close()
pygame.quit()
print "Generated icon"
