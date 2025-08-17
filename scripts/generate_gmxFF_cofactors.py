#!/usr/bin/env python3

import os
import sys
import subprocess
from parmed.amber import AmberParm

def require_file(path):
    if not os.path.isfile(path):
        sys.stderr.write(f"ERROR: Required file not found: {path}\n")
        sys.exit(1)

# ─── helper: detect metals in MOL2 (skip GAFF fallback if present) ─────────────
def mol2_has_metal(mol2_path):
    """Crude check for common metals in MOL2 atom name/type fields."""
    metals = {"Fe","Cu","Zn","Mg","Mn","Co","Ni","Mo","W","V","Ca","K","Na"}
    try:
        with open(mol2_path, "r") as f:
            in_atom = False
            for line in f:
                ls = line.strip()
                up = ls.upper()
                if up.startswith("@<TRIPOS>ATOM"):
                    in_atom = True
                    continue
                if up.startswith("@<TRIPOS>BOND"):
                    break
                if in_atom and ls:
                    parts = ls.split()
                    if len(parts) >= 6:
                        name = ''.join(c for c in parts[1] if c.isalpha())
                        atype = ''.join(c for c in parts[5] if c.isalpha())
                        def canon(el):
                            if not el: return el
                            if len(el) == 1: return el.upper()
                            return el[0].upper() + el[1:].lower()
                        if canon(name) in metals or canon(atype) in metals:
                            return True
    except Exception:
        # Be conservative on parse errors
        return True
    return False

# ─── NEW helper to run tleap + check for empty prmtop ───────────────────────────
def run_tleap(prefix, mol2_fn, frcmod_fn, sources):
    # write leap.in from a list of source files
    with open("leap.in", "w") as f:
        for src in sources:
            f.write(f"source {src}\n")
        f.write(f"""
LIG = loadMol2 {mol2_fn}
loadAmberParams {frcmod_fn}
saveAmberParm LIG {prefix}.prmtop {prefix}.rst7
quit
""")
    # run tleap and capture output
    res = subprocess.run(["tleap", "-f", "leap.in"],
                         capture_output=True, text=True)
    print("=== tleap stdout ===\n", res.stdout, file=sys.stderr)
    print("=== tleap stderr ===\n", res.stderr, file=sys.stderr)
    if res.returncode:
        return False

    prmtop = f"{prefix}.prmtop"
    if not os.path.isfile(prmtop) or os.path.getsize(prmtop) == 0:
        return False

    return True
# ────────────────────────────────────────────────────────────────────────────────

def main():
    # Prompt user for all required paths
    mol2       = input("Path to MOL2 file (e.g. lib/HEM/3ARC_HEM.mol2): ").strip()
    frcmod     = input("Path to FRCMOD file (e.g. lib/HEM/3ARC_HEM.frcmod): ").strip()
    prefix     = input("Output prefix (e.g. 3ARC_HEM): ").strip()
    leap_prot  = input("Path to leaprc.protein.ff14SB (e.g. /Users/sama578/opt/anaconda3/envs/py/dat/leap/cmd/leaprc.protein.ff14SB): ").strip()
    leap_lipid = input("Path to leaprc.lipid21 (e.g. /Users/sama578/opt/anaconda3/envs/py/dat/leap/cmd/leaprc.lipid21): ").strip()
    leap_gaff  = input("Path to leaprc.gaff (e.g. /Users/sama578/opt/anaconda3/envs/py/dat/leap/cmd/leaprc.gaff): ").strip()

    # 1) Verify inputs
    for p in (mol2, frcmod, leap_prot, leap_lipid, leap_gaff):
        require_file(p)

    # Change into directory of MOL2/FRCMOD so outputs go there
    workdir   = os.path.dirname(os.path.abspath(mol2)) or "."
    os.chdir(workdir)
    mol2_fn   = os.path.basename(mol2)
    frcmod_fn = os.path.basename(frcmod)

    print(f"\nParameterizing {mol2_fn} + {frcmod_fn} → prefix '{prefix}' in {workdir}\n")

    # 2) Write leap.in (initial version)
    #    (this will be overwritten by run_tleap when invoked)
    leap_in = f"""
source {leap_prot}
source {leap_lipid}
source {leap_gaff}
LIG = loadMol2 {mol2_fn}
loadAmberParams {frcmod_fn}
saveAmberParm LIG {prefix}.prmtop {prefix}.rst7
quit
"""
    with open("leap.in","w") as f:
        f.write(leap_in)

    # ─── steps 3–4 with a two-attempt run_tleap + fallback ──────────────
    # First attempt: protein + lipid21 + GAFF (using provided MOL2+FRCMOD)
    sources = [leap_prot, leap_lipid, leap_gaff]
    if not run_tleap(prefix, mol2_fn, frcmod_fn, sources):
        sys.stderr.write("First tleap build failed (protein+lipid21+gaff).\n")

        # Metal guard: do NOT use antechamber/GAFF for metal-containing ligands
        if mol2_has_metal(mol2_fn):
            sys.stderr.write("Detected metal center in MOL2; skipping GAFF fallback (antechamber).\n"
                             "Use curated FRCMOD/MCPB.py for metal complexes.\n")
            sys.exit(1)

        # Fallback (organic ligands only): generate GAFF mol2/frcmod via antechamber+parmchk2
        gaff_mol2   = f"{prefix}_gaff.mol2"
        gaff_frcmod = f"{prefix}.frcmod"

        try:
            # 1) antechamber --> GAFF atom types + AM1-BCC charges
            subprocess.run([
                "antechamber",
                "-i",  mol2_fn,   "-fi", "mol2",
                "-o",  gaff_mol2, "-fo", "mol2",
                "-c",  "bcc",     "-s",  "2",    "-at", "gaff"
            ], check=True)

            # 2) parmchk2 --> missing bond/angle/dihedral params
            subprocess.run([
                "parmchk2",
                "-i", gaff_mol2, "-f", "mol2",
                "-o", gaff_frcmod
            ], check=True)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"GAFF fallback failed during antechamber/parmchk2: {e}\n")
            sys.exit(1)

        # Retry tleap with GAFF outputs
        sources = [leap_prot, leap_gaff]
        if not run_tleap(prefix, gaff_mol2, gaff_frcmod, sources):
            sys.stderr.write("ERROR: GAFF fallback tleap build also failed—no prmtop generated\n")
            sys.exit(1)

    print(f"--> tleap succeeded: {prefix}.prmtop & {prefix}.rst7")
    # ─────────────────────────────────────────────────────────────────────────────

    # 5) Load prmtop/rst7 via AmberParm
    try:
        parm = AmberParm(f"{prefix}.prmtop", f"{prefix}.rst7")
    except ValueError as e:
        sys.stderr.write(f"ERROR: could not parse {prefix}.prmtop: {e}\n")
        sys.exit(1)
    print(f"Loaded AmberParm: {len(parm.atoms)} atoms, {len(parm.bond_types)} bonds")

    # 6) Write .gro and .itp
    parm.save(f"{prefix}.gro", format="gro")
    parm.save(f"{prefix}.itp", format="gromacs")
    print(f"--> Built {prefix}.gro & {prefix}.itp")

    # 7) Write master topol.top
    with open("topol.top","w") as f:
        f.write(f""";;
;; Generated by python script
;; Correspondance: sumansamantray06@gmail.com
;;
; Include forcefield parameters
#include "toppar/forcefield.itp"
#include "{os.path.basename(leap_prot)}"
#include "{os.path.basename(leap_gaff)}"
#include "{prefix}.itp"

[ system ]
{prefix} ligand in vacuum

[ molecules ]
{prefix}      1
""")
    print("--> Generated topol.top file")

    # 8) Extract [ defaults ] + [ atomtypes ] to sample_forcefield.itp
    srcfile = f"{prefix}.itp"
    dstfile = f"{prefix}_forcefield.itp"
    with open(srcfile) as src, open(dstfile,"w") as dst:
        in_block = False
        for line in src:
            stripped = line.strip()
            if stripped.startswith("[ defaults ]") or stripped.startswith("[ atomtypes ]"):
                in_block = True
            elif in_block and stripped.startswith("[") and not stripped.startswith("[ atomtypes ]"):
                break
            if in_block:
                dst.write(line)
    print(f"--> Generated {dstfile} file")

    # 9) Strip [ defaults ] & [ atomtypes ] from the .itp in-place
    keep = {
        "[ moleculetype ]",
        "[ atoms ]",
        "[ bonds ]",
        "[ pairs ]",
        "[ angles ]",
        "[ dihedrals ]",
    }
    lines, write = [], False
    with open(srcfile) as src:
        for line in src:
            stripped = line.strip()
            if any(stripped.startswith(h) for h in keep):
                write = True
            elif write and stripped.startswith("[") and stripped not in keep:
                write = False
            if write:
                lines.append(line)
    with open(srcfile,"w") as dst:
        dst.writelines(lines)
    print(f"--> Generated {srcfile} file")

if __name__=="__main__":
    main()
