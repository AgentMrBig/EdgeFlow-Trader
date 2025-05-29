
import random
import matplotlib.pyplot as plt
from simulate_pnl import simulate_strategy

# Define parameter ranges
PARAM_SPACE = {
    "ma_period": (5, 20),
    "tp_pips": (5, 50),
    "sl_pips": (5, 50)
}

# Generate random individual
def generate_individual():
    return {
        "ma_period": random.randint(*PARAM_SPACE["ma_period"]),
        "tp_pips": random.randint(*PARAM_SPACE["tp_pips"]),
        "sl_pips": random.randint(*PARAM_SPACE["sl_pips"])
    }

# Mutate individual
def mutate(individual, mutation_rate=0.2):
    for key in individual:
        if random.random() < mutation_rate:
            individual[key] = random.randint(*PARAM_SPACE[key])
    return individual

# Crossover two individuals
def crossover(parent1, parent2):
    child = {}
    for key in parent1:
        child[key] = parent1[key] if random.random() < 0.5 else parent2[key]
    return child

# Evaluate fitness by running simulation and returning total PnL
def evaluate(individual):
    print(f"Evaluating: {individual}")
    result = simulate_strategy(
        ma_period=individual["ma_period"],
        tp_pips=individual["tp_pips"],
        sl_pips=individual["sl_pips"],
        silent=True  # Suppress output files for faster GA runs
    )
    return result.get("total_pnl", 0)

# Genetic algorithm main loop
def evolve(pop_size=10, generations=10):
    population = [generate_individual() for _ in range(pop_size)]
    best_fitnesses = []

    for gen in range(generations):
        scores = [(ind, evaluate(ind)) for ind in population]
        scores.sort(key=lambda x: x[1], reverse=True)
        best_fitness = scores[0][1]
        best_fitnesses.append(best_fitness)
        print(f"Generation {gen+1}: Best PnL = ${best_fitness:.2f}")

        survivors = [s[0] for s in scores[:pop_size // 2]]
        offspring = [mutate(crossover(random.choice(survivors), random.choice(survivors))) for _ in range(pop_size // 2)]
        population = survivors + offspring

    # Plot best fitness per generation
    plt.figure(figsize=(10, 5))
    plt.plot(range(1, generations + 1), best_fitnesses, marker="o")
    plt.title("Best PnL by Generation")
    plt.xlabel("Generation")
    plt.ylabel("Best Total PnL ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("genetic_fitness_plot.png")
    print("✅ Optimization complete. Plot saved as 'genetic_fitness_plot.png'")

if __name__ == "__main__":
    evolve()
    # Log best parameters to CSV
    with open("best_params_log.csv", "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow(["generation", "ma_period", "tp_pips", "sl_pips", "pnl"])
        writer.writerow([gen+1, best_ind['ma_period'], best_ind['tp_pips'], best_ind['sl_pips'], best_score])
    with open("best_params.json", "w") as jsonfile:
        json.dump({"generation": gen+1, "params": best_ind, "pnl": best_score}, jsonfile, indent=2)
    
