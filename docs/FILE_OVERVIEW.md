# FILE_OVERVIEW.md

This document provides a detailed explanation of the main files and modules within the injection-generator project.

---

## 📁 `generator.py`

**Location:** `src/generator.py`

**Description:**  
This is the main entry point for the injection generator project. It coordinates the entire workflow, including reading configuration, launching browsers, generating payloads using Genetic Algorithms (GA), GANs, and optionally LLMs. It also sets up and tears down Selenium WebDriver sessions.

### Responsibilities:

- Reads `config.ini` for project settings.
- Sets up paths for HTML templates and Selenium drivers.
- Launches a browser using Selenium (Chrome, Firefox, or IE).
- Calls the `llm_mode` module to prepare LLM-generated content.
- Runs the Genetic Algorithm (`ga_main.py`) to generate initial injection attempts.
- Triggers the GAN (`gan_main.py`) to generate synthetic injections.
- Handles browser window sizing and alert handling.
- Closes the browser when processing is complete.

### Breakdown:

- **Configuration Reading:**
  Loads and parses `../config/config.ini`. Values are read into local variables to control program behavior (paths, mutation parameters, window sizes, etc.).

- **HTML Template Setup:**
  Uses `jinja2` to load a template file from the HTML directory. This template is used to embed injection payloads into valid HTML pages.

- **Browser Launch:**
  Depending on which driver (`chromedriver`, `geckodriver`, `IEDriverServer`) is listed in the config file, it launches that browser with a specified window size and position.

- **LLM Generation (Optional):**
  Invokes `llm_mode.main()` to generate payloads via a language model, storing them in files expected by the GA module.

- **Genetic Algorithm Execution:**
  Calls `GeneticAlgorithm(template, browser).main()` multiple times (based on `max_try_num`) to iteratively evolve and evaluate payloads.

- **GAN Execution:**
  Instantiates and runs the `GAN` class to generate further synthetic payloads from GA results.

- **Alert Handling:**
  Catches and dismisses unexpected browser alerts (e.g., JavaScript alert popups during rendering).

- **Cleanup:**
  Ensures the browser session is closed at the end to release system resources.

### Notes:

- The file uses `src.util.Utilty` for all helper functions like path joining and console printing.
- Paths in `config.ini` must be valid relative to `generator.py`'s location or absolute.
- If WebDriver (like `chromedriver`) is not configured correctly, a runtime error will occur.
- Make sure `tidy.exe` (used later in the GA module) has permission to execute on your system.

---

## 📁 `ga_main.py`

**Location:** `src/ga_main.py`

**Description:**  
This module implements a full Genetic Algorithm (GA) to generate and evolve HTML-based injection payloads. The goal is to identify the most effective combinations of known payload segments that produce meaningful, script-executing results when injected into HTML.

---

### Core Components:

#### Class: `Gene`

A lightweight data structure that holds:

- `genom_list`: A list of integer indexes (referring to payload segments).
- `evaluation`: The computed fitness score of this gene (based on HTML validation and JavaScript execution).

#### Class: `GeneticAlgorithm`

The main class that:

- Loads configuration values and the payload gene pool.
- Generates the initial population.
- Evaluates the fitness of each individual using both HTML validator (`tidy.exe`) and Selenium.
- Applies crossover and mutation to evolve new generations.
- Stores the best individuals in a CSV output file.

---

### Key Methods:

#### `__init__(...)`

Initializes the algorithm, loads config, sets paths, and reads GA parameters.

#### `create_genom(df_gene)`

Randomly creates an individual genome using index values referencing `df_gene` (payload segments).

#### `evaluation(obj_ga, df_gene, eval_place, individual_idx)`

Renders an HTML file with the individual's payload and:

- Validates the HTML using `tidy`.
- Detects running JavaScript via Selenium.
- Calculates and returns a fitness score.

#### `select(obj_ga, elite)`

Sorts the population and returns the top `elite` individuals.

#### `crossover(ga_first, ga_second)`

Performs two-point crossover between two genes to create two offspring.

#### `next_generation_gene_create(...)`

Removes least-fit individuals and adds elite and offspring to form the next generation.

#### `mutation(...)`

Randomly mutates individuals at both the genome and gene levels with a configured probability.

#### `main()`

Runs the entire GA process:

1. Loads genes from `gene_list.csv`.
2. Creates and evaluates populations.
3. Evolves generations via selection, crossover, and mutation.
4. Stores final results to `ga_result_*.csv`.
5. Deletes generated temporary `ga_eval_html_*.html` files after execution.

---

### Output:

- `ga_result_<browser>.csv`: Stores successful payloads and their fitness scores.
- `Best individual`: Printed to console for quick reference.

---

### Dependencies:

- Requires `tidy.exe` to be correctly configured in `config.ini`.
- Depends on `Selenium` for dynamic evaluation.
- Input gene data must be in `gene_list.csv`.

---

### Notes:

- HTML validation is done via CLI call to `tidy`, parsed with regex.
- JS script execution adds bonus fitness (`bingo_score`).
- All temporary HTML files are cleaned after execution unless an exception occurs.

---

## 📁 `gan_main.py`

**Location:** `src/gan_main.py`

**Description:**  
This module implements a Generative Adversarial Network (GAN) to synthesize HTML injection codes. It complements the Genetic Algorithm by learning from previously generated examples and producing new, potentially more effective payloads.

---

### Main Class: `GAN`

#### `__init__(template, browser)`

Initializes the GAN engine, loads configuration and training parameters, sets up paths and templates, and reads the gene list (`gene_list.csv`).

**Responsibilities:**

- Load config values from `config.ini`
- Prepare input paths for gene files, result directories, and pretrained weights
- Set GAN-specific hyperparameters such as `input_size`, `num_epoch`, `batch_size`, etc.

---

### Neural Network Models

#### `generator_model()`

- A neural network that takes a noise vector as input and produces a list of gene indexes.
- Layered with Dense, LeakyReLU, Dropout, and `tanh` for output activation.

#### `discriminator_model()`

- A binary classifier that distinguishes between real and generated gene sequences.
- Built using Dense and LeakyReLU layers, with a sigmoid activation output.

---

### Key Methods

#### `train(list_sigs)`

- Trains the GAN using previously discovered injection codes.
- Uses alternating training for discriminator and generator.
- Saves generator and discriminator weights at each epoch.
- Evaluates generated codes via Selenium and keeps the successful ones.

#### `transform_code2gene(generated_code)`

- Converts floating-point outputs of the generator into valid integer-based gene indexes.

#### `vector_mean(vector1, vector2)`

- A helper function to perform element-wise averaging between two vectors (used for synthesis).

---

### Main Workflow: `main()`

1. **Check for pretrained weights**  
   If found, load the generator and skip training. Otherwise, train a new model from GA output.

2. **Exploration Mode**  
   If pretrained weights are available:

   - Generate new codes from random noise
   - Render HTML and test using Selenium
   - Save successful injections to `gan_result_*.csv`

3. **Synthesis Mode**

   - Mix two successful noise vectors to generate new, combined payloads
   - Validate and store results in `gan_result_vec_*.csv`

4. **Training Mode**  
   If no pretrained weights:
   - Read `ga_result_*.csv` and extract genome vectors
   - Train the GAN using these real samples
   - Store the final generated successful payloads

---

### Output Files

- `gan_result_*.csv`  
  Stores successful injection strings and their HTML injection locations.

- `gan_result_vec_*.csv`  
  Stores synthesized payloads along with their origins and whether they executed successfully.

- `generator_*.weights.h5`, `discriminator_*.weights.h5`  
  Stored after each training epoch, representing the state of the trained models.

---

### Notes

- Uses `tanh` activation in the generator output and rescales values to gene indices.
- Uses dropout to prevent overfitting.
- Carefully logs and filters duplicate or failed payloads.
- Requires proper setup of `tidy.exe`, `chromedriver`, and template HTML to function.
- Leverages both exploration and synthesis to generate robust injection variants.

---

## 📁 `llm_mode.py`

**Location:** `src/llm_mode.py`

**Description:**  
This module integrates a Language Model (LLM) into the injection code generation pipeline. It generates novel injection payloads using LLM prompts based on extracted HTML contexts, then encodes those payloads into gene vectors for use in the Genetic Algorithm (GA) workflow.

---

### Key Responsibilities

- Extract context from a target URL or local HTML file
- Prompt a language model to generate potential injection payloads
- Parse and split those payloads into generic reusable components ("genes")
- Update the gene list used by the GA and map payloads into gene vectors
- Save results in `ga_result_chrome.csv` to feed into GA and GAN modules

---

### Key Functions

#### `load_gene_list()`

- Reads the existing gene list from `gene_list.csv`.
- Returns a list of known genes (injection components).

#### `save_gene_list(gene_list)`

- Overwrites the current gene list with a new one.
- Ensures the `result/` directory exists.

#### `update_gene_list(new_genes)`

- Adds new genes to the existing list only if they don’t already exist.
- Saves the updated list back to `gene_list.csv`.
- Returns the index positions of the given genes (used as a signature vector for GA).

#### `split_payload_into_generics(payload)`

- Tokenizes an injection payload into reusable components such as:
  - HTML tags (`<script>`, `</div>`, etc.)
  - JavaScript event handlers (`onload=`, `onclick=`, etc.)
  - Common JavaScript functions (`alert()`, `prompt()`, etc.)
  - JavaScript URIs (`javascript:alert(1)`)
  - Key-value attributes and leftovers

Returns a cleaned list of string tokens representing individual gene components.

---

### Main Entry Point: `main()`

1. **Context Extraction**

   - Loads a local HTML file (`../tests/test.html`) using `extract_context_from_url()`.

2. **Payload Generation**

   - Passes the context to `generate_payload()`, which uses an LLM to propose payloads.

3. **Gene Encoding**

   - For each payload:
     - Breaks it into component genes
     - Updates the gene list with new genes
     - Converts the payload to a gene vector using gene indexes

4. **Result Saving**
   - Saves the processed payloads to `result/ga_result_chrome.csv` in the same format expected by the GA:
     - `eval_place` (hardcoded as `body_tag`)
     - `sig_vector` (index list of genes)
     - `sig_string` (original payload)

---

### Output

- **`result/ga_result_chrome.csv`**  
  File containing LLM-generated payloads and their encoded gene vectors, formatted for downstream use in Genetic Algorithms and GANs.

---

### Notes

- The current target URL is hardcoded to a local test file but can be adapted.
- External helper modules used:
  - `context_extractor.py`: for HTML context scraping
  - `llm_util.py`: to interface with the LLM (e.g., OpenAI, local model)
- Ensures gene diversity by appending novel tokens, promoting generalization in later model stages.

---

## 🛠️ `config.ini`

**Location:** `config/config.ini`

**Purpose:**
Holds all user-defined and system parameters for controlling the behavior of the generator, GA, GAN, and Selenium browser settings.

**Key Sections:**

- `[Common]`: Directories and template configurations
- `[Genetic]`: Parameters for GA logic (mutation rates, population sizes, etc.)
- `[Selenium]`: WebDriver paths and window configurations
- `[GAN]`: Paths and hyperparameters for GAN training/evaluation

This file defines configurable parameters for all major components in the project, including HTML generation, the Genetic Algorithm (GA), the Generative Adversarial Network (GAN), and Selenium WebDriver settings.

---

## [Common]

| Parameter       | Description                                                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `html_dir`      | Path to the folder where generated HTML files will be stored. Used by both GA and GAN to output test HTML files.                  |
| `html_template` | Name of the HTML template file used to inject payloads. This file contains placeholders for script injection.                     |
| `ga_html_file`  | Patterned filename used to name HTML files generated by the Genetic Algorithm. The asterisk (`*`) is replaced with browser names. |
| `gan_html_file` | Static filename used for HTML file generated by the GAN module.                                                                   |
| `result_dir`    | Directory where evaluation results (CSV files) are saved. Can be relative (`../result`) or absolute.                              |
| `wait_time`     | Wait time (in seconds) between GA evaluations. Helps with throttling or debugging browser interaction.                            |

---

## [Genetic]

| Parameter                  | Description                                                                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `genom_length`             | Number of genes (tokens) in a single individual's genome. Determines the complexity of one injection code.                             |
| `max_genom_list`           | Size of the initial population per generation. More individuals mean more diverse exploration.                                         |
| `select_genom`             | Number of elite individuals selected per generation to be carried into the next one.                                                   |
| `individual_mutation_rate` | Probability of mutation at the individual level (i.e., changing genes in a whole individual). Ranges from 0.0 to 1.0.                  |
| `genom_mutation_rate`      | Probability of mutating each gene within an individual. Used during mutation phase.                                                    |
| `max_generation`           | Maximum number of generations to run the GA for each HTML placeholder.                                                                 |
| `max_fitness`              | If the average fitness score exceeds this value, GA stops early.                                                                       |
| `max_try_num`              | Number of times the GA is re-run (e.g., when starting from scratch). Useful for retries.                                               |
| `gene_dir`                 | Directory where the gene list (available injection tokens) is stored.                                                                  |
| `gene_file`                | CSV file name containing the gene list. Each gene is typically a string component of an injection payload.                             |
| `html_checker_dir`         | Path to the folder containing the HTML syntax checker (`tidy.exe`).                                                                    |
| `html_checker_file`        | Name of the HTML checker executable, typically `tidy.exe`.                                                                             |
| `html_checker_option`      | CLI option passed to tidy (e.g., `-f` for output to file, `-o` for overwrite).                                                         |
| `html_checked_file`        | File to which tidy outputs its syntax checking results. This file is read to extract error/warning counts.                             |
| `html_eval_place`          | Name of the HTML placeholder where injection will be evaluated (e.g., `body_tag`). Can support multiple placeholders separated by `@`. |
| `bingo_score`              | Bonus score added if an injected script successfully executes (as detected by Selenium).                                               |
| `warning_score`            | Penalty score per warning reported by tidy. Negative value.                                                                            |
| `error_score`              | Penalty score per error reported by tidy. More severe than warning.                                                                    |
| `result_file`              | Patterned filename for storing GA result output. The asterisk (`*`) is replaced by the browser name.                                   |

---

## [Selenium]

| Parameter         | Description                                                                                                            |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `driver_dir`      | Path to folder containing browser WebDriver executables (e.g., `chromedriver.exe`). Can be relative like `../drivers`. |
| `driver_list`     | Names of WebDriver executables, separated by `@` if multiple (e.g., `chromedriver.exe@geckodriver.exe`).               |
| `window_width`    | Width of the browser window launched by Selenium.                                                                      |
| `window_height`   | Height of the browser window.                                                                                          |
| `position_width`  | Horizontal position (x-axis) of the browser window on screen.                                                          |
| `position_height` | Vertical position (y-axis) of the browser window on screen.                                                            |

---

## [GAN]

| Parameter                   | Description                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `input_size`                | Length of random noise vector fed into the GAN's generator. Affects the diversity and resolution of generated payloads. |
| `batch_size`                | Number of samples per training batch for GAN.                                                                           |
| `num_epoch`                 | Number of epochs to train GAN when generator weights don't exist yet.                                                   |
| `max_sig_num`               | Number of times each GA-generated injection is used for training GAN.                                                   |
| `max_explore_codes_num`     | Number of individual codes the GAN attempts to generate and evaluate when using pretrained weights.                     |
| `max_synthetic_num`         | Number of new injection codes created by combining latent vectors of successful GAN outputs.                            |
| `weight_dir`                | Directory where GAN weight files are stored.                                                                            |
| `generator_weight_file`     | Patterned filename for saved weights of the generator model (e.g., `generator_*.weights.h5`).                           |
| `discriminator_weight_file` | Patterned filename for discriminator weights.                                                                           |
| `result_file`               | Patterned CSV file where GAN's successful payloads are saved.                                                           |
| `vec_result_file`           | Patterned CSV file where synthesized vector-based payloads are saved.                                                   |

---

## 🗂️ Additional Notes:

- Make sure the `drivers` folder has the correct `chromedriver.exe` and is configured properly in `config.ini`.
- Ensure file paths are absolute or correctly relative depending on where the script is run.
- `tidy.exe` (HTML validator) must be accessible and given the right permissions.

---
