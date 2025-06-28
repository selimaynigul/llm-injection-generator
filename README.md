# 🧬 PayloadGenerator - Injection Code Generator using Genetic Algorithms and GANs

- **Course**: CSE473 - Network and Information Security
- **Instructor**: Dr. Salih Sarp
- **University**: Gebze Technical University
- **Contributors**: Selim Aynigül, Beyza Acar, Berkehan Burak Şahin

## 📄 Description

This project focuses on the automatic generation of HTML/JavaScript injection codes. It leverages **Genetic Algorithms (GA)** to evolve candidate payloads based on their structural validity and execution behavior, and utilizes **Generative Adversarial Networks (GANs)** to synthetically generate realistic-looking injection patterns. The system evaluates the generated code using Tidy for HTML compliance and Selenium for browser-based behavior analysis.

The injection codes are generated in two steps.

1.  Gather the components of injection codes.
2.  Create some injection codes using Genetic Algorithm.
3.  Generate numerous injection codes using Generative Adversarial Networks.

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
