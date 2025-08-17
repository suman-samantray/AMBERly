# AMBERly

*A Python tool to seamlessly generate GROMACS-compatible force field files for ligands and cofactors starting from AMBER parameter files.*

---

## 🚀 Overview

**AMBERly** automates the conversion of AMBER force field parameters into **GROMACS-ready** topology and coordinate files.  
It is designed for ligands and cofactors, handling MOL2 + FRCMOD inputs, and producing all files necessary for simulations in GROMACS.

### ✨ Key Features
- Prompts user for:
  - **MOL2** file path  
  - **FRCMOD** file path  
  - **Output prefix**  
  - AMBER `leaprc` force field files (protein, lipid, GAFF)
- Validates input files and runs **tleap** to build AMBER topology (`.prmtop`) and coordinates (`.rst7`).
- Falls back to **antechamber + parmchk2** (for GAFF generation) if tleap fails and no metals are present.
- Converts AMBER outputs to GROMACS formats (`.gro`, `.itp`) via **ParmEd**.
- Generates:
  - `topol.top` (master topology)
  - `_forcefield.itp` ([ defaults ] + [ atomtypes ])
  - Cleaned `.itp` (without redundant sections)
- Transparent tleap setup: stdout/stderr fully printed.
- Avoids GAFF auto-generation for **metal-containing cofactors**.

---

## 📂 Versions

### 1. Simple version (no lipids)
**File:** `simple_generate_gmxFF_cofactors.py`

Run with:
```bash
$ python simple_generate_gmxFF_cofactors.py
```

**Prompts for:**
- Path to MOL2 file (e.g. `lib/HEM/3ARC_HEM.mol2`)  
- Path to FRCMOD file (e.g. `lib/HEM/3ARC_HEM.frcmod`)  
- Output prefix (e.g. `3ARC_HEM`)  
- Path to `leaprc.protein.ff14SB`  
  - Example: `/Users/you/opt/anaconda3/envs/py/dat/leap/cmd/leaprc.protein.ff14SB`  
- Path to `leaprc.gaff`  
  - Example: `/Users/you/opt/anaconda3/envs/py/dat/leap/cmd/leaprc.gaff`

---

### 2. Extended version (lipid support + better automation)
**File:** `generate_gmxFF_cofactors.py`

Run with:
```bash
$ python generate_gmxFF_cofactors.py
```

**Prompts for:**
- Path to MOL2 file (e.g. `lib/HEM/3ARC_HEM.mol2`)  
- Path to FRCMOD file (e.g. `lib/HEM/3ARC_HEM.frcmod`)  
- Output prefix (e.g. `3ARC_HEM`)  
- Path to `leaprc.protein.ff14SB`  
- Path to `leaprc.lipid21`  
- Path to `leaprc.gaff`  

---

## 📦 Installation

Clone this repo and ensure you have **AMBER**, **ParmEd**, and **GROMACS** installed and in your PATH.

```bash
git clone https://github.com/yourusername/amberly.git
cd amberly
conda install -c conda-forge parmed
```

---

## 🧪 Example Workflow

```bash
$ python simple_generate_gmxFF_cofactors.py
Path to MOL2 file: lib/HEM/3ARC_HEM.mol2
Path to FRCMOD file: lib/HEM/3ARC_HEM.frcmod
Output prefix: 3ARC_HEM
Path to leaprc.protein.ff14SB: /path/to/leaprc.protein.ff14SB
Path to leaprc.gaff: /path/to/leaprc.gaff
```

**Output files generated:**
- `3ARC_HEM.itp`  
- `3ARC_HEM_forcefield.itp`  
- `3ARC_HEM.gro`  
- `topol.top`

---

## 📖 Citation

If you use **AMBERly** in your research, please cite this repository.

---

## 📜 License

Distributed under the BSD 3-Clause License. See `LICENSE` for details.

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.8+-3776AB.svg?style=flat&logo=python&logoColor=white"/>
  <img alt="License" src="https://img.shields.io/badge/License-BSD%203--Clause-blue.svg"/>
  <img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen.svg"/>
</p>

---

