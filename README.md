# LLM-Based Injection Generator (Pre-LLM Version)

A hybrid XSS injection generator using Genetic Algorithms and GANs.

Note: LLM support is planned but not yet added.

## Features

- Genetic Algorithm for initial payload generation
- GAN for generating new variants
- Selenium-based validation
- HTML syntax validation via Tidy

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/injection-generator.git
cd injection-generator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Dependencies

- Put `chromedriver.exe` into `web_drivers/`
- Put `tidy.exe` into `tidy/` folder

### 3. Run

```bash
python generator.py
```

## Output Files

- `result/ga_result_*.csv` – GA outputs
- `result/gan_result_*.csv` – Valid GAN outputs
- `result/gan_result_vec_*.csv` – Synthesized GAN outputs

## HTML Template

Used file: `html/eval_template.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <title>XSS Test</title>
  </head>
  <body>
    {{ body_tag }}
  </body>
</html>
```

## Gene List Format

Each row in `gene_list.csv` is a token or tag:

```
<script>
</script>
<img src=x onerror=alert(1)>
...
```

## .gitignore

```
tidy/
web_drivers/
__pycache__/
*.pyc
*.weights.h5
result/
.DS_Store
```

## Future Work

- Add LLM guidance module
- Use LLMs for better mutation or payload scoring
