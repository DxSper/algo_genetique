import math
import random
from threading import Event, Thread
import time
from queue import Queue, Empty

## CTRL + C (KbInterrupt) Fix:
import sys
import win32api

def handler(a, b=None):
    sys.exit(1)
def install_handler():
    if sys.platform == "win32":
        win32api.SetConsoleCtrlHandler(handler, True)

install_handler()
##



def genome_translate(f):
    def function(genome, higher=40, lower=-40, **fct_cfg):
        inputs = [(x * (higher - lower)) + lower for x in genome]
        return f(inputs, **fct_cfg)
    return function



@genome_translate
def ackley(inputs, a=20, b=0.2, c=2.0 * math.pi):
    assert len(inputs) > 0
    ninv = 1 / len(inputs)
    sum1 = sum([x**2 for x in inputs])
    sum2 = sum([math.cos(c * x) for x in inputs])
    return a + math.exp(1) - (a * math.exp((-b)*math.sqrt(ninv * sum1))) - math.exp(ninv * sum2)

assert ackley([0.5]) < 1e-15
assert ackley([0.5, 0.5, 0.5]) < 1e-15

@genome_translate
def alpine1(inputs):
    return sum([abs(x * math.sin(x) + (0.1 * x)) for x in inputs])

assert alpine1([0.5]) < 1e-15
assert alpine1([0.5, 0.5, 0.5]) < 1e-15
assert alpine1([0.0, 1.0, 0.0]) > 1e-15


FONCTIONS = {
    "alpine1": alpine1,
    "ackley": ackley,
}



class Cell:
    def __init__(self, f, genome, **fct_cfg):
        self.genome = genome
        self.output = None
        self.fct_cfg = fct_cfg
        self.f = f

    def apply(self):
        self.output = self.f(self.genome, **self.fct_cfg)

    def reset(self):
        self.output = None

    def child(self):
        new_genome = self.genome.copy()
        i = random.randrange(0, len(self.genome))
        new_genome[i] = random.random()
        return Cell(self.f, new_genome, **self.fct_cfg)


Ev = Event()


class Dish(Thread):

    def __init__(self, fct, nb_cells = 1000, nb_dim = 1, keep_best = 0.25, q=Queue, **fct_cfg):

        Thread.__init__(self)

        self.nb_best_keep = int(keep_best * nb_cells)
        self.nb_cells = nb_cells
        self.nb_dim = nb_dim
        self.ngen = 1
        # Queue:
        self.q = q
        
        self.cells = []
        for _ in range(0, self.nb_cells):
            self.genome = [random.random() for _ in range(self.nb_dim)]
            cell = Cell(FONCTIONS[fct], self.genome, **fct_cfg)
            self.cells.append(cell)
        
        

    def new_generation(self):
        
        # Contient le code pour chaque génération
        for cell in self.cells:
            cell.apply()

        self.cells = sorted(self.cells, key=lambda cell: cell.output)

        best_genome_avg = sum(self.cells[0].genome) / len(self.cells[0].genome)
        
        best_genome = min(self.cells[0].genome)
        

        # À chaque fin de génération, envoyer un dictionnaire "data" contenant les données de cette génération dans la Queue
        data = {"nb_generation": self.ngen,
                "best_output": self.cells[0].output,
                "best_genome": best_genome
                }
        
        # Mettre les données dans la queue 
        self.q.put(data)

        # Effacer de la liste les X% les plus faibles
        self.cells = self.cells[:self.nb_best_keep]

        # Créer des enfants jusqu'à ce que la population soit entière
        nb_cell = 0
        while len(self.cells) < self.nb_cells:
            child_cell = self.cells[nb_cell % self.nb_best_keep].child()
            self.cells.append(child_cell)
            nb_cell += 1

        for cell in self.cells:
            cell.reset()

        # Incrémente le compteur de génération
        self.ngen += 1

    def run(self):
        # Boucle infinie
        # Attendre que l'évent soit True:
        while Ev.is_set():
            # Appeler la fonction new_generation
            self.new_generation()








# Création de la Queue
result_queue = Queue()
# Création des objets Dish
ObjDish1 = Dish("ackley", nb_dim=100, q=result_queue, a=40)
ObjDish2 = Dish("ackley", nb_dim=100, q=result_queue, a=40)
# Autorisé (event True)
Ev.set()
ObjDish1.start()
ObjDish2.start()
# Connaitre le temps actuelle 
tstart = time.time()

while (time.time() - tstart) < 10:  # Si on a commencé il y a moins de 10 sec
    try:
        # Récupéré les items dans la queue en boucle et les afficher
        while True:
            data = result_queue.get_nowait() # Utilisation de nowait pour ne pas bloquer la queue
            print(data) # affichage des données
    except Empty:
        pass  # Si les données sont vide
    
Ev.clear()
print("Fini !")


