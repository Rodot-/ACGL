'''
make a little curses game with a class that impliments key binding to callbacks
'''
from ACGL import App, Sprite, MultiSprite, PhysicsEngine, Point
import curses
from functools import partial
import random

class Game(App):

	def __init__(self):

		super(Game, self).__init__()

		self.dt = 0.05

		self.physics = PhysicsEngine(-10, self.dt, mu_k = 0.8, app = self)		

		self.player = Sprite('''*_*
/+\\
 | 
/ \\''')
		box = '''+--+
|  |
+--+'''

		N_BOXES = 20
		TAIL_LEN = 10

		tail = [Sprite('-') for i in xrange(N_BOXES)]
		for i in xrange(TAIL_LEN):
			tail = [MultiSprite('-', tail[i]) for i in xrange(N_BOXES)] #+ [self.player]
		tail = [MultiSprite('+', tail[i]) for i in xrange(N_BOXES)]
		self.sprites = [MultiSprite('#', tail[i]) for i in xrange(N_BOXES)] + [self.player]

		for b in self.sprites[::]:
			b.move((random.randint(1,20), random.randint(1,20)))
			b.set_vel((random.randint(1,20), random.randint(1,20)))

		# each of these bindings is kind of like a game in itself, exiting when the state changes
		self.bind(0, self.initialize)
		self.bind(1, self.game_logic)
		self.bind(2, self.pause)


	def initialize(self):

		self.create_world()
		self.state = 1

	def set_paused(self):

		self.state = 3 - self.state

	def pause(self):

		self.poll_input()
		self.wait(int(self.dt*1000))

	def create_world(self):
		'''does the bindings'''

		self.bind_key('w', self.player.get_move((0,-1)))
		self.bind_key('a', self.player.get_move((-1,0)))
		self.bind_key('d', self.player.get_move((1,0)))
		self.set_physics_bounds()
		
		self.bind_key(curses.KEY_RESIZE, self.set_physics_bounds)

		self.bind_key('q', self.quit)
		self.bind_key(' ', self.wave)
		self.bind_key('p', self.set_paused)

		# rendering pipeline, should allocate a heap for sprites

	def set_physics_bounds(self):

		x, y = self.stdscr.getmaxyx()[::-1]
		self.physics.set_bounds(x, y)

	def game_logic(self):

		self.poll_input()

		for sprite in self.sprites: # special effects
			if isinstance(sprite, MultiSprite):
				sprite.trail()

		for sprite in self.sprites: # physics
			self.physics.update_sprite(sprite)

		self.conditional_state() # player control update
	
		self.draw() 
		self.wait(int(self.dt*1000)) # wait a little bit before starting again

	def conditional_state(self):
		if self.player.pos.y + self.player.shape[0] < self.physics.bounds.y:
			self.in_air()
		else:
			self.on_ground()

	def in_air(self):

		self.bind_key('d', partial(self.player.set_vel,(5,None)))
		self.bind_key('a', partial(self.player.set_vel,(-5,None)))
		if ord('s') in self.state_bindings:
			self.unbind_key('s')
		if ord('w') in self.state_bindings:
			self.unbind_key('w')

	def on_ground(self):

		self.bind_key('w', self.player.get_acc((0,10)))
		self.bind_key('a', self.player.get_move((-1,0)))
		self.bind_key('d', self.player.get_move((1,0)))

	def draw_sprites(self):

		for sprite in self.sprites:
			sprite.draw(self)

	def draw(self):
		''' run through the rendering pipeline'''
		self.clear()
		self.draw_sprites()
		self.draw_frame()

	def wave(self):

		self.player.image = '''*_*
\\|/
 | 
/ \\'''.strip().split('\n')
		self.bind_key(' ', self.unwave)
		self.draw()

	
	def unwave(self):
	
		self.player.image = '''*_*
/|\\
 | 
/ \\'''.strip().split('\n')
		self.bind_key(' ', self.wave)	
		self.draw()

	def clear(self):

		self.stdscr.clear()

	def reset(self):
		'''reset the game state, makes a function only execute once'''
		self.state = 0

	def draw_frame(self):

		self.stdscr.move(0,0)
		self.stdscr.refresh()

	def quit(self):
		
		self.running = False

	def set_state(self, state):

		self.state = state

if __name__ == '__main__':

	app = Game()

	
	app.mainloop()

		

