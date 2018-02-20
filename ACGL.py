'''
make a little curses game with a class that impliments key binding to callbacks
'''

import curses
from functools import partial
import random

def _():
	pass


class App(object):
	'''implimented as a finite state machine'''
	def __init__(self):

		self.state_bindings = {}
		self.key_bindings = {}
		self.state = 0 # lowest base case
		self.default = 0
		self.running = True
		self.stdscr = None

	def mainloop(self):

		with self as stdscr:
			while self.running:
				self.state_bindings[self.state]()
					
	def chain_state(self, new, signal=None):
		'''returns a decorator to set the next state of a function based on a signal'''
		def _chain_state_decorator(func):
			def _wrapper(*args, **kwargs):

				sig = func(*args, **kwargs)
				if sig == signal:
					self.state = new
			return _wrapper
		return _chain_state_decorator

	def reset(self):
		
		self.state = 0

	def poll_input(self):

		key = self.stdscr.getch()
		if key in self.key_bindings:
			self.key_bindings[key]()

	def bind_key(self, key, func):
		'''abstraction so we convert the key to its ordinal'''
		if type(key) is str:
			self.key_bindings[ord(key)] = func
		else:
			self.key_bindings[key] = func

	def bind(self, state, func):

		self.state_bindings[state] = func

	def unbind(self, state):

		del self.state_bindings[state]

	def unbind_key(self, key):

		del self.state_bindings[ord(key)]

	def __enter__(self):

		self.stdscr = curses.initscr()
		self.stdscr.nodelay(True)
		curses.noecho()
		curses.cbreak()
		self.stdscr.keypad(True)
		self.stdscr.scrollok(0)

		return self.stdscr

	def __exit__(self, *args):

		curses.nocbreak()
		self.stdscr.keypad(False)
		curses.echo()
		curses.endwin()

	def wait(self, delay=500):

		curses.napms(delay)

class Point:

	def __init__(self, x, y):

		self.x = x
		self.y = y

	def __iter__(self):

		yield self.x
		yield self.y

	def __getitem__(self, i):

		if i == 0:
			return self.x
		elif i == 1:
			return self.y
		else:
			raise IndexError("Index Out of Range")
			
	def __add__(self, other):

		new = Point(self.x+other[0], self.y+other[1])
		return new


class Sprite(object):

	def __init__(self, image = ''):

		self.pos = Point(0,0)
		self.vel = Point(0,0)
		self.image = image.strip().split('\n')
		self.shape = (len(self.image), max(map(len, self.image)))
		# should fill a buffer of space for the shape to work nicely

	def reset(self):

		self.state = 0

	def draw(self, app):

		pos = Point(self.pos.x, self.pos.y) # Rounded grid position
		pos.x = int(pos.x + (-0.5 if pos.x < 0 else 0.5))
		pos.y = int(pos.y + (-0.5 if pos.y < 0 else 0.5))

		LINES, COLUMNS = app.stdscr.getmaxyx()
		w, l = self.shape

		y_min = min(-pos.y, w) if pos.y < 0 else 0
		y_max = max(LINES-pos.y, y_min) if pos.y+w > LINES else w

		for i in xrange(y_max - y_min):

			x_min = min(-pos.x, l) if pos.x < 0 else 0
			x_max = max(COLUMNS-pos.x, x_min) if pos.x+l > COLUMNS else l

			x = max(pos.x, 0) if pos.x < 0 else min(pos.x, COLUMNS-1)
			y = max(pos.y, 0) if pos.y < 0 else min(pos.y, LINES-1)

			for j in xrange(x_max - x_min):
				if self.image[i+y_min][j+x_min] != ' ': # allow for transparent pixels
					try:	
						app.stdscr.addch(y+i,x+j,self.image[i+y_min][j+x_min])
					except curses.error:
						pass

	def get_move(self, delta_pos):
		'''returns the move partial function'''
		return partial(self.move, delta_pos)

	def move(self, delta_pos):

		self.pos += delta_pos

	def get_acc(self, delta_vel):

		return partial(self.accelerate, delta_vel)

	def accelerate(self, delta_vel):

		self.vel += delta_vel

	def set_pos(self, pos):

		if type(pos) is tuple:
			if pos[0] is not None:
				self.pos.x = pos[0]
			if pos[1] is not None:
				self.pos.y = pos[1]
		else:
			self.pos = pos

	def set_vel(self, vel):

		if type(vel) is tuple:
			if vel[0] is not None:
				self.vel.x = vel[0]
			if vel[1] is not None:
				self.vel.y = vel[1]
		else:
			self.vel = vel

class MultiSprite(Sprite):
	'''multiple sprite whose draw functions are determined by their get_relative function'''

	def __init__(self, image = '', child=None):

		super(MultiSprite, self).__init__(image)
		self.child = child

	def draw(self, app):

		self.child.draw(app)		
		super(MultiSprite, self).draw(app)

	def trail(self): # a fun example method for a use for multisprites
		if isinstance(self.child, MultiSprite):
			self.child.trail()
		self.child.set_pos((self.pos.x, self.pos.y))

class PhysicsEngine:

	def __init__(self, g = -10, dt=0.05, mu_k = 0.4, **kwargs):
		'''first kwarg will be g'''
		self.g = g
		self.dt = dt
		self.acc = Point(0,0)
		self.mu_k = mu_k
		self.bounds = Point(170, 50)
		self.bounce = Point(0.5,0.5)
		self.__dict__.update(kwargs)

	def set_bounds(self, x, y):

		self.bounds.x = x
		self.bounds.y = y

	def update_sprite(self, sprite):

		self.acc = Point(0,0)
		self.manage_bounds(sprite)
		if sprite.pos.y+sprite.shape[0] < self.bounds.y:
			self.gravity(sprite)
		else:
			self.friction(sprite)
			if sprite.pos.y+sprite.shape[0] > self.bounds.y:
				sprite.pos.y = self.bounds.y-sprite.shape[0]
				if abs(sprite.vel.y) < 0.5/self.dt: 
					sprite.vel.y = 0
				else:
					sprite.vel.y *= -self.bounce.y
		sprite.vel.y += self.acc.y*self.dt
		sprite.vel.x += self.acc.x*self.dt
		sprite.pos.y -= sprite.vel.y*self.dt + self.acc.y*self.dt*self.dt*0.5 
		sprite.pos.x += sprite.vel.x*self.dt + self.acc.x*self.dt*self.dt*0.5 

	def get_update_funcs(self, *sprites):

		return (partial(self.update_sprite, sprite) for sprite in sprites)

	def manage_bounds(self, sprite):

		if (sprite.pos.x < 0) or (sprite.pos.x+sprite.shape[1] > self.bounds.x):
			sprite.pos.x = 0 if sprite.pos.x < 0 else self.bounds.x-sprite.shape[1]
			if abs(sprite.vel.x) < 0.5/self.dt:
				sprite.vel.x = 0
			else:
				sprite.vel.x *= -self.bounce.x

	def gravity(self, sprite):

		self.acc.y += self.g

	def friction(self, sprite):

		if sprite.vel.x:
			mag = abs(self.g*self.mu_k)
			sign = sprite.vel.x/abs(sprite.vel.x)
			a = -sign*min(abs(sprite.vel.x/self.dt), mag)
			self.acc.x += a 

