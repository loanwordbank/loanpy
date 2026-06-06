"""Phoneme clustering: CV grouping, glide clustering, and gap collapsing."""

CLUSTER_BETWEEN_VOWELS = ("ɣ", "w", "v", "β", "ð")
LIQUID_AFTER_L = ("t͡ʃ", "d")


class Cluster:
    """Static helpers for segment clustering in CLDF pipelines.

    Clustering reduces fine-grained segment lists to coarser units used in
    alignment and correspondence mining (e.g. ``f.l`` for consonant clusters,
    ``a.ʊ`` for vowel sequences).

    Examples
    --------
    Typical workflow during CLDF conversion::

        segments = form.split()
        cv = dataset.get_cv_profile(form)
        clusters = Cluster.cv(segments, cv)
        glides = Cluster.glides(segments, cv)
        hun_clusters = Cluster.liquid(glides)

    After pairwise alignment, gaps may be collapsed::

        alm_a, alm_b = Cluster.gaps(alm_a, alm_b)

    Notes
    -----
    Used in **CLDF conversion** scripts (``cldfbench_*.py``) for datasets such as
    UEW-hu, SeimaTurbino-hu, UESz-year-origin, and WestOldTurkic, where clustered
    segments are written to ``forms.csv`` columns like ``Clusters`` or
    ``Cluster_cv``.
    """

    @staticmethod
    def cv(segments: list[str], cv_profile: list[str]) -> list[str]:
        """Join adjacent segments that share the same C/V class.

        Parameters
        ----------
        segments:
            IPA (or other) segments, one symbol per list element.
        cv_profile:
            Parallel list of ``"C"`` and ``"V"`` labels.

        Returns
        -------
        list[str]
            Clustered segments joined with ``"."`` within each run of C or V.

        Examples
        --------
        >>> Cluster.cv(["f", "l", "a"], ["C", "C", "V"])
        ['f.l', 'a']
        """
        result = []
        for i, (segment, cv) in enumerate(zip(segments, cv_profile)):
            if i == 0 or cv != cv_profile[i - 1]:
                result.append(segment)
            else:
                result[-1] += "." + segment
        return result

    @staticmethod
    def glides(
        segments: list[str],
        cv_profile: list[str],
        cluster_between_vowels: tuple[str, ...] = CLUSTER_BETWEEN_VOWELS,
    ) -> list[str]:
        """Cluster glides between vowels.

        Parameters
        ----------
        segments, cv_profile:
            Parallel segment and C/V lists (same length).
        cluster_between_vowels:
            Segments to attach to a preceding vowel cluster when sandwiched by vowels.

        Returns
        -------
        list[str]
            Further clustered segment list.

        Raises
        ------
        ValueError
            If ``segments`` and ``cv_profile`` differ in length.

        Notes
        -----
        Used in **CLDF conversion** (e.g. UESz-year-origin ``Cluster_glide`` column,
        WestOldTurkic and koeblergothic ``Clusters``). Default glide symbols include
        Gothic intervocalic ``β`` and ``ð``. For Hungarian ``l.d`` / ``l.t͡ʃ`` clusters,
        call :meth:`liquid` after :meth:`glides`.
        """
        if len(segments) != len(cv_profile):
            raise ValueError("segments and cv_profile must have the same length")
        cluster2 = []
        profile2 = []
        for idx, phoneme in enumerate(segments):
            if (
                idx != 0
                and phoneme in cluster_between_vowels
                and cv_profile[idx - 1] == "V"
            ):
                cluster2[-1] += f".{phoneme}"
                profile2[-1] += f".{cv_profile[idx]}"
            else:
                cluster2.append(phoneme)
                profile2.append(cv_profile[idx])

        cluster3 = []
        for idx, phoneme in enumerate(cluster2):
            if (
                idx != 0
                and profile2[idx] == "V"
                and any(f".{ph}" in cluster3[-1] for ph in cluster_between_vowels)
            ):
                cluster3[-1] += f".{phoneme}"
            else:
                cluster3.append(phoneme)
        return cluster3

    @staticmethod
    def liquid(
        segments: list[str],
        cluster_after_l: tuple[str, ...] = LIQUID_AFTER_L,
    ) -> list[str]:
        """Cluster selected consonants immediately following ``l``.

        Parameters
        ----------
        segments:
            Segment list, typically after :meth:`glides`.
        cluster_after_l:
            Segments to attach when immediately following ``l``.

        Returns
        -------
        list[str]
            Further clustered segment list.

        Notes
        -----
        Used in **CLDF conversion** for Hungarian ``Monogap`` alignments in
        WestOldTurkic (after :meth:`glides` on the Hungarian side).
        """
        result = []
        for idx, phoneme in enumerate(segments):
            if (
                idx != 0
                and phoneme in cluster_after_l
                and result[-1] == "l"
            ):
                result[-1] += f".{phoneme}"
            else:
                result.append(phoneme)
        return result

    @staticmethod
    def gaps(seqA: list[str], seqB: list[str]) -> tuple[list[str], list[str]]:
        """Collapse consecutive gaps on ``seqB`` into a single gap per position.

        When two adjacent positions in ``seqB`` are gaps (``"-"``), the matching
        symbol in ``seqA`` is merged into the previous token. Trailing gaps may
        introduce a ``"+"`` marker in ``seqA``.

        Parameters
        ----------
        seqA, seqB:
            Parallel aligned token lists.

        Returns
        -------
        tuple[list[str], list[str]]
            Collapsed alignment pair.

        Notes
        -----
        Used in **CLDF conversion** for WestOldTurkic (``Monogap`` alignments) after
        global pairwise alignment.
        """
        seqA_new, seqB_new = [], []
        for idx, (tokA, tokB) in enumerate(zip(seqA, seqB)):
            if idx != 0 and tokB == "-" and seqB_new[-1] == "-":
                seqA_new[-1] += f".{tokA}"
            else:
                seqA_new.append(tokA)
                seqB_new.append(tokB)
        if seqB_new[-1] == "-":
            seqA_new.insert(-1, "+")
            seqB_new.pop(-1)
        return seqA_new, seqB_new
