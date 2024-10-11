import math
import random
from threading import Event, Thread
import time
from queue import Queue, Empty

# GUI
import tkinter as tk
import uuid  # Pour générer un identifiant unique
from tkinter import ttk 

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

class Dish(Thread):
    
    def __init__(self, fct, nb_cells = 1000, nb_dim = 10, keep_best = 0.25, q=Queue, ask_quit=Event, started=Event, dish_id=str, **fct_cfg):

        Thread.__init__(self)

        self.nb_best_keep = int(keep_best * nb_cells)
        self.nb_cells = nb_cells
        self.nb_dim = nb_dim
        self.ngen = 1

        self.f = fct
        # Queue:
        self.q = q
        
        # Ask quit & Started:
        self.ask_quit = ask_quit
        self.started = started
        # Dish Id:
        self.dish_id = dish_id

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
        
      
        best_genome = self.cells[0].genome  # Meilleur génome complet

        # À chaque fin de génération, envoyer un dictionnaire "data" contenant les données de cette génération dans la Queue
        data = {"nb_generation": self.ngen,
                "best_output": self.cells[0].output,
                "best_genome": best_genome,
                "id": self.dish_id,
                "function_name": self.f
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
        while not self.ask_quit.is_set():
            self.started.wait(1)    
            while self.started.is_set() and (not self.ask_quit.is_set()):
                # Appeler la fonction new_generation
                self.new_generation()
                time.sleep(0.1)

# Création de MainWindow héritant de tkinter.tk
class MainWindow(tk.Tk):
    def __init__(self, q=Queue):
        tk.Tk.__init__(self)

        self.title("Algo génétique")
        self.q = q
        self.ask_quit = Event()
        self.started = Event()
        self.dish = []
        



        # Create a Visualiser instance
        self.visualiser = Visualiser(self)
        self.visualiser.pack(side="top", fill="both", expand=True)



        self.popup_open = False  # Attribut pour suivre l'état de la pop-up

        self.start_btn = tk.Button(self, text="Start", command=self.toogle_start)
        self.start_btn.pack(side="top")

        self.new_btn = tk.Button(self, text="New", command=self.new_algorithm)
        self.new_btn.pack(side="top")

        self.protocol("WM_DELETE_WINDOW", self.clean_exit)

        self.update()   

        try:
            self.mainloop()
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
            self.clean_exit()
    
    def toogle_start(self):
        if self.started.is_set():
            self.started.clear() # Arreter les algos
            self.start_btn.config(text="Start")
        else:
            self.ask_quit.clear()
            self.started.set()
            self.start_btn.config(text="Stop")
    
    def clean_exit(self):
        self.ask_quit.set()  # Indiquez que nous voulons quitter
        for dish in self.dish:
            dish.ask_quit.set()  # Demander à chaque thread de se terminer
            dish.join()  # Attendre que chaque thread se termine
        self.quit()  # Quitter la boucle principale
        self.destroy(   )

    
    def update(self):
        results = {}
        try:
            while True:
                data = self.q.get_nowait()
                print(f"Données reçues de la queue : {data}")
                results[data['id']] = data
                print(results)

                if data['id'] in self.visualiser.algo_visualisers:
                    print("Trouvé!") 
                    self.visualiser.update_visualiser(data)  # Call the update method on the visualizer
                    print("data envoyé au visualiser !")
        except Empty:
            pass

        # Planifier la prochaine mise à jour
        self.after(1000, self.update)




    def new_algorithm(self):
        try:
            # Create a pop-up
            
            popup = NewAlgoPopup(self)
            self.wait_window(popup)  # Attendre que le pop-up soit fermé
            # Retrieve the selected function after the pop-up is closed
            if popup.selected_function:
                print("function selected")
                
                Thread(target=self.start_new_dish, args=(popup,)).start()
                
            else:
                print("erreur")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")

    def start_new_dish(self, popup):
        # Create a new Dish object
        print(popup.algorithm_id)
        new_dish = Dish(popup.selected_function, nb_cells=popup.nb_cells, nb_dim=popup.nb_dim, keep_best=popup.keep_best, q=self.q, ask_quit=self.ask_quit, started=self.started, dish_id=popup.algorithm_id)
        self.dish.append(new_dish)  # Add to the list of Dish

        # Update the visualizer for the new algorithm
        # Create a new visualizer and add it to the visualizers dictionary
        self.visualiser.new_algo(popup.algorithm_id, popup.selected_function, popup.nb_dim)
        # Store the visualizer in the class variable
        self.visualiser.algo_visualisers[popup.algorithm_id] # Store the visualizer ID

        # Start the Dish thread
        new_dish.start()    
        print("Started the dish thread")
    

class NewAlgoPopup(tk.Toplevel):  # Pop up
    def __init__(self, window):
        super().__init__()  # Pas besoin de passer master ici
        self.window = window
        self.title("Nouvel Algorithme")  # Ajoutez un titre à la fenêtre
        self.geometry("200x200")  # Vous pouvez définir une taille pour la fenêtre
        self.minsize(500, 600)  

        self.title_label = tk.Label(self, text="Nouvel Algorithme")
        self.title_label.pack(pady=10)

        # Paramètres par défaut pour Dish
        self.nb_cells = 10000
        self.nb_dim = 10
        self.keep_best = 0.25
        self.function_name = "ackley"

        self.algorithm_id = None
        self.selected_function = None

        self.function_listbox = tk.Listbox(self)
        self.function_listbox.pack(side="top", fill=tk.BOTH, expand=True)

        for function in FONCTIONS.keys():
            self.function_listbox.insert(tk.END, function)

        self.accept_btn = tk.Button(self, text="Accept", command=self.accept)
        self.accept_btn.pack(side="bottom", pady=10)

        self.cancel_btn = tk.Button(self, text="Cancel", command=self.cancel)
        self.cancel_btn.pack(side="bottom", pady=5)

    def accept(self):
        self.algorithm_id = str(uuid.uuid4())
        selected_index = self.function_listbox.curselection()
        if selected_index:
            self.selected_function = self.function_listbox.get(selected_index[0])
            print(f"Fonction sélectionnée : {self.selected_function}")
            print(f"Identifiant de l'algorithme : {self.algorithm_id}")
            self.destroy()  # Ferme le frame après acceptation
        else:
            print("Aucune fonction sélectionnée.")


    def cancel(self):
        self.destroy()  # Ferme le frame sans faire d'actions


class Visualiser(tk.Frame):  # Frame
    def __init__(self, master=None, algo_id=None):
        super().__init__(master)
        self.master = master
        self.algo_id = algo_id
        
        self.algo_visualisers = {}

        # Labels to display algorithm information
        self.function_label = tk.Label(self, text="Function: N/A")
        self.function_label.grid(row=0, column=0, padx=10, pady=5)

        self.algorithm_id_label = tk.Label(self, text="Algorithm ID: N/A")
        self.algorithm_id_label.grid(row=1, column=0, padx=10, pady=5)

        self.generations_label = tk.Label(self, text="Generations: 0")
        self.generations_label.grid(row=2, column=0, padx=10, pady=5)

        self.best_output_label = tk.Label(self, text="Best Output: N/A")
        self.best_output_label.grid(row=3, column=0, padx=10, pady=5)

        self.best_genome_label = tk.Label(self, text="Best Genome: N/A")  # Initial value
        self.best_genome_label.grid(row=4, column=0, padx=10, pady=5)

    def new_algo(self, algo_id, function_name, num_dimensions):
        # Create labels for the new algorithm information
        algo_id_label = tk.Label(self, text=f"Algorithm ID: {algo_id}")
        algo_id_label.grid(row=0, column=len(self.algo_visualisers) + 1, padx=10, pady=5)

        generations_label = tk.Label(self, text="Generations: 0")  # Initial value
        generations_label.grid(row=1, column=len(self.algo_visualisers) + 1, padx=10, pady=5)

        best_output_label = tk.Label(self, text="Best Output: N/A")  # Initial value
        best_output_label.grid(row=2, column=len(self.algo_visualisers) + 1, padx=10, pady=5)
        
        best_genome_label = tk.Label(self, text="Best Genome: N/A")  # Initial value
        best_genome_label.grid(row=3, column=len(self.algo_visualisers) + 1, padx=10, pady=5)
        
        # Create a list to visualize genomes
        genome_visualiser = []

        # Create a Progressbar for each dimension
        for dim in range(num_dimensions):
            progress_bar = ttk.Progressbar(self, maximum=1000)
            progress_bar.grid(row=4 + dim, column=len(self.algo_visualisers) + 1, padx=10, pady=5)
            genome_visualiser.append(progress_bar)  # Add the progress bar to the genome visualizer list

        # Store the new visualizer data in the dictionary
        self.algo_visualisers[algo_id] = {
            "fct": algo_id_label,
            "nb_gen": generations_label,
            "output": best_output_label,
            "genome": genome_visualiser,
            "function_name": function_name  # Store the function name
        }

        # Update the function label with the selected function name
        self.function_label.config(text=f"Function: {function_name}")
        
    
    def update_visualiser(self, data):
        # Mettre à jour les labels avec les dernières données 
        algo_id = data['id']
        if algo_id in self.algo_visualisers:
            # Mettre à jour les informations de génération et de sortie
            self.algo_visualisers[algo_id]["nb_gen"].config(text=f"Generations: {data['nb_generation']}")
            self.algo_visualisers[algo_id]["output"].config(text=f"Best Output: {data['best_output']}")
            
            # Mettre à jour le nom de la fonction
            self.algo_visualisers[algo_id]["fct"].config(text=f"Function: {self.algo_visualisers[algo_id]['function_name']}")

            # Mettre à jour la barre de progression pour chaque gène du meilleur génome
            best_genome_full = data['best_genome']  # Utiliser le meilleur génome complet
            genome_visualiser = self.algo_visualisers[algo_id]["genome"]
            for g, gene in enumerate(best_genome_full):
                if g < len(genome_visualiser):  # Assurez-vous que l'indice est valide
                    genome_visualiser[g].config(value=int(gene * 1000))  # Mettre à jour la valeur de la barre de progression





if __name__ == "__main__":
    q = Queue()
    window = MainWindow(q)
    window.mainloop()
