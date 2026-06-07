Quick start
===========

Cluster segments during CLDF export
-----------------------------------

When building a CLDF ``forms.csv``, cluster segments for alignment columns::

   from loanpy import Cluster

   segments = "f l a".split()
   cv = ["C", "C", "V"]
   clusters = Cluster.cv(segments, cv)
   # ['f.l', 'a']

   glides = Cluster.glides(segments, cv)
   hun_clusters = Cluster.liquid(glides)

Mine sound correspondences
--------------------------

From cognate rows that alternate descendant / ancestor languages::

   import csv
   from loanpy import get_sound_correspondences

   with open("cognates.csv", encoding="utf-8") as f:
       rows = list(csv.DictReader(f))
   stats = get_sound_correspondences(rows, aligned_col="Uralign")
   scorer = stats["AbsoluteFrequency"]

Load a TOML scorer written with :func:`add_separator`::

   import tomllib
   from loanpy import load_scorer

   with open("scorers/globalign.toml", "rb") as f:
       data = tomllib.load(f)
   scorer = load_scorer(data, missing=-1000, imputed=12)

Score an alignment
------------------

Prosody-aware pairwise alignment (UEW, Seima–Turbino)::

   from loanpy import Uralign

   seq_d = ["ɟ", "ŋ"]
   seq_a = ["j", "ŋ"]
   alm_d, alm_a = Uralign.hu(seq_d.copy(), seq_a.copy(), "C", "C")
   score = Uralign.get_score(alm_d, alm_a, scorer, freq_filter=2)

Global alignment with gap collapsing and cluster-aware scoring (Gothic, Turkic)::

   from loanpy import Altign

   alm_hun, alm_donor = Altign.gaps(alm_hun, alm_donor)
   score = Altign.get_score(alm_hun, alm_donor, scorer, freq_filter=2)

Adapt donor segments
--------------------

::

   from loanpy import Adapt

   ad = Adapt()
   ad.get_substitutions(donor_set, recipient_set, distance_fn, extra={})
   adapted = ad.substitute(donor_segments)
   repaired = ad.repair(adapted, cv_profile, phonotactic_templates)

Typical integrations
--------------------

* **CLDF conversion** — ``cldfbench`` dataset modules call ``Cluster``,
  ``Uralign``, and ``Altign`` when writing segmentation and alignment columns.
* **Loanword detection pipelines** — analysis scripts combine ``Adapt``,
  ``Uralign``, ``Altign``, and ``get_sound_correspondences`` over wordlist/cognate tables.

These patterns apply to any paired descendant–ancestor data; language names and
file layouts are project-specific.
