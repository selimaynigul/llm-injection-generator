# 🧬 PayloadGenerator - Injection Code Generator using Genetic Algorithms and GANs

- **Course**: CSE 473 - Network and Information Security
- **Instructor**: Dr. Salih Sarp
- **Contributors**: Selim Aynigül, Beyza Acar, Berkehan Burak Şahin

## 📄 Description

**PayloadGenerator** is a hybrid HTML/JavaScript injection code generation framework designed for use in security testing and research. The tool combines **Genetic Algorithms (GA)** and **Generative Adversarial Networks (GANs)** to automatically produce, evaluate, and refine candidate injection payloads that mimic real-world XSS-like attack vectors.

This project was developed as part of the **CSE 473 - Network and Information Security** course, under the supervision of **Dr. Salih Sarp**.

---

### 🔍 Objectives

- Automate the generation of potentially malicious payloads for use in security testing.
- Use Genetic Algorithms to evolve payloads based on fitness functions reflecting syntactic validity and browser behavior.
- Leverage Generative Adversarial Networks to explore and synthesize novel payload variants that resemble "real" injection patterns.
- Analyze the payloads both statically (HTML validation via Tidy) and dynamically (runtime behavior in browsers using Selenium).

---

### 🧠 Methodology

1. **Token Collection (Gene Bank Creation)**:

   - The system begins by collecting basic HTML/JS fragments (genes), either manually or using LLM-based context generation.
   - These genes are stored in `gene_list.csv` and serve as the building blocks for new payloads.

2. **Payload Evolution via Genetic Algorithms**:

   - A population of candidate payloads is formed by selecting combinations of genes.
   - Fitness is calculated by:
     - Passing the payload through **Tidy** to detect HTML errors/warnings.
     - Injecting the payload into a browser via **Selenium** and detecting behavior (e.g., script execution).
   - The best-performing payloads are selected, crossed over, and mutated to form the next generation.
   - This process continues until the average population fitness exceeds a threshold.

3. **Payload Generation via GAN**:

   - The GA-generated payloads are encoded into numerical vectors.
   - A GAN model is trained to synthesize new payload vectors based on the statistical distribution of known good vectors.
   - These vectors are decoded back into payloads and evaluated similarly.
   - Additionally, novel payloads are created by interpolating between known good vectors.

4. **LLM-Driven Support (Pluggable)**:
   - An LLM module can be optionally used to generate context-aware payloads using prompts and extracted HTML from test environments.

---

### 🧪 Evaluation Strategy

- **HTML Tidy**:

  - Ensures payloads are well-formed HTML.
  - Penalizes syntax errors and warnings.

- **Selenium Execution**:

  - Loads the HTML in a real browser (Chrome).
  - Detects whether the payload triggers behavior such as popups or script alerts.
  - Positive triggers result in bonus fitness scores.

- **GAN Output Filtering**:
  - Only successful or unique payloads from the generator are preserved and logged.
  - Synthesized payloads are evaluated similarly for real-world behavior.

---

### 📁 Project Structure (Key Modules)

- `generator.py`: Main controller that initializes GA and GAN runs.
- `ga_main.py`: Core implementation of the Genetic Algorithm logic.
- `gan_main.py`: GAN generator and synthesizer module.
- `llm_mode.py`: Extracts DOM context and queries an LLM for payloads.
- `config.ini`: Centralized configuration for file paths, mutation parameters, model settings, etc.

---

### 🔐 Use Cases

- Web application penetration testing
- Security research on evasive payload generation
- Academic demonstrations of hybrid AI-based code synthesis
- Benchmarking browser-based defenses

---

### 📦 Output

All generated payloads and analysis results are saved in:

- `result/ga_result_*.csv`: GA-evolved payloads and vectors
- `result/gan_result_*.csv`: Valid GAN-generated payloads
- `result/gan_result_vec_*.csv`: Interpolated/synthesized payloads

You can open these files to inspect the generated injection attempts.

---

## 🛠️ Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/injection-generator.git
   cd injection-generator/my_generator
   ```

2. **Get the web driver for selenium**:

   [!] This project uses the Google chrome driver.

   You have to download the [chrome driver](http://chromedriver.chromium.org/downloads) for selenium.  
    And you have to move downloaded driver file to `drivers` directory.

```
  PS C:\injection-generator\PayloadGenerator> mkdir drivers
  PS C:\injection-generator\PayloadGenerator> mv chromedriver.exe drivers
  PS C:\injection-generator\PayloadGenerator> ls .\drivers\
```

3. **Get html checker (tidy)**:

   [!] This project uses the `tidy 5.4.0 win64`.

And you have to move the `tidy.exe` file to the `C:\tools\tidy` directory (the default path is set as `C:\tools\tidy` in the `config.ini` file to avoid permission issues that may occur if it is placed directly under the project’s `tools` folder).

4. **Install required packages**:

```bash
pip install -r requirements.txt
```

6. **Run the project from the outermost (root) directory**:

Make sure you are in the root directory of the project (`injection-generator/my_generator`) before running the following command:

```bash
python -m src.generator
```

## Operation check environment

- Hardware
  - OS: Windows 10
  - CPU: Intel(R) Core(TM) i7-6500U 2.50GHz
  - GPU: None
  - Memory: 8.0GB
- Software
  - Python 3.6.0
  - Jinja2==2.10
  - Keras==2.1.6
  - numpy==1.13.3
  - pandas==0.23.0
  - selenium==3.14.0

## ▶️ Usage Examples

- Example command:
  ```bash
  python -m src.generator
  ```
- Outputs:
  - `result/ga_result_*.csv`: Genetic Algorithm results.
  - `result/gan_result_*.csv`: GAN-generated payloads.
  - `html/`: Evaluated HTML files.

## 🛠️ Troubleshooting

- **PermissionError when running tidy**:

  - Run the terminal **as Administrator** or ensure `tidy.exe` has execution permissions.

- **ModuleNotFoundError (e.g., 'src')**:

  - Always run from the root directory using `python -m src.generator`.

- **NoSuchDriverException from Selenium**:

  - Make sure `chromedriver.exe` is compatible with your Chrome version and is in the correct path.
