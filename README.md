# VLQ Single-T CLIC Paper

Minimal source package for the 12-page paper version supplied as
`VLQ_SingleT_CLIC_Paper-3.pdf`.

Build with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The supplied reference PDF has SHA-256:

```text
93863a4a97f4ebb59bef8f3a3d8de2e79debe92b91a1b3b147c4e1aba1c63fc2
```

PDF bytes can vary with the TeX distribution, fonts, and build timestamp. The
expected document has 12 pages and the title:

> Agnostic search for a vector-like top partner at a lepton collider via the
> recoil mass technique
