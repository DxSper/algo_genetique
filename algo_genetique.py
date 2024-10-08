import math
import random

# Étape 1
a = 20
b = 0.2
c = 2.0 * math.pi

def map_input(genome, higher, lower):
    return [x * (higher - lower) + lower for x in genome]

# Fonction Ackley
def mon_decorateur(f):
    def fonction_modifiee(genome, **fct_cfg):
        higher = fct_cfg['a']
        lower = fct_cfg['b']
        input_traduits = map_input(genome, higher, lower)
        return f(input_traduits)
    return fonction_modifiee

@mon_decorateur
def ackley(inputs, a=20, b=0.2):
    assert len(inputs) > 0
    ninv = 1 / len(inputs)
    sum1 = sum([x**2 for x in inputs])
    sum2 = sum([math.cos(c * x) for x in inputs])
    return a + math.exp(1) - (a * math.exp((-b) * math.sqrt(ninv * sum1))) - math.exp(ninv * sum2)


@mon_decorateur
def rosenbrock(inputs, a=1, b=100):
    assert len(inputs) > 1
    return sum(b * (inputs[i + 1] - inputs[i] ** 2) ** 2 + (a - inputs[i]) ** 2 for i in range(len(inputs) - 1))

# Dictionnaire des fonctions 
function_dict = {
    'ackley': ackley,
    'rosenbrock': rosenbrock
}

# Tests

print(ackley([0.5, 0.5, 0.5], a=40, b=-40))
print(rosenbrock([0.5, 1.0, 0.0], a=10, b=-5))
print("test réussie")


# Étape 4
import random

class Cell:
    def __init__(self, genome, function, **fct_cfg):
        self.genome = genome
        self.output = None
        self.function = function # je sauvegarde la fonction original
        
        self.fct_cfg = fct_cfg
        
    def apply(self):
        self.output = self.function(self.genome, **self.fct_cfg)

    def reset(self):
        self.output = None

    def child(self):
        new_genome = self.genome.copy()
        i = random.randrange(0, len(self.genome))
        new_genome[i] = random.random()
        return Cell(new_genome, self.function, **self.fct_cfg)

# Étape 5

def main(**initialisation):
    
    # Initialisation avec **kwargs
    NB_CELLS_TOTAL = initialisation.get('nb_cells_total', 1000)
    NB_DIMENSIONS = initialisation.get('nb_dimensions', 10)
    NB_BEST_KEEP = int((initialisation.get('nb_best_keep') / 100.0) * NB_CELLS_TOTAL)

    function_cells = initialisation.get('funct_used')
    fctconfig = initialisation.get('config')
    cells = []
    for _ in range(0, NB_CELLS_TOTAL):
        genome = [random.random() for _ in range(NB_DIMENSIONS)]
        cells.append(Cell(genome, function_cells, a=fctconfig['a'], b=fctconfig['b']))
    ngen = 1


    # Boucle infinie
    while True:
        for cell in cells:
            cell.apply()

        cells = sorted(cells, key=lambda cell: cell.output)

        best_genome_avg = sum(cells[0].genome) / len(cells[0].genome)
        print("{}| Best score {}, genome min {} < avg {} < max {}".format(
            ngen,
            cells[0].output,
            min(cells[0].genome),
            best_genome_avg,
            max(cells[0].genome)
        ))

        # Effacer de la liste les X% les plus faibles
        cells = cells[:NB_BEST_KEEP]

        # Créer des enfants jusqu'à ce que la population soit entière
        nb_cell = 0
        while len(cells) < NB_CELLS_TOTAL:
            child_cell = cells[nb_cell % NB_BEST_KEEP].child()
            cells.append(child_cell)
            nb_cell += 1

        for cell in cells:
            cell.reset()

        ngen += 1


fct_cfg = {}
fct_cfg['a'] = 40
fct_cfg['b'] = -40

main(nb_cells_total=10000, nb_dimension=100, nb_best_keep=25.0, funct_used=function_dict['ackley'], config=fct_cfg)