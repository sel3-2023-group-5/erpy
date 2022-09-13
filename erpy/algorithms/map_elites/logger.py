from dataclasses import dataclass
from typing import Type, List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import wandb

from erpy.algorithms.map_elites.population import MAPElitesPopulation
from erpy.loggers.wandb_logger import WandBLoggerConfig, WandBLogger


@dataclass
class MAPElitesLoggerConfig(WandBLoggerConfig):
    archive_dimension_labels: List[str]
    normalize_heatmaps: bool

    @property
    def logger(self) -> Type[WandBLogger]:
        return MAPElitesLogger


class MAPElitesLogger(WandBLogger):
    def __init__(self, config: MAPElitesLoggerConfig):
        super(MAPElitesLogger, self).__init__(config=config)

    @property
    def config(self) -> MAPElitesLoggerConfig:
        return super().config

    def log(self, population: MAPElitesPopulation) -> None:
        # Log archive fitnesses
        fitnesses = [cell.evaluation_result.fitness for cell in population.archive.values()]
        super()._log_values(name='archive/fitness', values=fitnesses, step=population.generation)

        # Log archive ages
        ages = [cell.genome.age for cell in population.archive.values()]
        super()._log_values(name='archive/age', values=ages, step=population.generation)

        # Log archive coverage
        coverage = population.coverage

        # Log a 2D heatmap
        if len(population.config.archive_dimensions) == 2:
            x_dim, y_dim = population.config.archive_dimensions
            fitness_map = np.zeros((x_dim, y_dim))

            for cell_index, cell in population.archive.items():
                x, y = cell_index
                fitness = cell.evaluation_result.fitness
                if abs(fitness) != np.inf:
                    fitness_map[x, y] = fitness

            mask = fitness_map == 0
            if self.config.normalize_heatmaps:
                fitness_map /= np.max(fitness_map)

            ax = sns.heatmap(fitness_map, mask=mask, linewidth=0., xticklabels=[0] + [None] * (x_dim - 2) + [1],
                             yticklabels=[0] + [None] * (y_dim - 2) + [1],
                             vmin=0,
                             vmax=np.max(fitness_map))
            ax.set_xlabel(self.config.archive_dimension_labels[0])
            ax.set_ylabel(self.config.archive_dimension_labels[1])
            ax.invert_yaxis()

            wandb.log({'archive/coverage': coverage,
                       'archive/normalized_fitness_map': wandb.Image(ax)}, step=population.generation)
            plt.close()
