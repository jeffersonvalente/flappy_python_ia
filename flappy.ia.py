import pygame
import neat
import time
import os
import random
pygame.font.init()


#tamanho da tela
WIN_WIDTH = 500
WIN_HEIGHT = 800


#importação das imagens do jogo e rescala o tamanho em 2x
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
             pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
             pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))

STAT_FONT = pygame.font.SysFont('comicsans', 50)

#classe do passaro
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0 #posição q o passaro olha
        self.tick_count = 0 #contatodor de movimento do passarinho
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]
        
    def jump(self):
        self.vel = -10.5 #faz subir na tela
        self.tick_count = 0
        self.height = self.y
        
    def move(self):
        self.tick_count += 1

        # aceleração de queda
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # calculate displacement

        # velocidade do terminal
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # tilt up
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  #tilt para baixo
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
   
    def draw(self, win):
        self.img_count += 1
        
        #verifica qual imagem usar
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        
        #garente qeu a imagem do passarinho caindo seja usada ao cair
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2     
        
        #rotacionar as imagens
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)
        
    def get_mask(self):
        return pygame.mask.from_surface(self.img)
    
class Pipe: #criando os canos
    GAP = 200
    VEL = 5
    
    def __init__(self,x):
        self.x = x
        self.height = 0
                
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) #inverte a imagem do cano no topo
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()
    
    #função do posicionamento dos canos    
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()#ajusta o cano no topo
        self.bottom = self.height + self.GAP
    
    #movimento dos canos
    def move(self):
        self.x -= self.VEL
        
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top)) #desenha no topo
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom)) #desenha embaixo
    
    #colisão cmo os canos
    def collide (self, bird):
        bird_mask = bird.get_mask() #mascaras de pixels
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        
        if t_point or b_point:
            return True
        
        return False
    
class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
        
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        #formula para dar continuidade a tela
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH
    
    def draw(self,win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))
  
  
#função para rotacionar a imagem              
def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0))
    
    for pipe in pipes:
       pipe.draw(win)
      
    text = STAT_FONT.render("Score: " +str(score), 1,(255,255,255))
    win.blit(text,(WIN_WIDTH - 10 - text.get_width(), 10)) #
    
    base.draw(win)
        
    bird.draw(win)
    pygame.display.update()
 
def main(genomes, config):
    nets = []
    ge= []    
    birds = []
    
    for g in genomes:
        net = neat.nn.FeedForwardNetwork(g, config)
        nets.append(nets)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)
        
        
        
    base = Base(730)
    pipes = [Pipe(600)] #altera distancia entre os canos
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock =pygame.time.Clock()
    
    score = 0
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        
        #bird.move()
        add_pipe = False
        rem = []
        for pipe in pipes:#cria o laço principal dos pipes
            for x, bird in enumarete(birds):
                if pipe.collide(bird):
                    ge[x].fitness =- 1 #cada vez que o passaro bate no cano eh expulso
                    birds.pop(x) 
                    nets.pop(x)
                    ge.pop(x)
                    
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            pipe.move()
                
        if add_pipe: #adiciona placar
            score += 1
            pipes.append(Pipe(600)) #altera distancia entre os canos
            
        for r in rem: 
            pipes.remove(r)
        
        for bird in birds:
            if bird.y + bird.img.get_height() >= 730: #bate no chao
                pass
        
            
        base.move()
        draw_window(win, bird, pipes, base, score)
        
    pygame.quit()
    quit()            
                
main()

def run(config_path): #cria a rede que vai treinar
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path) #chama as propriedades do arquivo
    
    #cria a população
    p = neat.Population(config)
    
    #saida dos resultados
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    winner = p.run(,50)
    
 
if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path =os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
    






