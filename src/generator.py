# -*- coding: utf-8 -*-
"""
generator.py
This script automates the process of generating and evaluating web payloads using different AI techniques and web browsers.
It is designed to help with tasks such as security testing or automated web content generation.
Main Features:
--------------
- Reads configuration settings from a config.ini file.
- Supports multiple web browsers (Chrome, Firefox, Internet Explorer) using Selenium WebDriver.
- Uses Jinja2 templates to generate HTML files for testing.
- Integrates three main AI modules:
    1. LLM (Large Language Model) for generating payloads.
    2. Genetic Algorithm (GA) for evolving and optimizing payloads.
    3. Generative Adversarial Network (GAN) for creating more diverse payloads.
- Automatically manages browser windows and handles browser alerts.
- Provides clear, labeled console output for each step (OK, NOTE, FAIL, WARNING).
How it works:
-------------
1. Loads configuration and sets up paths and parameters.
2. For each browser specified in the configuration:
    - Launches the browser and sets its window size and position.
    - Runs the LLM module to generate initial payloads.
    - Uses the Genetic Algorithm to create and evolve payloads over several iterations.
    - Applies the GAN to further generate and refine payloads.
    - Handles any browser alerts that may appear.
    - Closes the browser when done.
Intended Audience:
------------------
- Users interested in automated web testing, security research, or AI-driven web content generation.
- No advanced programming knowledge required; the script is designed to be easy to follow and modify.
"""
import os
import sys
import configparser
from selenium import webdriver
from src.util import Utilty
from src.ga_main import GeneticAlgorithm
from src.gan_main import GAN
from src.llm_mode import main as llm_main
from jinja2 import Environment, FileSystemLoader
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoAlertPresentException

# Type of printing.
OK = 'ok'         # [*]
NOTE = 'note'     # [+]
FAIL = 'fail'     # [-]
WARNING = 'warn'  # [!]
NONE = 'none'     # No label.

if __name__ == "__main__":
    util = Utilty()

    # Read config.ini.
    full_path = os.path.dirname(os.path.abspath(__file__))
    config = configparser.ConfigParser()
    try:
        config.read(util.join_path(full_path, '../config/config.ini'))
    except FileExistsError as e:
        util.print_message(FAIL, 'File exists error: {}'.format(e))
        sys.exit(1)

    # Common setting value.
    html_dir = util.join_path(full_path, config['Common']['html_dir'])
    html_template = config['Common']['html_template']

    # Genetic Algorithm setting value.
    html_eval_place_list = config['Genetic']['html_eval_place'].split('@')
    max_try_num = int(config['Genetic']['max_try_num'])

    # Selenium setting value.
    driver_dir = util.join_path(full_path, config['Selenium']['driver_dir'])
    driver_list = config['Selenium']['driver_list'].split('@')
    window_width = int(config['Selenium']['window_width'])
    window_height = int(config['Selenium']['window_height'])
    position_width = int(config['Selenium']['position_width'])
    position_height = int(config['Selenium']['position_height'])

    # Setting template.
    env = Environment(loader=FileSystemLoader(html_dir))
    template = env.get_template(html_template)

    # Start revolution using each browser.
    for browser in driver_list:
        # Create Web driver.
        obj_browser = None
        if 'geckodriver' in browser:
            obj_browser = webdriver.Firefox(executable_path=util.join_path(driver_dir, browser))
            util.print_message(NOTE, 'Launched : {} {}'.format(obj_browser.capabilities['browserName'],
                                                               obj_browser.capabilities['browserVersion']))
        elif 'chrome' in browser:
            chrome_driver_path = util.join_path(driver_dir, browser)
            service = Service(executable_path=chrome_driver_path)
            obj_browser = webdriver.Chrome(service=service)

            util.print_message(NOTE, 'Launched : {} {}'.format(obj_browser.capabilities['browserName'],
                                                               obj_browser.capabilities['browserVersion']))
        elif 'IE' in browser:
            obj_browser = webdriver.Ie(executable_path=util.join_path(driver_dir, browser))
            util.print_message(NOTE, 'Launched : {} {}'.format(obj_browser.capabilities['browserName'],
                                                               obj_browser.capabilities['browserVersion']))
        else:
            util.print_message(FAIL, 'Invalid browser driver : {}'.format(browser))
            sys.exit(1)

        # Browser setting.
        obj_browser.set_window_size(window_width, window_height)
        obj_browser.set_window_position(position_width, position_height)

        # Generate payload with LLM and prepare necessary files for GA
        llm_main()

        # Create a few individuals from gene list.
        for idx in range(max_try_num):
            util.print_message(NOTE, '{}/{} Create individuals using Genetic Algorithm.'.format(idx + 1, max_try_num))
            ga = GeneticAlgorithm(template, obj_browser)
            individual_list = ga.main()

        # Generate many individuals from ga result.
        util.print_message(NOTE, 'Generate individual using Generative Adversarial Networks.')
        gan = GAN(template, obj_browser)
        gan.main()

        try:
            alert = obj_browser.switch_to.alert
            alert.dismiss()  # or alert.accept()
        except NoAlertPresentException:
            pass

        # Close browser.
        obj_browser.close()
