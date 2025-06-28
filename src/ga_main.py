# -*- coding: utf-8 -*-
import os
import sys
import random
import re
import codecs
import subprocess
import time
import locale
import configparser
import pandas as pd
from decimal import Decimal
from src.util import Utilty

# Type of printing.
OK = 'ok'         # [*] Used for successful operations.
NOTE = 'note'     # [+] Used for informational messages.
FAIL = 'fail'     # [-] Used for failed operations.
WARNING = 'warn'  # [!] Used for warning messages.
NONE = 'none'     # No label.

# -----------------------------------------------------------------------------
# Gene class: Container for a single gene (individual) in the genetic algorithm.
# -----------------------------------------------------------------------------
class Gene:
    genom_list = None      # List of gene indices representing the individual's genome.
    evaluation = None      # Fitness score of the individual.

    def __init__(self, genom_list, evaluation):
        """
        Initialize a Gene object.

        Args:
            genom_list (list): List of gene indices.
            evaluation (float): Fitness score.
        """
        self.genom_list = genom_list
        self.evaluation = evaluation

    def getGenom(self):
        """Return the genome list."""
        return self.genom_list

    def getEvaluation(self):
        """Return the evaluation (fitness score)."""
        return self.evaluation

    def setGenom(self, genom_list):
        """Set the genome list."""
        self.genom_list = genom_list

    def setEvaluation(self, evaluation):
        """Set the evaluation (fitness score)."""
        self.evaluation = evaluation

# -----------------------------------------------------------------------------
# GeneticAlgorithm class: Implements the genetic algorithm for code generation.
# -----------------------------------------------------------------------------
class GeneticAlgorithm:
    def __init__(self, template, browser):
        """
        Initialize the GeneticAlgorithm object.

        Args:
            template: Jinja2 template object for HTML rendering.
            browser: Selenium WebDriver object for browser automation.
        """
        self.util = Utilty()
        self.template = template
        self.obj_browser = browser

        # Read configuration from config.ini file.
        full_path = os.path.dirname(os.path.abspath(__file__))
        config = configparser.ConfigParser()
        try:
            config.read(self.util.join_path(full_path, '../config/config.ini'))
        except FileExistsError as e:
            self.util.print_message(FAIL, 'File exists error: {}'.format(e))
            sys.exit(1)
        # Load common settings from config.
        self.wait_time = float(config['Common']['wait_time'])
        self.html_dir = self.util.join_path(full_path, config['Common']['html_dir'])
        self.html_template = config['Common']['html_template']
        self.html_template_path = self.util.join_path(self.html_dir, self.html_template)
        self.html_file = config['Common']['ga_html_file']
        self.result_dir = self.util.join_path(full_path, config['Common']['result_dir'])

        # Load genetic algorithm parameters from config.
        self.genom_length = int(config['Genetic']['genom_length'])
        self.max_genom_list = int(config['Genetic']['max_genom_list'])
        self.select_genom = int(config['Genetic']['select_genom'])
        self.individual_mutation_rate = float(config['Genetic']['individual_mutation_rate'])
        self.genom_mutation_rate = float(config['Genetic']['genom_mutation_rate'])
        self.max_generation = int(config['Genetic']['max_generation'])
        self.max_fitness = int(config['Genetic']['max_fitness'])
        self.gene_dir = self.util.join_path(full_path, config['Genetic']['gene_dir'])
        self.genes_path = self.util.join_path(self.gene_dir, config['Genetic']['gene_file'])
        html_checker_dir = self.util.join_path(full_path, config['Genetic']['html_checker_dir'])
        self.html_checker = self.util.join_path(html_checker_dir, config['Genetic']['html_checker_file'])
        self.html_checker_option = config['Genetic']['html_checker_option']
        self.html_checked_path = self.util.join_path(self.html_dir, config['Genetic']['html_checked_file'])
        self.html_eval_place_list = config['Genetic']['html_eval_place'].split('@')
        self.bingo_score = float(config['Genetic']['bingo_score'])
        self.warning_score = float(config['Genetic']['warning_score'])
        self.error_score = float(config['Genetic']['error_score'])
        self.result_file = config['Genetic']['result_file']
        self.result_list = []  # Stores results of successful individuals.

    # -------------------------------------------------------------------------
    # create_genom: Create a random individual (gene) for the initial population.
    # -------------------------------------------------------------------------
    def create_genom(self, df_gene):
        """
        Create a random individual (gene) for the population.

        Args:
            df_gene (DataFrame): DataFrame containing gene pool.

        Returns:
            Gene: A new Gene object with random genome.
        """
        lst_gene = []
        for _ in range(self.genom_length):
            lst_gene.append(random.randint(0, len(df_gene.index)-1))
        self.util.print_message(OK, 'Created individual : {}.'.format(lst_gene))
        return Gene(lst_gene, 0)

    # -------------------------------------------------------------------------
    # evaluation: Evaluate the fitness of an individual.
    # -------------------------------------------------------------------------
    def evaluation(self, obj_ga, df_gene, eval_place, individual_idx):
        """
        Evaluate the fitness of an individual.

        Args:
            obj_ga (Gene): The individual to evaluate.
            df_gene (DataFrame): DataFrame containing gene pool.
            eval_place (str): The HTML placeholder to inject the gene.
            individual_idx (int): Index of the individual.

        Returns:
            tuple: (score, error_flag)
        """
        # Build HTML syntax by rendering the template with the individual's genome.
        indivisual = self.util.transform_gene_num2str(df_gene, obj_ga.genom_list)
        html = self.template.render({eval_place: indivisual})
        eval_html_path = self.util.join_path(self.html_dir, self.html_file.replace('*', str(individual_idx)))
        with codecs.open(eval_html_path, 'w', encoding='utf-8') as fout:
            fout.write(html)

        # Evaluate HTML syntax using an external checker (e.g., tidy).
        command = self.html_checker + ' ' + self.html_checker_option + ' ' + \
                  self.html_checked_path + ' ' + eval_html_path
        enc = locale.getpreferredencoding()
        env_tmp = os.environ.copy()
        env_tmp['PYTHONIOENCODING'] = enc
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env_tmp)

        # Read the result of HTML checking.
        str_eval_result = ''
        with codecs.open(self.html_checked_path, 'r', encoding='utf-8') as fin:
            str_eval_result = fin.read()
        # Extract warning and error counts from the checker output.
        str_pattern = r'.*Tidy found ([0-9]+) warnings and ([0-9]+) errors.*$'
        obj_match = re.match(str_pattern, str_eval_result.replace('\t', '').replace('\r', '').replace('\n', ''))
        warnings = 0.0
        errors = 0.0
        if obj_match:
            warnings = int(obj_match.group(1)) * -0.1
            errors = int(obj_match.group(2)) * -1.0
        else:
            # If parsing failed, return error.
            return None, 1

        # Compute the score based on warnings and errors.
        int_score = warnings + errors

        # Evaluate the HTML by running it in Selenium (browser automation).
        selenium_score, error_flag = self.util.check_individual_selenium(self.obj_browser, eval_html_path)
        if error_flag:
            return None, 1

        # If Selenium detects a successful script execution, add bonus score.
        if selenium_score > 0:
            self.util.print_message(OK, 'Detect running script: "{}" in {}.'.format(indivisual, eval_place))

            # Add bingo score for successful execution.
            int_score += self.bingo_score
            self.result_list.append([eval_place, obj_ga.genom_list, indivisual])

            # Output evaluation results.
            self.util.print_message(OK, 'Evaluation result : Browser={} {}, '
                                        'Individual="{} ({})", '
                                        'Score={}'.format(self.obj_browser.name,
                                                          self.obj_browser.capabilities['version'],
                                                          indivisual,
                                                          obj_ga.genom_list,
                                                          str(int_score)))
        return int_score, 0

    # -------------------------------------------------------------------------
    # select: Select elite individuals based on fitness (elitism).
    # -------------------------------------------------------------------------
    def select(self, obj_ga, elite):
        """
        Select elite individuals from the population.

        Args:
            obj_ga (list): List of Gene objects (population).
            elite (int): Number of elite individuals to select.

        Returns:
            list: List of elite Gene objects.
        """
        # Sort individuals in descending order of evaluation (fitness).
        sort_result = sorted(obj_ga, reverse=True, key=lambda u: u.evaluation)

        # Extract the top 'elite' individuals.
        return [sort_result.pop(0) for _ in range(elite)]

    # -------------------------------------------------------------------------
    # crossover: Perform two-point crossover between two individuals.
    # -------------------------------------------------------------------------
    def crossover(self, ga_first, ga_second):
        """
        Perform two-point crossover between two individuals.

        Args:
            ga_first (Gene): First parent.
            ga_second (Gene): Second parent.

        Returns:
            list: List containing two offspring Gene objects.
        """
        genom_list = []

        # Randomly select two crossover points.
        cross_first = random.randint(0, self.genom_length)
        cross_second = random.randint(cross_first, self.genom_length)
        one = ga_first.getGenom()
        second = ga_second.getGenom()

        # Create offspring by exchanging segments between parents.
        progeny_one = one[:cross_first] + second[cross_first:cross_second] + one[cross_second:]
        progeny_second = second[:cross_first] + one[cross_first:cross_second] + second[cross_second:]
        genom_list.append(Gene(progeny_one, 0))
        genom_list.append(Gene(progeny_second, 0))

        return genom_list

    # -------------------------------------------------------------------------
    # next_generation_gene_create: Create the next generation population.
    # -------------------------------------------------------------------------
    def next_generation_gene_create(self, ga, ga_elite, ga_progeny):
        """
        Create the next generation by combining elites and offspring.

        Args:
            ga (list): Current population.
            ga_elite (list): Elite individuals.
            ga_progeny (list): Offspring individuals.

        Returns:
            list: Next generation population.
        """
        # Sort current population in ascending order of evaluation (lowest fitness first).
        next_generation_geno = sorted(ga, reverse=False, key=lambda u: u.evaluation)

        # Remove as many individuals as the sum of elites and offspring to maintain population size.
        remove_count = min(len(next_generation_geno), len(ga_elite) + len(ga_progeny))
        for _ in range(remove_count):
            next_generation_geno.pop(0)
            ## SELIM: burası degisti

        # Add elite and offspring individuals to the next generation.
        next_generation_geno.extend(ga_elite)
        next_generation_geno.extend(ga_progeny)
        return next_generation_geno

    # -------------------------------------------------------------------------
    # mutation: Apply mutation to the population.
    # -------------------------------------------------------------------------
    def mutation(self, obj_ga, induvidual_mutation, genom_mutation, df_genes):
        """
        Apply mutation to individuals and their genes.

        Args:
            obj_ga (list): Population (list of Gene objects).
            induvidual_mutation (float): Probability of mutating an individual.
            genom_mutation (float): Probability of mutating a gene.
            df_genes (DataFrame): DataFrame containing gene pool.

        Returns:
            list: Mutated population.
        """
        lst_ga = []
        for idx in obj_ga:
            # Decide whether to mutate the individual.
            if induvidual_mutation > (random.randint(0, 100) / Decimal(100)):
                lst_gene = []
                for idx2 in idx.getGenom():
                    # Decide whether to mutate each gene.
                    if genom_mutation > (random.randint(0, 100) / Decimal(100)):
                        lst_gene.append(random.randint(0, len(df_genes.index)-1))
                    else:
                        lst_gene.append(idx2)
                idx.setGenom(lst_gene)
                lst_ga.append(idx)
            else:
                lst_ga.append(idx)
        return lst_ga

    # -------------------------------------------------------------------------
    # main: Main control loop for the genetic algorithm.
    # -------------------------------------------------------------------------
    def main(self):
        """
        Main loop for running the genetic algorithm.

        Returns:
            list: List of successful individuals (results).
        """
        # Load gene pool from CSV file.
        df_genes = pd.read_csv(self.genes_path, encoding='utf-8').fillna('')

        # Prepare the result file (write header if file does not exist).
        save_path = self.util.join_path(self.result_dir, self.result_file.replace('*', self.obj_browser.name))
        if os.path.exists(save_path) is False:
            pd.DataFrame([], columns=['eval_place', 'sig_vector', 'sig_string']).to_csv(save_path,
                                                                                        mode='w',
                                                                                        header=True,
                                                                                        index=False)

        # Evaluate individuals for each evaluation place in the HTML template.
        for eval_place in self.html_eval_place_list:
            self.util.print_message(NOTE, 'Evaluating html place : {}'.format(eval_place))

            # Generate the initial population (1st generation).
            self.util.print_message(NOTE, 'Create population.')
            current_generation = []
            for _ in range(self.max_genom_list):
                current_generation.append(self.create_genom(df_genes))

            # Iterate through generations.
            for int_count in range(1, self.max_generation + 1):
                self.util.print_message(NOTE, 'Evaluate individual : {}/{} generation.'.format(str(int_count),
                                                                                               self.max_generation))
                for indivisual, idx in enumerate(range(self.max_genom_list)):
                    self.util.print_message(OK, 'Evaluation individual in {}: '
                                                '{}/{} in {} generation'.format(eval_place,
                                                                                indivisual + 1,
                                                                                self.max_genom_list,
                                                                                str(int_count)))
                    evaluation_result, eval_status = self.evaluation(current_generation[indivisual],
                                                                     df_genes,
                                                                     eval_place,
                                                                     idx)

                    idx += 1
                    if eval_status == 1:
                        indivisual -= 1
                        continue
                    current_generation[indivisual].setEvaluation(evaluation_result)
                    time.sleep(self.wait_time)

                # Select elite individuals.
                elite_genes = self.select(current_generation, self.select_genom)

                # Perform crossover among elite individuals to produce offspring.
                progeny_gene = []
                for i in range(0, self.select_genom):
                    progeny_gene.extend(self.crossover(elite_genes[i - 1], elite_genes[i]))

                # Create the next generation by combining elites and offspring.
                next_generation_individual_group = self.next_generation_gene_create(current_generation,
                                                                                    elite_genes,
                                                                                    progeny_gene)

                # Apply mutation to the next generation.
                next_generation_individual_group = self.mutation(next_generation_individual_group,
                                                                 self.individual_mutation_rate,
                                                                 self.genom_mutation_rate,
                                                                 df_genes)

                # Calculate fitness statistics for the current generation.
                fits = [_.getEvaluation() for _ in current_generation]
                flt_avg = sum(fits) / float(len(fits))
                self.util.print_message(NOTE, '{} generation result: '
                                              'Min={}, Max={}, Avg={}.'.format(int_count,
                                                                               min(fits),
                                                                               max(fits),
                                                                               flt_avg))

                # Check if the average fitness exceeds the threshold to stop evolution.
                if flt_avg > self.max_fitness:
                    self.util.print_message(NOTE, 'Finish evolution: average={}'.format(str(flt_avg)))
                    break

                # Move to the next generation.
                current_generation = next_generation_individual_group

        # Save the results of successful individuals to the result file.
        pd.DataFrame(self.result_list).to_csv(save_path, mode='a', header=True, index=False)

        # Output the best individual found.
        str_best_individual = ''
        for gene_num in elite_genes[0].getGenom():
            str_best_individual += str(df_genes.loc[gene_num].values[0])
        str_best_individual = str_best_individual.replace('%s', ' ').replace('&quot;', '"').replace('%comma', ',')
        self.util.print_message(NOTE, 'Best individual : "{}"'.format(str_best_individual))
        self.util.print_message(NOTE, 'Done creation of injection codes using Genetic Algorithm.')

        # Clean up: Remove all generated evaluation HTML files after testing.
        try:
            for filename in os.listdir(self.html_dir):
                if filename.startswith('ga_eval_html') and filename.endswith('.html'):
                    full_path = os.path.join(self.html_dir, filename)
                    os.remove(full_path)
                    self.util.print_message(OK, f'Removed temp HTML: {full_path}')
        except Exception as e:
            self.util.print_exception(e, 'Could not delete ga_eval_html files.')

        return self.result_list

