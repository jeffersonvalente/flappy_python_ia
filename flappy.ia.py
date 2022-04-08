import pygame
import neat
import time
import os
import random
import visualize
import pickle
import random
pygame.font.init()

#dificuldade
PIMP_VEL = 10
#PIMP_HEIGHT= random.randrange(55, 550)

#tamanho da tela
WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 40)
END_FONT = pygame.font.SysFont("comicsans", 60)
DRAW_LINES = False
#melhor = print('\nBest genome:\n{!s}'.format(winner))

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy IA do Jeffin")

#importação das imagens do jogo e rescala o tamanho em 2x
pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())
gen = 0
#winner = 0

#classe do passaro
class Bird:
    IMGS = bird_images
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
        self.vel = -PIMP_VEL #faz subir na tela
        self.tick_count = 0
        self.height = self.y
    
    #adiciona descida    
    #def down(self):
    #    self.vel = +(PIMP_VEL*2) #faz subir na tela
    #    self.tick_count = 0
    #    self.height = self.y
        
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
#   VEL = 20 #aumetnar aumenta a dificuldade
    VEL = PIMP_VEL
    def __init__(self,x):
        self.x = x
        self.height = 0
                
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False
        self.set_height()
    
    #função do posicionamento dos canos    
    def set_height(self):
        #self.height = random.randrange(50, 550) #aumentar aumeta a dificuldade MAX 650
        self.height = random.randrange(75, 550)
        self.top = self.height - self.PIPE_TOP.get_height()#ajusta o cano no topo
        self.bottom = self.height + self.GAP
    
    #movimento dos canos
    def move(self):
        self.x -= self.VEL
        
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top)) #desenha no topo
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom)) #desenha embaixo
    
    #colisão cmo os canos
    def collide (self, bird, win):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask,top_offset)

        if b_point or t_point:
            return True

        return False
    
class Base:
    VEL = PIMP_VEL
    WIDTH = base_img.get_width()
    IMG = base_img
    
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH
        
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
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

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0,0))
    
    for pipe in pipes:
       pipe.draw(win)
    
    base.draw(win)  
    for bird in birds:
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255,0,0), (bird.x+bird.img.get_width()/2, bird.y + bird.img.get_height()/2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # draw bird
        bird.draw(win)

    #placar
    score_label = STAT_FONT.render("Placar " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # gen
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # vivo
    score_label = STAT_FONT.render("Vivo: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))
    
    #melhor
#    score_label = STAT_FONT.render("Melhor: " + str(len(winner)),1,(255,255,255))
#    win.blit(score_label, (10, 50))

        
    pygame.display.update()
 
def eval_genomes(genomes, config):
    global WIN, gen
    win = WIN
    gen += 1
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0   
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230,350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0
    clock = pygame.time.Clock()
    run = True
    paused = False
    
    while run and len(birds) > 0:
        clock.tick(120)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
        if paused == True:
            continue
                           
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
                
        
        #faz o bichinho se mexer sozinho
        for x, bird in enumerate(birds):
            ge[x].fitness += 0.1
            bird.move()
            
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            
            if output[0] > 0.5:
                bird.jump()
            #else:
            #    bird.down()
        
        base.move()
        
        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move() #cria o laço principal dos pipes
            
            #ajusta colisão
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
                
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
                

        if add_pipe: #marca os pontos
            score += 1
            for genome in ge:
                genome.fitness +=5
            pipes.append(Pipe(WIN_WIDTH)) #altera distancia entre os canos
            
        for r in rem: 
            pipes.remove(r)
        
        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))
                
                           
        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)
        if score > 99:
            paused = True
        #if score > 20: #quando o score chega reinicia com o melhor da geração passada
        #    pickle.dump(nets[0],open("best.pickle", "wb"))
        #    break
         

def run(config_path): #cria a rede que vai treinar
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_path)
    
    #cria a população
    p = neat.Population(config)
    
    #saida dos resultados
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    #melhor das gerações
    winner = p.run(eval_genomes, 10000)#altera o numero gerações
    print('\nBest genome:\n{!s}'.format(winner))
    

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path =os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
    






