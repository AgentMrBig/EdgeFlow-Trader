
import random
import csv
import matplotlib.pyplot as plt
from simulate_pnl import simulate_strategy

POPULATION_SIZE = 10
GENERATIONS = 20
MUTATION_RATE = 0.2

def random_params():
    return {
        "ma_period": random.randint(5, 20),
        "tp_pips": random.randint(10, 50),
        "sl_pips": random.randint(5, 50),
    }

def mutate(params):
    new_params = params.copy()
    if random.random() < MUTATION_RATE:
        new_params["ma_period"] = random.randint(5, 20)
    if random.random() < MUTATION_RATE:
        new_params["tp_pips"] = random.randint(10, 50)
    if random.random() < MUTATION_RATE:
        new_params["sl_pips"] = random.randint(5, 50)
    return new_params

def crossover(p1, p2):
    return {
        "ma_period": random.choice([p1["ma_period"], p2["ma_period"]]),
        "tp_pips": random.choice([p1["tp_pips"], p2["tp_pips"]]),
        "sl_pips": random.choice([p1["sl_pips"], p2["sl_pips"]]),
    }

def evaluate(params):
    print(f"Evaluating: {params}")
    result = simulate_strategy(
        ma_period=params["ma_period"],
        tp_pips=params["tp_pips"],
        sl_pips=params["sl_pips"],
        output_csv="simulated_trades.csv",
        performance_log="timeblock_profit.csv",
        equity_curve_png=None,
        silent=True
    )
    return result.get("total_pnl", 0) if result else 0

def evolve():
    population = [random_params() for _ in range(POPULATION_SIZE)]
    history = []

    with open("generation_log.csv", "w", newline="") as logf:
        writer = csv.writer(logf)
        writer.writerow(["Generation", "BestPnL", "BestParams"])

        for gen in range(1, GENERATIONS + 1):
            scores = [(ind, evaluate(ind)) for ind in population]
            scores.sort(key=lambda x: x[1], reverse=True)
            best_individual, best_score = scores[0]
            writer.writerow([gen, best_score, best_individual])
            print(f"Generation {gen}: Best PnL = ${best_score:.2f} with Params = {best_individual}")
            history.append(best_score)

            next_gen = [best_individual]
            while len(next_gen) < POPULATION_SIZE:
                parent1 = random.choice(scores[:5])[0]
                parent2 = random.choice(scores[:5])[0]
                child = mutate(crossover(parent1, parent2))
                next_gen.append(child)
            population = next_gen

    plt.plot(range(1, GENERATIONS + 1), history, marker="o")
    plt.xlabel("Generation")
    plt.ylabel("Best Total PnL ($)")
    plt.title("Strategy Optimization Progress")
    plt.grid(True)
    plt.savefig("optimization_progress.png")
    print("Optimization progress plot saved to optimization_progress.png")

if __name__ == "__main__":
    evolve()
