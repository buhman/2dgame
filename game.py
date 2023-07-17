#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Written by Zack Buhman & Jack Stephenson
# Art done by Jack Stephenson
# About: This project started as a learning project.
#		 Since then it has evolved into a game based
#		 the idea that you keep jumping to get a high
#		 score.


try:
	import android
except ImportError:
	android = None

global getuser
if not android:
	from getpass import getuser
	from database import EncryptedDatabase
else:
	global getuser
	def getuser(): return 'android'
	EncryptedDatabase = None

import icon
import os
import pygame
import random
import time

global DEBUG_ENABLED
DEBUG_ENABLED = os.path.exists("setup.py") or android #enable the debug HUD in android by default
#DEBUG_ENABLED = os.path.exists("setup.py") and not android #disable the debug HUD in android by default

def hsv_to_rgb(h, s, v):
	if s == 0.0:
		return v, v, v
	i = int(h * 6.0)
	f = (h * 6.0) - i
	p = v * (1.0 - s)
	q = v * (1.0 - s * f)
	t = v * (1.0 - s * (1.0 - f))
	i = i % 6
	if i == 0:
		return v, t, p
	if i == 1:
		return q, v, p
	if i == 2:
		return p, v, t
	if i == 3:
		return p, q, v
	if i == 4:
		return t, p, v
	if i == 5:
		return v, p, q

class Timer(object):
	def __init__(self):
		self.time = None
		self.elapsed = 0
	def start(self):
		self.time = time.time()
	def clock(self):
		self.elapsed = time.time() - self.time


class Box(object):
	def __init__(self, x, y, color = pygame.Color(255, 255, 255)):
		self.width = 25
		self.height = 25
		self.color = color
		self._x = x
		self._y = y

		self.x_velocity = 0.0
		self.y_velocity = 0.0

		self.last_y = y

		self.bounciness = 0.9

		self.band_ridgity = 0.05
		self.band_elasticity = 0.8

		self.terminal_velocity = 10

		self.mouse_hold = False

	def update(self):
		if self.mouse_hold:
			mouse_x, mouse_y = pygame.mouse.get_pos()
			self.x_velocity += self.band_ridgity * (mouse_x - self._x - self.width / 2)
			self.y_velocity += self.band_ridgity * (mouse_y - self._y - self.height / 2)
			self.x_velocity *= self.band_elasticity
			self.y_velocity *= self.band_elasticity

		self._x += self.x_velocity
		self._y += self.y_velocity

	def draw(self, surface):
		self.update()

		rect = pygame.rect.Rect(self._x, self._y, self.width, self.height)
		pygame.draw.rect(surface, self.color, rect, 1)

		self.draw_mouse_band(surface)

	def draw_mouse_band(self, surface):
		if self.mouse_hold:
			pygame.draw.line(surface, (255, 0, 0), (self._x + self.width / 2, self._y + self.height / 2), pygame.mouse.get_pos())

class Platform(Box):
	def __init__(self, x, y, color = pygame.Color(0, 255, 0)):
		super(Platform, self).__init__(x, y, color)
		self.width = 50
		self.height = 5

		self.touched = False

		self.x_velocity = random.randint(-2, 2)

class Character(Box):
	def __init__(self, x, y, color):
		super(Character, self).__init__(x, y, color)
		self.points = 0
		self.top = False
	def update(self):
		super(Character, self).update()
		if self.top:
			self._y -= self.y_velocity * 0.9
			self.top = False

	def draw(self, surface):
		self.update()
		#if self.x_velocity > 0:
		#	gfxdraw.aacircle(surface, int(self._x + self.width / 2), int(self._y + self.height / 2), int(self.width / 2), (0, 255, 128))
		#elif self.x_velocity < 0:
		#	gfxdraw.aacircle(surface, int(self._x + self.width / 2), int(self._y + self.height / 2), int(self.width / 2), (255, 128, 0))
		#else:
		#	gfxdraw.aacircle(surface, int(self._x + self.width / 2), int(self._y + self.height / 2), int(self.width / 2), (255, 255, 0))

		color = hsv_to_rgb(abs(self.y_velocity) / 10, 1, 1)
		color = tuple(i * 255 for i in color)

		pygame.draw.circle(surface, color, (int(self._x + self.width / 2), int(self._y + self.height / 2)), int(self.width / 2), 1)

		self.draw_mouse_band(surface)

class FadingText(Timer):
	def __init__(self, text, font, duration):
		super(FadingText, self).__init__()
		self.text = text
		self.duration = duration
		self.start()
		self.font = font

	def draw(self):
		self.clock()

		fade = int(255 - 255 * (self.elapsed / self.duration))

		if fade < 0:
			fade = 0

		return self.font.render(self.text, True, (fade, fade, fade))


class Background(object):
	def __init__(self, surface, cell_size = 50):
		self.surface = surface
		self.y_velocity = 0
		self.offset = 0
		self.cell_size = cell_size
		self.color = (128, 128, 128)

	def update(self):
		self.offset += self.y_velocity

	def draw(self):
		self.update()
		for x in range(0, self.surface.get_width(), self.cell_size):
			for y in range(int(self.offset) % self.cell_size, self.surface.get_height(), self.cell_size):
				pygame.draw.line(self.surface, self.color, (x, 0), (x, self.surface.get_height()))
				pygame.draw.line(self.surface, self.color, (0, y), (self.surface.get_width(), y))

class Game(object):

	def __init__(self, screen):
		self.screen = screen
		self.font = pygame.font.Font(pygame.font.get_default_font(), 12)
		self.fading_text_list = []

		self.high_scores = {}

		if not android:
			self.database = EncryptedDatabase('highscores.encrypted', b'password')
			self.load_scores()

		self.clock = pygame.time.Clock()

		self.background = Background(self.screen, 50)
		self.background.color = (0, 0, 128)

		self.generate_blocks()
		self.create_character()

		self.render_timer = Timer()
		self.physics_timer = Timer()
		self.event_timer = Timer()
		self.hud_timer = Timer()

		self.total_distance = 0
		self.max_distance = 0
		self.level = 0
		self.fps = 60

		self.display_scores = False

		self.paused = False
		self._running = True

		self.loop()

	def load_scores(self):
		try:
			self.high_scores = self.database.load_database()
			self.add_fading_text("Loaded high scores.")
		except ValueError:
			self.add_fading_text("Failed to load high scores.")

	def save_scores(self):
		self.database.save_database(self.high_scores)

	def generate_blocks(self):
		self.initial_block_density = 20
		self.block_density = self.initial_block_density

		self.object_list = []

		for _ in range(self.block_density):
			self.object_list.append(Platform(random.randint(0, self.screen.get_width()), random.randint(-self.screen.get_height(), self.screen.get_height())))

	def create_character(self):
		self.character = Character(250, 100, pygame.Color(255, 0, 0))

	def render(self):

		self.render_timer.start()
		self.screen.fill((0, 0, 0))

		self.background.draw()

		for body in self.object_list:
			body.draw(self.screen)

		self.character.draw(self.screen)
		self.render_timer.clock()

		self.hud_timer.start()
		self.draw_hud()
		self.hud_timer.clock()

		pygame.display.flip()

	def draw_hud(self):
		max_distance_surface = self.font.render("Max Distance: %0.2f" % self.max_distance, True, (255, 255, 255))
		if DEBUG_ENABLED:
			timer_text = "Events: %0.2fms Physics: %0.2fms" % (self.event_timer.elapsed * 1000,
						self.physics_timer.elapsed * 1000)


			timer_text2 = "Render: %0.2fms HUD: %0.2fms" % (self.render_timer.elapsed * 1000,
						self.hud_timer.elapsed * 1000)

			fps_surface = self.font.render("FPS: %0.2f" % self.clock.get_fps(), True, (255, 255, 255))
			timer_surface = self.font.render(timer_text, True, (255, 255, 255))
			timer2_surface = self.font.render(timer_text2, True, (255, 255, 255))

			points_surface = self.font.render("Points: %s" % self.character.points, True, (255, 255, 255))
			level_surface = self.font.render("Level: %s" % self.level, True, (255, 255, 255))
			objects_surface = self.font.render("Blocks: %s" % len(self.object_list), True, (255, 255, 255))
			distance_surface = self.font.render("Net Distance: %0.2f" % self.total_distance, True, (255, 255, 255))

			self.screen.blit(fps_surface, (2, 0))
			self.screen.blit(timer_surface, (2, timer_surface.get_height() + 2))
			self.screen.blit(timer2_surface, (2, (timer_surface.get_height() + 2) * 2))

			self.screen.blit(level_surface, (self.screen.get_width() - level_surface.get_width() - 2, 0))
			self.screen.blit(objects_surface, (self.screen.get_width() - objects_surface.get_width() - 2, (points_surface.get_height() + 2) * 1))
			self.screen.blit(points_surface, (self.screen.get_width() - points_surface.get_width() - 2, (points_surface.get_height() + 2) * 2))
			self.screen.blit(distance_surface, (self.screen.get_width() - distance_surface.get_width() - 2, (points_surface.get_height() + 2) * 3))
			self.screen.blit(max_distance_surface, (self.screen.get_width() - max_distance_surface.get_width() - 2, (points_surface.get_height() + 2) * 4))

		elif not DEBUG_ENABLED:
			self.screen.blit(max_distance_surface, (self.screen.get_width() - max_distance_surface.get_width() - 2, 0))

		if self.display_scores:
			self.draw_scores()

		if self.character._y == self.screen.get_height():
			reset_text = "Press [Enter] to reset." if not android else "Double tap screen to reset."

			dead_surface = self.font.render("Oh, dear, you appear to have died.", True, (255, 255, 255))
			dead_surface2 = self.font.render(reset_text, True, (255, 255, 255))
			self.screen.blit(dead_surface, (int(self.screen.get_width()*0.5 - dead_surface.get_width()*0.5), int(self.screen.get_height() / 2)))
			self.screen.blit(dead_surface2, (int(self.screen.get_width()*0.5 - dead_surface2.get_width()*0.5), int(self.screen.get_height() / 2 + dead_surface2.get_height() + 2)))

		for i, text_object in enumerate(self.fading_text_list):
			index = i + 1
			surface = text_object.draw()
			self.screen.blit(surface, (2, self.screen.get_height() - surface.get_height() * index - 2 * index))

			if text_object.elapsed > text_object.duration:
				self.fading_text_list.pop(i)


	def add_fading_text(self, text, duration = 5):
		self.fading_text_list.append(FadingText(text, self.font, duration))

	def draw_scores(self):
		surface_list = []
		for score, person in self.high_scores.items():
			surface_list.append((float(score), self.font.render("%s: %0.2f" % (person, float(score)), True, (255, 255, 255))))

		surface_list.sort()
		surface_list.reverse()

		for index, surface_item in enumerate(surface_list):
			surface = surface_item[1]
			self.screen.blit(surface, (int(self.screen.get_width() * 0.5) - surface.get_width()*0.5,
										int(self.screen.get_height() * 0.5) - len(surface_list) * surface.get_height()*0.5 + surface.get_height()*index))

	def on_event(self, event):
		if not android:
			if event.type is pygame.KEYDOWN:
				if event.key is pygame.K_SPACE:
					self.paused = not self.paused
		else:
			if event.type is pygame.MOUSEBUTTONDOWN:
				self.paused = not self.paused

		if self.level is 12:
			self.add_fading_text("%s: You have been advanced to master Jedi Mode" % getuser())
			self.reset_game(False)

		if event.type is pygame.QUIT:
			self._running = False

		if event.type is pygame.KEYDOWN and event.key is pygame.K_ESCAPE:
			self._running = False

		if not self.paused and not android:
			if not event.type is pygame.KEYDOWN:
				speed = 2
			else:
				speed = 5

			if event.type in (pygame.KEYDOWN, pygame.KEYUP):

				if event.key in (pygame.K_a, pygame.K_LEFT):
					self.character.x_velocity = -speed
				if event.key in (pygame.K_d, pygame.K_RIGHT):
					self.character.x_velocity = speed
				if event.key is pygame.K_RETURN:
					if self.character._y == self.screen.get_height():
						self.reset_game(True)

			if event.type == pygame.KEYDOWN:
				if event.key is pygame.K_t:
					global DEBUG_ENABLED
					DEBUG_ENABLED = not DEBUG_ENABLED
				if event.key is pygame.K_h:
					self.display_scores = not self.display_scores

			if DEBUG_ENABLED and not android:
				if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
					object_list = list(self.object_list)
					object_list.append(self.character)
					for body in object_list:
						x, y = int(body._x), int(body._y)
						if event.pos[0] in range(x, x + body.width):
							if event.pos[1] in range(y, y + body.height):
								body.mouse_hold = event.type is pygame.MOUSEBUTTONDOWN
								break
						if body.mouse_hold:
							body.mouse_hold = event.type is pygame.MOUSEBUTTONDOWN
							break
					else:
						if event.type is pygame.MOUSEBUTTONDOWN:
							p = Platform(*event.pos)
							p._x -= p.width / 2
							p._y -= p.height / 2
							self.object_list.append(p)

		elif android:
			if event.type == pygame.MOUSEBUTTONDOWN:
				if self.character._y == self.screen.get_height():
					self.reset_game(True)

	def reset_game(self, m):
		self.create_character()
		self.generate_blocks()
		self.level = 0
		if m:
			self.append_score()
			self.total_distance = 0
			self.max_distance = 0
			self.fps = 60
		else:
			self.fps = 120


	def append_score(self):
		if len(self.high_scores) < 10:
			self.high_scores[self.max_distance] = getuser()
			self.add_fading_text("%s: %s added to high scores" % (getuser(), self.max_distance))
		else:
			for score in self.high_scores.keys():
				if self.max_distance > float(score):
					del self.high_scores[score]
					self.high_scores[self.max_distance] = getuser()
					self.add_fading_text("%s: %s added to high scores" % (getuser(), self.max_distance))
					return

	def update_platforms(self):
		for index, object in enumerate(self.object_list):
			if self.character.y_velocity < 0:
				if self.character._y < self.screen.get_height()*.25:
					object.y_velocity = -self.character.y_velocity
					self.background.y_velocity = +self.character.y_velocity
					self.character.top = True
				else:
					object.y_velocity = 0
					self.background.y_velocity = 0
					#self.character._y -= self.character.y_velocity * 0.5

			else:
				object.y_velocity = 0

			if object._y + object.height > self.screen.get_height():
				self.object_list.pop(index)

			if object._x + object.width < 0:
				object._x = self.screen.get_width()
			if object._x > self.screen.get_width():
				object._x = -object.width

		self.block_density = self.initial_block_density - int(self.character.points / 15.5)

		if self.block_density < 2:
			self.block_density = 2

		if len(self.object_list) < self.block_density:
			self.object_list.append(Platform(random.randint(0, self.screen.get_width()), -random.randint(0, self.screen.get_height())))

	def gravity(self):

		if self.character.y_velocity < self.character.terminal_velocity:
			self.character.y_velocity += 0.25

	def collisions(self):

		if self.character._y + self.character.height >= self.screen.get_height():
			self.character._y = self.screen.get_height()
			self.character.y_velocity = 0
		if self.character._x - self.character.width >= self.screen.get_width():
			self.character._x = 0
		elif self.character._x <= 0:
			self.character._x = self.screen.get_width() - self.character.width

		for platform in self.object_list:
			if platform._y > 0:
				if platform._x + platform.width >= self.character._x and self.character._x + self.character.width >= platform._x:
					if self.character._y + self.character.height >= platform._y:
						if self.character._y + self.character.width <= platform._y + platform.height + self.character.terminal_velocity - platform.height + 1:
							if self.character.y_velocity >= 0:
								self.character.y_velocity = -10 - self.level
								if not platform.touched:
									self.character.points += 1
									platform.touched = True

									if self.character.points % 25 == 0:
										self.level = (self.character.points / 25)
										self.add_fading_text("Achieved level %s" % str(self.level), 10 * self.level)
										self.character.y_velocity -= 10 * self.level
										self.character.terminal_velocity = 10 + self.level

	def loop(self):
		while self._running:
			self.event_timer.start()
			for event in pygame.event.get():
				self.on_event(event)
			self.event_timer.clock()

			if not self.paused:
				self.physics_timer.start()
				self.update_platforms()
				self.gravity()
				self.collisions()
				self.physics_timer.clock()

				self.total_distance -= self.character.y_velocity
				if self.max_distance < self.total_distance:
					self.max_distance = self.total_distance

				if android:
					self.character.x_velocity = android.accelerometer_reading()[0]
					self.character.x_velocity *= -2

				self.clock.tick(self.fps)
				self.render()

		if not android:
			self.save_scores()
		pygame.quit()

def run(resolution):
	pygame.font.init()

	icon_surface = pygame.image.fromstring(icon.text, (32, 32), "RGB")

	screen = pygame.display.set_mode(resolution)
	pygame.display.set_icon(icon_surface)
	pygame.display.set_caption("2dgame - Dr. Buhman, Ph.D. & Mr. Stephenson, GCSE")

	g = Game(screen)
	if android and DEBUG_ENABLED:
		g.add_fading_text(screen, 10)

# Android's interpreter will execute main by default
def main():
	import sys
	import traceback
	try:
		pygame.init()
		android.accelerometer_enable(True)
		mode = None
		for mode in pygame.display.list_modes():
			if mode[1] <= 640:
				break
		run(mode)
	except:
		with open("traceback.txt", 'w') as f:
			traceback.print_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2], None, f)


# __name__ != __main__ on android
if __name__ == "__main__":
	pygame.init()
	run((500, 500))
