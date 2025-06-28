# -*- coding: utf-8 -*-
import os
import sys
import random
import codecs
import configparser
import numpy as np
import pandas as pd
from keras.optimizers import SGD
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers import LeakyReLU
from keras.layers import Dropout
from keras import backend as K
from src.util import Utilty
from keras.layers import Input  # Add Input layer if necessary
import glob

# Type of printing.
OK = 'ok'         # [*] Success message
NOTE = 'note'     # [+] Informational message
FAIL = 'fail'     # [-] Failure message
WARNING = 'warn'  # [!] Warning message
NONE = 'none'     # No label.

# Generative Adversarial Networks.
class GAN:
    """
    This class implements a Generative Adversarial Network (GAN) for generating injection codes.
    It uses Keras for building and training the generator and discriminator models.
    The class also handles configuration loading, data preprocessing, model training, and evaluation.
    """
    def __init__(self, template, browser):
        """
        Initialize the GAN class with the provided HTML template and Selenium browser instance.
        Loads configuration values, sets up paths, and loads gene data.
        """
        self.util = Utilty()
        self.template = template
        self.obj_browser = browser

        # Read config.ini.
        full_path = os.path.dirname(os.path.abspath(__file__))
        config = configparser.ConfigParser()
        try:
            config.read(self.util.join_path(full_path, '../config/config.ini'))
        except FileExistsError as e:
            self.util.print_message(FAIL, 'File exists error: {}'.format(e))
            sys.exit(1)

        # Load common configuration values.
        self.wait_time = float(config['Common']['wait_time'])
        self.html_dir = self.util.join_path(full_path, config['Common']['html_dir'])
        self.html_file = config['Common']['gan_html_file']
        self.result_dir = self.util.join_path(full_path, config['Common']['result_dir'])
        self.eval_html_path = self.util.join_path(self.html_dir, self.html_file)

        # Load genetic algorithm configuration values.
        self.genom_length = int(config['Genetic']['genom_length'])
        self.gene_dir = self.util.join_path(full_path, config['Genetic']['gene_dir'])
        self.genes_path = self.util.join_path(self.gene_dir, config['Genetic']['gene_file'])
        self.ga_result_file = config['Genetic']['result_file']
        self.eval_place_list = config['Genetic']['html_eval_place'].split('@')

        # Load GAN-specific configuration values.
        self.input_size = int(config['GAN']['input_size'])
        self.batch_size = int(config['GAN']['batch_size'])
        self.num_epoch = int(config['GAN']['num_epoch'])
        self.max_sig_num = int(config['GAN']['max_sig_num'])
        self.max_explore_codes_num = int(config['GAN']['max_explore_codes_num'])
        self.max_synthetic_num = int(config['GAN']['max_synthetic_num'])
        self.weight_dir = self.util.join_path(full_path, config['GAN']['weight_dir'])
        self.gen_weight_file = config['GAN']['generator_weight_file']
        self.dis_weight_file = config['GAN']['discriminator_weight_file']
        self.gan_result_file = config['GAN']['result_file']
        self.gan_vec_result_file = config['GAN']['vec_result_file']
        self.generator = None

        # Load gene list from CSV file.
        self.df_genes = pd.read_csv(self.genes_path, encoding='utf-8').fillna('')
        self.flt_size = len(self.df_genes) / 2.0

        # Path to the trained generator weights.
        self.weight_path = self.util.join_path(self.weight_dir,
                                               self.gen_weight_file.replace('*', str(self.num_epoch - 1)))

    # Build generator model.
    def generator_model(self):
        """
        Constructs the generator neural network model.
        The generator takes random noise as input and outputs a vector representing a candidate injection code.
        """
        model = Sequential()
        model.add(Input(shape=(self.input_size,)))  # Input layer
        model.add(Dense(units=self.input_size*10, kernel_initializer='glorot_uniform'))
        model.add(LeakyReLU(0.2))
        model.add(Dropout(0.5))

        model.add(Dense(units=self.input_size*10, kernel_initializer='glorot_uniform'))
        model.add(LeakyReLU(0.2))
        model.add(Dropout(0.5))

        model.add(Dense(units=self.input_size*5, kernel_initializer='glorot_uniform'))
        model.add(LeakyReLU(0.2))
        model.add(Dropout(0.5))

        model.add(Dense(units=self.genom_length, kernel_initializer='glorot_uniform'))
        model.add(Activation('tanh'))  # Output activation
        return model

    # Build discriminator model.
    def discriminator_model(self):
        """
        Constructs the discriminator neural network model.
        The discriminator takes a candidate injection code and outputs a probability of being real or fake.
        """
        model = Sequential()
        model.add(Dense(units=self.genom_length * 10, input_dim=self.genom_length, kernel_initializer='glorot_uniform'))
        model.add(LeakyReLU(0.2))
        model.add(Dense(units=self.genom_length*10, kernel_initializer='glorot_uniform'))
        model.add(LeakyReLU(0.2))
        model.add(Dense(units=1, kernel_initializer='glorot_uniform'))
        model.add(Activation('sigmoid'))  # Output activation
        return model

    # Train GAN model (generate injection codes).
    def train(self, list_sigs):
        """
        Trains the GAN using the provided list of signature vectors.
        For each epoch and batch, generates new codes, updates the discriminator and generator,
        and evaluates generated codes using Selenium.
        """
        # Load training data (GA results).
        X_train = []
        X_train = np.array(list_sigs)
        X_train = (X_train.astype(np.float32) - self.flt_size)/self.flt_size

        # Build and compile discriminator.
        discriminator = self.discriminator_model()
        d_opt = SGD(learning_rate=0.1, momentum=0.1)
        discriminator.compile(loss='binary_crossentropy', optimizer=d_opt)

        # Build generator and combined GAN model.
        discriminator.trainable = False
        self.generator = self.generator_model()
        dcgan = Sequential([self.generator, discriminator])
        g_opt = SGD(learning_rate=0.1, momentum=0.3)
        dcgan.compile(loss='binary_crossentropy', optimizer=g_opt)

        # Training loop.
        num_batches = int(len(X_train) / self.batch_size)
        lst_scripts = []
        for epoch in range(self.num_epoch):
            for batch in range(num_batches):
                # Generate random noise as input for the generator.
                noise = np.array([np.random.uniform(-1, 1, self.input_size) for _ in range(self.batch_size)])

                # Generate new injection codes using the generator.
                generated_codes = self.generator.predict(noise, verbose=0)

                # Train discriminator on real data.
                image_batch = X_train[batch * self.batch_size:(batch + 1) * self.batch_size]
                X = image_batch
                y = [random.uniform(0.7, 1.2) for _ in range(self.batch_size)]
                d_loss = discriminator.train_on_batch(X, y)
                # Train discriminator on fake data.
                X = generated_codes
                y = [random.uniform(0.0, 0.3) for _ in range(self.batch_size)]
                d_loss = discriminator.train_on_batch(X, y)

                # Train generator via the combined model.
                noise = np.array([np.random.uniform(-1, 1, self.input_size) for _ in range(self.batch_size)])
                g_loss = dcgan.train_on_batch(noise, [1]*self.batch_size)

                # Convert generated codes to HTML and evaluate.
                for generated_code in generated_codes:
                    lst_genom = []
                    for gene_num in generated_code:
                        gene_num = (gene_num * self.flt_size) + self.flt_size
                        gene_num = int(np.round(gene_num))
                        if gene_num == len(self.df_genes):
                            gene_num -= 1
                        lst_genom.append(int(gene_num))
                    str_html = self.util.transform_gene_num2str(self.df_genes, lst_genom)
                    self.util.print_message(OK, 'Train GAN : epoch={}, batch={}, g_loss={}, d_loss={}, {} ({})'.
                                            format(epoch, batch, g_loss, d_loss,
                                                   np.round((generated_code * self.flt_size) + self.flt_size),
                                                   str_html))

                    # Evaluate generated injection code using Selenium.
                    for eval_place in self.eval_place_list:
                        # Render HTML with the generated code.
                        html = self.template.render({eval_place: str_html})
                        with codecs.open(self.eval_html_path, 'w', encoding='utf-8') as fout:
                            fout.write(html)

                        # Use Selenium to check if the code is effective.
                        selenium_score, error_flag = self.util.check_individual_selenium(self.obj_browser,
                                                                                         self.eval_html_path)
                        if error_flag:
                            continue

                        # If the code is effective, save it.
                        if selenium_score > 0:
                            self.util.print_message(WARNING, 'Detect running script: "{}" in {}.'.format(str_html,
                                                                                                         eval_place))
                            lst_scripts.append([eval_place, str_html])

            # Save model weights after each epoch.
            self.generator.save_weights(self.util.join_path(self.weight_dir,
                                                            self.gen_weight_file.replace('*', str(epoch))))
            discriminator.save_weights(self.util.join_path(self.weight_dir,
                                                           self.dis_weight_file.replace('*', str(epoch))))

        return lst_scripts

    # Transform from generated codes to gene list.
    def transform_code2gene(self, generated_code):
        """
        Converts a generated code vector into a list of gene indices.
        This is used to map the continuous output of the generator to discrete gene values.
        """
        lst_genom = []
        for gene_num in generated_code:
            gene_num = (gene_num * self.flt_size) + self.flt_size
            gene_num = int(np.round(gene_num))
            if gene_num == len(self.df_genes):
                gene_num -= 1
            lst_genom.append(int(gene_num))
        return lst_genom

    # Mean of two vectors.
    def vector_mean(self, vector1, vector2):
        """
        Computes the element-wise mean of two vectors.
        Used for synthesizing new injection codes from two existing ones.
        """
        return (vector1 + vector2)/2
    


    # Main control.
    def main(self):
        """
        Main entry point for the GAN process.
        Handles both training and inference (exploration and synthesis) depending on the existence of trained weights.
        Saves results to CSV files.
        """
        # Define saving paths for results.
        gan_save_path = self.util.join_path(self.result_dir, self.gan_result_file.replace('*', self.obj_browser.name))
        vec_save_path = self.util.join_path(self.result_dir, self.gan_vec_result_file.replace('*', self.obj_browser.name))      

        def load_ga_results(result_dir):
            """
            Loads all genetic algorithm result CSV files from the result directory and concatenates them.
            """
            result_files = glob.glob(os.path.join(result_dir, "ga_result_*.csv"))
            df_all = pd.concat([pd.read_csv(f) for f in result_files], ignore_index=True)
            return df_all
        
        df_sigs = load_ga_results(self.result_dir)

        # If trained weights exist, perform exploration and synthesis.
        if os.path.exists(self.weight_path):
            # Load the trained generator model.
            self.generator = self.generator_model()
            self.generator.load_weights('{}'.format(self.weight_path))

            # Explore valid injection codes using the generator.
            valid_code_list = []
            result_list = []
            for idx in range(self.max_explore_codes_num):
                self.util.print_message(NOTE, '{}/{} Explore valid injection code.'.format(idx + 1,
                                                                                           self.max_explore_codes_num))
                
                # Generate injection codes from random noise.
                noise = np.array([np.random.uniform(-1, 1, self.input_size) for _ in range(1)])
                generated_codes = self.generator.predict(noise, verbose=0)
                str_html = self.util.transform_gene_num2str(self.df_genes, self.transform_code2gene(generated_codes[0]))

                print("[+] Trying:", str_html)  # Print the generated code for debugging

                # Evaluate the generated code using Selenium.
                for eval_place in self.eval_place_list:
                    html = self.template.render({eval_place: str_html})
                    with codecs.open(self.eval_html_path, 'w', encoding='utf-8') as fout:
                        fout.write(html)

                    selenium_score, error_flag = self.util.check_individual_selenium(self.obj_browser,
                                                                                     self.eval_html_path)
                    if error_flag:
                        continue

                    # If the code is valid, save it.
                    if selenium_score > 0:
                        self.util.print_message(WARNING, 'Find valid injection code: "{}" in {}.'.format(str_html,
                                                                                                         eval_place))
                        valid_code_list.append([str_html, noise])
                        result_list.append([eval_place, str_html])

            if len(valid_code_list) == 0:
                self.util.print_message(FAIL, "No valid injection codes were found. Skipping synthesis step.")
                return []
            

            # Save generated injection codes to CSV.
            if len(result_list) == 0:
                self.util.print_message(WARNING, "GAN exploration completed but no valid injection code was found.")

            if os.path.exists(gan_save_path) is False:
                pd.DataFrame(result_list, columns=['eval_place', 'injection_code']).to_csv(gan_save_path,
                                                                                           mode='w',
                                                                                           header=True,
                                                                                           index=False)
            else:
                pd.DataFrame(result_list).to_csv(gan_save_path, mode='a', header=False, index=False)
                
            
            # Synthesize new injection codes from valid ones.
            if len(valid_code_list) < 2:
                self.util.print_message(WARNING, "Not enough valid injection codes to synthesize.")
                return

            vector_result_list = []
            seen_codes = set()
            for idx in range(self.max_synthetic_num):
                noise_idx1 = np.random.randint(0, len(valid_code_list))
                noise_idx2 = np.random.randint(0, len(valid_code_list))
                self.util.print_message(NOTE, '{}/{} Synthesize injection codes.'.format(idx+1, self.max_synthetic_num))
                self.util.print_message(OK, 'Use two injection codes : ({}) + ({}).'.
                                        format(valid_code_list[noise_idx1][0], valid_code_list[noise_idx2][0]))

                # Synthesize new noise vector by averaging two valid ones.
                synthesized_noise = self.vector_mean(valid_code_list[noise_idx1][1], valid_code_list[noise_idx2][1])
                generated_codes = self.generator.predict(synthesized_noise, verbose=0)
                str_html = self.util.transform_gene_num2str(self.df_genes, self.transform_code2gene(generated_codes[0]))

                # Avoid duplicate codes.
                if str_html in seen_codes:
                    continue
                seen_codes.add(str_html)

                # Evaluate synthesized code using Selenium.
                for eval_place in self.eval_place_list:
                    hit_flag = 'Failure'
                    html = self.template.render({eval_place: str_html})
                    with codecs.open(self.eval_html_path, 'w', encoding='utf-8') as fout:
                        fout.write(html)

                    selenium_score, error_flag = self.util.check_individual_selenium(self.obj_browser,
                                                                                     self.eval_html_path)
                    if error_flag:
                        continue

                    # If the code is effective, mark as 'Bingo'.
                    if selenium_score > 0:
                        self.util.print_message(WARNING, 'Find running script: "{}".'.format(str_html))
                        hit_flag = 'Bingo'

                    # Save the result.
                    vector_result_list.append([eval_place, str_html,
                                               valid_code_list[noise_idx1][0],
                                               valid_code_list[noise_idx2][0],
                                               hit_flag])

            # Save synthesized injection codes to CSV.
            if os.path.exists(vec_save_path) is False:
                pd.DataFrame(vector_result_list,
                             columns=['eval_place', 'synthesized_code',
                                      'origin_code1', 'origin_code2', 'bingo']).to_csv(vec_save_path,
                                                                                       mode='w',
                                                                                       header=True,
                                                                                       index=False)
            else:
                pd.DataFrame(vector_result_list).to_csv(vec_save_path, mode='a', header=False, index=False)
        else:
            # If no trained weights, train the GAN using GA results.
            sig_path = self.util.join_path(self.result_dir, self.ga_result_file.replace('*', self.obj_browser.name))
            df_temp = pd.read_csv(sig_path, encoding='utf-8').fillna('')
            df_sigs = df_temp[~df_temp.duplicated()]

            list_sigs = []
            # Extract genome list from GA results.
            for idx in range(len(df_sigs)):
                list_temp = df_sigs.iloc[idx, 1].replace('[', '').replace(']', '').split(',')
                list_sigs.append([int(s) for s in list_temp])

            # Generate individuals (injection codes) for training.
            lst_scripts = []
            target_sig_list = []
            for target_sig in list_sigs:
                self.util.print_message(NOTE, 'Start generating injection codes using {}'.format(target_sig))
                target_sig_list.extend([target_sig for _ in range(self.max_sig_num)])
            lst_scripts.extend(self.train(target_sig_list))

            # Save generated injection codes to CSV.
            if os.path.exists(gan_save_path) is False:
                pd.DataFrame(lst_scripts, columns=['eval_place', 'injection_code']).to_csv(gan_save_path,
                                                                                           mode='w',
                                                                                           header=True,
                                                                                           index=False)
            else:
                pd.DataFrame(lst_scripts).to_csv(gan_save_path, mode='a', header=False, index=False)

        self.util.print_message(NOTE, 'Done generation of injection codes using Generative Adversarial Networks.')



if __name__ == '__main__':
    # Entry point for running the GAN script.
    # Loads configuration, sets up the HTML template and Selenium browser, and starts the GAN process.
    from selenium import webdriver
    from jinja2 import Environment, FileSystemLoader
    import configparser
    from selenium.webdriver.chrome.service import Service

    full_path = os.path.dirname(os.path.abspath(__file__))

    # Load configuration file.
    config = configparser.ConfigParser()
    config.read(os.path.join(full_path, 'config.ini'))

    # Set up Jinja2 HTML template environment.
    html_dir = os.path.join(full_path, config['Common']['html_dir'])
    html_template = config['Common']['html_template']
    env = Environment(loader=FileSystemLoader(html_dir))
    template = env.get_template(html_template)

    # Set up Selenium Chrome browser.
    driver_path = os.path.join(full_path, config['Selenium']['driver_dir'], config['Selenium']['driver_list'])
    service = Service(executable_path=driver_path)
    browser = webdriver.Chrome(service=service)

    # Instantiate and run the GAN process.
    gan = GAN(template, browser)
    gan.main()

    browser.close()
