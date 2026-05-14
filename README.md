# Code Repository

This repository contains the complete codebase for my **Honours year project**, based on research into cost-effective deployment and optimisation of next-generation (B5G/6G) reconfigurable RAN and optical X-haul networks. It includes implementations, datasets, and utilities for generating, analysing, and optimising network configurations.

Algorithms provided:

- **Greedy Algorithm:** Fast, heuristic-based solutions for initial network configurations.
- **Genetic Algorithm:** Evolutionary optimisation for exploring larger solution spaces.
- **Local Search:** Iterative improvement for refining solutions.
- **CPLEX Models:** Exact mathematical programming approaches, including shortest-path and full graph optimisation.

Helper scripts are included for preprocessing data, running batch experiments, and analysing results.

The project explores deployment strategies for next-generation (B5G/6G) reconfigurable RAN and optical X-haul networks, balancing **cost, scalability, and performance**.

---

**Associated Research Papers:**

- [**Optical X-haul for Beyond 5G: Cost-effective Deployment Strategies**](https://opg.optica.org/abstract.cfm?uri=OFC-2025-M1I.3)  
  *Presented at the Optical Fiber Communication Conference (OFC) 2025.*  
  Focus: CPLEX shortest path model for efficient X-haul deployment.

- [**Cost Optimal Network Planning for Converged Optical X-haul in Beyond 5G Networks**](https://doi.org/10.1364/JOCN.567406)  
  *Published in the Journal of Optical Communications and Networking (JOCN).*  
  Focus: CPLEX full graph model with Steiner tree post-processing for optimal network design.

- **Genetic Algorithm for Multi-layered Location-Allocation-Routing Problems in Network Planning**  
  *Submitted to Operations Research (under review).*  
  Focus: Establishes the Steiner tree theorem and demonstrates the genetic algorithm as a scalable alternative to CPLEX for large datasets.
<!-- [Paper 3 Title](link) -->  

**Deakin Mathematics Yearbook Report:**  

- [A cost effective framework fo the design and deployment of B5G in rural Australia](https://dro.deakin.edu.au/articles/book/Mathematics_Yearbook_2024/29670008?file=57115337) - published in the Deakin Mathematics Yearbook 2024.

---

## Citation

If you use this repository, datasets, or implementations in academic work, please cite this repository.

GitHub provides a built-in **"Cite this repository"** option via the repository sidebar.

### BibTeX

```bibtex
@software{laird2025networkplanning,
  author = {Laird, Brianna and Ranaweera, Chathurika and Ugon, Julien},
  title        = {B5G Network Planning Algorithms},
  year         = {2025-09-15},
  url          = {https://github.com/breezy-codes/B5G-network-planning-algorithms}
}
```

---

## Repository Structure

The project is organised into modular components. Below is the folder layout, along with a description of each directory:

> 📂 **[Repository](.)/**
>
> - 📁 [code](code)/ — *Core source code*
>   - 📁 [logs](code/logs)/ — *Experiment logs*
>   - 📁 [modules](code/modules)/ — *Shared modules & utilities*
>     - 📁 [algorithms](code/modules/algorithms)/ — *Algorithm-specific helpers*
>     - 📁 [data-classes](code/modules/data_classes)/ — *Custom dataclasses for components*
>     - 📄 [README.md](code/modules/README.md) — *Guide to the modules and algorithms*
>   - 📁 [results](code/results)/ — *Results from algorithm & CPLEX runs*
>   - 🐍 [CPLEX_graph_model.py](code/CPLEX_graph_model.py) — *CPLEX full graph model implementation*
>   - 🐍 [CPLEX_shortest_path.py](code/CPLEX_shortest_path.py) — *CPLEX shortest-path model implementation*
>   - 🐍 [genetic_algorithm.py](code/genetic_algorithm.py) — *Genetic algorithm implementation*
>   - 📓 [greedy_solution_generator.ipynb](code/greedy_solution_generator.ipynb) — *Greedy algorithm implementation notebook*
>   - 🐍 [local_search.py](code/local_search.py) — *Local search algorithm implementation*
>   - 📄 [README.md](code/README.md) — *Guide to running algorithms*
>
> - 📁 [dataset](dataset)/ — *Input datasets*
>   - 📁 [full-dataset](dataset/full-dataset)/ — *Large-scale experiments*
>   - 📁 [small-dataset](dataset/small-dataset)/ — *Debug & quick runs*
>   - 📄 [README.md](dataset/README.md) — *Dataset format & usage*
>
> - 📁 [figures](figures)/ — *Diagrams, plots, and figures*
>
> - 📁 [scripts](scripts)/ — *Processing & analysis tools*
> - 📄 [LICENSE](LICENSE) — *Project license*
> - 📄 [requirements.txt](requirements.txt) - *Python requirements for the project*
> - 📄 [README.md](README.md) — *Main repository documentation*

---

## Algorithms

### Greedy Algorithm

- **Purpose:** Provides a fast, heuristic-based solution for initial network configurations.
- **Advantages:** Lightweight, quick to implement, and useful as a baseline.
- **Implementation:** See [`code/greedy_solution_generator.ipynb`](code/greedy_solution_generator.ipynb).

### Genetic Algorithm

- **Purpose:** Explores larger solution spaces through evolutionary optimisation.
- **Advantages:** Finds higher-quality solutions at the cost of runtime and computational resources.
- **Implementation:** See [`code/genetic_algorithm.py`](code/genetic_algorithm.py).
- **Features:**
  - Customisable crossover and mutation operators
  - Configurable selection strategies
  - Logging of population performance over time

### Local Search

- **Purpose:** Provides an alternative to genetic algorithms for refining solutions via iterative improvement.
- **Advantages:** Efficient for fine-tuning and escaping local optima.
- **Implementation:** See [`code/local_search.py`](code/local_search.py).

### CPLEX Models (Exact Solution Methods)

- **CPLEX Shortest Path:** Uses mathematical programming to find exact optimal network paths.
  - **Implementation:** See [`code/CPLEX_shortest_path.py`](code/CPLEX_shortest_path.py).
- **CPLEX Graph Model:** Provides full graph-based optimisation for deployment strategies, delivering exact solutions.
  - **Implementation:** See [`code/CPLEX_graph_model.py`](code/CPLEX_graph_model.py).

---

## Datasets

The repository includes two datasets designed on a region within rural Australia, each tailored for different testing scenarios:

- **Full Dataset:**
  Large-scale, complex data designed to fully test algorithms and evaluate scalability.

- **Small Dataset:**
  Simplified data for debugging, quick experiments, and verifying correctness.

See the [README in `dataset/`](./dataset/README.md) for details on dataset structure and usage.

---

## Scripts and Utilities

Located in the `scripts/` directory, these tools support:

- **Dataset Updates:** Updating dataset files when changes are made.
- **Visualisation:** Viewing datasets on a map and plotting algorithm iteration results.

See the [README in `scripts/`](./scripts/README.md) for details on available scripts and their usage.

---

## Figures

The `figures/` folder stores images, diagrams, and charts used for documentation within this README. This includes dataset visualisations.

---

## Results

Algorithm outputs are stored under `heuristic-algorithm/results/`, with logs in `heuristic-algorithm/code/logs/`.

---

## Meet the Lead Developer (kidding!)

<table>
  <tr>
    <td align="center">
      <img src="https://briannalaird.com/_images/phoebe1.JPG" alt="Phoebe the cat with the code" width="500px"><br>
      <strong>Phoebe: Lead Developer</strong>
    </td>
    <td align="center">
      <img src="https://briannalaird.com/_images/phoebe2.JPG" alt="Phoebe the cat with the code" width="500px"><br>
      <strong>Phoebe: Chief Bug Finder</strong>
    </td>
  </tr>
</table>

> **Contribution Rule:** If you submit code, you must include a photo of your cat.
> No cat? No commit! (Phoebe enforces this strictly.)

---

## Getting Started

1. **Clone the repository:**

   ```bash
   git clone https://github.com/breezy-codes/B5G-network-planning-algorithms.git
   cd B5G-network-planning-algorithms
   ```

2. **Install dependencies** (Python 3.9+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

3. **Explore the project:**  
   Review the folder structure and documentation to understand available algorithms, datasets, and utilities.

4. **Run experiments:**
   - For the **Greedy Algorithm**, open and run the notebook:

     ```bash
     jupyter notebook code/greedy_solution_generator.ipynb
     ```

   - For the **Genetic Algorithm**, execute:

     ```bash
     python code/genetic_algorithm.py
     ```

   - For the **Local Search**, run:

     ```bash
     python code/local_search.py
     ```

   - For **CPLEX models**, execute either:

     ```bash
     python code/CPLEX_shortest_path.py
     ```

     or

     ```bash
     python code/CPLEX_graph_model.py
     ```

5. **Inspect results:**
   - Outputs will be saved in the [`results/`](code/results/) directory.
   - Logs can be found in [`code/logs/`](code/logs/).
   - Use the provided scripts in [`scripts/`](scripts/) for further analysis or visualisation of results.

---

## Contribution Guidelines

- Fork the repository and create a feature branch.
- Add documentation for all new scripts or algorithms.
- Include experiment logs and a summary of results for reproducibility.
- Optional (but encouraged): Share a photo of your cat colleague.

---

## License

This project is released under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.
